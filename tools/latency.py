#!/usr/bin/env python3
"""How late is the channel: post timestamp against the moment it was received.

T40. Every latency argument in this repository rests on a number nobody had
measured. The poll interval is thirty seconds and D-027 spent a paragraph on
whether that is too fast; that argument is only worth having if the upstream
costs less than thirty seconds itself. If a post reaches the public view two
minutes after the alert is announced, our interval is a small term beside a
large one and the honest report says so.

**What this measures.** For every event in the store, ``ts_ingest`` minus
``ts_source``: the interval between the timestamp the channel put on the post
and the moment this collector parsed it. Reported as a distribution over the
window the store covers, with the count, the span in days, and the median, p90,
p99 and maximum.

**What it does not measure, and the distinction is the whole point.**

*Not* the channel's own latency. The measured lag is the sum of at least three
terms: how long the source took to publish after the alert was announced, how
long the public web view took to show it, and how long this collector waited
before its next poll. Only the third is ours and only the third is known
exactly. The tool therefore prints the poll interval beside the figures and
labels the difference an upper bound on the upstream, never a measurement of
it.

*Not* the latency of an alert. ``ts_source`` is the post's timestamp, and the
post is already downstream of whatever announcement it reports.

**The resolution floor.** The channel's web view carries an RFC-3339 timestamp
with seconds, so the floor is one second and not one minute. It is still a
floor: a lag reported as 0 s means "below the resolution of the two clocks
involved", and the two clocks are not synchronised with each other. Anything
under a couple of seconds is noise, and negative lags are reported separately
rather than clamped, because a clock that runs backwards is a finding and not
an outlier to be tidied away.

**Acceptance, from T40.** Median, p90 and max over at least a week, recorded in
``docs/CHANNEL.md`` with the collection dates and the interval used. This tool
computes them and refuses to print a summary line for a window shorter than
seven days: a distribution over one afternoon is an anecdote with percentiles
on it. ``--allow-short`` prints it anyway, clearly marked, for a dry run.

Usage:

    python3 tools/latency.py --store /var/lib/mavo/store.sqlite3
    python3 tools/latency.py --store store.sqlite3 --interval-s 30 --json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

#: T40's acceptance. A shorter window is a dry run, not a measurement.
MINIMUM_DAYS = 7.0

#: Below this, the two unsynchronised clocks are the dominant term.
NOISE_FLOOR_S = 2.0


def _quantile(ordered: list[float], q: float) -> float:
    """Nearest-rank quantile. No interpolation between two observations.

    Interpolation invents a value that was never measured. For a latency
    distribution read off a small sample that is exactly the wrong trade: the
    reader wants to know what actually happened, not what would have happened
    between two things that did.
    """
    if not ordered:
        raise ValueError("no observations")
    rank = max(1, min(len(ordered), int(-(-q * len(ordered) // 1))))
    return ordered[rank - 1]


def _read_lags(store: Path) -> tuple[list[float], list[float], datetime, datetime]:
    """Lags in seconds, split into forward and negative, plus the window.

    Both tables are read. `events` and `kinds` are different streams and a
    latency argument about one of them is an argument about the transport they
    share, so pooling them is honest here in a way that pooling sample strata
    is not.
    """
    if not store.exists():
        raise SystemExit(f"latency: no store at {store}")
    forward: list[float] = []
    negative: list[float] = []
    first: datetime | None = None
    last: datetime | None = None
    with sqlite3.connect(f"file:{store}?mode=ro", uri=True) as conn:
        for table in ("events", "kinds"):
            try:
                rows = conn.execute(
                    f"SELECT ts_source, ts_ingest FROM {table}"  # noqa: S608
                ).fetchall()
            except sqlite3.OperationalError:
                continue  # a store written before this table existed
            for raw_source, raw_ingest in rows:
                source = datetime.fromisoformat(raw_source)
                ingest = datetime.fromisoformat(raw_ingest)
                if source.tzinfo is None or ingest.tzinfo is None:
                    # F61's class: a naive timestamp is not a value. Counted by
                    # its absence from both lists rather than assumed to be UTC.
                    continue
                lag = (ingest - source).total_seconds()
                (negative if lag < 0 else forward).append(lag)
                first = source if first is None or source < first else first
                last = source if last is None or source > last else last
    if first is None or last is None:
        raise SystemExit("latency: the store holds no timestamped rows")
    return forward, negative, first, last


def _summary(
    forward: list[float], negative: list[float],
    first: datetime, last: datetime, interval_s: float,
) -> dict[str, object]:
    ordered = sorted(forward)
    span_days = (last - first).total_seconds() / 86400.0
    median = _quantile(ordered, 0.50)
    return {
        "observations": len(ordered),
        "negative_lags": len(negative),
        "most_negative_s": min(negative) if negative else None,
        "window_first": first.isoformat(),
        "window_last": last.isoformat(),
        "window_days": round(span_days, 2),
        "meets_t40_window": span_days >= MINIMUM_DAYS,
        "median_s": round(median, 1),
        "p90_s": round(_quantile(ordered, 0.90), 1),
        "p99_s": round(_quantile(ordered, 0.99), 1),
        "max_s": round(ordered[-1], 1),
        "at_or_below_noise_floor": sum(1 for x in ordered if x <= NOISE_FLOOR_S),
        "poll_interval_s": interval_s,
        "upstream_upper_bound_s": round(max(0.0, median - interval_s / 2.0), 1),
    }


def _render(summary: dict[str, object]) -> str:
    lines = [
        "post timestamp to receipt, from the store [measured]",
        f"  window        {summary['window_first']} .. {summary['window_last']}"
        f"  ({summary['window_days']} days)",
        f"  observations  {summary['observations']}",
        f"  median        {summary['median_s']} s",
        f"  p90           {summary['p90_s']} s",
        f"  p99           {summary['p99_s']} s",
        f"  max           {summary['max_s']} s",
        f"  at or below the {NOISE_FLOOR_S} s clock floor: "
        f"{summary['at_or_below_noise_floor']}",
    ]
    if summary["negative_lags"]:
        lines.append(
            f"  negative lags {summary['negative_lags']}, most negative "
            f"{summary['most_negative_s']} s. A post received before it was "
            "posted means the two clocks disagree; it is a finding, not an "
            "outlier [measured]"
        )
    lines += [
        "",
        f"poll interval {summary['poll_interval_s']} s, which contributes a "
        "uniform 0 to one interval of the lag above [reported, from the unit]",
        f"upstream upper bound {summary['upstream_upper_bound_s']} s "
        "[inference]: the median minus half an interval. An upper bound on "
        "everything before this collector, not a measurement of the channel.",
    ]
    if not summary["meets_t40_window"]:
        lines += [
            "",
            f"NOT A T40 MEASUREMENT: the window is "
            f"{summary['window_days']} days and the acceptance asks for "
            f"{MINIMUM_DAYS}. Printed because --allow-short was given.",
        ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--store", type=Path, required=True,
                        help="the SQLite store written by `mavo watch`")
    parser.add_argument("--interval-s", type=float, default=30.0,
                        help="the poll interval the collector ran at (D-027)")
    parser.add_argument("--allow-short", action="store_true",
                        help="print a summary for a window under a week, marked")
    parser.add_argument("--json", action="store_true", help="machine-readable")
    args = parser.parse_args(argv)

    forward, negative, first, last = _read_lags(args.store)
    if not forward:
        print("latency: no forward lags; every row is negative or unparsed",
              file=sys.stderr)
        return 1
    summary = _summary(forward, negative, first, last, args.interval_s)

    if not summary["meets_t40_window"] and not args.allow_short:
        print(
            f"latency: the store spans {summary['window_days']} days and T40 "
            f"asks for at least {MINIMUM_DAYS}. A distribution over one "
            "afternoon is an anecdote with percentiles on it. Re-run with "
            "--allow-short for a dry run.",
            file=sys.stderr,
        )
        return 2

    print(json.dumps(summary, indent=2) if args.json else _render(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
