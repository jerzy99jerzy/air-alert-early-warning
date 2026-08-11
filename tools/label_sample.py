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
hashes the sampled post ids and writes the seed and hash into a draw record
beside the CSV; `score` recomputes the hash from the file it is given and
refuses a mismatch against the record (F87: this comparison was promised from
the first version and had no mechanism until 0.21.5.0). Changing the seed is
allowed and is visible; changing it silently is not.

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
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mavo.areas import AreaTable  # noqa: E402
from mavo.backfill import SNAPSHOT_NAME as PAGE_RANGE  # noqa: E402
from mavo.sources.telegram import (  # noqa: E402
    _TEXT,
    _TIME,
    _strip,
    classify,
    classify_kind_message,
)

# F87. The block regex in `telegram.py` isolates a message but discards its
# post id. This one keeps it, so the `post_id` column holds the channel's own
# id rather than a row number, the docstring's "hash of the sampled post ids"
# is what the fingerprint actually is, and a sampled row can be traced to its
# post instead of only to its text.
_BLOCK_WITH_ID = re.compile(
    r'data-post="[^"/]+/(\d+)"(.*?)(?=data-post="[^"/]+/\d+"|\Z)', re.S
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


def _sidecar(csv_path: Path) -> Path:
    """The draw record beside the sample: seed, fingerprint, stratum counts."""
    return csv_path.with_suffix(csv_path.suffix + ".draw.json")


def _collect(
    corpus: Path, table: AreaTable
) -> tuple[list[dict[str, str]], list[dict[str, str]], int, int]:
    """Every design-window message, split into the three strata.

    The fourth return is the number of messages that resolved an area and were
    then refused by ``classify`` - printed by the caller rather than silently
    dropped from the population, because a population trimmed without a count
    is a denominator nobody can check (F87).
    """
    boundary = _boundary()
    resolved_rows: list[dict[str, str]] = []
    unknown_rows: list[dict[str, str]] = []
    refused = 0
    classify_refused = 0
    for path in sorted(corpus.glob("page-*.html")):
        match = PAGE_RANGE.search(path.name)
        if match is None:
            continue
        if int(match.group(2)) > boundary:
            refused += 1
            continue
        body = path.read_text(encoding="utf-8", errors="replace")
        for block_match in _BLOCK_WITH_ID.finditer(body):
            post_id, block = block_match.group(1), block_match.group(2)
            text_match = _TEXT.search(block)
            if text_match is None:
                continue
            text = _strip(text_match.group(1)).strip()
            time_match = _TIME.search(block)
            when = time_match.group(1) if time_match else ""
            areas, unknown = table.resolve_all(text)
            kinds = classify_kind_message(text, table)
            row = {
                # F87. The channel's own id, not a row number: the fingerprint
                # is computed over these, and a sampled row is traceable to its
                # post rather than only to a text prefix.
                "post_id": post_id,
                "when": when,
                # Every area the message names, not the first. A channel
                # message routinely lists five raions and the report emits an
                # event for each; showing one would ask the labeller to judge
                # something the product does not do. Found in the first real
                # draw, where 4 of 40 rows were multi-area.
                "resolved_code": " ".join(area.code for area in areas),
                "resolved_name": " / ".join(area.name for area in areas),
                "oblast": " / ".join(dict.fromkeys(area.oblast for area in areas)),
                # What the report would print for this message, so the labeller
                # judges the output rather than the intermediate state. Unknown
                # prints as unknown here exactly as it does on the page.
                "kind": kinds[0][2].value if kinds else "unknown",
                "border_km": (
                    " / ".join(area.border_interval for area in areas)
                    if areas else "unknown"
                ),
                # Three strata, not two, since 0.21.3.0. The western stratum
                # exists because it is the only one the product is for and it
                # is 3.5% of traffic: a proportional draw of fifty rows
                # contains one or two western messages, and S8 asks for a
                # figure about the areas near the border. See `_draw`.
                # A message naming any western area is western: it is one this
                # product would report on, whatever else it also names.
                "stratum": (
                    "unknown_tag" if not areas
                    else "western" if any(area.is_western for area in areas)
                    else "front_line"
                ),
                "area_ok": "",
                "kind_ok": "",
                "distance_ok": "",
                "note": "",
                "text": text.replace("\n", " / ")[:400],
            }
            if areas:
                classified = classify(text, table)
                if classified is None:
                    classify_refused += 1
                    continue
                resolved_rows.append(row)
            elif unknown:
                row["note"] = "tags: " + " ".join(unknown)
                unknown_rows.append(row)
    return resolved_rows, unknown_rows, refused, classify_refused


def _draw(args: argparse.Namespace) -> int:
    corpus = Path(args.corpus)
    if not corpus.is_dir():
        print(f"label-sample: {corpus} is not a directory", file=sys.stderr)
        return 2
    table = AreaTable.from_csv(Path(args.map))
    resolved, unknown, refused, classify_refused = _collect(corpus, table)
    if not resolved:
        print("label-sample: nothing resolved, so there is nothing to label. That is a "
              "finding, not an empty sample", file=sys.stderr)
        return 1

    western = [row for row in resolved if row["stratum"] == "western"]
    front_line = [row for row in resolved if row["stratum"] == "front_line"]

    # Deliberate oversampling of the west, and the consequence is stated here
    # and again in `score`: the result is **not** an error rate for the
    # channel's traffic. It is one for the areas this product reports on, which
    # is the question S8 asks. A proportional draw would answer the first
    # question, which nobody is asking, using a sample of one or two rows for
    # the second.
    rng = random.Random(args.seed)
    want_unknown = min(len(unknown), max(0, args.size // 5))
    remaining = args.size - want_unknown
    want_western = min(len(western), remaining // 2)
    want_front = remaining - want_western
    if want_western < remaining // 2:
        print(f"label-sample: only {len(western)} western messages exist in the "
              f"design window, so the western stratum is smaller than asked for. "
              f"That is a property of the corpus, not a sampling failure",
              file=sys.stderr)
    sample = rng.sample(western, want_western)
    sample += rng.sample(front_line, min(want_front, len(front_line)))
    sample += rng.sample(unknown, want_unknown) if want_unknown else []

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(sample)

    # F87. The docstring has promised since the first version that `score`
    # reports a fingerprint mismatch rather than tolerating it, and nothing
    # implemented the comparison: the draw printed a hash to a terminal and
    # the terminal is not a reader. The draw record now lands beside the CSV,
    # `score` compares against it, and the promise has a mechanism.
    fingerprint = _fingerprint([row["post_id"] for row in sample])
    record = _sidecar(out)
    record.write_text(
        json.dumps(
            {
                "seed": args.seed,
                "fingerprint": fingerprint,
                "rows": len(sample),
                "drawn": {
                    "western": want_western,
                    "front_line": min(want_front, len(front_line)),
                    "unknown_tag": want_unknown,
                },
            },
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )

    print("label-sample draw [measured, design window only]")
    print(f"  pages refused above the boundary: {refused}")
    print(f"  population: {len(western)} western, {len(front_line)} front-line, "
          f"{len(unknown)} with unresolved tags")
    if classify_refused:
        print(f"  resolved an area but refused by classify: {classify_refused} "
              "(outside the population; the rate is about messages the report renders)")
    print(f"  drawn: {want_western} western, {min(want_front, len(front_line))} "
          f"front-line, {want_unknown} unresolved")
    print("  ^ the west is oversampled on purpose. The resulting rate is about the")
    print("    areas this product reports on, not about the channel's traffic.")
    print(f"  sample: {len(sample)} rows")
    print(f"  seed: {args.seed}")
    print(f"  fingerprint: {fingerprint} (over the sampled post ids)")
    print(f"  written to: {out}")
    print(f"  draw record: {record}")
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

    western = [row for row in rows if row.get("stratum") == "western"]
    front_line = [row for row in rows if row.get("stratum") == "front_line"]
    unknown = [row for row in rows if row.get("stratum") == "unknown_tag"]
    legacy = [row for row in rows if row.get("stratum") == "resolved"]
    if legacy:
        print("label-sample: this file was drawn before 0.21.3.0, when resolved "
              "messages were one stratum rather than western and front-line. "
              "Redraw it: scoring it would report a figure about a mixture "
              "nobody chose", file=sys.stderr)
        return 2

    print("label-sample score [measured]")
    print(f"  rows labelled: {len(rows)}")
    recomputed = _fingerprint([row.get("post_id", "") for row in rows])
    record = _sidecar(path)
    if record.is_file():
        recorded = json.loads(record.read_text(encoding="utf-8"))
        if recorded.get("fingerprint") != recomputed:
            # F87. This comparison is what the module docstring has promised
            # all along. A file whose rows do not match its own draw record has
            # been edited, mixed from two draws, or redrawn without its record,
            # and a rate over it would be a measurement of nobody knows what.
            print(f"label-sample: fingerprint mismatch. The draw record says "
                  f"{recorded.get('fingerprint')}, the file's rows hash to "
                  f"{recomputed}. The rows scored must be the rows drawn; "
                  "refusing", file=sys.stderr)
            return 2
        print(f"  fingerprint: {recomputed} (matches the draw record, "
              f"seed {recorded.get('seed')})")
    else:
        print(f"  fingerprint: {recomputed}")
        print(f"  WARNING: no draw record at {record.name}; the fingerprint is "
              "printed but nothing here can verify these are the rows that were "
              "drawn. Quote the draw output alongside the score.")
    print()
    for column in verdicts:
        label = column.replace("_ok", "").upper()
        print(f"  ERROR RATE, {label:9} western stratum:     {rate(western, column)}")
    print()
    for column in verdicts:
        label = column.replace("_ok", "")
        print(f"  error rate, {label:9} front-line stratum:  {rate(front_line, column)}")
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

    print(f"  WHOLE-ROW ERROR RATE, western stratum:    {whole(western)}")
    print(f"  whole-row error rate, front-line stratum: {whole(front_line)}")
    print("  ^ the western figure is the one S8 is judged on: it is about the areas")
    print("    this product reports on, and a row counts as wrong if any of the three")
    print("    is wrong, because a reader sees one line rather than three fields.")
    print()
    print("  NO COMBINED RATE IS PRINTED, and that is deliberate. The west was")
    print("  oversampled on purpose, so a pooled figure would be neither the rate")
    print("  for the product nor the rate for the channel: it would be an average")
    print("  over a mixture whose weights were chosen by the sampler.")
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
