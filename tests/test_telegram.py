"""The Telegram adapter: parsing, classification, and refusing to be an outage."""

from __future__ import annotations

import pytest

from mavo.areas import AreaTable
from mavo.errors import SourceUnavailable
from mavo.schema import AlertState, ThreatKind, ThreatSource
from mavo.sources.telegram import (
    TelegramChannelSource,
    classify,
    classify_state,
    probe,
)
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


# Rewritten at 0.22.0.0, and the rewrite is part of F90. These three messages
# used to be written as oblast prose - `Львівська область<br/>Повітряна
# тривога` - with no hashtag, which is the shape the sprint-6 oblast-stem dict
# could read and **not a shape this channel emits**: 99.34% of messages carry a
# `#Name_unit` tag and an oblast name appears in 515 of 69,676 occurrences
# (`docs/CHANNEL.md`). The fixture was written to match the implementation, so
# the suite measured the parser against its own assumption and went on passing
# while the live path parsed nothing - the same pattern as F85's cutoff fixture
# and F82's sample. These are the live shape: subject in prose, area in the tag.
LVIV = "UA46060000000042587"
LUTSK = "UA07080000000034745"

PAGE = "".join(
    [
        _message(
            101,
            "2026-09-01T21:04:00+00:00",
            "🔴 Повітряна тривога в Львівський район. Ракетна небезпека"
            "<br/>#Львівський_район",
        ),
        _message(
            102,
            "2026-09-01T21:11:00+00:00",
            "🟢 Відбій тривоги в Луцький район<br/>#Луцький_район",
        ),
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
    assert active[0].area_id == LVIV
    assert active[0].kind is ThreatKind.MISSILE


def test_parses_an_all_clear_as_clear_not_as_absence() -> None:
    (clear,) = [event for event in _source().poll() if event.state is AlertState.CLEAR]
    assert clear.area_id == LUTSK


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


def test_every_real_message_resolves_its_area_against_the_register() -> None:
    """F23 closed, and F90 is why it stayed open on paper for two sprints.

    The pin this replaces asserted 0 of 20 and carried the message "update this
    pin and close F23", built to flip the moment the gazetteer landed. The
    gazetteer landed in sprint 7 and it did not flip, because both this test
    and `probe` called `classify` without an area table, and the None default
    selected the superseded oblast-stem dict. The tripwire was wired to the
    path the repair did not touch.

    Measured against the same twenty real messages that have been in this
    repository since sprint 4: **20 of 20 carry a tag that resolves to a unique
    register code.** Mutation: pass `None` instead of the table; this returns
    to zero, which is the defect.
    """
    table = AreaTable.from_csv()
    resolved = sum(bool(table.resolve_all(message)[0]) for message in _real_messages())
    assert resolved == 20, "the register table no longer resolves every real tag"


def test_the_live_path_classifies_the_alert_messages_it_is_given() -> None:
    """The number the README quoted as 0 of 20, measured on the shipped table.

    **15 of 20**, and the five that produce no alert mention are not misses:
    they carry no alert-state marker because they are threat declarations,
    which belong to the kind stream. 15 alert plus 5 declaration is 20, and the
    two sets are disjoint - the same 15 and 5 the state-marker and kind-marker
    pins have carried separately since sprint 4. Mutation: drop the table
    argument.
    """
    table = AreaTable.from_csv()
    messages = _real_messages()
    classified = sum(classify(message, table) is not None for message in messages)
    assert classified == 15
    declarations = [m for m in messages if classify(m, table) is None]
    assert len(declarations) == 5
    assert all(classify_state(message) is None for message in declarations), (
        "a message with no alert mention must be a declaration, not a lost alert"
    )


def test_probe_uses_the_register_table_and_not_the_superseded_dict() -> None:
    """F90. `probe` is the whole live path, and it built its source untabled.

    `mavo collect` is the one command that touches the channel, it goes through
    `probe`, and `probe` constructed `TelegramChannelSource(transport, url)`
    with no areas - so the 127-row register table shipped in sprint 7 was never
    reachable from the live path, and every live poll ran the pre-sprint-7
    oblast dict. The README told readers to expect almost nothing to parse and
    was right about the symptom for the wrong reason: the table was correct and
    the call was not.

    Mutation: drop the table from `probe`'s construction; `parsed` returns to 0.
    """
    page = "".join(
        f'<div class="tgme_widget_message" data-post="air_alert_ua/{i}">'
        f'{TXT}\U0001f534 Повітряна тривога в Самбірський район'
        f" #Самбірський_район</div>"
        f'<time datetime="2026-08-11T10:0{i}:00+00:00"></time></div>'
        for i in range(3)
    )
    report, _ = probe(StubTransport(page))
    assert report.messages == 3
    assert report.parsed == 3, "the live path must reach the register table"
    assert report.unparsed_count == 0


def test_a_partial_all_clear_is_not_classified_as_clear() -> None:
    # F26. A yellow message says the all-clear and that the alert continues.
    # Reading it as CLEAR would be actively wrong; today it is not read at all,
    # which is wrong but not dangerous. The distinction is the whole point.
    # Amended at 0.22.0.0. The claim "it is not read at all" was true of the
    # oblast dict this test was written against and stopped being true in
    # sprint 7, unnoticed because the assertion called the untabled path (F90).
    # The area resolves and the contradiction is now stated rather than
    # dropped: cleared as the subject, listed as still running, so
    # PARTIAL_CLEAR. That is the F26 outcome the entry asked for - a stated
    # contradiction rather than a confident wrong reading.
    partial = next(m for m in _real_messages() if "ще триває" in m)
    resolved = classify(partial, AreaTable.from_csv())
    assert resolved is not None
    assert resolved[1] is AlertState.PARTIAL_CLEAR


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
    page = _message(
        301, "2026-09-01T21:04:00+00:00",
        "🔴 Повітряна тривога в Львівський район #Львівський_район",
    ) + _message(
        302, "2026-09-01T21:11:00+00:00",
        "🔴 Повітряна тривога в Луцький район #Луцький_район",
    )
    events = {event.area_id: event.ts_source.isoformat() for event in _source(page).poll()}
    assert events == {
        LVIV: "2026-09-01T21:04:00+00:00",
        LUTSK: "2026-09-01T21:11:00+00:00",
    }


def test_f50_pairing_survives_the_inverted_order_too() -> None:
    # Block-scoped search does not care where inside the block the footer sits.
    # The guard is the block boundary, not the internal order.
    inverted = (
        '<div class="tgme_widget_message" data-post="air_alert_ua/401">'
        '<time datetime="2026-09-01T21:04:00+00:00"></time>'
        f"{TXT}🔴 Повітряна тривога в Львівський район #Львівський_район</div></div>"
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
