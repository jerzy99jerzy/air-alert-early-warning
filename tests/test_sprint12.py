"""Sprint 12: the event stream in the contract, schema v3 (T50, D-024).

The consumer needs history, and `state.json` v2 carried only the current
picture and seven-day counts. These regressions pin the properties D-024
settled, and each one is written so its data can distinguish the correct
implementation from the plausible wrong one.

The measurement behind the sizes: production ingested 27 events in 97 minutes
on 2026-08-11, and the per-message estimate over the corpus gives roughly 800
events a day across all of Ukraine. Both are far above the 200-event cap first
proposed, which is why the cap here is a safety net at 5,000 rather than a
design parameter.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo.report import (
    FEED_WINDOW_S,
    SCHEMA_VERSION,
    STREAM_CAP,
    STREAM_WINDOW_S,
    compose,
    to_contract,
    to_feed,
    write_feed,
)
from mavo.schema import AlertState, AreaRole, Provenance, ThreatEvent, ThreatKind

NOW = datetime(2026, 8, 12, 3, 30, tzinfo=UTC)
WEST = "UA46060000000042587"  # Lvivskyi raion, Lviv oblast, from the shipped register
EAST = "UA14100000000010319"  # Kalmiuskyi raion, Donetsk oblast


def _event(
    code: str,
    minutes_ago: float,
    *,
    state: AlertState = AlertState.ACTIVE,
    role: AreaRole = AreaRole.SUBJECT,
    kind: ThreatKind = ThreatKind.MISSILE,
) -> ThreatEvent:
    stamp = NOW - timedelta(minutes=minutes_ago)
    return ThreatEvent(
        area_id=code,
        state=state,
        ts_source=stamp,
        ts_ingest=stamp,
        source_id="sprint12",
        kind=kind,
        provenance=Provenance.REPORTED,
        role=role,
    )


def test_the_schema_version_is_declared_as_three() -> None:
    """A consumer refusing what it cannot read needs the number to move.

    F75 is the precedent: the CLI announced v1 while the file carried v2, and
    a consumer trusting the announcement would have parsed the wrong shape.
    """
    assert SCHEMA_VERSION == 3
    payload = to_contract(compose([_event(WEST, 1)], as_of=NOW))
    assert payload["v"] == 3


def test_the_short_window_is_twenty_minutes_not_an_hour() -> None:
    """The window length is a decision, so the data has to be able to see it.

    An event nineteen minutes old is in and one twenty-one minutes old is out.
    A test built only from recent events would pass under any window from ten
    minutes to a day, which is the failure class this repository has logged
    four times: the data chosen by the implementation rather than by the
    question. Mutation: widen the window to 3600.
    """
    assert STREAM_WINDOW_S == 1200
    report = compose([_event(WEST, 19), _event(EAST, 21)], as_of=NOW)
    stream = to_contract(report)["events"]
    assert isinstance(stream, dict)
    ids = [item["area_id"] for item in stream["items"]]
    assert WEST in ids, "an event inside the window is missing from the stream"
    assert EAST not in ids, "an event older than the window is in it"


def test_the_window_start_is_published_so_a_reader_can_see_a_gap() -> None:
    """Gap detection on the consumer side needs the window's own left edge.

    A phone asleep for twenty-five minutes wakes to a stream that cannot, by
    itself, be distinguished from a quiet twenty minutes. `window_start` is
    what the page compares against its last successful update, so it is part
    of the contract rather than something the consumer derives.
    Mutation: publish `generated_at` in its place.
    """
    stream = to_contract(compose([_event(WEST, 1)], as_of=NOW))["events"]
    assert isinstance(stream, dict)
    expected = (NOW - timedelta(seconds=STREAM_WINDOW_S)).isoformat(timespec="seconds")
    assert stream["window_start"] == expected
    assert stream["window_s"] == STREAM_WINDOW_S


def test_continuation_events_are_carried_and_not_only_subjects() -> None:
    """The loss this project has already made once, pinned so it cannot recur.

    One message clears an area and lists five others as still under alert:
    one `subject` and five `continuation`. Carrying only subjects would drop
    the five areas that are still dangerous, which is the shape of F82 and of
    the 4,064 continuation areas discarded before T37.
    Mutation: filter the stream to `role == subject`.
    """
    events = [
        _event(WEST, 2, state=AlertState.CLEAR),
        *[
            _event(f"UA0502007000000000{n}", 2, role=AreaRole.CONTINUATION)
            for n in range(5)
        ],
    ]
    stream = to_contract(compose(events, as_of=NOW))["events"]
    assert isinstance(stream, dict)
    roles = [item["role"] for item in stream["items"]]
    assert roles.count("continuation") == 5, "continuation events were dropped"
    assert roles.count("subject") == 1


def test_the_stream_carries_the_east_as_well_as_the_west() -> None:
    """Full visibility is the decision, so a filter would be a defect.

    D-024: the stream is all of Ukraine. The `west` flag is beside each event
    for the consumer to colour by, not a selection made here.
    Mutation: keep only events whose area is western.
    """
    events = [_event(WEST, 3), _event(EAST, 3)]
    stream = to_contract(compose(events, as_of=NOW))["events"]
    assert isinstance(stream, dict)
    assert len(stream["items"]) == 2
    assert {item["west"] for item in stream["items"]} == {True, False}


def test_a_full_window_truncates_the_oldest_and_says_so() -> None:
    """The cap is a safety net, and a net that lies about catching is worse.

    Truncation keeps the newest events, because a reader looking at a feed
    during a mass alert wants the last hour and not the first. `truncated`
    exists so that a bounded window and a quiet one are distinguishable, which
    is this repository's oldest invariant in a new place.
    Mutation: keep the oldest, or drop the flag.
    """
    events = [
        _event(f"UA{n:017d}", minutes_ago=1 + n / 1000) for n in range(STREAM_CAP + 10)
    ]
    stream = to_contract(compose(events, as_of=NOW))["events"]
    assert isinstance(stream, dict)
    assert stream["truncated"] is True
    assert len(stream["items"]) == STREAM_CAP
    newest_kept = max(item["at"] for item in stream["items"])
    oldest_kept = min(item["at"] for item in stream["items"])
    dropped = (NOW - timedelta(minutes=1 + (STREAM_CAP + 9) / 1000)).isoformat(
        timespec="seconds"
    )
    assert newest_kept >= oldest_kept
    assert oldest_kept > dropped, "truncation kept the oldest rather than the newest"


def test_an_empty_window_is_a_window_and_not_a_missing_field() -> None:
    """Nothing happened is an answer, and it has to look like one.

    An absent `events` block and an empty one read identically to a careless
    consumer, so the block is always present and the emptiness is explicit.
    With roughly eleven events per twenty minutes across all of Ukraine, the
    empty case is the common case at four in the morning.
    Mutation: omit the block when there is nothing in it.
    """
    stream = to_contract(compose([_event(WEST, 90)], as_of=NOW))["events"]
    assert isinstance(stream, dict)
    assert stream["items"] == []
    assert stream["truncated"] is False
    assert stream["window_s"] == STREAM_WINDOW_S


def test_the_daily_counts_split_west_from_the_rest_and_add_up() -> None:
    """The context that keeps the short window from being a keyhole.

    A quiet twenty minutes in the west during a night when the east is burning
    is a different fact from a quiet night, and a reader near the border is
    entitled to both. Mutation: count the west twice, or drop the split.
    """
    events = [_event(WEST, 200), _event(EAST, 300), _event(WEST, 5)]
    counts = to_contract(compose(events, as_of=NOW))["counts_24h"]
    assert isinstance(counts, dict)
    assert counts["west"] == 2
    assert counts["rest"] == 1
    assert counts["total"] == 3


def test_the_feed_file_carries_a_day_and_the_same_shape(tmp_path: Path) -> None:
    """`feed.json` is the long window, fetched on demand rather than per cycle.

    Same item shape as the short stream so the consumer has one parser. The
    day-long window is why it is a separate file: at roughly 800 events a day
    it is 18 KiB gzipped, which is cheap once and not cheap every two minutes.
    Mutation: write the twenty-minute window into the feed file.
    """
    assert FEED_WINDOW_S == 86400
    report = compose([_event(WEST, 19), _event(EAST, 600)], as_of=NOW)
    payload = to_feed(report)
    assert payload["v"] == SCHEMA_VERSION
    assert payload["window_s"] == FEED_WINDOW_S
    assert len(payload["items"]) == 2, "the feed window is not a day long"

    written = write_feed(report, tmp_path / "feed.json")
    on_disk = json.loads(written.read_text(encoding="utf-8"))
    assert on_disk["window_s"] == FEED_WINDOW_S
    assert not list(tmp_path.glob(".feed-*.tmp")), "a temporary file was left behind"


def test_the_feed_is_written_beside_the_contract_by_one_composition(
    tmp_path: Path,
) -> None:
    """Two files, one picture. Two compositions could disagree.

    The failure this forecloses is a feed describing a moment the contract
    does not, which a consumer would render as history contradicting the
    present. Mutation: compose twice.
    """
    report = compose([_event(WEST, 1)], as_of=NOW)
    contract = to_contract(report)
    feed = to_feed(report)
    assert feed["generated_at"] == contract["generated_at"]


@pytest.mark.parametrize("field", ["window_start", "window_s", "truncated", "items"])
def test_the_feed_and_the_stream_answer_to_the_same_field_names(field: str) -> None:
    """One vocabulary, so the consumer writes one reader and not two."""
    report = compose([_event(WEST, 1)], as_of=NOW)
    stream = to_contract(report)["events"]
    assert isinstance(stream, dict)
    assert field in stream
    assert field in to_feed(report)


def test_the_publishing_loop_writes_both_files_every_cycle(tmp_path: Path) -> None:
    """The gap this release shipped with, closed.

    `--feed` reached the CLI and `feed_path` reached `publish`'s signature,
    and nothing exercised the loop with it: the one-shot path was tested and
    the continuous one, which is the path production actually runs, was not.
    A feed that stops being refreshed while `state.json` keeps moving is
    exactly the divergence the two-file design has to avoid, and it would have
    looked to a reader like history that stopped at some earlier hour.

    Both files are checked on the second cycle rather than the first, because
    a first-cycle-only write is indistinguishable from a heartbeat that works.
    Mutation: drop the `write_feed` call from the loop, or guard it on the
    picture having changed.
    """
    from mavo.report import publish

    state = tmp_path / "state.json"
    feed = tmp_path / "feed.json"
    outcome = publish(
        lambda: [_event(WEST, 1)],
        state,
        interval_s=0,
        max_cycles=2,
        sleep=lambda _s: None,
        feed_path=feed,
    )
    assert outcome.cycles == 2
    assert state.exists() and feed.exists(), "the loop wrote only one file"

    first = json.loads(feed.read_text(encoding="utf-8"))
    assert first["v"] == SCHEMA_VERSION
    assert first["window_s"] == FEED_WINDOW_S

    # The heartbeat property, on the feed as well: rewritten every cycle even
    # when nothing changed, because a consumer polling a file that stopped
    # being written cannot tell a dead producer from a quiet night.
    feed.unlink()
    publish(
        lambda: [_event(WEST, 1)],
        state,
        interval_s=0,
        max_cycles=1,
        sleep=lambda _s: None,
        feed_path=feed,
    )
    assert feed.exists(), "the feed is not rewritten on an unchanged picture"


def test_the_loop_without_a_feed_path_writes_only_the_contract(
    tmp_path: Path,
) -> None:
    """The negative control for the check above.

    Without it, a loop that wrote the feed unconditionally to a default path
    would pass the previous test and quietly create a file nobody asked for.
    """
    from mavo.report import publish

    state = tmp_path / "state.json"
    publish(
        lambda: [_event(WEST, 1)],
        state,
        interval_s=0,
        max_cycles=1,
        sleep=lambda _s: None,
    )
    assert state.exists()
    assert list(tmp_path.iterdir()) == [state], "the loop wrote an unasked-for file"


def test_a_refusal_says_how_long_it_waited_and_what_was_raised() -> None:
    """T55. The line that eleven refusals were logged through before anybody
    noticed it answers no question.

    A stall that hit the ten-second ceiling and a rejection that bounced in
    twenty milliseconds produced the same journal entry, so the field
    measurement in T39 could rule out a rate limiter and the tunnel but could
    not choose between what was left. The elapsed time and the exception class
    are what separate those hypotheses.

    Mutation: drop either half.
    """
    import urllib.error
    from unittest import mock

    from mavo.errors import SourceUnavailable
    from mavo.transport import UrllibTransport

    transport = UrllibTransport(timeout_s=5.0)
    with mock.patch("urllib.request.urlopen",
                    side_effect=urllib.error.URLError("timed out")):
        try:
            transport.fetch("https://example.invalid/x")
        except SourceUnavailable as refusal:
            message = str(refusal)
        else:  # pragma: no cover - the mock always raises
            raise AssertionError("the transport did not refuse")

    assert "after " in message and "s," in message, message
    assert "URLError" in message, message


def test_the_elapsed_figure_distinguishes_a_fast_failure_from_a_slow_one() -> None:
    """The data has to be able to tell the two apart, or the check is prose.

    A refusal that bounces immediately and one that waits are given different
    durations here, and the assertion is on the difference rather than on the
    presence of a number. Without this, a build that printed a constant would
    pass.
    """
    import itertools
    import urllib.error
    from unittest import mock

    from mavo.errors import SourceUnavailable
    from mavo.transport import UrllibTransport

    def refuse_after(seconds: float) -> str:
        # The stub held exactly two readings until 0.36.0.0, which modelled a
        # fetch that reads the clock twice. F109 reads it again to decide
        # whether a retry still fits inside the deadline, so a two-value
        # iterator now runs out mid-fetch. Unbounded after the first reading:
        # the figure under test is the difference between the start and the
        # refusal, and holding every later reading at `seconds` keeps that
        # difference exactly what the test names.
        clock = itertools.chain([0.0], itertools.repeat(seconds))
        with mock.patch("urllib.request.urlopen",
                        side_effect=urllib.error.URLError("no route")), \
             mock.patch("time.monotonic", side_effect=lambda: next(clock)):
            try:
                UrllibTransport(timeout_s=10.0).fetch("https://example.invalid/x")
            except SourceUnavailable as refusal:
                return str(refusal)
        raise AssertionError("the transport did not refuse")

    assert "after 0.02s" in refuse_after(0.02), refuse_after(0.02)
    assert "after 9.98s" in refuse_after(9.98), refuse_after(9.98)


def test_the_collect_line_bounds_the_whole_attempt(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Measured in the command as well as in the transport.

    A transport that refuses without timing itself would otherwise produce a
    line with no duration at all, and a diagnostic present for one
    implementation and absent for another teaches a reader to stop trusting
    it. Checked by running the command against a transport that refuses,
    rather than by reading the command's source: the first version of this
    test asserted on a string in `cli.py`, which would have passed against a
    build that printed the substring in a comment.

    Mutation: print the transport's message alone.
    """
    from unittest import mock

    from mavo.cli import main
    from mavo.errors import SourceUnavailable

    with mock.patch("mavo.cli.UrllibTransport") as transport:
        transport.return_value.fetch.side_effect = SourceUnavailable(
            "https://t.me/s/x: <urlopen error timed out> [after 9.99s, URLError]"
        )
        assert main(["collect"]) == 3

    line = capsys.readouterr().out
    assert "[UNREACHABLE]" in line
    assert "attempt " in line and "s)" in line, line
    assert "after 9.99s" in line, "the transport's own figure was dropped"


