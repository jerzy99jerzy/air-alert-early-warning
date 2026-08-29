#!/usr/bin/env python3
"""What the collector was doing, counted three ways that do not overlap.

T66. `tools/latency.py` reads the event store, and the event store by
construction cannot tell silence from blindness: a poll that never returned
writes nothing, a quiet channel writes nothing, and the two are the same row
count. That reasoning is exact, and it is about the `events` table. It is not
true of a table with one row per attempt, which is what `feed_attempts` is and
what D-036 decided the collector writes to.

So the three quantities are separated here rather than inferred:

- **attempts made** - rows in the window, one per poll, whatever happened
- **attempts that failed** - rows whose outcome is a refusal
- **stretches with neither** - intervals between consecutive rows longer than
  the cadence allows, during which this collector produced no evidence at all

The third is the one nothing in this project could previously report, and it
is the term `docs/CHANNEL.md` section 8a needs before a latency tail can be
attributed: a minute we were blind for is not a minute the channel was slow.

## What this tool refuses to do

**It will not guess the cadence.** The interval is a property of a systemd
timer this tool cannot read, and inferring it from the median gap would make
the instrument agree with whatever the data already says - a gap detector
calibrated on the gaps it is looking for. `--cadence-s` is required.

**It will not call the window edges observed.** Rows before `--since` and
after `--until` are outside the query, so whether the collector was running up
to the first row and after the last one is unknown from this table alone. The
head and tail are printed as unknown rather than folded into the covered time,
which would flatter the figure by exactly the amount nobody measured.

**It reports NULL as unknown.** `elapsed_s` is NULL for every row written
before 0.41.0.0 and for any caller that did not time itself. Those rows are
excluded from the duration summary and counted, so a summary over half the
rows cannot read as a summary over all of them.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mavo.store import EventStore  # noqa: E402

#: A gap is a stretch this collector cannot account for. Two cadences of
#: silence is the threshold: one cadence is the ordinary spacing between
#: consecutive polls and cannot be a gap, and a threshold at exactly one
#: cadence would report jitter as blindness on every timer that has any.
#: `RandomizedDelaySec=5` against a 30 s interval is 17% of one cadence
#: `[measured, docs/DEPLOYMENT.md]`, so the margin is not tight.
GAP_CADENCES = 2.0


@dataclass(frozen=True, slots=True)
class Gap:
    """A stretch between two attempts with no attempt in it."""

    after: datetime
    before: datetime

    @property
    def seconds(self) -> float:
        return (self.before - self.after).total_seconds()


@dataclass(frozen=True, slots=True)
class Completeness:
    """The three counts, plus what could not be counted.

    ``unknown_head`` and ``unknown_tail`` are seconds at the edges of the
    requested window with no row on one side, and they are seconds this tool
    declines to classify. They are separate fields rather than added to
    ``unobserved_s`` because an unobserved stretch is a measurement and an
    unclassified edge is an absence of one.
    """

    feed: str
    cadence_s: float
    attempts: int
    refusals: int
    gaps: tuple[Gap, ...]
    first: datetime | None
    last: datetime | None
    unknown_head_s: float | None
    unknown_tail_s: float | None
    durations: tuple[float, ...]
    untimed: int

    @property
    def reads(self) -> int:
        return self.attempts - self.refusals

    @property
    def unobserved_s(self) -> float:
        return sum(gap.seconds for gap in self.gaps)

    @property
    def refusal_share(self) -> float | None:
        """Refusals over attempts, or None when there were no attempts.

        None rather than 0.0: a window with no polls in it has no refusal rate,
        and printing 0% for it would report perfect health for a dead collector.
        """
        return self.refusals / self.attempts if self.attempts else None

    def render(self) -> str:
        lines = [
            f"feed={self.feed} cadence={self.cadence_s:g}s "
            f"gap threshold={self.cadence_s * GAP_CADENCES:g}s",
        ]
        if not self.attempts:
            lines.append("attempts=0 - this collector left no record in the window")
            lines.append("refusals=unknown  unobserved=unknown")
            lines.append(
                "NOTE: no rows is not a quiet channel. It is a window in which "
                "nothing was written, and this table cannot say why."
            )
            return "\n".join(lines)
        share = self.refusal_share
        assert share is not None  # attempts is non-zero above
        lines.append(
            f"attempts={self.attempts}  read={self.reads}  refused={self.refusals} "
            f"({share:.1%})"
        )
        lines.append(
            f"window={self.first.isoformat()} .. {self.last.isoformat()}"
            if self.first and self.last
            else "window=unknown"
        )
        lines.append(
            f"gaps={len(self.gaps)}  unobserved={self.unobserved_s:.0f}s"
            + (
                f"  longest={max(gap.seconds for gap in self.gaps):.0f}s"
                if self.gaps
                else ""
            )
        )
        for gap in sorted(self.gaps, key=lambda item: item.seconds, reverse=True)[:10]:
            lines.append(
                f"  unobserved {gap.after.isoformat()} .. {gap.before.isoformat()} "
                f"({gap.seconds:.0f}s)"
            )
        if len(self.gaps) > 10:
            lines.append(f"  ... and {len(self.gaps) - 10} more")
        head = "unknown" if self.unknown_head_s is None else f"{self.unknown_head_s:.0f}s"
        tail = "unknown" if self.unknown_tail_s is None else f"{self.unknown_tail_s:.0f}s"
        lines.append(
            f"edges: before the first attempt {head}, after the last {tail} "
            "- outside this table, not inside it"
        )
        if self.durations:
            ordered = sorted(self.durations)
            lines.append(
                f"attempt duration: n={len(ordered)} median={median(ordered):.3f}s "
                f"max={ordered[-1]:.3f}s"
            )
        if self.untimed:
            lines.append(
                f"untimed={self.untimed} attempt(s) carry no duration and are "
                "excluded above, not counted as zero"
            )
        return "\n".join(lines)


def _parse(stamp: str) -> datetime:
    """Read a stored timestamp back, refusing one with no offset."""
    parsed = datetime.fromisoformat(stamp)
    if parsed.tzinfo is None:
        raise ValueError(
            f"{stamp!r} has no UTC offset; the store writes offsets and a row "
            "without one was written by something else"
        )
    return parsed.astimezone(UTC)


def measure(
    store: EventStore,
    feed: str,
    cadence_s: float,
    since: datetime | None = None,
    until: datetime | None = None,
) -> Completeness:
    """Count attempts, refusals and unobserved stretches over a window."""
    rows = store.attempts(feed, since=since, until=until)
    stamps = [_parse(str(row["started_at"])) for row in rows]
    refusals = sum(1 for row in rows if row["outcome"] == "refused")
    threshold = timedelta(seconds=cadence_s * GAP_CADENCES)
    gaps = tuple(
        Gap(after=earlier, before=later)
        for earlier, later in zip(stamps, stamps[1:], strict=False)
        if later - earlier > threshold
    )
    durations = tuple(
        float(row["elapsed_s"]) for row in rows if row["elapsed_s"] is not None
    )
    first = stamps[0] if stamps else None
    last = stamps[-1] if stamps else None
    return Completeness(
        feed=feed,
        cadence_s=cadence_s,
        attempts=len(rows),
        refusals=refusals,
        gaps=gaps,
        first=first,
        last=last,
        unknown_head_s=(
            (first - since).total_seconds() if since is not None and first else None
        ),
        unknown_tail_s=(
            (until - last).total_seconds() if until is not None and last else None
        ),
        durations=durations,
        untimed=len(rows) - len(durations),
    )


def main(argv: list[str] | None = None) -> int:
    """Report attempt completeness for one feed. Returns a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--store", required=True, help="path to the event store")
    parser.add_argument("--feed", default="channel", help="feed name in feed_attempts")
    parser.add_argument(
        "--cadence-s",
        type=float,
        required=True,
        help="the timer interval, in seconds. Required: this tool cannot read "
             "the timer, and inferring it from the data would calibrate the gap "
             "detector on the gaps it is looking for",
    )
    parser.add_argument("--since", help="ISO timestamp with an offset, inclusive")
    parser.add_argument("--until", help="ISO timestamp with an offset, exclusive")
    args = parser.parse_args(argv)

    if args.cadence_s <= 0:
        print("attempts: --cadence-s must be positive", file=sys.stderr)
        return 2
    path = Path(args.store)
    if not path.exists():
        print(f"attempts: no store at {path}", file=sys.stderr)
        return 2
    try:
        window = tuple(
            _parse(value) if value else None for value in (args.since, args.until)
        )
    except ValueError as bad:
        print(f"attempts: {bad}", file=sys.stderr)
        return 2
    print(
        measure(
            EventStore(path), args.feed, args.cadence_s, since=window[0], until=window[1]
        ).render()
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
