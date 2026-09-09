"""How late is the channel: post timestamp against the moment it was received.

Lived in `tools/` for twenty-three releases. D-038 moved `attempts.py` here on
the discriminator *where must the reader stand to read its input*, and this
file answers that question the same way and was left behind anyway: it opens
the event store by `sqlite3` connection, `tools/` is never installed by the
wheel, and so the instrument built for T40 could not run on the only machine
that holds a store. A decision applied to one instance rather than to its
class is the shape this repository logs about itself, and the repair is T84
rather than a second exception.

Nothing about the measurement changed in the move. The module is the file that
sat in `tools/`, its eleven regressions are the same regressions, and the only
edits are this paragraph, the usage lines below and the import path they name.

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

Usage, on the host where the store lives:

    mavo latency --store /var/lib/mavo/events
    mavo latency --store /var/lib/mavo/events --interval-s 33 --json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

#: T40's acceptance. A shorter window is a dry run, not a measurement.
MINIMUM_DAYS = 7.0

#: Below this, the two unsynchronised clocks are the dominant term.
NOISE_FLOOR_S = 2.0

#: The two streams that carry a source timestamp, named as the schema names
#: them. **`kind_events`, not `kinds`** - F154. This module read a table called
#: `kinds` from the release it was written until 0.54.0.0, `mavo/store.py` has
#: never created one, and the `OperationalError` branch below turned the miss
#: into a silent skip labelled *a store written before this table existed*. On
#: a real store the instrument therefore reported a distribution over the alert
#: stream alone while its own docstring said it pooled both. Measured on a
#: store built by `EventStore` with nine rows in each table: nine observations,
#: not eighteen. The eleven regressions could not see it because the fixture
#: created a table with the name this module used, which is the fourth instance
#: of test data chosen by the implementation rather than against it.
TABLES = ("events", "kind_events")


@dataclass
class SourceLags:
    """Every lag one source contributed, and the rows that carry none.

    `constructed` counts rows whose source timestamp *is* the observation, to
    the microsecond. Those are not fast readings, they are readings with
    nothing on the other side of the subtraction: the API path stamps an
    all-clear with the moment it noticed the alert had stopped being listed,
    because the source never says when an alert ended. Folding them into the
    distribution would put a spike at zero and pull every percentile down, and
    reporting them as measured zeroes is the unknown-never-zero invariant
    broken in the one instrument built to measure lateness.
    """

    forward: list[float] = field(default_factory=list)
    negative: list[float] = field(default_factory=list)
    constructed: int = 0
    unparsed: int = 0
    first: datetime | None = None
    last: datetime | None = None

    def observe(self, source: datetime, lag: float) -> None:
        (self.negative if lag < 0 else self.forward).append(lag)
        self.first = source if self.first is None or source < self.first else self.first
        self.last = source if self.last is None or source > self.last else self.last


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


def _read_lags(store: Path) -> tuple[dict[str, SourceLags], list[str]]:
    """Lags per source, plus the tables this store does not hold.

    **Per source, and that is F155.** Until 0.54.0.0 this pooled every row in
    the store into one distribution. That was true while one feed existed. The
    store now holds the channel era and the API era (D-040), the two quantities
    are not the same measurement - a post timestamp against receipt, against an
    alert's declared start against the snapshot that first listed it - and a
    single median over both is a number with no referent. It is the same shape
    as `compose()` keying freshness on `(area_id, kind)` with no source
    dimension, which is F-class enough to be worth naming twice.

    An absent table is reported rather than skipped. The previous behaviour
    swallowed it as backwards compatibility and swallowed F154 with it.
    """
    if not store.exists():
        raise SystemExit(f"latency: no store at {store}")
    per_source: dict[str, SourceLags] = defaultdict(SourceLags)
    absent: list[str] = []
    with closing(sqlite3.connect(f"file:{store}?mode=ro", uri=True)) as conn:
        for table in TABLES:
            try:
                rows = conn.execute(
                    f"SELECT ts_source, ts_ingest, source_id FROM {table}"  # noqa: S608
                ).fetchall()
            except sqlite3.OperationalError:
                absent.append(table)
                continue
            for raw_source, raw_ingest, source_id in rows:
                name = source_id or "unattributed"
                lags = per_source[name]
                source = datetime.fromisoformat(raw_source)
                ingest = datetime.fromisoformat(raw_ingest)
                if source.tzinfo is None or ingest.tzinfo is None:
                    # F61's class: a naive timestamp is not a value. Counted
                    # rather than assumed to be UTC.
                    lags.unparsed += 1
                    continue
                if source == ingest:
                    lags.constructed += 1
                    continue
                lags.observe(source, (ingest - source).total_seconds())
    if not per_source or all(
        lags.first is None and lags.constructed == 0 for lags in per_source.values()
    ):
        # Not an empty distribution, which would print as a store with no
        # traffic. A store whose every stamp is naive has told us nothing about
        # lateness and must say so rather than report zero rows as a quiet feed.
        raise SystemExit("latency: the store holds no timestamped rows")
    return dict(per_source), absent


def _summary_of(name: str, lags: SourceLags, interval_s: float) -> dict[str, object]:
    """One source's distribution. Raises nothing; an empty source is reported."""
    ordered = sorted(lags.forward)
    first, last = lags.first, lags.last
    span_days = (last - first).total_seconds() / 86400.0 if first and last else 0.0
    common: dict[str, object] = {
        "source": name,
        "observations": len(ordered),
        "negative_lags": len(lags.negative),
        "most_negative_s": min(lags.negative) if lags.negative else None,
        "constructed_stamps": lags.constructed,
        "unparsed_stamps": lags.unparsed,
        "window_first": first.isoformat() if first else None,
        "window_last": last.isoformat() if last else None,
        "window_days": round(span_days, 2),
        "meets_t40_window": span_days >= MINIMUM_DAYS and bool(ordered),
        "poll_interval_s": interval_s,
    }
    if not ordered:
        common.update({
            "median_s": None, "p90_s": None, "p99_s": None, "max_s": None,
            "at_or_below_noise_floor": 0, "upstream_upper_bound_s": None,
        })
        return common
    median = _quantile(ordered, 0.50)
    common.update({
        "median_s": round(median, 1),
        "p90_s": round(_quantile(ordered, 0.90), 1),
        "p99_s": round(_quantile(ordered, 0.99), 1),
        "max_s": round(ordered[-1], 1),
        "at_or_below_noise_floor": sum(1 for x in ordered if x <= NOISE_FLOOR_S),
        "upstream_upper_bound_s": round(max(0.0, median - interval_s / 2.0), 1),
    })
    return common


