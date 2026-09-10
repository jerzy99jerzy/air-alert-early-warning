"""T40's instrument, tested on stores this file builds.

The measurement itself is a week of a real host and cannot be tested. What can
be tested is every way the instrument could report a number that reads well and
is not true: interpolating a percentile nobody observed, tidying a negative lag
away, calling a window a measurement when it is an afternoon, presenting the
lag as the channel's own when a third of it may be our own poll interval, or
pooling two feeds that measure different things into one median.

**The schema below is the store's, and at 0.53.5.1 it was not.** This file
created a table called `kinds`; `mavo/store.py` has only ever created
`kind_events`. The instrument read `kinds`, missed it on every real store, and
swallowed the miss as backwards compatibility - and these regressions could not
see any of it, because the fixture had been written to match the code rather
than the schema the code claims to read. F154, and another instance of the
class this repository has logged four times. The names here are now taken from
`mavo/store.py`, and `test_the_schema_here_is_the_stores_schema` fails if they
drift again.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo.latency import (
    MINIMUM_DAYS,
    TABLES,
    SourceLags,
    _quantile,
    _read_lags,
    _summary,
    _summary_of,
    main,
)
from mavo.store import EventStore

SCHEMA = """
CREATE TABLE events (content_hash TEXT, area_id TEXT, state TEXT,
                     ts_source TEXT NOT NULL, ts_ingest TEXT NOT NULL,
                     source_id TEXT NOT NULL);
CREATE TABLE kind_events (content_hash TEXT, area_id TEXT, kind TEXT,
                          ts_source TEXT NOT NULL, ts_ingest TEXT NOT NULL,
                          source_id TEXT NOT NULL);
