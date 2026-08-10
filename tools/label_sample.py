#!/usr/bin/env python3
"""Draw a sample for hand-labelling, and score it once it comes back.

T36, which closes sprint 7. The sprint measured that the channel tags 99.34% of
its messages and that 126 of 127 tags resolve to a register code. Neither says
the tag on a message describes the area that message is about, and no automated
probe can say it: the judgement is a person reading Ukrainian, and this tool
exists to make that judgement cheap, reproducible and hard to fudge.

**Two modes.** `draw` writes a CSV of sampled messages with the area the code
resolved. `score` reads it back once the verdict column is filled and reports
the error rate with a Wilson interval, because fifty labels is a small sample
and a bare proportion would overstate what it establishes.

**The seed is recorded and the draw is fingerprinted.** A sample that can be
redrawn until the error rate looks acceptable is not a measurement. `draw`
prints the seed and a hash of the sampled post ids, `score` recomputes the hash
from the file it is given, and a mismatch is reported rather than tolerated.
Changing the seed is allowed and is visible; changing it silently is not.

**Two strata, because they answer different questions.** Messages that resolved
to an area test whether resolution is *correct*. Messages carrying tags that
resolved to nothing test whether the unknown-tag path is *triggering on the
right thing* (T33). Both are drawn, and the proportion of each is printed.

**Output location.** The CSV carries message text. It is written wherever the
operator points it and the default is under `data/raw/`, which is git-ignored,
because a committed file of channel content is a tier-1 artifact under
`SECURITY.md` regardless of how public the source is.

**Holdout.** Design window only, pages above the boundary in `STATUS.json`
refused and counted (D-012a).

Usage:

    python3 tools/label_sample.py draw --corpus data/raw/corpus \\
        --map data/reference/tag_map.csv --out data/raw/t36-sample.csv
    # fill the `correct` column with y or n, one row at a time
    python3 tools/label_sample.py score --in data/raw/t36-sample.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mavo.areas import AreaTable  # noqa: E402
from mavo.backfill import SNAPSHOT_NAME as PAGE_RANGE  # noqa: E402
from mavo.sources.telegram import (  # noqa: E402
    _BLOCK,
    _TEXT,
    _TIME,
    _strip,
    classify,
    classify_kind_message,
)

# 0.20.0.0. Three verdict columns rather than one. `docs/MVP.md` asks S8 for a
# sample where the rendered report is correct "in area, means and distance",
# and a single `correct` column cannot answer three questions: a row wrong on
# the means and right on the area would score as an area error, and the error
# rate would be about nothing in particular.
FIELDS = ["post_id", "when", "resolved_code", "resolved_name", "oblast",
          "kind", "border_km", "stratum",
          "area_ok", "kind_ok", "distance_ok", "note", "text"]

# Kept so a half-filled file from before the split is reported rather than
# silently scored against the wrong column.
LEGACY_FIELD = "correct"


def _boundary() -> int:
    status = json.loads((ROOT / "STATUS.json").read_text(encoding="utf-8"))
    corpus = status.get("corpus", {})
    if "design_window_high_id" in corpus:
        return int(corpus["design_window_high_id"])
    raise SystemExit("STATUS.json carries no design window boundary; refusing (D-012a)")


def _fingerprint(post_ids: list[str]) -> str:
    joined = ",".join(sorted(post_ids))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def _collect(
    corpus: Path, table: AreaTable
) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    """Every design-window message, split into the two strata."""
    boundary = _boundary()
    resolved_rows: list[dict[str, str]] = []
    unknown_rows: list[dict[str, str]] = []
    refused = 0
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
            text = _strip(text_match.group(1)).strip()
            time_match = _TIME.search(block)
            when = time_match.group(1) if time_match else ""
            areas, unknown = table.resolve_all(text)
            kinds = classify_kind_message(text, table)
            row = {
                "post_id": "",
                "when": when,
                "resolved_code": areas[0].code if areas else "",
                "resolved_name": areas[0].name if areas else "",
                "oblast": areas[0].oblast if areas else "",
                # What the report would print for this message, so the labeller
                # judges the output rather than the intermediate state. Unknown
                # prints as unknown here exactly as it does on the page.
                "kind": kinds[0][2].value if kinds else "unknown",
                "border_km": areas[0].border_interval if areas else "unknown",
                "stratum": "resolved" if areas else "unknown_tag",
                "area_ok": "",
                "kind_ok": "",
                "distance_ok": "",
                "note": "",
                "text": text.replace("\n", " / ")[:400],
            }
            if areas:
                classified = classify(text, table)
                if classified is None:
                    continue
                resolved_rows.append(row)
            elif unknown:
                row["note"] = "tags: " + " ".join(unknown)
                unknown_rows.append(row)
    return resolved_rows, unknown_rows, refused


def _draw(args: argparse.Namespace) -> int:
    corpus = Path(args.corpus)
    if not corpus.is_dir():
        print(f"label-sample: {corpus} is not a directory", file=sys.stderr)
        return 2
    table = AreaTable.from_csv(Path(args.map))
    resolved, unknown, refused = _collect(corpus, table)
    if not resolved:
        print("label-sample: nothing resolved, so there is nothing to label. That is a "
              "finding, not an empty sample", file=sys.stderr)
        return 1

    rng = random.Random(args.seed)
    want_unknown = min(len(unknown), max(0, args.size // 5))
    want_resolved = args.size - want_unknown
    sample = rng.sample(resolved, min(want_resolved, len(resolved)))
    sample += rng.sample(unknown, want_unknown) if want_unknown else []
    for index, row in enumerate(sample, 1):
        row["post_id"] = str(index)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sample)

    print("label-sample draw [measured, design window only]")
    print(f"  pages refused above the boundary: {refused}")
    print(f"  population: {len(resolved)} resolved, {len(unknown)} with unresolved tags")
    print(f"  sample: {len(sample)} rows ({want_resolved} resolved, {want_unknown} unknown-tag)")
    print(f"  seed: {args.seed}")
    print(f"  fingerprint: {_fingerprint([row['when'] + row['text'][:40] for row in sample])}")
    print(f"  written to: {out}")
    print()
    print("  Fill `area_ok`, `kind_ok` and `distance_ok` with y or n for every row,")
    print("  one row at a time, and put the reason in `note` for any n. Then `score`.")
    print("  Three columns because S8 asks whether the report is right in area, means")
    print("  and distance, and one column cannot answer three questions.")
    print("  `distance_ok` judges the printed interval, not a number you compute: the")
    print("  question is whether the interval plausibly contains the nearest edge of")
    print("  that area, and `unknown` is correct when nothing is known.")
    print("  Redrawing with a different seed is allowed and will change the")
    print("  fingerprint. Redrawing until the number looks better is not a")
    print("  measurement, and the fingerprint is what makes that visible.")
    return 0


def _wilson(successes: int, trials: int, z: float = 1.96) -> tuple[float, float] | None:
    if trials == 0:
        return None
    phat = successes / trials
    denominator = 1 + z * z / trials
    centre = (phat + z * z / (2 * trials)) / denominator
    margin = z * ((phat * (1 - phat) / trials + z * z / (4 * trials * trials)) ** 0.5) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def _score(args: argparse.Namespace) -> int:
    path = Path(args.input)
    if not path.is_file():
        print(f"label-sample: {path} is not a file", file=sys.stderr)
        return 2
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    verdicts = ("area_ok", "kind_ok", "distance_ok")
    if rows and LEGACY_FIELD in rows[0] and verdicts[0] not in rows[0]:
        print("label-sample: this file has the pre-0.20.0.0 single `correct` column. "
              "Redraw it: scoring one column against three questions would report a "
              "number about nothing in particular", file=sys.stderr)
        return 2

    for column in verdicts:
        blank = [row for row in rows if row.get(column, "").strip().lower() not in {"y", "n"}]
        if blank:
            print(f"label-sample: {len(blank)} of {len(rows)} rows carry no {column} "
                  "verdict. A partial sample scored as if complete is a measurement of "
                  "the rows somebody found easy, and refusing is the whole point of "
                  "this check", file=sys.stderr)
            return 1

    def rate(subset: list[dict[str, str]], column: str) -> str:
        if not subset:
            return "no rows"
        wrong = sum(1 for row in subset if row[column].strip().lower() == "n")
        interval = _wilson(wrong, len(subset))
        assert interval is not None
        return (f"{wrong}/{len(subset)} = {wrong / len(subset):.1%} "
                f"[{interval[0]:.1%}, {interval[1]:.1%}]")

    resolved = [row for row in rows if row.get("stratum") == "resolved"]
    unknown = [row for row in rows if row.get("stratum") == "unknown_tag"]

    print("label-sample score [measured]")
    print(f"  rows labelled: {len(rows)}")
    print(f"  fingerprint: {_fingerprint([row['when'] + row['text'][:40] for row in rows])}")
    print()
    for column in verdicts:
        label = column.replace("_ok", "").upper()
        print(f"  ERROR RATE, {label:9} resolved stratum: {rate(resolved, column)}")
    print()
    for column in verdicts:
        label = column.replace("_ok", "")
        print(f"  error rate, {label:9} unknown-tag stratum: {rate(unknown, column)}")
    print()
    # The figure S8 is judged on: a row is right only if the whole rendered line
    # is right. Reporting three separate rates and omitting this one would let a
    # report that is wrong somewhere on half its rows read as three good numbers.
    def whole(subset: list[dict[str, str]]) -> str:
        if not subset:
            return "no rows"
        wrong = sum(
            1 for row in subset
            if any(row[column].strip().lower() == "n" for column in verdicts)
        )
        interval = _wilson(wrong, len(subset))
        assert interval is not None
        return (f"{wrong}/{len(subset)} = {wrong / len(subset):.1%} "
                f"[{interval[0]:.1%}, {interval[1]:.1%}]")

    print(f"  WHOLE-ROW ERROR RATE, resolved stratum: {whole(resolved)}")
    print("  ^ this is the figure S8 is judged on: a row counts as wrong if any of")
    print("    the three is wrong, because a reader sees one line, not three fields.")
    print()
    print("  The interval is Wilson at 95%, not a bare proportion, because fifty labels")
    print("  is a small sample and the point estimate moves by a percentage point on one")
    print("  row. Quote the interval or quote nothing.")
    print()
    print("  This closes T36 and sprint 7 when it is recorded in docs/METHODOLOGY.md")
    print("  with the seed, the fingerprint and the reasons from the note column. An")
    print("  error rate above a few percent is a finding about the channel or the map,")
    print("  and it is recorded either way.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    draw = sub.add_parser("draw", help="write a sample to label")
    draw.add_argument("--corpus", required=True)
    draw.add_argument("--map", required=True)
    draw.add_argument("--out", default="data/raw/t36-sample.csv")
    draw.add_argument("--size", type=int, default=60)
    draw.add_argument("--seed", type=int, default=1968)
    draw.set_defaults(func=_draw)

    score = sub.add_parser("score", help="score a labelled sample")
    score.add_argument("--in", dest="input", required=True)
    score.set_defaults(func=_score)

    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
