#!/usr/bin/env python3
"""How much would a western-only report actually say, and how often?

The measurement that follows from the tag join. The channel labels 99% of its
messages with a hashtag naming a raion or hromada, and 96.5% of tag occurrences
in the design window belong to front-line oblasts in the east and south. Those
carry nothing for a reader on the Polish side. The remaining 3.5% are the
western oblasts, which are the only alerts that can plausibly end in a crossing,
and the tag is what separates them.

**What this measures.** Messages carrying at least one western tag, per night
and per episode, plus how many distinct raions each episode touches. Episodes
are clusters separated by a quiet gap, because an alert and its all-clear are
one event and a report that fires on both has doubled its own volume for
nothing.

**Why episodes rather than messages.** A western raion tag appears about 58
times across 99 design nights, and the counts sit in a narrow band across almost
every western raion, which is what a simultaneous multi-raion alert looks like
rather than independent ones. Whether that is what it is, is exactly what this
tool checks: an episode touching thirty raions at once is a western-wide alert,
one touching a single raion is local.

**What it does not measure.** Anything about crossings, and anything about
correctness of the tag itself. It reports what a western-filtered feed would
have said and how often, which is the number the report tier is designed
against.

**Holdout.** Pages above the boundary in `STATUS.json` are refused and counted
(D-012a). Nothing is written.

Usage:

    python3 tools/west_activity.py --corpus data/raw/corpus --map data/reference/tag_map.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mavo.sources.telegram import _BLOCK, _TEXT, _TIME, _parse_timestamp  # noqa: E402

PAGE_RANGE = re.compile(r"page-(\d+)-(\d+)\.html$")
TAG = re.compile(r"#([\w\u0400-\u04FF’'-]+?)_(район|громада|область)", re.UNICODE)
WEST = (
    "Львівська", "Волинська", "Закарпатська", "Івано-Франківська",
    "Тернопільська", "Рівненська", "Хмельницька", "Чернівецька",
)


def _boundary() -> int:
    status = json.loads((ROOT / "STATUS.json").read_text(encoding="utf-8"))
    corpus = status.get("corpus", {})
    if "design_window_high_id" in corpus:
        return int(corpus["design_window_high_id"])
    raise SystemExit("STATUS.json carries no design window boundary; refusing to read (D-012a)")


def _western_tags(mapping: Path) -> dict[str, str]:
    """Tag to oblast, for tags the map places in a western oblast."""
    table: dict[str, str] = {}
    with mapping.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            oblast = row.get("oblast", "")
            if any(term in oblast for term in WEST):
                table[row["tag"]] = oblast
    return table


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--map", required=True, help="tag_map.csv")
    parser.add_argument("--gap-minutes", type=int, default=90,
                        help="quiet gap that ends an episode (default 90)")
    parser.add_argument("--cutover-hour", type=int, default=15)
    parser.add_argument("--window-nights", type=int, default=99,
                        help="nights in the design window, the rate denominator (default 99)")
    args = parser.parse_args(argv)

    directory = Path(args.corpus)
    if not directory.is_dir():
        print(f"west-activity: {directory} is not a directory", file=sys.stderr)
        return 2

    boundary = _boundary()
    pages, refused = [], 0
    for path in sorted(directory.glob("page-*.html")):
        match = PAGE_RANGE.search(path.name)
        if match is None:
            continue
        if int(match.group(2)) <= boundary:
            pages.append(path)
        else:
            refused += 1
    if not pages:
        print("west-activity: no pages below the boundary; that is a finding, not a zero",
              file=sys.stderr)
        return 1

    western = _western_tags(Path(args.map))
    stamped: list[tuple[datetime, frozenset[str]]] = []
    messages = 0
    western_messages = 0

    for path in pages:
        body = path.read_text(encoding="utf-8", errors="replace")
        for block in _BLOCK.findall(body):
            messages += 1
            text_match = _TEXT.search(block)
            time_match = _TIME.search(block)
            if text_match is None or time_match is None:
                continue
            found = {
                f"{name}_{unit}"
                for name, unit in TAG.findall(text_match.group(1))
                if f"{name}_{unit}" in western
            }
            if not found:
                continue
            when = _parse_timestamp(time_match.group(1))
            if when is None:
                continue
            western_messages += 1
            stamped.append((when.astimezone(UTC), frozenset(found)))

    stamped.sort(key=lambda pair: pair[0])

    episodes: list[tuple[datetime, datetime, set[str], int]] = []
    gap = timedelta(minutes=args.gap_minutes)
    for when, tags in stamped:
        if episodes and when - episodes[-1][1] <= gap:
            start, _end, areas, count = episodes[-1]
            episodes[-1] = (start, when, areas | set(tags), count + 1)
        else:
            episodes.append((when, when, set(tags), 1))

    nights: Counter[str] = Counter()
    per_night_areas: defaultdict[str, set[str]] = defaultdict(set)
    for start, _end, areas, _count in episodes:
        night = (start - timedelta(hours=args.cutover_hour)).date().isoformat()
        nights[night] += 1
        per_night_areas[night] |= areas
    covered = len({(w - timedelta(hours=args.cutover_hour)).date() for w, _t in stamped})

    print("west-activity [measured, design window only]")
    print(f"  pages read              {len(pages)}")
    print(f"  pages refused           {refused} (boundary {boundary}, D-012a)")
    print(f"  messages read           {messages}")
    print(f"  western tags in the map {len(western)}")
    print(f"  episode gap             {args.gap_minutes} min")
    print()
    share = western_messages / messages if messages else 0.0
    print(f"  messages with a western tag: {western_messages}/{messages} ({share:.2%})")
    print(f"  nights with any western activity: {covered}")
    print(f"  episodes: {len(episodes)}")
    if covered:
        print(f"  episodes per active night: {len(episodes) / covered:.2f}")
    print()
    print("  THE NUMBER THE REPORT TIER IS DESIGNED AGAINST")
    span_nights = args.window_nights
    # The denominator is every night in the window, not the subset in which the
    # phenomenon occurs. Dividing by active nights answers "how busy is a busy
    # night", which is not a rate any recipient experiences, and the first
    # version of this tool printed exactly that (docs/CHANNEL.md, section 6a).
    print(f"  episodes per week over ALL nights in the window: "
          f"{len(episodes) * 7 / span_nights:.2f}" if span_nights else "  rate unknown")
    wide = sum(1 for _s, _e, areas, _c in episodes if len(areas) >= 30)
    if span_nights:
        print(f"  of which region-wide (30+ areas): {wide * 7 / span_nights:.2f} per week")
    print(f"  for contrast, over active nights only: "
          f"{len(episodes) / (covered / 7):.2f} per week [do not quote this one]"
          if covered else "")
    print("  Read it as the volume a western-only report would have produced, not as")
    print("  a claim that any of it precedes a crossing. Nothing here knows that.")
    print()
    sizes = Counter(len(areas) for _s, _e, areas, _c in episodes)
    print("  episode breadth (distinct western areas touched):")
    for size in sorted(sizes):
        print(f"    {size:>3} areas: {sizes[size]:>4} episodes")
    print()
    print("  A band of episodes touching most western raions at once is a")
    print("  western-wide alert; single-area episodes are local. The split decides")
    print("  whether the report should be one line or a list.")
    print()
    print("  busiest nights by episode count:")
    for night, count in nights.most_common(10):
        print(f"    {night}  {count:>3} episodes, {len(per_night_areas[night]):>3} areas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