"""

BASE = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


def _store(tmp_path: Path, lags_s: list[float], *, span_days: float = 8.0,
           table: str = "events", naive: bool = False,
           source: str = "telegram", path: Path | None = None) -> Path:
    store = path if path is not None else tmp_path / "store.sqlite3"
    fresh = not store.exists()
    with closing(sqlite3.connect(store)) as conn, conn:
        if fresh:
            conn.executescript(SCHEMA)
        step = timedelta(days=span_days / max(1, len(lags_s) - 1)) \
            if len(lags_s) > 1 else timedelta(0)
        for i, lag in enumerate(lags_s):
            ts_source = BASE + step * i
            ingest = ts_source + timedelta(seconds=lag)
            a, b = ts_source.isoformat(), ingest.isoformat()
            if naive:
                a = ts_source.replace(tzinfo=None).isoformat()
            conn.execute(
                f"INSERT INTO {table} VALUES ('h', 'UA46', 's', ?, ?, ?)",  # noqa: S608
                (a, b, source))
    return store


def _lags(store: Path, source: str = "telegram") -> SourceLags:
    per_source, _absent = _read_lags(store)
    return per_source[source]


def test_the_schema_here_is_the_stores_schema(tmp_path: Path) -> None:
    """F154's own regression: the fixture may not invent a table name.

    The instrument names two tables. Both must exist in a store the package
    itself writes, or this file is testing a database nobody has.
    """
    real = EventStore(tmp_path / "real.sqlite3")
    with closing(sqlite3.connect(real.path)) as conn:
        present = {
            row[0] for row in
            conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert set(TABLES) <= present, (
        f"the instrument reads {TABLES} and the store holds {sorted(present)}"
    )


def test_a_percentile_is_an_observation_and_not_an_average_of_two() -> None:
    """Nearest rank, no interpolation: every printed figure was measured."""
    assert _quantile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.0
    assert _quantile([1.0, 2.0, 3.0, 4.0], 0.9) == 4.0
    assert _quantile([5.0], 0.99) == 5.0


def test_a_negative_lag_is_reported_rather_than_clamped(tmp_path: Path) -> None:
    """A post received before it was posted means the clocks disagree. That is
    a finding about the measurement, and hiding it would make the distribution
    look tidier than the data underneath it."""
    store = _store(tmp_path, [10.0, 12.0, -4.0, 11.0])
    lags = _lags(store)
    assert lags.negative == [-4.0]
    assert -4.0 not in lags.forward
    summary = _summary_of("telegram", lags, 30.0)
    assert summary["negative_lags"] == 1
    assert summary["most_negative_s"] == -4.0


def test_a_naive_timestamp_is_dropped_rather_than_assumed_to_be_utc(
        tmp_path: Path) -> None:
    """F61's class. A naive timestamp is not a value in this repository, and
    guessing its zone would silently manufacture a lag of hours."""
    store = _store(tmp_path, [10.0, 11.0], naive=True)
    with pytest.raises(SystemExit) as refused:
        _read_lags(store)
    # Not an empty distribution, which would print as a store with no traffic.
    assert "no timestamped rows" in str(refused.value)


def test_both_streams_are_read(tmp_path: Path) -> None:
    """And the second one is `kind_events`, which is what the store calls it."""
    store = _store(tmp_path, [10.0, 20.0])
    _store(tmp_path, [30.0, 40.0], table="kind_events", path=store)
    assert sorted(_lags(store).forward) == [10.0, 20.0, 30.0, 40.0]


def test_a_table_the_store_does_not_hold_is_named_rather_than_skipped(
        tmp_path: Path) -> None:
    """F154's mechanism, not its instance.

    Reading a table that is not there used to `continue` under a comment about
    old stores, so a typo and a genuine schema gap were the same silence. The
    absent table is now returned and printed.
    """
    store = tmp_path / "partial.sqlite3"
    with closing(sqlite3.connect(store)) as conn, conn:
        conn.executescript(
            "CREATE TABLE events (content_hash TEXT, area_id TEXT, state TEXT,"
            " ts_source TEXT NOT NULL, ts_ingest TEXT NOT NULL,"
            " source_id TEXT NOT NULL);"
        )
        conn.execute(
            "INSERT INTO events VALUES ('h','UA46','s',?,?,'telegram')",
            (BASE.isoformat(), (BASE + timedelta(seconds=9)).isoformat()))
    _per_source, absent = _read_lags(store)
    assert absent == ["kind_events"]


def test_two_sources_are_reported_separately_and_never_pooled(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """F155. The store holds the channel era and the API era.

    A post timestamp against receipt and an alert's declared start against the
    snapshot that first listed it are different quantities. One median over
    both names neither, which is the shape of the source-dimension blindness
    `compose()` carried until 0.53.0.0.
    """
    store = _store(tmp_path, [10.0] * 10, span_days=9.0, source="telegram")
    _store(tmp_path, [600.0] * 10, span_days=9.0, source="ukrainealarm",
           path=store)
    assert main(["--store", str(store)]) == 0
    out = capsys.readouterr().out
    assert "source telegram" in out and "source ukrainealarm" in out
    assert "10.0 s" in out and "600.0 s" in out
    per_source, _absent = _read_lags(store)
    assert set(per_source) == {"telegram", "ukrainealarm"}


def test_one_source_can_be_selected(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    store = _store(tmp_path, [10.0] * 10, span_days=9.0, source="telegram")
    _store(tmp_path, [600.0] * 10, span_days=9.0, source="ukrainealarm",
           path=store)
    assert main(["--store", str(store), "--source", "telegram"]) == 0
    assert "source ukrainealarm" not in capsys.readouterr().out


def test_a_source_the_store_does_not_hold_is_a_refusal(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    store = _store(tmp_path, [10.0] * 10, span_days=9.0)
    assert main(["--store", str(store), "--source", "rso"]) == 1
    assert "no rows from source" in capsys.readouterr().err


def test_a_stamp_that_is_its_own_observation_is_held_out_of_the_distribution(
        tmp_path: Path) -> None:
    """The API stamps an all-clear with the moment it stopped being listed.

    That row's lag is zero by construction rather than by measurement. Counted
    into the distribution it would put a spike at zero and drag every
    percentile down, which is the unknown-never-zero invariant broken inside
    the one instrument built to measure lateness.
    """
    store = _store(tmp_path, [40.0] * 10, span_days=9.0)
    _store(tmp_path, [0.0] * 10, span_days=9.0, path=store)
    lags = _lags(store)
    assert lags.constructed == 10
    assert lags.forward == [40.0] * 10
    assert _summary_of("telegram", lags, 30.0)["median_s"] == 40.0


def test_a_short_window_is_refused_by_default(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """T40 asks for a week. An afternoon with percentiles on it is an anecdote
    wearing the clothes of a measurement."""
    store = _store(tmp_path, [10.0] * 20, span_days=0.5)
    assert main(["--store", str(store)]) == 2
    assert "anecdote" in capsys.readouterr().err


def test_a_short_window_prints_when_asked_and_says_it_is_not_a_measurement(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    store = _store(tmp_path, [10.0] * 20, span_days=0.5)
    assert main(["--store", str(store), "--allow-short"]) == 0
    assert "NOT A T40 MEASUREMENT" in capsys.readouterr().out


def test_a_full_window_reports_the_three_figures_the_acceptance_names(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    store = _store(tmp_path, [float(x) for x in range(1, 101)], span_days=9.0)
    assert main(["--store", str(store)]) == 0
    out = capsys.readouterr().out
    assert "median" in out and "p90" in out and "max" in out
    assert "50.0 s" in out and "90.0 s" in out and "100.0 s" in out


def test_the_poll_interval_is_named_and_the_upstream_is_only_bounded(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The lag is ours plus theirs. A tool that called it the channel's latency
    would be asserting a decomposition it cannot perform."""
    store = _store(tmp_path, [40.0] * 30, span_days=9.0)
    main(["--store", str(store), "--interval-s", "30"])
    out = capsys.readouterr().out
    assert "poll interval 30.0 s" in out
    assert "upper bound" in out and "[inference]" in out
    assert "channel latency" not in out.lower()


