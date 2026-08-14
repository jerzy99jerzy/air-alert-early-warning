"""P1. What the channel tags that the register map does not hold (T16, T34).

`data/reference/tag_map.csv` holds 127 rows built from the **design window**:
48,540 messages over 99 nights. The corpus is 61,041 messages over 118 days.
Tags that appear only outside the window are therefore absent from the map by
construction, not by oversight, and `AreaTable.resolve_all` returns them in its
second element - the one its own docstring calls load-bearing, because a caller
that ignores it has turned a new area into silence.

This tool reads that second element across the whole corpus and answers three
questions the near-miss pile raised and nobody has costed:

1. **How many distinct tags does the channel emit that the map cannot
   resolve, and how many messages do they account for?** If this is a handful
   of rare tags, extending the map buys nothing and P2 is not worth its
   documentation debt.

2. **How many of those messages carry a threat-kind marker?** This is the
   number that decides. `Загроза артобстрілу` over `Покровська територіальна
   громада` carries both a declaration marker and a kind, and is lost on the
   tag alone. Every such message is a kind declaration the join never sees.

3. **Are they concentrated outside the design window?** If the unresolved tags
   cluster in the held-out period, the cause is the map's construction and the
   repair is mechanical. If they are spread evenly, something else is going on
   and extending the map is treating a symptom.

**A correction this tool exists to support.** `docs/METHODOLOGY.md` attributes
the artillery near-misses to T34. T34 is the 321 design-window messages
carrying **no tag at all**. These messages carry a tag that the map does not
hold, which is a different population with a different repair, and no task in
`TODO.md` covers it. That mis-attribution is why the work looked scheduled.

## What this deliberately does not do

It does not resolve anything against KATOTTG, propose additions to the map, or
estimate what coverage would become. Those need the numbers below to exist
first, and one of them may make the whole line of work not worth taking.

## Usage

    PYTHONPATH=. python3 tools/unmapped_tags.py --raw data/raw --sample 40

The corpus is gitignored (tier 1), so this cannot run in CI and its output is a
measurement to be recorded in `docs/METHODOLOGY.md` by hand, with its date and
the message count it read. Same discipline as `tools/kind_coverage.py`, whose
corpus reader this reuses rather than writing a second one that could disagree
with it.
"""
from __future__ import annotations

import argparse
import random
from collections import Counter
from datetime import datetime
from pathlib import Path

from mavo.areas import AreaTable, parse_tags
from mavo.backfill import read_snapshot_messages
from mavo.schema import ThreatKind
from mavo.sources.telegram import (
    KIND_DECLARE_MARKERS,
    KIND_LIFT_MARKERS,
    KIND_MARKERS,
)

#: The design window's upper post id, from STATUS.json's corpus block. Used
#: only to split the report, never to filter: a tag is unresolved or it is not,
#: and which side of the boundary it fell on is a diagnosis rather than a
#: criterion.
DESIGN_WINDOW_HIGH_ID = 309380


def _kind_signal(text: str) -> tuple[bool, bool, tuple[ThreatKind, ...]]:
    """(declares, lifts, kinds named) read from the text alone.

    Read from the text rather than through `classify_kind_message`, and the
    difference is not stylistic. That function returns nothing when the area
    does not resolve, and every message in this population is one whose tag did
    not resolve, so routing through it produces two counters that are zero by
    construction and read as a finding. The first run of this tool did exactly
    that; the numbers below are what the message says, independent of whether
    anything could be done with it.
    """
    lowered = text.lower()
    declares = any(marker.lower() in lowered for marker in KIND_DECLARE_MARKERS)
    lifts = any(marker.lower() in lowered for marker in KIND_LIFT_MARKERS)
    kinds = tuple({kind for stem, kind in KIND_MARKERS.items() if stem.lower() in lowered})
    return declares, lifts, kinds


