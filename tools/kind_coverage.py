"""How much of the alert stream the kind stream can actually explain (T16).

Reads the saved page snapshots under `data/raw` and answers the question the
regime split depends on and nobody has asked of real data: **when an alert is
raised, does anything in the recent past say what is flying?**

The join implemented in `mavo/kinds.py` is only worth its complexity if the
answer is yes often enough. If most alerts still come out UNKNOWN, that is not a
bug in the join; it is a finding about the source, and it demotes the regime
split from a property of the world to a property of the generator, which is what
`docs/METHODOLOGY.md` already labels it as speculation pending exactly this
measurement.

## What it prints, and what each number decides

- **declarations** and **lifts**: how much of a stream there is at all. If this
  is tiny, nothing below matters.
- **share of unparsed messages that were declarations**: how much of the old
  parse-failure rate this sprint recovered.
- **declaration-to-lift interval distribution**: this replaces
  `DEFAULT_KIND_TTL`, which is currently an assumption with a label on it. The
  median and the 90th percentile are the numbers to carry back into the code.
- **join coverage**: the share of alerts that receive a regime, at several
  candidate TTLs. This is the decision number.
- **ambiguity rate**: how often two kinds are live over one oblast at once. High
  ambiguity means the oblast is the wrong join granularity and the hromada level
  has to be attempted, with everything that costs.

## Usage

    python3 tools/kind_coverage.py --raw data/raw

The corpus is not in the repository (`data/raw` is gitignored, tier 1). This
tool therefore cannot run in CI and its output is a measurement to be recorded
in `docs/METHODOLOGY.md` by hand, with its date and the snapshot count it read.
"""

from __future__ import annotations

import argparse
import random
import re
import statistics
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from mavo.areas import AreaTable  # noqa: E402
from mavo.backfill import SNAPSHOT_NAME  # noqa: E402
from mavo.kinds import KindIndex, apply_kinds  # noqa: E402
from mavo.schema import KindEvent, KindState, ThreatKind  # noqa: E402
from mavo.sources.telegram import (  # noqa: E402
    _BLOCK,
    _TEXT,
    _TIME,
    KIND_DECLARE_MARKERS,
    KIND_LIFT_MARKERS,
    KIND_MARKERS,
    AreaMention,
    _parse_timestamp,
    classify_kind_message,
    classify_message,
)

CANDIDATE_TTLS = (
    timedelta(hours=1),
    timedelta(hours=3),
    timedelta(hours=6),
    timedelta(hours=12),
    timedelta(hours=24),
)


