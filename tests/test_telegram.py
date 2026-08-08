"""The Telegram adapter: parsing, classification, and refusing to be an outage."""

from __future__ import annotations

import pytest

from mavo.errors import SourceUnavailable
from mavo.schema import AlertState, ThreatKind, ThreatSource
from mavo.sources.telegram import TelegramChannelSource, classify, probe
from mavo.transport import FailingTransport, StubTransport

TXT = '<div class="tgme_widget_message_text js-message_text">'


def _message(when: str, text: str) -> str:
    """One channel message in the shape the page serves it."""
    return f'<time datetime="{when}"></time>{TXT}{text}</div>'


PAGE = "".join(
    [
        _message(
            "2026-09-01T21:04:00+00:00",
            "🔴 Львівська область<br/>Повітряна тривога. Ракетна небезпека",
        ),
        _message("2026-09-01T21:11:00+00:00", "🟢 Волинська область<br/>Відбій тривоги"),
        _message("2026-09-01T21:20:00+00:00", "Підтримати проєкт можна тут"),
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
        _message("not-a-date", "Львів Повітряна тривога"),
        _message("2026-09-01T21:04:00+00:00", "А" * 50_000),
        _message("2026-09-01T21:04:00+00:00", "\x00\xff binary"),
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


def test_means_markers_match_four_of_twenty_real_messages() -> None:
    # F35. The 2026-08-08 measurement pinned the state layer (15) and the area
    # layer (0) as assertions but left the means layer (4) in prose, so two of
    # three layers could not drift quietly and one could. Pinned like the
    # others: this flips when the marker table is redesigned, deliberately.
    from mavo.sources.telegram import KIND_MARKERS

    matched = sum(
        any(marker in message.lower() for marker in KIND_MARKERS)
        for message in _real_messages()
    )
    assert matched == 4, "means table changed; update this pin alongside F23"
