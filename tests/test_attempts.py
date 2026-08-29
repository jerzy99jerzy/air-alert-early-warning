"""T66: the three counts, and the cases where two of them look alike.

Every assertion here exists because a simpler implementation passes without
it. The gap detector is the part worth attacking: a version that counts every
interval as a gap, one that counts none, and one that quietly treats the
window edges as covered all produce a plausible number.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import attempts as attempts_tool  # noqa: E402

from mavo.store import EventStore  # noqa: E402  isort: skip

FEED = "channel"
URL = "https://t.me/s/air_alert_ua"
T0 = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)
CADENCE = 33.0


def _store(tmp_path: Path) -> EventStore:
    return EventStore(tmp_path / "attempts.sqlite3")


def _poll(store: EventStore, offset_s: float, *, refused: bool = False,
          elapsed: float | None = 0.31) -> None:
    when = T0 + timedelta(seconds=offset_s)
    if refused:
        store.record_refusal(FEED, URL, when, "timed out", elapsed)
    else:
        store.record_read(FEED, URL, when, 20, 0, elapsed)


def test_a_run_of_polls_at_cadence_holds_no_gap(tmp_path: Path) -> None:
    """The ordinary case must be empty, or every later count is noise."""
    store = _store(tmp_path)
    for index in range(20):
        _poll(store, CADENCE * index)
    measured = attempts_tool.measure(store, FEED, CADENCE)
    assert measured.attempts == 20
    assert measured.refusals == 0
    assert measured.gaps == (), "polls at the cadence are not a stretch with neither"
    assert measured.unobserved_s == 0.0


def test_a_missed_stretch_is_reported_and_bounded(tmp_path: Path) -> None:
    """A stretch with no attempt in it is the quantity nothing else could see.

    Ten minutes of silence between two polls is not a quiet channel and not a
    refusal: it is time in which this collector produced no evidence of any
    kind, and it is the term `docs/CHANNEL.md` 8a needs to attribute a latency
    tail.
    """
    store = _store(tmp_path)
    _poll(store, 0)
    _poll(store, CADENCE)
    _poll(store, CADENCE + 600)
    _poll(store, CADENCE + 633)
    measured = attempts_tool.measure(store, FEED, CADENCE)
    assert len(measured.gaps) == 1
    assert measured.gaps[0].seconds == pytest.approx(600.0)
    assert measured.unobserved_s == pytest.approx(600.0)
    assert measured.attempts == 4, "a gap does not change how many polls happened"


def test_jitter_within_the_threshold_is_not_a_gap(tmp_path: Path) -> None:
    """`RandomizedDelaySec` must not read as blindness.

    Without this the previous assertion passes against a detector triggering
    at one cadence, which on the production timer would report a gap on every
    poll that drifted by a second.
    """
    store = _store(tmp_path)
    _poll(store, 0)
    _poll(store, CADENCE + 5)
    _poll(store, 2 * CADENCE + 8)
    assert attempts_tool.measure(store, FEED, CADENCE).gaps == ()


def test_a_refusal_is_an_attempt_and_not_a_gap(tmp_path: Path) -> None:
    """The three counts do not overlap, and this is where two of them meet.

    A poll that refused produced evidence: it says the collector was alive and
    the far end was not reachable. Counting it as unobserved would merge "we
    tried and were refused" with "we were not there", which is the whole
    distinction this instrument exists for.
    """
    store = _store(tmp_path)
    _poll(store, 0)
    _poll(store, CADENCE, refused=True)
    _poll(store, 2 * CADENCE)
    measured = attempts_tool.measure(store, FEED, CADENCE)
    assert (measured.attempts, measured.refusals, measured.reads) == (3, 1, 2)
    assert measured.gaps == ()
    assert measured.refusal_share == pytest.approx(1 / 3)


def test_an_empty_window_reports_unknown_rather_than_health(tmp_path: Path) -> None:
    """No rows is not a clean run.

    A refusal rate of 0% over zero attempts is the shape of this project's
    founding defect: an instrument that reports the flattering value when it
    has measured nothing.
    """
    store = _store(tmp_path)
    measured = attempts_tool.measure(store, FEED, CADENCE)
    assert measured.attempts == 0
    assert measured.refusal_share is None
    rendered = measured.render()
    assert "refusals=unknown" in rendered
    assert "0.0%" not in rendered and "0%" not in rendered


def test_the_window_edges_are_unknown_not_covered(tmp_path: Path) -> None:
    """Whether the collector ran before the first row is outside this table."""
    store = _store(tmp_path)
    _poll(store, 300)
    _poll(store, 300 + CADENCE)
    measured = attempts_tool.measure(
        store,
        FEED,
        CADENCE,
        since=T0,
        until=T0 + timedelta(seconds=900),
    )
    assert measured.unknown_head_s == pytest.approx(300.0)
    assert measured.unknown_tail_s == pytest.approx(900 - 300 - CADENCE)
    assert measured.unobserved_s == 0.0, (
        "an unclassified edge is not a measured stretch of blindness; adding "
        "them would report as measured a quantity nobody measured"
    )
    assert "outside this table, not inside it" in measured.render(), (
        "the edge seconds are known; what happened in them is not, and the "
        "line has to say which of the two it is reporting"
    )


def test_a_window_without_bounds_reports_its_edges_as_unknown(tmp_path: Path) -> None:
    """No `--since` means the head is unknown, not zero."""
    store = _store(tmp_path)
    _poll(store, 0)
    measured = attempts_tool.measure(store, FEED, CADENCE)
    assert measured.unknown_head_s is None
    assert measured.unknown_tail_s is None
    assert "before the first attempt unknown" in measured.render()


def test_an_untimed_attempt_is_excluded_and_counted(tmp_path: Path) -> None:
    """A row written before `elapsed_s` existed is not a fetch that took no time."""
    store = _store(tmp_path)
    _poll(store, 0, elapsed=None)
    _poll(store, CADENCE, elapsed=0.5)
    measured = attempts_tool.measure(store, FEED, CADENCE)
    assert measured.durations == (0.5,)
    assert measured.untimed == 1
    assert "untimed=1" in measured.render()


def test_the_window_filters_by_the_bounds_it_was_given(tmp_path: Path) -> None:
    """`since` inclusive, `until` exclusive, so adjacent windows partition."""
    store = _store(tmp_path)
    for index in range(4):
        _poll(store, CADENCE * index)
    early = attempts_tool.measure(
        store, FEED, CADENCE, since=T0, until=T0 + timedelta(seconds=2 * CADENCE)
    )
    late = attempts_tool.measure(
        store, FEED, CADENCE, since=T0 + timedelta(seconds=2 * CADENCE)
    )
    assert (early.attempts, late.attempts) == (2, 2)


def test_the_cadence_is_required_rather_than_inferred(tmp_path: Path) -> None:
    """The command refuses to run without it.

    Inferring the interval from the median gap would calibrate the detector on
    the data it is judging, so the argument is required and a caller who omits
    it gets an error rather than a default.
    """
    store = _store(tmp_path)
    _poll(store, 0)
    with pytest.raises(SystemExit):
        attempts_tool.main(["--store", str(store.path)])
    assert attempts_tool.main(
        ["--store", str(store.path), "--cadence-s", "33"]
    ) == 0
    assert attempts_tool.main(
        ["--store", str(store.path), "--cadence-s", "0"]
    ) == 2


def test_a_missing_store_is_refused_rather_than_created(tmp_path: Path) -> None:
    """Opening a store would create an empty one, which reads as a dead collector."""
    assert attempts_tool.main(
        ["--store", str(tmp_path / "absent.sqlite3"), "--cadence-s", "33"]
    ) == 2
