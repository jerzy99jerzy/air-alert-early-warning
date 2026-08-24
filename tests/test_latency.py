"""T40's instrument, tested on stores this file builds.

The measurement itself is a week of a real host and cannot be tested. What can
be tested is every way the instrument could report a number that reads well and
is not true: interpolating a percentile nobody observed, tidying a negative lag
away, calling a window a measurement when it is an afternoon, or presenting the
lag as the channel's own when a third of it may be our own poll interval.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tools.latency import MINIMUM_DAYS, _quantile, _read_lags, _summary, main

SCHEMA = """
CREATE TABLE events (content_hash TEXT, area_id TEXT, state TEXT,
                     ts_source TEXT NOT NULL, ts_ingest TEXT NOT NULL);
CREATE TABLE kinds (content_hash TEXT, area_id TEXT, kind TEXT,
                    ts_source TEXT NOT NULL, ts_ingest TEXT NOT NULL);
"""

BASE = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


def _store(tmp_path: Path, lags_s: list[float], *, span_days: float = 8.0,
           table: str = "events", naive: bool = False) -> Path:
    path = tmp_path / "store.sqlite3"
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.executescript(SCHEMA)
        step = timedelta(days=span_days / max(1, len(lags_s) - 1)) \
            if len(lags_s) > 1 else timedelta(0)
        for i, lag in enumerate(lags_s):
            source = BASE + step * i
            ingest = source + timedelta(seconds=lag)
            a, b = source.isoformat(), ingest.isoformat()
            if naive:
                a, b = source.replace(tzinfo=None).isoformat(), b
            conn.execute(
                f"INSERT INTO {table} VALUES ('h', 'UA46', 's', ?, ?)",  # noqa: S608
                (a, b))
    return path


def test_a_percentile_is_an_observation_and_not_an_average_of_two():
    """Nearest rank, no interpolation: every printed figure was measured."""
    assert _quantile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.0
    assert _quantile([1.0, 2.0, 3.0, 4.0], 0.9) == 4.0
    assert _quantile([5.0], 0.99) == 5.0


def test_a_negative_lag_is_reported_rather_than_clamped(tmp_path):
    """A post received before it was posted means the clocks disagree. That is
    a finding about the measurement, and hiding it would make the distribution
    look tidier than the data underneath it."""
    store = _store(tmp_path, [10.0, 12.0, -4.0, 11.0])
    forward, negative, _, _ = _read_lags(store)
    assert negative == [-4.0]
    assert -4.0 not in forward
    summary = _summary(forward, negative, BASE, BASE + timedelta(days=8), 30.0)
    assert summary["negative_lags"] == 1
    assert summary["most_negative_s"] == -4.0


def test_a_naive_timestamp_is_dropped_rather_than_assumed_to_be_utc(tmp_path):
    """F61's class. A naive timestamp is not a value in this repository, and
    guessing its zone would silently manufacture a lag of hours."""
    store = _store(tmp_path, [10.0, 11.0], naive=True)
    with pytest.raises(SystemExit) as refused:
        _read_lags(store)
    # Not an empty distribution, which would print as a store with no traffic.
    assert "no timestamped rows" in str(refused.value)


def test_both_streams_are_read(tmp_path):
    store = _store(tmp_path, [10.0, 20.0], table="kinds")
    forward, _, _, _ = _read_lags(store)
    assert sorted(forward) == [10.0, 20.0]


def test_a_short_window_is_refused_by_default(tmp_path, capsys):
    """T40 asks for a week. An afternoon with percentiles on it is an anecdote
    wearing the clothes of a measurement."""
    store = _store(tmp_path, [10.0] * 20, span_days=0.5)
    assert main(["--store", str(store)]) == 2
    assert "anecdote" in capsys.readouterr().err


def test_a_short_window_prints_when_asked_and_says_it_is_not_a_measurement(
        tmp_path, capsys):
    store = _store(tmp_path, [10.0] * 20, span_days=0.5)
    assert main(["--store", str(store), "--allow-short"]) == 0
    out = capsys.readouterr().out
    assert "NOT A T40 MEASUREMENT" in out


def test_a_full_window_reports_the_three_figures_the_acceptance_names(
        tmp_path, capsys):
    store = _store(tmp_path, [float(x) for x in range(1, 101)], span_days=9.0)
    assert main(["--store", str(store)]) == 0
    out = capsys.readouterr().out
    assert "median" in out and "p90" in out and "max" in out
    assert "50.0 s" in out and "90.0 s" in out and "100.0 s" in out


def test_the_poll_interval_is_named_and_the_upstream_is_only_bounded(
        tmp_path, capsys):
    """The lag is ours plus theirs. A tool that called it the channel's latency
    would be asserting a decomposition it cannot perform."""
    store = _store(tmp_path, [40.0] * 30, span_days=9.0)
    main(["--store", str(store), "--interval-s", "30"])
    out = capsys.readouterr().out
    assert "poll interval 30.0 s" in out
    assert "upper bound" in out and "[inference]" in out
    assert "channel latency" not in out.lower()


def test_the_upper_bound_subtracts_half_an_interval_and_never_goes_negative(
        tmp_path):
    forward = [40.0] * 10
    s = _summary(forward, [], BASE, BASE + timedelta(days=8), 30.0)
    assert s["upstream_upper_bound_s"] == 25.0
    s2 = _summary([2.0] * 10, [], BASE, BASE + timedelta(days=8), 30.0)
    assert s2["upstream_upper_bound_s"] == 0.0


def test_the_window_test_uses_the_acceptance_figure(tmp_path):
    s = _summary([1.0], [], BASE, BASE + timedelta(days=MINIMUM_DAYS), 30.0)
    assert s["meets_t40_window"] is True
    s2 = _summary([1.0], [], BASE, BASE + timedelta(days=MINIMUM_DAYS - 0.1), 30.0)
    assert s2["meets_t40_window"] is False


def test_a_missing_store_is_a_refusal_and_not_an_empty_report(tmp_path):
    with pytest.raises(SystemExit):
        _read_lags(tmp_path / "absent.sqlite3")