def test_the_upper_bound_subtracts_half_an_interval_and_never_goes_negative(
        ) -> None:
    lags = SourceLags(forward=[40.0] * 10, first=BASE,
                      last=BASE + timedelta(days=8))
    assert _summary_of("telegram", lags, 30.0)["upstream_upper_bound_s"] == 25.0
    quick = SourceLags(forward=[2.0] * 10, first=BASE,
                       last=BASE + timedelta(days=8))
    assert _summary_of("telegram", quick, 30.0)["upstream_upper_bound_s"] == 0.0


def test_the_window_test_uses_the_acceptance_figure() -> None:
    met = SourceLags(forward=[1.0], first=BASE,
                     last=BASE + timedelta(days=MINIMUM_DAYS))
    assert _summary_of("telegram", met, 30.0)["meets_t40_window"] is True
    short = SourceLags(forward=[1.0], first=BASE,
                       last=BASE + timedelta(days=MINIMUM_DAYS - 0.1))
    assert _summary_of("telegram", short, 30.0)["meets_t40_window"] is False


def test_a_source_with_no_forward_lag_is_reported_rather_than_omitted() -> None:
    """An empty source is a fact about that source, not a reason to drop it."""
    lags = SourceLags(constructed=4)
    summary = _summary_of("ukrainealarm", lags, 30.0)
    assert summary["observations"] == 0
    assert summary["median_s"] is None
    assert summary["constructed_stamps"] == 4
    assert summary["meets_t40_window"] is False
    assert "sources" in _summary({"ukrainealarm": lags}, [], 30.0)