def _quantiles(values: list[int]) -> str:
    if not values:
        return "n=0"
    ordered = sorted(values)
    def at(fraction: float) -> int:
        return ordered[min(len(ordered) - 1, int(fraction * len(ordered)))]
    return (f"n={len(ordered)} min={ordered[0]} median={at(0.5)} "
            f"p90={at(0.9)} max={ordered[-1]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw"))
    parser.add_argument("--sample", type=int, default=0, metavar="N",
                        help="print N unresolved-tag messages, chosen at random. "
                             "Reading them is a precondition for quoting any "
                             "figure below: an unresolved tag may be a real area, "
                             "a typo, or a construction this parser mishandles, "
                             "and only a person can tell those apart")
    parser.add_argument("--seed", type=int, default=20260814,
                        help="sampling seed, printed with the output so the "
                             "sample can be reproduced exactly")
    arguments = parser.parse_args()

    if not arguments.raw.exists():
        print(f"unmapped-tags: {arguments.raw} does not exist. "
              "The corpus is not in the tree.")
        return 1

    areas = AreaTable.from_csv()
    messages: list[tuple[datetime, str]] = read_snapshot_messages(arguments.raw)
    print(f"unmapped-tags: {len(messages)} messages read from {arguments.raw}")
    print(f"unmapped-tags: map holds {len(areas)} rows, "
          f"{len(areas.unresolved)} of them marked unresolved in the file itself")
    if not messages:
        return 1

    tagged = 0
    untagged = 0
    fully_resolved = 0
    with_unresolved = 0
    unresolved_tags: Counter[str] = Counter()
    unresolved_with_kind = 0
    unresolved_with_kind_tags: Counter[str] = Counter()
    would_declare = 0
    would_lift = 0
    ambiguous_markers = 0
    marker_without_kind = 0
    kinds_lost: Counter[ThreatKind] = Counter()
    examples: list[str] = []

    for _, text in messages:
        tags = parse_tags(text)
        if not tags:
            untagged += 1
            continue
        tagged += 1
        _, unknown = areas.resolve_all(text)
        if not unknown:
            fully_resolved += 1
            continue
        with_unresolved += 1
        unresolved_tags.update(unknown)
        examples.append(text)

        declares, lifts, kinds = _kind_signal(text)
        if not (declares or lifts or kinds):
            continue
        unresolved_with_kind += 1
        unresolved_with_kind_tags.update(unknown)
        would_declare += 1 if declares else 0
        would_lift += 1 if lifts else 0
        for kind in kinds:
            kinds_lost[kind] += 1
        if declares and lifts:
            ambiguous_markers += 1
        if (declares or lifts) and not kinds:
            marker_without_kind += 1

    print()
    print("== tags, over the whole corpus ==")
    print(f"messages with no tag at all         {untagged:>8}  (T34's population)")
    print(f"messages with at least one tag      {tagged:>8}")
    print(f"  every tag resolved                {fully_resolved:>8}")
    print(f"  at least one tag unresolved       {with_unresolved:>8}")
    print(f"distinct unresolved tags            {len(unresolved_tags):>8}")

    print()
    print("== what the unresolved tags cost the kind join ==")
    print(f"unresolved-tag messages carrying a kind signal   {unresolved_with_kind:>8}")
    print(f"  of those, carrying a declaration marker        {would_declare:>8}")
    print(f"  of those, carrying a lift marker               {would_lift:>8}")
    print(f"  carrying both markers at once                  {ambiguous_markers:>8}")
    print(f"  carrying a marker but naming no kind           {marker_without_kind:>8}")
    if kinds_lost:
        print("  by kind: " + ", ".join(
            f"{kind.value}={count}" for kind, count in kinds_lost.most_common()))
    print()
    print("  Read these two blocks together. A large first number with a small")
    print("  second one means extending the map buys area coverage and not kind")
    print("  coverage, which is a different argument and a weaker one.")

    print()
    print("== the unresolved tags themselves, most frequent first ==")
    for tag, count in unresolved_tags.most_common(40):
        with_signal = unresolved_with_kind_tags.get(tag, 0)
        print(f"  {count:>6}  {with_signal:>5} with kind signal   {tag}")
    if len(unresolved_tags) > 40:
        print(f"  ... and {len(unresolved_tags) - 40} more")

    print()
    print("== occurrence counts, so a long tail is visible as one ==")
    print("  " + _quantiles(list(unresolved_tags.values())))
    singletons = sum(1 for count in unresolved_tags.values() if count == 1)
    print(f"  tags occurring exactly once: {singletons} of {len(unresolved_tags)}")
    print("  A pile dominated by singletons is typos and one-off constructions.")
    print("  A pile with a heavy head is areas the map does not hold. These call")
    print("  for different repairs and the distinction is not visible in a total.")

    if arguments.sample and examples:
        rng = random.Random(arguments.seed)
        chosen = rng.sample(examples, min(arguments.sample, len(examples)))
        print()
        print(f"== {len(chosen)} unresolved-tag messages, seed {arguments.seed} ==")
        print("   Read before quoting anything above.")
        for text in chosen:
            flat = " ".join(text.split())
            print(f"  - {flat[:300]}")

    print()
    print("unmapped-tags: nothing here resolves a tag or proposes a map change.")
    print("  Both need these numbers to exist first, and one of them may say the")
    print("  work is not worth taking.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
