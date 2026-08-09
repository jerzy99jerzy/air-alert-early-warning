#!/usr/bin/env python3
"""Does the state register's wording match what the channel actually emits?

S7's first question, and the one the five-sprint plan rests on. The shipped
pattern table keyed on oblast names and scored 0 of 20 against real messages
(F23), because the channel names raions and hromadas. The proposed replacement
is the Ukrainian state register (KATOTTG, Кодифікатор адміністративно-
територіальних одиниць та територій територіальних громад), which carries every
raion and hromada with a stable code. Whether its *names* appear in the
channel's *wording* is an empirical question that nothing in this repository has
answered, and it is answered here rather than assumed.

**What this measures.** The share of design-window messages in which at least
one register name is recognisable, broken down by category and by oblast, plus
the register entries that never appear at all. Both halves matter: a high hit
rate with a handful of entries doing all the work is a different situation from
a high hit rate spread across the register.

**Three axes, and the third is the one that matters.** Stem matching against
free text, the same restricted to stems that are unambiguous across oblasts,
and the channel's own structure. The first run of this tool reported 16.56% on
the first axis and attributed the top stem to Lviv oblast; a grep showed the
text was `Миколаївський район`, a raion of *Mykolaiv* oblast, listed beside its
neighbours. Two lessons, both now built in: a stem shared across oblasts is
evidence of nothing until disambiguated, and this tool must never again present
an arbitrary first match as an attribution.

**The structural axis.** The same grep showed what the free-text search was
working around: the channel emits lists (`<br/>• Вознесенський район`) and
hashtags (`#Миколаївський_район`). Those carry the unit type explicitly and
need no stemming. Structure is measured separately from prose because if the
structure is reliable the register stops being a search vocabulary and becomes
what it should be, a table to validate and geocode against.

**What none of this measures.** Whether a match is *correct* for the message it
sits in. That is S7's hand-labelled sample and is not this tool's job to
assert.

**Matching.** Ukrainian is inflected: the register holds `Володимирський` and a
message may carry `у Володимирському районі`. Matching is therefore on a
truncated stem rather than the full form, which trades precision for recall
deliberately: this probe exists to find out whether the vocabulary is there, and
a stem that over-matches inflates the number in a direction the next step will
catch. The truncation length is a flag and is printed on every run.

**Holdout.** Pages above the boundary frozen in `STATUS.json` are refused and
counted (D-012a). Nothing is written.

Usage:

    python3 tools/register_probe.py --corpus data/raw/corpus --register katottg.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mavo.sources.telegram import _BLOCK, _TEXT, _strip  # noqa: E402

PAGE_RANGE = re.compile(r"page-(\d+)-(\d+)\.html$")
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


def _design_pages(directory: Path, boundary: int) -> tuple[list[Path], int]:
    kept: list[Path] = []
    refused = 0
    for path in sorted(directory.glob("page-*.html")):
        match = PAGE_RANGE.search(path.name)
        if match is None:
            continue
        if int(match.group(2)) <= boundary:
            kept.append(path)
        else:
            refused += 1
    return kept, refused


TAG = re.compile(r"#([\w\u0400-\u04FF’\'-]+?)_(район|громада|область)", re.UNICODE)
BULLET = re.compile(r"[•·]\s*([^<\n•]{2,60}?)\s+(район|громада|область)", re.UNICODE)


def _entries(register: Path, west_only: bool, stem: int) -> dict[str, list[tuple[str, str, str]]]:
    """Stem to entries. Each entry is (category, full name, oblast name)."""
    data = json.loads(register.read_text(encoding="utf-8"))
    oblasts = {item["level1"]: item["name"] for item in data["items"] if item["category"] == "O"}
    if west_only:
        oblasts = {code: name for code, name in oblasts.items()
                   if any(term in name for term in WEST)}
    table: dict[str, list[tuple[str, str, str]]] = {}
    for item in data["items"]:
        if item["category"] not in {"P", "H"}:
            continue
        if item["level1"] not in oblasts:
            continue
        name = item["name"]
        if len(name) <= stem:
            continue
        table.setdefault(name[:stem].lower(), []).append(
            (item["category"], name, oblasts[item["level1"]])
        )
    return table


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--register", required=True, help="KATOTTG JSON")
    parser.add_argument("--stem", type=int, default=6, help="stem length for matching (default 6)")
    parser.add_argument("--all-oblasts", action="store_true",
                        help="match the whole country instead of the eight western oblasts")
    args = parser.parse_args(argv)

    directory = Path(args.corpus)
    if not directory.is_dir():
        print(f"register-probe: {directory} is not a directory", file=sys.stderr)
        return 2

    boundary = _boundary()
    pages, refused = _design_pages(directory, boundary)
    if not pages:
        print("register-probe: no pages below the boundary. Nothing measured, and that is "
              "a finding rather than a zero", file=sys.stderr)
        return 1

    table = _entries(Path(args.register), not args.all_oblasts, args.stem)
    # Ambiguity is judged against the whole country, never against the restricted
    # scope. The defect this replaces: `Миколаївський` is unique among the eight
    # western oblasts and collides with a raion of Mykolaiv oblast, so a scope
    # restriction made a colliding stem look clean. A restriction on the register
    # is not a restriction on the text.
    nationwide = _entries(Path(args.register), False, args.stem)
    hits: Counter[str] = Counter()
    by_category: Counter[str] = Counter()
    by_oblast: Counter[str] = Counter()
    messages = 0
    matched_messages = 0
    unambiguous_messages = 0
    tagged_messages = 0
    bulleted_messages = 0
    tags: Counter[str] = Counter()
    bullets: Counter[str] = Counter()
    tag_units: Counter[str] = Counter()

    # A stem is ambiguous when its entries do not all sit in one oblast. Those
    # stems are counted and excluded from the second figure rather than silently
    # attributed to whichever entry the register happened to list first.
    ambiguous = {
        key for key in table
        if len({oblast for _c, _n, oblast in nationwide.get(key, [])}) > 1
    }

    for path in pages:
        body = path.read_text(encoding="utf-8", errors="replace")
        for block in _BLOCK.findall(body):
            text_match = _TEXT.search(block)
            messages += 1
            if text_match is None:
                continue
            lowered = _strip(text_match.group(1)).lower()
            raw = text_match.group(1)
            for name, unit in TAG.findall(raw):
                tags[f"{name}_{unit}"] += 1
                tag_units[unit] += 1
            if TAG.search(raw):
                tagged_messages += 1
            for name, unit in BULLET.findall(_strip(raw)):
                bullets[f"{name.strip()} {unit}"] += 1
            if BULLET.search(_strip(raw)):
                bulleted_messages += 1

            found = {stem for stem in table if stem in lowered}
            if not found:
                continue
            matched_messages += 1
            if found - ambiguous:
                unambiguous_messages += 1
            for stem in found:
                hits[stem] += 1
                if stem in ambiguous:
                    by_category["ambiguous"] += 1
                    continue
                category, _name, oblast = table[stem][0]
                by_category[category] += 1
                by_oblast[oblast] += 1

    scope = "whole country" if args.all_oblasts else "eight western oblasts"
    print("register-probe [measured, design window only]")
    print(f"  pages read           {len(pages)}")
    print(f"  pages refused        {refused} (above the frozen boundary {boundary}, D-012a)")
    print(f"  messages read        {messages}")
    print(f"  register scope       {scope}")
    print(f"  register stems       {len(table)}")
    print(f"  stem length          {args.stem}")
    print()
    share = matched_messages / messages if messages else 0.0
    unambiguous_share = unambiguous_messages / messages if messages else 0.0
    print(f"  A. any register stem, including ambiguous ones: "
          f"{matched_messages}/{messages} ({share:.2%})")
    print("     Read this as an upper bound and nothing else. A stem shared across")
    print("     oblasts matches a message about a different part of the country.")
    print(f"  B. at least one stem unambiguous across oblasts: "
          f"{unambiguous_messages}/{messages} ({unambiguous_share:.2%})")
    print(f"     stems colliding somewhere in the country: {len(ambiguous)} of {len(table)}")
    print(f"  C. carries a hashtag of the form #Name_unit: "
          f"{tagged_messages}/{messages} ({tagged_messages / messages if messages else 0:.2%})")
    print(f"  D. carries a bulleted 'Name unit' list item: "
          f"{bulleted_messages}/{messages} ({bulleted_messages / messages if messages else 0:.2%})")
    print()
    print("  C and D need no stemming and carry the unit type explicitly. If either")
    print("  is high, the register stops being a search vocabulary and becomes what")
    print("  it should be: a table to validate and geocode against.")
    print()
    print("  hashtag units:", dict(tag_units) or "none")
    print(f"  distinct hashtags: {len(tags)} | distinct bulleted names: {len(bullets)}")
    print("  top 10 hashtags:")
    for tag, count in tags.most_common(10):
        print(f"    {count:>6}  #{tag}")
    print("  top 10 bulleted names:")
    for name, count in bullets.most_common(10):
        print(f"    {count:>6}  {name}")
    print()
    print("  by category (P raion, H hromada, ambiguous excluded from attribution):",
          dict(by_category) or "none")
    print(f"  register entries never seen: {len(table) - len(hits)} of {len(table)} stems")
    print()
    print("  top 15 stems by message count:")
    for stem, count in hits.most_common(15):
        category, name, oblast = table[stem][0]
        collisions = len(table[stem])
        note = f" (+{collisions - 1} same-stem entries)" if collisions > 1 else ""
        print(f"    {count:>6}  {name} [{category}] {oblast}{note}")
    print()
    print("  by oblast (unambiguous stems only, and still not a correctness claim):")
    for oblast, count in by_oblast.most_common():
        print(f"    {count:>6}  {oblast}")
    print()
    print("  A high number carried by two or three stems is a different situation from")
    print("  the same number spread across the register. Read the two lists together.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