def test_a_missing_store_is_a_refusal_and_not_an_empty_report(
        tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        _read_lags(tmp_path / "absent.sqlite3")


def test_an_empty_ordering_has_no_percentile_to_report() -> None:
    """A quantile of nothing is not zero, and pretending otherwise would be the
    unknown-never-zero invariant broken in one line of arithmetic."""
    with pytest.raises(ValueError):
        _quantile([], 0.5)


def test_every_held_out_row_is_named_in_the_output(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Constructed, negative and unparsed rows are printed, not just dropped.

    Three counts that would otherwise be invisible subtraction: a reader
    comparing `observations` against the row count of the store must be able to
    see where the difference went.
    """
    store = _store(tmp_path, [40.0] * 12, span_days=9.0)
    _store(tmp_path, [0.0] * 3, span_days=9.0, path=store)
    _store(tmp_path, [-5.0], span_days=9.0, path=store)
    _store(tmp_path, [7.0], span_days=9.0, naive=True, path=store)
    assert main(["--store", str(store)]) == 0
    out = capsys.readouterr().out
    assert "constructed stamps 3" in out
    assert "negative lags 1" in out
    assert "unparsed stamps 1" in out


def test_a_source_with_nothing_measurable_is_printed_as_such(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """An empty source is a fact about that source and gets a line of its own."""
    store = _store(tmp_path, [40.0] * 12, span_days=9.0, source="telegram")
    _store(tmp_path, [0.0] * 4, span_days=9.0, source="ukrainealarm", path=store)
    assert main(["--store", str(store)]) == 0
    out = capsys.readouterr().out
    assert "no forward lag on this source" in out


def test_a_store_with_no_measurable_lag_at_all_is_a_refusal(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Every row constructed is not a fast feed; it is nothing to report."""
    store = _store(tmp_path, [0.0] * 6, span_days=9.0)
    assert main(["--store", str(store)]) == 1
    assert "no forward lags" in capsys.readouterr().err


def test_the_absent_tables_are_named_in_the_output(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A figure taken over a store missing a stream says which stream."""
    store = tmp_path / "partial.sqlite3"
    with closing(sqlite3.connect(store)) as conn, conn:
        conn.executescript(
            "CREATE TABLE events (content_hash TEXT, area_id TEXT, state TEXT,"
            " ts_source TEXT NOT NULL, ts_ingest TEXT NOT NULL,"
            " source_id TEXT NOT NULL);"
        )
        for day in range(10):
            at = BASE + timedelta(days=day)
            conn.execute(
                "INSERT INTO events VALUES ('h','UA46','s',?,?,'telegram')",
                (at.isoformat(), (at + timedelta(seconds=9)).isoformat()))
    assert main(["--store", str(store)]) == 0
    assert "kind_events" in capsys.readouterr().out


def test_the_json_form_carries_the_same_fields(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import json

    store = _store(tmp_path, [40.0] * 12, span_days=9.0)
    assert main(["--store", str(store), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["sources"][0]["source"] == "telegram"
    assert payload["sources"][0]["median_s"] == 40.0
    assert payload["absent_tables"] == []


def test_the_subcommand_forwards_every_flag_the_instrument_has(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """F157. `--source` existed in the instrument and not on the parser.

    Two documents told an operator to run `mavo latency --source telegram`, and
    that command exited 2 with `unrecognized arguments`. The instrument's own
    regressions could not see it, because they call `main` directly and the
    defect was in the wrapper - a test of the module is not a test of the
    command, and this one goes through `mavo.cli` for exactly that reason.
    """
    from mavo.cli import main as cli_main

    store = _store(tmp_path, [10.0] * 10, span_days=9.0, source="telegram")
    _store(tmp_path, [600.0] * 10, span_days=9.0, source="ukrainealarm",
           path=store)
    assert cli_main(["latency", "--store", str(store), "--interval-s", "33",
                     "--source", "telegram"]) == 0
    out = capsys.readouterr().out
    assert "source telegram" in out
    assert "source ukrainealarm" not in out


def test_an_unreadable_timestamp_is_counted_rather_than_fatal(
        tmp_path: Path) -> None:
    """One corrupt row must not take the reading down with it.

    Inherited from the version in `tools/`, where `fromisoformat` was called
    without a guard, and not noticed when this function was rewritten. A store
    that dies on the row it cannot parse reports nothing about the rows it can.
    """
    store = _store(tmp_path, [40.0] * 10, span_days=9.0)
    with closing(sqlite3.connect(store)) as conn, conn:
        conn.execute(
            "INSERT INTO events VALUES ('h','UA46','s',?,?,'telegram')",
            ("not-a-timestamp", BASE.isoformat()))
    lags = _lags(store)
    assert lags.unparsed == 1
    assert len(lags.forward) == 10