#: Verbatim from the production journal, 2026-08-11, including the line break
#: mid-word that the channel's own markup produces. Copied rather than
#: composed: a fixture written from the parser's expectations is the failure
#: class this repository has logged five times, and this message is the reason
#: the marker exists.
REAL_KAB = (
    "\U0001f7e0   22:05 \u041a\u0410\u0411 "
    "\u043d\u0430\u043f\u0440\u044f\u043c\u043e\u043a "
    "\u041a\u0440\u0430\u043c\u0430\u0442\u043e\u0440\u0441\u044c\u043a\n"
    "\u043a\n"
    " #\u0414\u043e\u043d\u0435\u0446\u044c\u043a\u0430_\u043e\u0431\u043b\u0430\u0441\u0442\u044c"
)


def test_a_direction_announcement_is_a_declaration() -> None:
    """The message that went unparsed on every poll for a day.

    The channel names a munition and a direction and no declaration word, so
    it carried a kind marker, failed the declare test, carried no alert state,
    and was counted as unparsed roughly seven hundred times before anybody
    read the journal. Mutation: remove the marker.
    """
    from mavo.schema import KindState, ThreatKind
    from mavo.sources.telegram import classify_kind_message

    declarations = classify_kind_message(REAL_KAB)
    assert len(declarations) == 1, declarations
    _area, oblast, kind, state = declarations[0]
    assert oblast == "donetsk"
    assert kind is ThreatKind.GLIDE_BOMB
    assert state is KindState.DECLARED