def _summary(
    per_source: dict[str, SourceLags], absent: list[str], interval_s: float
) -> dict[str, object]:
    """Every source, never pooled, with the tables that were not there."""
    return {
        "sources": [
            _summary_of(name, per_source[name], interval_s)
            for name in sorted(per_source)
        ],
        "absent_tables": absent,
        "poll_interval_s": interval_s,
    }


def _render(summary: dict[str, object]) -> str:
    """One block per source. Never a pooled line, however tempting."""
    lines: list[str] = []
    sources = summary["sources"]
    assert isinstance(sources, list)
    for block in sources:
        assert isinstance(block, dict)
        lines.append(
            f"post timestamp to receipt, source {block['source']} [measured]"
        )
        if block["observations"]:
            lines += [
                f"  window        {block['window_first']} .. "
                f"{block['window_last']}  ({block['window_days']} days)",
                f"  observations  {block['observations']}",
                f"  median        {block['median_s']} s",
                f"  p90           {block['p90_s']} s",
                f"  p99           {block['p99_s']} s",
                f"  max           {block['max_s']} s",
                f"  at or below the {NOISE_FLOOR_S} s clock floor: "
                f"{block['at_or_below_noise_floor']}",
                f"  upstream upper bound {block['upstream_upper_bound_s']} s "
                "[inference]: the median minus half an interval. An upper "
                "bound on everything before this collector, not a measurement "
                "of the source.",
            ]
        else:
            lines.append(
                "  no forward lag on this source; every row it wrote is "
                "constructed, negative or unparsed [measured]"
            )
        if block["constructed_stamps"]:
            lines.append(
                f"  constructed stamps {block['constructed_stamps']}: rows "
                "whose source time is the observation itself, held out of the "
                "distribution rather than counted as zero lag"
            )
        if block["negative_lags"]:
            lines.append(
                f"  negative lags {block['negative_lags']}, most negative "
                f"{block['most_negative_s']} s. A row received before it was "
                "stamped means the two clocks disagree; it is a finding, not "
                "an outlier [measured]"
            )
        if block["unparsed_stamps"]:
            lines.append(
                f"  unparsed stamps {block['unparsed_stamps']}: a timestamp "
                "without an offset is not a value and is not assumed to be UTC"
            )
        if not block["meets_t40_window"]:
            lines.append(
                f"  NOT A T40 MEASUREMENT: the window is "
                f"{block['window_days']} days and the acceptance asks for "
                f"{MINIMUM_DAYS}"
            )
        lines.append("")
    lines.append(
        f"poll interval {summary['poll_interval_s']} s, which contributes a "
        "uniform 0 to one interval of every lag above [reported, from the unit]"
    )
    absent = summary["absent_tables"]
    assert isinstance(absent, list)
    if absent:
        lines.append(
            "tables this store does not hold, and their rows are therefore "
            f"absent from every figure above: {', '.join(absent)}"
        )
    lines.append(
        "sources are reported separately and never pooled: a post timestamp "
        "against receipt and an alert's declared start against the snapshot "
        "that first listed it are different quantities, and one median over "
        "both would name neither"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--store", type=Path, required=True,
                        help="the SQLite store written by the collectors")
    parser.add_argument("--interval-s", type=float, default=30.0,
                        help="the poll interval the collector ran at (D-027)")
    parser.add_argument("--source", default=None,
                        help="report one source_id rather than every one")
    parser.add_argument("--allow-short", action="store_true",
                        help="print a summary for a window under a week, marked")
    parser.add_argument("--json", action="store_true", help="machine-readable")
    args = parser.parse_args(argv)

    per_source, absent = _read_lags(args.store)
    if args.source is not None:
        if args.source not in per_source:
            print(f"latency: no rows from source {args.source!r}; the store "
                  f"holds {', '.join(sorted(per_source))}", file=sys.stderr)
            return 1
        per_source = {args.source: per_source[args.source]}
    summary = _summary(per_source, absent, args.interval_s)

    sources = summary["sources"]
    assert isinstance(sources, list)
    if not any(block["observations"] for block in sources):
        print("latency: no forward lags; every row is constructed, negative "
              "or unparsed", file=sys.stderr)
        return 1
    if not any(block["meets_t40_window"] for block in sources) and not args.allow_short:
        spans = ", ".join(
            f"{block['source']} {block['window_days']}" for block in sources
        )
        print(
            f"latency: no source spans the {MINIMUM_DAYS} days T40 asks for "
            f"(days by source: {spans}). A distribution over one afternoon is "
            "an anecdote with percentiles on it. Re-run with --allow-short "
            "for a dry run.",
            file=sys.stderr,
        )
        return 2

    print(json.dumps(summary, indent=2) if args.json else _render(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
