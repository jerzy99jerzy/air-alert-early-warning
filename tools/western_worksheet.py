#!/usr/bin/env python3
"""Turn a preserved `state.json` snapshot into a worksheet a person fills in.

**This tool produces the question, never the answer.** It reads what the
instrument claimed at one instant and writes one row per western area with the
verdict columns empty. The verdicts come from reading the channel, which is the
only part of this check that is independent of the instrument, and the only
part that cannot be automated without destroying the thing being measured.

Why it exists. On 2026-08-18 a real raid put eight western raions under alert
and the payload was preserved. Reading that payload back with a script - which
is what happened at the time - compares the instrument's output against the
instrument's own reference tables, so agreement is guaranteed by construction
rather than measured. The snapshot is a frozen claim. It becomes evidence only
when somebody puts the channel's own messages beside it.

What this cannot become. Eight rows carry no useful interval and this is not
T36, whose acceptance asks for fifty rows drawn from the tags-without-prose
population with a Wilson bound. What eight rows can do is something the
fifty-row sample and the twenty-message sample of 2026-08-10 both cannot: judge
intervals that reach the border. The 2026-08-10 sample judged intervals 700 to
1,000 km wide, where an error of tens of kilometres is invisible.

Usage:
    python3 tools/western_worksheet.py --snapshot ~/mavo-snapshot-TIMESTAMP.json
    python3 tools/western_worksheet.py --snapshot SNAP --feed FEED --out sheet.csv

With `--feed` the sheet also carries the transition times the day file records
for each area, so the `time_ok` column can be judged against something more
precise than `since`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

WESTERN = (
    "lviv", "volyn", "zakarpattia", "ivano-frankivsk",
    "ternopil", "rivne", "khmelnytskyi", "chernivtsi",
)

COLUMNS = (
    "katottg", "oblast", "oblast_name", "area_name",
    "border_km_lower", "border_km_upper",
    "alert", "kind", "since", "feed_transitions",
    "area_ok", "time_ok", "distance_plausible", "note",
)

VERDICTS = ("area_ok", "time_ok", "distance_plausible")


def _raion_names() -> dict[str, str]:
    """KATOTTG code to the raion's own name, read from the register map.

    `state.json` carries `oblast_name` and no raion name, so a sheet built from
    the snapshot alone would ask somebody to check "rivne" against a channel
    that names Dubno, Sarny and Varash separately. The name is the column the
    reading is actually done on.
    """
    path = Path(__file__).resolve().parent.parent / "data/reference/tag_map.csv"
    names: dict[str, str] = {}
    with path.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            code = (row.get("katottg_code") or "").strip()
            if code:
                names.setdefault(code, (row.get("register_name") or "").strip())
    return names


def _digest(path: Path) -> str:
    """The snapshot's fingerprint, so the sheet cannot drift from its source.

    A worksheet that does not name the exact bytes it was drawn from can be
    re-derived from a different snapshot and scored as though it were the same
    measurement. The 2026-08-10 sample carries a fingerprint for this reason
    and so does this one.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _transitions(feed: dict[str, Any], code: str) -> str:
    """Every transition the day file records for one area, oldest first."""
    marks = [
        f"{item.get('at')}={item.get('alert')}/{item.get('role')}"
        for item in feed.get("items", ())
        if item.get("area_id") == code or item.get("katottg") == code
    ]
    return " ".join(marks)


