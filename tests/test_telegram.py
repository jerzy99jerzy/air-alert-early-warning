"""The Telegram adapter: parsing, classification, and refusing to be an outage."""

from __future__ import annotations

import pytest

from mavo.errors import SourceUnavailable
from mavo.schema import AlertState, ThreatKind, ThreatSource
from mavo.sources.telegram import TelegramChannelSource, classify, probe
from mavo.transport import FailingTransport, StubTransport

TXT = '<div class="tgme_widget_message_text js-message_text">'


def _message(post_id: int, when: str, text: str) -> str:
    """One channel message in the shape the live page serves it.

    The text div comes first and the ``<time>`` element sits in the footer,
    after it. The old helper had the two inverted, which is the order the old
    page-wide regex required, so the suite measured the parser against its own
    assumption and the one-message timestamp shift on live pages was invisible
    (F50). This helper is the live order; ``test_f50`` holds the pairing.
    """
    return (
        f'<div class="tgme_widget_message" data-post="air_alert_ua/{post_id}">'
        f"{TXT}{text}</div>"
        f'<a class="tgme_widget_message_date"><time datetime="{when}"></time></a></div>'
    )


PAGE = "".join(
    [
        _message(
            101,
            "2026-09-01T21:04:00+00:00",
            "🔴 Львівська область<br/>Повітряна тривога. Ракетна небезпека",
        ),
        _message(102, "2026-09-01T21:11:00+00:00", "🟢 Волинська область<br/>Відбій тривоги"),
        _message(103, "2026-09-01T21:20:00+00:00", "Підтримати проєкт можна тут"),
    ]
)


def _source(body: str = PAGE) -> TelegramChannelSource:
    return TelegramChannelSource(StubTransport(body))


def test_adapter_satisfies_the_protocol() -> None:
    assert isinstance(_source(), ThreatSource)


def test_parses_an_active_alert_with_its_means() -> None:
    events = list(_source().poll())
    active = [event for event in events if event.state is AlertState.ACTIVE]
    assert len(active) == 1
    assert active[0].area_id == "lviv"
    assert active[0].kind is ThreatKind.MISSILE


def test_parses_an_all_clear_as_clear_not_as_absence() -> None:
    (clear,) = [event for event in _source().poll() if event.state is AlertState.CLEAR]
    assert clear.area_id == "volyn"


def test_unclassified_messages_are_counted_not_dropped() -> None:
    source = _source()
    source.poll()
    assert source.report.messages == 3
    assert source.report.parsed == 2
    assert source.report.unparsed_count == 1


def test_latency_is_recorded_because_it_eats_the_budget() -> None:
    report, elapsed = probe(StubTransport(PAGE))
    assert report.parsed == 2
    assert elapsed >= 0.0


@pytest.mark.parametrize(
    "body",
    [
        "",
        "not html at all",
        f"{TXT}no time element</div>",
        _message(201, "not-a-date", "Львів Повітряна тривога"),
        _message(202, "2026-09-01T21:04:00+00:00", "А" * 50_000),
        _message(203, "2026-09-01T21:04:00+00:00", "\x00\xff binary"),
    ],
)
def test_hostile_bodies_do_not_raise(body: str) -> None:
    # MT7. A parser that raises turns a hostile string into an outage during
    # exactly the window that matters.
    source = _source(body)
    assert source.poll() is not None


def test_an_unreachable_source_refuses_rather_than_returning_nothing() -> None:
    # Distinct from a source that is reachable and quiet. Conflating the two is
    # the same defect as UNKNOWN resolving to CLEAR, one layer down.
    with pytest.raises(SourceUnavailable):
        TelegramChannelSource(FailingTransport()).poll()


def test_classify_returns_none_rather_than_a_default() -> None:
    assert classify("Львівська область") is None
    assert classify("Повітряна тривога") is None
    assert classify("") is None


def test_repeated_polls_produce_identical_content_hashes() -> None:
    first = {event.content_hash() for event in _source().poll()}
    second = {event.content_hash() for event in _source().poll()}
    assert first == second


# --- Measured against real channel content, 2026-08-08 -----------------------

def _real_messages() -> list[str]:
    from tests.fixtures.real_messages import MESSAGES

    return list(MESSAGES)


def test_state_markers_are_correct_against_real_messages() -> None:
    # Measured 15/20. The five misses are threat-type messages, a different
    # class of message rather than a failure of these markers.
    from mavo.sources.telegram import CLEAR_MARKERS, START_MARKERS

    matched = sum(
        any(marker in message.lower() for marker in START_MARKERS + CLEAR_MARKERS)
        for message in _real_messages()
    )
    assert matched == 15