def test_a_lift_containing_the_new_marker_still_reads_as_a_lift() -> None:
    """The ordering T46 requires re-checking rather than assuming.

    `lifting` is evaluated first and the declare test runs only under
    `not lifting`, so widening the declare table cannot turn a lift into a
    fresh declaration. That inversion is the risk this file has warned about
    twice, and this is the check that keeps the warning honest.
    Mutation: evaluate the declare test before the lift test.
    """
    from mavo.schema import KindState
    from mavo.sources.telegram import classify_kind_message

    lift = ("\u0412\u0456\u0434\u0431\u0456\u0439 \u0437\u0430\u0433\u0440\u043e\u0437\u0438 "
            "\u041a\u0410\u0411 \u043d\u0430\u043f\u0440\u044f\u043c\u043e\u043a "
            "\u041a\u0440\u0430\u043c\u0430\u0442\u043e\u0440\u0441\u044c\u043a "
            "#\u0414\u043e\u043d\u0435\u0446\u044c\u043a\u0430_\u043e\u0431\u043b\u0430\u0441\u0442\u044c")
    declarations = classify_kind_message(lift)
    assert declarations, "the lift resolved to nothing at all"
    assert declarations[0][3] is KindState.LIFTED


def test_the_marker_alone_declares_nothing() -> None:
    """Breadth is bounded on the other side: a declaration needs a declare
    marker **and** exactly one kind marker. A direction with no munition named
    is a message this cannot act on, and guessing would be the collapse the
    whole file refuses. Mutation: drop the one-kind requirement."""
    from mavo.sources.telegram import classify_kind_message

    vague = ("\u041d\u0430\u043f\u0440\u044f\u043c\u043e\u043a "
             "\u041a\u0440\u0430\u043c\u0430\u0442\u043e\u0440\u0441\u044c\u043a "
             "#\u0414\u043e\u043d\u0435\u0446\u044c\u043a\u0430_\u043e\u0431\u043b\u0430\u0441\u0442\u044c")
    assert classify_kind_message(vague) == ()


def test_a_message_with_an_alert_state_is_still_an_alert() -> None:
    """A message carrying an alert state is an alert, whatever else it
    mentions. The new marker must not steal one. Mutation: move the state
    check after the declare test."""
    from mavo.sources.telegram import classify_kind_message

    both = ("\u041f\u043e\u0432\u0456\u0442\u0440\u044f\u043d\u0430 "
            "\u0442\u0440\u0438\u0432\u043e\u0433\u0430 \u041a\u0410\u0411 "
            "\u043d\u0430\u043f\u0440\u044f\u043c\u043e\u043a "
            "\u041a\u0440\u0430\u043c\u0430\u0442\u043e\u0440\u0441\u044c\u043a "
            "#\u0414\u043e\u043d\u0435\u0446\u044c\u043a\u0430_\u043e\u0431\u043b\u0430\u0441\u0442\u044c")
    assert classify_kind_message(both) == ()
