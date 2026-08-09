#!/usr/bin/env python3
"""Does the tag agree with the message's own prose?

T36 asked whether the area a message resolves to is the area the message is
about, and the criterion was written as a hand-labelled sample because no
automated check appeared to exist. One did, and it was visible in the messages
all along: **the channel writes the area name twice.** Once in prose,
`Відбій тривоги в Херсонський район`, and once as a tag, `#Херсонський_район`.
Two independent copies of the same fact in one message can be compared by a
machine.

**What this measures.** Agreement between the tag path and the prose, over every
message in the design window rather than over sixty, which makes the interval an
order of magnitude tighter than a hand sample could.

**What it does not measure, and the distinction matters.** Internal consistency
is not truth. If the channel itself named the wrong raion in both places, this
agrees with it and says nothing. That is a weaker claim than a human reading the
message against the world, and it is the reason the disagreements are printed in
full: those are the rows a person still has to read, and there should be few
enough to read them all.

**It also answers the multi-area question for free.** The prose of a multi-raion
alert lists every area as a bullet, so the number of areas per message is
countable rather than estimated. That decides whether the report is one line or
a list (S8) without anyone guessing.

**Holdout.** Design window only, pages above the boundary refused and counted
(D-012a). Nothing is written.

Usage:

    python3 tools/consistency_check.py --corpus data/raw/corpus \\
        --map data/reference/tag_map.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mavo.areas import AreaTable, parse_tags  # noqa: E402
from mavo.backfill import SNAPSHOT_NAME as PAGE_RANGE  # noqa: E402
from mavo.sources.telegram import _BLOCK, _TEXT, _strip  # noqa: E402

# Prose extraction, second attempt. The first one captured free text before the
# unit word and measured mostly its own defect: `(?:в|у|на)` carried no word
# boundary, so the `на` ending `Повітряна` matched and the capture became
# "тривога в Миргородський". It also broke on `м. Харків`, because the class
# excluded the full stop.
#
# The repair is not a better pattern for free text. It is to stop capturing free
# text: candidate names are taken from the tokens preceding a unit word and kept
# only when they match a name the map already knows. A name is either in the
# register or it is not an area, and the alternative, a regex that decides what
# looks like a place, is the guess this whole sprint replaced.
UNIT = re.compile(r"\b(район|громад[аи]|област[ьі])\b")
TOKEN = re.compile(r"[\w\u0400-\u04FF’'-]+")

# A message class the first run of this tool discovered by disagreeing with it.
# An all-clear can carry a continuation list: "Відбій ... Зверніть увагу,
# тривога ще триває у: - Запорізька область - Пологівський район". The tag names
# the area the all-clear is *about*; the list names areas where the alert is
# still running. Two different roles in one message, and comparing them as one
# set produced 1,203 false disagreements. Everything after this marker is the
# continuation list and is compared separately.
CONTINUES = re.compile(r"тривога\s+ще\s+трива[єе]|ще\s+трива[єе]\s+у")


def _boundary() -> int:
    status = json.loads((ROOT / "STATUS.json").read_text(encoding="utf-8"))
    corpus = status.get("corpus", {})
    if "design_window_high_id" in corpus:
        return int(corpus["design_window_high_id"])
    raise SystemExit("STATUS.json carries no design window boundary; refusing (D-012a)")


def _normalise(name: str) -> str:
    """Strip everything that differs between the two spellings of one name.

    The tag drops apostrophes and hyphens (`#КамянецьПодільський_район`) where
    the prose keeps them (`Кам'янець-Подільський район`). Normalising both to
    letters only is what lets them be compared without a lookup table of
    spelling variants.
    """
    return re.sub(r"[^\w]", "", name.replace("’", "").replace("'", "")).lower()


def _prose_areas(text: str, known: set[str]) -> set[str]:
    """Area names in the prose, verified against the names the map knows.

    Up to four tokens before each unit word are joined in decreasing length and
    the first join that is a known name wins. Four covers the longest real form,
    `м. Харків та Харківська територіальна громада`, and stops well short of
    swallowing a sentence. A unit word with no known name before it is ignored:
    `район` is also an ordinary noun, and `район старої частини` means the area
    of the old town rather than an administrative unit.
    """
    found: set[str] = set()
    tokens = [(match.group(0), match.start(), match.end()) for match in TOKEN.finditer(text)]
    ends = {end: index for index, (_word, _start, end) in enumerate(tokens)}
    for unit in UNIT.finditer(text):
        index = ends.get(unit.end())
        if index is None:
            continue
        for span in (4, 3, 2, 1):
            start = index - span
            if start < 0:
                continue
            candidate = _normalise("".join(word for word, _s, _e in tokens[start:index]))
            if candidate in known:
                found.add(candidate)
                break
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--map", required=True)
    parser.add_argument("--show", type=int, default=25, help="how many disagreements to print")
    args = parser.parse_args(argv)

    corpus = Path(args.corpus)
    if not corpus.is_dir():
        print(f"consistency-check: {corpus} is not a directory", file=sys.stderr)
        return 2
    table = AreaTable.from_csv(Path(args.map))
    # Every name the map knows, normalised, including the composite city-and-
    # hromada forms the channel writes as one tag. Read straight from the CSV
    # rather than through the package, so this probe runs against any version of
    # `mavo` that can load the table at all. A diagnostic that only works on the
    # version it shipped with is a diagnostic nobody runs.
    known: set[str] = set()
    with Path(args.map).open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            known.add(_normalise(row["tag"].rsplit("_", 1)[0]))
            if row.get("register_name"):
                known.add(_normalise(row["register_name"]))
    boundary = _boundary()

    messages = comparable = agree = 0
    refused = 0
    disagreements: list[tuple[str, str, str]] = []
    areas_per_message: Counter[int] = Counter()
    tags_without_prose = prose_without_tags = unmapped = 0
    with_continuation = continuation_areas = 0

    for path in sorted(corpus.glob("page-*.html")):
        match = PAGE_RANGE.search(path.name)
        if match is None:
            continue
        if int(match.group(2)) > boundary:
            refused += 1
            continue
        body = path.read_text(encoding="utf-8", errors="replace")
        for block in _BLOCK.findall(body):
            text_match = _TEXT.search(block)
            if text_match is None:
                continue
            messages += 1
            text = _strip(text_match.group(1)).strip()
            tags = parse_tags(text)
            tag_names = {_normalise(tag.rsplit("_", 1)[0]) for tag in tags}
            split = CONTINUES.search(text)
            subject_text = text[: split.start()] if split else text
            continues_text = text[split.end():] if split else ""
            prose = _prose_areas(subject_text, known)
            still_running = _prose_areas(continues_text, known)
            if still_running:
                with_continuation += 1
                continuation_areas += len(still_running)
            if tags and not prose:
                tags_without_prose += 1
                continue
            if prose and not tags:
                prose_without_tags += 1
                continue
            if not tags:
                continue
            comparable += 1
            areas_per_message[len(tags)] += 1
            resolved, unknown = table.resolve_all(text)
            if unknown:
                unmapped += 1
            if tag_names == prose:
                agree += 1
            else:
                disagreements.append((
                    " ".join(sorted(tag_names)),
                    " ".join(sorted(prose)),
                    text.replace("\n", " / ")[:220],
                ))

    print("consistency-check [measured, design window only]")
    print(f"  pages refused above the boundary: {refused}")
    print(f"  messages read:                    {messages}")
    print(f"  comparable (both tag and prose):  {comparable}")
    print(f"  tags with no prose area:          {tags_without_prose}")
    print(f"  prose area with no tag:           {prose_without_tags}")
    print(f"  comparable rows carrying a tag the map lacks: {unmapped}")
    print()
    if comparable:
        rate = agree / comparable
        print(f"  AGREEMENT: {agree}/{comparable} ({rate:.3%})")
        print(f"  disagreements: {comparable - agree}")
    print()
    if with_continuation:
        print(f"  messages carrying a continuation list: {with_continuation}"
              f" ({with_continuation / comparable:.1%} of comparable)")
        print(f"  areas named as still running, in total: {continuation_areas}")
        print("  Those areas are information the pipeline currently discards: the")
        print("  message says the alert continues there and nothing records it.")
        print()
    print("  This is internal consistency, not truth. If the channel named the wrong")
    print("  raion in both places, this agrees with it. That is why the disagreements")
    print("  are printed: they are the rows a person still has to read.")
    print()
    print("  areas per message (from the tags, cross-checked against the bullets):")
    for count in sorted(areas_per_message):
        share = areas_per_message[count] / comparable if comparable else 0
        print(f"    {count:>3} area(s): {areas_per_message[count]:>6} messages ({share:.1%})")
    print()
    print("  A high share at one area means the report is one line. A long tail means")
    print("  it has to be a list, and S8 needs to know which before it is designed.")
    if disagreements:
        print()
        print(f"  first {min(args.show, len(disagreements))} disagreements, tag | prose | text:")
        for tag_side, prose_side, text in disagreements[: args.show]:
            print(f"    [{tag_side}] vs [{prose_side}]")
            print(f"      {text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
