"""Attempt completeness: the three counts that do not overlap (T66, D-038).

Lived in `tools/` for exactly one release. D-038 moved it here, and the
discriminator is where the input lives: an instrument that reads the **store**
must run on the host that writes the store, so it ships inside the wheel as
`mavo attempts` and the manual audit polices its documentation. An instrument
that reads the **tree** stays in `tools/`, where the gate runs it. `tools/`
was never installed and never documented for the operator, so the instrument
built to read the production table could not be run on the only machine that
has one - found on deploy day, one command after the table gained its first
rows.

- **attempts made** - rows in the window, one per poll, whatever happened
- **attempts that failed** - rows whose outcome is a refusal
- **stretches with neither** - intervals between consecutive rows longer than
  the cadence allows, during which the collector produced no evidence at all
- **unseen messages** - traffic that moved between two pages we did read,
  from the id bounds (F123); a different quantity from unobserved time and
  reported beside it, never added to it

What it refuses to do is unchanged from the first version: it will not guess
the cadence, it will not call the window edges observed, and it reports NULL
as unknown rather than as zero.
"""


from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import median

from mavo.store import EventStore

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
    #: Messages that passed between two consecutive read pages without being
    #: seen, summed over the window. Added at 0.42.0.0, once `feed_attempts`
    #: began carrying page bounds (F123). It is a different quantity from
    #: `unobserved_s`: a stretch with no attempt in it is time we were not
    #: looking, and this is traffic that moved while we were.
    unseen_messages: int
    #: Consecutive read pairs whose bounds could not be compared, because one
    #: side carried no ids. Counted rather than skipped, so a total computed
    #: over half the pairs cannot read as a total over all of them.
    uncomparable_pairs: int

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
        lines.append(
            f"unseen messages={self.unseen_messages}"
            + (
                f"  uncomparable pairs={self.uncomparable_pairs} (bounds missing "
                "on one side, not counted as zero)"
                if self.uncomparable_pairs
                else ""
            )
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
    # One pass over a stream, one row held at a time - the latency vector
    # aside, which is kept whole because the median needs it (D-038). The tuple-of-
    # dicts version was measured at 3.6 s and ~248 MiB over a synthetic year;
    # nothing below needs more than the previous row.
    threshold = timedelta(seconds=cadence_s * GAP_CADENCES)
    attempts_seen = refusals = untimed = 0
    unseen = uncomparable = 0
    gaps: list[Gap] = []
    durations: list[float] = []
    first: datetime | None = None
    last: datetime | None = None
    previous_stamp: datetime | None = None
    previous_page_last: int | None = None  # last_id of the previous *read* row
    previous_was_read = False
    for row in store.iter_attempts(feed, since=since, until=until):
        stamp = _parse(str(row["started_at"]))
        attempts_seen += 1
        if first is None:
            first = stamp
        if previous_stamp is not None and stamp - previous_stamp > threshold:
            gaps.append(Gap(after=previous_stamp, before=stamp))
        previous_stamp = stamp
        last = stamp
        if row["elapsed_s"] is None:
            untimed += 1
        else:
            durations.append(float(row["elapsed_s"]))
        if row["outcome"] == "refused":
            refusals += 1
            continue
        # Only pages count below. A refusal carries no bounds and is not a
        # pair whose comparison failed; it is not a page at all.
        if previous_was_read or previous_page_last is not None:
            if previous_page_last is None or row["first_id"] is None:
                uncomparable += 1
            else:
                unseen += max(0, int(row["first_id"]) - previous_page_last - 1)
        if row["first_id"] is not None or row["last_id"] is not None:
            previous_page_last = (
                int(row["last_id"]) if row["last_id"] is not None else None
            )
        else:
            previous_page_last = None
        previous_was_read = True
    return Completeness(
        feed=feed,
        cadence_s=cadence_s,
        attempts=attempts_seen,
        refusals=refusals,
        gaps=tuple(gaps),
        first=first,
        last=last,
        unknown_head_s=(
            (first - since).total_seconds() if since is not None and first else None
        ),
        unknown_tail_s=(
            (until - last).total_seconds() if until is not None and last else None
        ),
        durations=tuple(durations),
        untimed=untimed,
        unseen_messages=unseen,
        uncomparable_pairs=uncomparable,
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