def read_messages(directory: Path) -> list[tuple[datetime, str]]:
    """Every message in every snapshot, deduplicated by post id."""
    seen: dict[str, tuple[datetime, str]] = {}
    for snapshot in sorted(directory.glob("page-*.html")):
        if SNAPSHOT_NAME.search(snapshot.name) is None:
            continue
        body = snapshot.read_text(encoding="utf-8", errors="replace")
        for block in _BLOCK.finditer(body):
            chunk = block.group(0)
            post = re.search(r'data-post="[^/]+/(\d+)"', chunk)
            text_match = _TEXT.search(chunk)
            time_match = _TIME.search(chunk)
            if post is None or text_match is None or time_match is None:
                continue
            ts = _parse_timestamp(time_match.group(1))
            if ts is None:
                continue
            seen[post.group(1)] = (ts, re.sub(r"<[^>]+>", " ", text_match.group(1)))
    return sorted(seen.values())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--sample",
        type=int,
        default=0,
        metavar="N",
        help=(
            "print N classified messages and N near-misses (messages carrying a "
            "marker or a kind stem that classified to nothing). Reviewing this "
            "output is a precondition for quoting any coverage figure: the "
            "marker tables were written before the corpus existed, so until a "
            "sample has been read, coverage measures the parser, not the channel"
        ),
    )
    arguments = parser.parse_args()

    if not arguments.raw.exists():
        print(f"kind-coverage: {arguments.raw} does not exist. The corpus is not in the tree.")
        return 1

    areas = AreaTable.from_csv()
    messages = read_messages(arguments.raw)
    print(f"kind-coverage: {len(messages)} messages read from {arguments.raw}")
    if not messages:
        return 1

    declarations: list[KindEvent] = []
    alerts: list[tuple[datetime, AreaMention]] = []
    unparsed = 0
    kinds_seen: Counter[ThreatKind] = Counter()
    marker_hits: Counter[str] = Counter()
    classified_texts: list[str] = []
    near_misses: list[str] = []

    for ts, text in messages:
        lowered = text.lower()
        found = classify_kind_message(text, areas)
        if found:
            classified_texts.append(text)
            for marker in KIND_DECLARE_MARKERS + KIND_LIFT_MARKERS:
                if marker in lowered:
                    marker_hits[marker] += 1
        elif any(marker in lowered for marker in KIND_DECLARE_MARKERS + KIND_LIFT_MARKERS) or any(
            stem in lowered for stem in KIND_MARKERS
        ):
            # A marker or a means stem fired and the classifier still said
            # nothing: exactly the set where an over-broad marker, a missing
            # lift phrasing, or an inversion would hide. This is the pile the
            # sample review exists to read.
            near_misses.append(text)
        if found:
            for area_id, oblast, kind, state in found:
                kinds_seen[kind] += 1
                declarations.append(
                    KindEvent(
                        area_id=area_id,
                        kind=kind,
                        state=state,
                        ts_source=ts,
                        ts_ingest=ts,
                        source_id="corpus",
                        oblast=oblast,
                    )
                )
            continue
        mentions = classify_message(text, areas)
        if not mentions:
            unparsed += 1
            continue
        alerts.extend((ts, mention) for mention in mentions)

    declared = sum(1 for event in declarations if event.state is KindState.DECLARED)
    lifted = len(declarations) - declared
    print(f"  declarations={declared} lifts={lifted} still-unparsed={unparsed}")
    print(f"  kinds named: {dict(kinds_seen)}")
    print(f"  marker hits on classified messages: {dict(marker_hits)}")
    print(f"  near-misses (marker or stem present, classified to nothing): {len(near_misses)}")

    if arguments.sample:
        # Seeded, so two people arguing about the sample are reading the same one.
        chooser = random.Random(309381)
        for label, pool in (("classified", classified_texts), ("near-miss", near_misses)):
            picked = chooser.sample(pool, min(arguments.sample, len(pool))) if pool else []
            print(f"\n  sample of {label} messages ({len(picked)} of {len(pool)}):")
            for text in picked:
                flat = " ".join(text.split())
                print(f"    [{label}] {flat[:200]}")
        print(
            "\n  ^ read both piles before quoting coverage. The declare table is looking"
            "\n    for an over-broad match (небезпека in non-declarations); the near-miss"
            "\n    pile for lifts phrased without відбій загрози, which the current table"
            "\n    would either drop or, worse, invert into a fresh declaration."
        )

    # Declaration to lift, per oblast and kind, in minutes.
    intervals: list[float] = []
    by_key: dict[tuple[str, ThreatKind], list[KindEvent]] = {}
    for event in declarations:
        by_key.setdefault((event.oblast, event.kind), []).append(event)
    for group in by_key.values():
        group.sort(key=lambda event: event.ts_source)
        open_at: datetime | None = None
        for event in group:
            if event.state is KindState.DECLARED:
                open_at = open_at or event.ts_source
            elif open_at is not None:
                intervals.append((event.ts_source - open_at).total_seconds() / 60.0)
                open_at = None
    if intervals:
        ordered = sorted(intervals)
        print(
            f"  declaration-to-lift minutes: n={len(ordered)} "
            f"median={statistics.median(ordered):.0f} "
            f"p90={ordered[int(0.9 * (len(ordered) - 1))]:.0f} "
            f"max={ordered[-1]:.0f}"
        )
        print("  ^ this replaces DEFAULT_KIND_TTL, which is currently an assumption")
    else:
        print("  declaration-to-lift: no closed pairs. The TTL stays an assumption")

    # Join coverage at candidate TTLs. Alerts are rebuilt as events at their own
    # timestamps; only the ACTIVE ones are asked about, since a regime attaches
    # to a threat rather than to its ending.
    from mavo.schema import AlertState, ThreatEvent

    active = [
        ThreatEvent(
            area_id=mention.area_id,
            state=mention.state,
            ts_source=ts,
            ts_ingest=ts,
            source_id="corpus",
            kind=mention.kind,
            oblast=mention.oblast,
        )
        for ts, mention in alerts
        if mention.state is AlertState.ACTIVE
    ]
    print(f"  active alerts: {len(active)}")
    for ttl in CANDIDATE_TTLS:
        _joined, report = apply_kinds(active, KindIndex(declarations, ttl=ttl))
        print(f"  ttl={ttl}: {report.line()}")

    print(
        "\nkind-coverage: record the chosen TTL and the coverage in "
        "docs/METHODOLOGY.md with today's date and the snapshot count above."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