def build(snapshot: Path, feed_path: Path | None, out: Path) -> int:
    payload: dict[str, Any] = json.loads(snapshot.read_text(encoding="utf-8"))
    feed: dict[str, Any] = (
        json.loads(feed_path.read_text(encoding="utf-8")) if feed_path else {}
    )

    names = _raion_names()
    areas = [a for a in payload.get("areas", ()) if a.get("oblast") in WESTERN]
    if not areas:
        # Not a failure of the tool. A snapshot with no western area under
        # alert is the ordinary case, and saying so beats writing an empty
        # sheet somebody later reads as eight rows that all passed.
        print(
            f"western-worksheet: {snapshot.name} has no western area under "
            "alert; there is nothing here to check by hand",
            file=sys.stderr,
        )
        return 1

    # Nearest first, which is the order a reader would work in and the order in
    # which an error matters most.
    areas.sort(key=lambda a: (
        a.get("border_km_lower") is None, a.get("border_km_lower") or 0.0
    ))

    with out.open("w", encoding="utf-8", newline="") as handle:
        handle.write(f"# snapshot   {snapshot.name}\n")
        handle.write(f"# sha256     {_digest(snapshot)}\n")
        handle.write(f"# generated_at {payload.get('generated_at')}\n")
        if feed_path:
            handle.write(f"# feed       {feed_path.name}\n")
            handle.write(f"# feed sha256 {_digest(feed_path)}\n")
        handle.write(
            "# verdicts: y / n / ? - '?' is a real answer and means the "
            "channel did not say, not that the row was skipped\n"
        )
        handle.write(
            "# area_ok: did the channel name this raion in this window\n"
            "# time_ok: does `since` match when the channel announced it, "
            "within the poll interval of 30 s\n"
            "# distance_plausible: is the printed interval consistent with "
            "where the raion is; judged against a map, not against "
            "border_km.csv, which is the file under test\n"
        )
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for area in areas:
            code = area.get("katottg") or area.get("area_id") or ""
            writer.writerow({
                "katottg": code,
                "oblast": area.get("oblast", ""),
                "oblast_name": area.get("oblast_name", ""),
                # Empty when the register cannot name it, and empty is honest:
                # a blank asks the reader to look it up rather than handing
                # them the parent's name to check a child against.
                "area_name": names.get(code, ""),
                "border_km_lower": area.get("border_km_lower"),
                "border_km_upper": area.get("border_km_upper"),
                "alert": area.get("alert", ""),
                "kind": area.get("kind", ""),
                "since": area.get("since", ""),
                "feed_transitions": _transitions(feed, code) if feed else "",
                "area_ok": "", "time_ok": "", "distance_plausible": "",
                "note": "",
            })
    print(f"western-worksheet: {len(areas)} row(s) written to {out}")
    print("western-worksheet: fill one row at a time against the channel, then")
    print("western-worksheet: run this tool with --score to read it back")
    return 0


def score(sheet: Path) -> int:
    """Read a filled sheet back and report it without improving it.

    No pooled rate and no interval. Eight rows cannot carry one, and printing a
    percentage over eight rows invites it into a sentence where it will be read
    as the correctness of the instrument. The three columns are reported
    separately and so is the whole-row count, because a reader sees one line
    and a row is wrong if any of the three is.
    """
    rows = [
        row for row in csv.DictReader(
            line for line in sheet.read_text(encoding="utf-8").splitlines()
            if not line.startswith("#")
        )
    ]
    if not rows:
        print(f"western-worksheet: {sheet} has no rows", file=sys.stderr)
        return 1
    blank = [
        row["katottg"] for row in rows
        if any(not (row.get(column) or "").strip() for column in VERDICTS)
    ]
    if blank:
        # A partially filled sheet scored as though it were complete reports a
        # rate over the rows somebody happened to reach first, which is not a
        # sample. `label_sample.py` refuses the same way and for the same
        # reason.
        for code in blank:
            print(f"western-worksheet: {code} is not fully filled", file=sys.stderr)
        print(
            f"western-worksheet: {len(blank)} of {len(rows)} row(s) incomplete; "
            "refusing to score a partial sheet",
            file=sys.stderr,
        )
        return 1
    print(f"western-worksheet: {len(rows)} rows, {sheet.name}")
    for column in VERDICTS:
        tally = {"y": 0, "n": 0, "?": 0}
        for row in rows:
            tally[row[column].strip().lower()] = (
                tally.get(row[column].strip().lower(), 0) + 1
            )
        print(f"  {column:20s} y={tally.get('y', 0)} n={tally.get('n', 0)} "
              f"?={tally.get('?', 0)}")
    whole = sum(
        1 for row in rows
        if all(row[column].strip().lower() == "y" for column in VERDICTS)
    )
    print(f"  {'whole row correct':20s} {whole} of {len(rows)}")
    print("western-worksheet: no rate and no interval; eight rows carry neither")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--feed", type=Path)
    parser.add_argument("--out", type=Path, default=Path("western-worksheet.csv"))
    parser.add_argument("--score", type=Path)
    args = parser.parse_args()
    if args.score is not None:
        return score(args.score)
    if args.snapshot is None:
        parser.error("--snapshot is required unless --score is given")
    return build(args.snapshot, args.feed, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