def test_area_table_fails_totally_against_real_messages() -> None:
    # F23, pinned as a measurement rather than described in prose. The channel
    # names raions and hromadas, never oblasts, so an oblast-keyed table cannot
    # match by construction. This assertion flips when the gazetteer lands, and
    # flipping it is the point: it will not be possible to fix F23 quietly.
    from mavo.sources.telegram import AREAS

    matched = sum(
        any(pattern in message.lower() for pattern in AREAS)
        for message in _real_messages()
    )
    assert matched == 0, "area table now matches; update this pin and close F23"


def test_classifier_hit_rate_against_real_messages_is_zero() -> None:
    classified = sum(classify(message) is not None for message in _real_messages())
    assert classified == 0, "classifier now matches; update this pin and close F23"


def test_a_partial_all_clear_is_not_classified_as_clear() -> None:
    # F26. A yellow message says the all-clear and that the alert continues.
    # Reading it as CLEAR would be actively wrong; today it is not read at all,
    # which is wrong but not dangerous. The distinction is the whole point.
    partial = next(m for m in _real_messages() if "ще триває" in m)
    assert classify(partial) is None


def test_means_markers_match_five_of_twenty_real_messages() -> None:
    """The means layer, pinned so a table change cannot pass quietly.

    F35. The 2026-08-08 measurement pinned the state layer (15) and the area
    layer (0) as assertions and left the means layer in prose, so two of three
    layers could not drift quietly and one could. Pinned like the others: this
    flips when the marker table is redesigned, deliberately.

    **It flipped at 0.19.3.0, from four to five, and the flip is the first
    measurement of the F71 repair against real channel text.** The message it
    gained is `Атака дронів-камікадзе типу Молнія`, which the old table
    refused because `дрон` was absent while its declare marker matched: one of
    the four failure modes F71 recorded, appearing in the twenty messages that
    have been in this repository since sprint 4. A second message,
    `Загроза керованих авіабомб`, now matches on `авіабомб` as well as `каб`,
    which changes no outcome and is recorded so the count is explicable.

    Five of twenty is not a coverage claim. Twenty messages was never a sample
    for that, and the measurement that is one is T45.
    """
    from mavo.sources.telegram import KIND_MARKERS

    matched = sum(
        any(marker in message.lower() for marker in KIND_MARKERS)
        for message in _real_messages()
    )
    assert matched == 5, "means table changed; update this pin alongside F23"


# --- F50, the pairing --------------------------------------------------------

def test_f50_footer_time_pairs_with_its_own_message() -> None:
    """Two messages in the live order must each carry their own timestamp.

    The page-wide regex this replaces paired message N's time with message
    N+1's text, dropped the first text on the page, and orphaned the last time.
    The assertion is exact: both events present, each with the timestamp its
    own footer carries, none shifted onto a neighbour.
    """
    page = _message(301, "2026-09-01T21:04:00+00:00", "🔴 Львівська область Повітряна тривога") \
        + _message(302, "2026-09-01T21:11:00+00:00", "🔴 Волинська область Повітряна тривога")
    events = {event.area_id: event.ts_source.isoformat() for event in _source(page).poll()}
    assert events == {
        "lviv": "2026-09-01T21:04:00+00:00",
        "volyn": "2026-09-01T21:11:00+00:00",
    }


def test_f50_pairing_survives_the_inverted_order_too() -> None:
    # Block-scoped search does not care where inside the block the footer sits.
    # The guard is the block boundary, not the internal order.
    inverted = (
        '<div class="tgme_widget_message" data-post="air_alert_ua/401">'
        '<time datetime="2026-09-01T21:04:00+00:00"></time>'
        f"{TXT}🔴 Львівська область Повітряна тривога</div></div>"
    )
    (event,) = _source(inverted).poll()
    assert event.ts_source.isoformat() == "2026-09-01T21:04:00+00:00"


def test_f61_a_naive_content_timestamp_never_becomes_an_event(tmp_path) -> None:
    """F61. A valid-but-offsetless datetime in content must die at the parser.

    ``datetime="2026-09-01T21:00:00"`` parses cleanly and produces a naive
    ``ts_source``. The store refuses naive timestamps (F52), so an event built
    from one converts hostile or malformed *content* into an *outage* one layer
    up, at ``append`` - exactly the composition the never-raise contract exists
    to prevent. A9 covered ``datetime="nonsense"``; this is the case that parses.
    """
    from pathlib import Path

    from mavo.store import EventStore

    body = _message(950, "2026-09-01T21:00:00", "Повітряна тривога у Львівській області")
    source = TelegramChannelSource(StubTransport(body))
    events = source.poll()
    assert all(
        event.ts_source.tzinfo is not None for event in events
    ), "an event with a naive ts_source left poll(); the store will refuse it"
    # The composition itself: whatever poll returns, the store accepts.
    EventStore(Path(tmp_path) / "f61.sqlite").append(events)
    # The message is not silently dropped either: it is counted as unparsed.
    assert source.report.messages == 1
    assert source.report.parsed == 0
    assert source.report.unparsed_count == 1
