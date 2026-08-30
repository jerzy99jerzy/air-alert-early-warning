#!/usr/bin/env python3
"""What `/alerts` claims about each region's level, against what the map resolves.

The switchover to `api.ukrainealarm.com` (D-040) moved this project onto a
source that names regions in prose at a level the area table was never built
for. `data/reference/tag_map.csv` holds 118 raion rows, 7 hromada rows and 2
oblast rows, and the table was assembled from the channel's hashtags, which are
raion-shaped by construction. Whether that mismatch costs anything today is a
question about the live payload and nothing in this repository can answer it.

**This reads the raw JSON and not `parse_alerts`.** `ApiAlert` carries
`region_id`, `region_name`, `oblast`, `alert_type`, `started_at` and the alert's
own dict, and `regionType` survives none of them: the field naming the level is
dropped before anything downstream can see it. Measuring the level through the
parser that discards it would produce a confident zero.

## What this prints, and what each part decides

1. **The key inventory.** Every key seen at region level and at alert level,
   counted, before any interpretation. The payload's shape is read rather than
   assumed, because writing this tool against a remembered shape is the defect
   it exists to measure (F129: a mapping written from the local palette instead
   of from the source's claim, internally consistent, invisible to the gate).

2. **The level histogram.** `regionType` counted. This sizes the hole: an
   oblast-level entry whose name the table cannot hold reaches no store row at
   all, and the map draws nothing for it.

3. **The join, in four cells.** Per region, `AreaTable.resolve_prose` against
   the name the API sent, and for each hit whether the resolved row's `unit`
   agrees with the unit word standing in that same name. The cells are
   deliberately four rather than two:

   - `ok`, resolved and the level agrees;
   - `LEVEL`, resolved and the level disagrees. Kharkiv oblast resolves to the
     Kharkiv city hromada and carries the city's border interval onto the map.
     This cell prints nowhere in production;
   - `miss`, nothing resolved. Visible today as `unresolved`;
   - `ambig`, more than one row. Also visible today as `unresolved`, which is
     why the two are separated here (W3).

4. **The exact name strings, listed.** The repair for the misses is oblast rows
   in the table, and those rows must be keyed on the forms the API actually
   sends. Writing them from a guessed declension would be F129 committed in a
   data file, where the gate cannot see it either.

5. **`regionId`, listed beside each name.** Already parsed and unused. If it is
   stable, a table keyed on it removes prose resolution from this path
   entirely, along with the whole class of defect this tool is measuring. The
   listing is here so that fork can be decided on data rather than on taste.

## What this does not do

It writes nothing: no store, no snapshot, no file, no key to disk, and it never
prints the key. It makes one GET. It is a reading, not a source, and D-013's
argument about this endpoint stands unchanged.

## Usage

    sudo -u mavo /opt/mavo/venv/bin/python3 region_levels.py

    python3 region_levels.py --stub payload.json     # no key, no network

Exit codes match `mavo collect-api`: 2 no key, 3 unreachable, 0 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from mavo.areas import _UNIT_CODE, UNIT, AreaTable
from mavo.errors import SourceUnavailable
from mavo.sources.ukrainealarm import API_BASE, TIMEOUT_S, read_key
from mavo.transport import UrllibTransport

UNIT_NAME = {"P": "raion", "H": "hromada", "O": "oblast"}


def unit_word_code(name: str) -> str | None:
    """The level the name's own unit word claims, or None when it carries none.

    `resolve_prose` reads the same word through `_UNIT_CODE` and then uses it
    only to break ties between two rows sharing a name. Read here directly, so
    that a hit at the wrong level is a cell in the table below rather than a
    silence.
    """
    words = [match.group(0) for match in UNIT.finditer(name)]
    if len(words) != 1:
        return None
    return _UNIT_CODE.get(words[0][:5])


def inventory(payload: object) -> tuple[Counter[str], Counter[str], int]:
    """Keys seen at region level, keys seen at alert level, and region count."""
    region_keys: Counter[str] = Counter()
    alert_keys: Counter[str] = Counter()
    regions = 0
    if not isinstance(payload, list):
        return region_keys, alert_keys, regions
    for region in payload:
        if not isinstance(region, dict):
            continue
        regions += 1
        region_keys.update(str(key) for key in region)
        active = region.get("activeAlerts")
        if isinstance(active, list):
            for alert in active:
                if isinstance(alert, dict):
                    alert_keys.update(str(key) for key in alert)
    return region_keys, alert_keys, regions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stub", help="read the payload from this file instead of the API")
    parser.add_argument("--key-file", help="path to the API key (default: the package's)")
    args = parser.parse_args(argv)

    if args.stub:
        body = Path(args.stub).read_text(encoding="utf-8")
    else:
        try:
            key = read_key(path=Path(args.key_file) if args.key_file else None)
        except (SourceUnavailable, OSError) as missing:
            print(f"[NO-KEY] {missing}")
            return 2
        try:
            body = UrllibTransport(timeout_s=TIMEOUT_S).fetch(
                f"{API_BASE}/alerts",
                headers={"Authorization": key, "Accept": "application/json"},
            )
        except SourceUnavailable as unreachable:
            print(f"[UNREACHABLE] {unreachable}")
            return 3

    try:
        payload = json.loads(body)
    except ValueError as malformed:
        print(f"[MALFORMED] {malformed}")
        return 3

    region_keys, alert_keys, regions = inventory(payload)
    print(f"regions={regions} bytes={len(body)}")
    print("\nkeys, region level:")
    for key, count in region_keys.most_common():
        print(f"  {count:4d}  {key}")
    print("keys, alert level:")
    for key, count in alert_keys.most_common():
        print(f"  {count:4d}  {key}")

    if not isinstance(payload, list):
        print("\npayload is not a list; nothing further can be said about it")
        return 0

    table = AreaTable.from_csv()
    levels: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    cells: Counter[str] = Counter()
    rows: list[tuple[str, str, str, str, str, str, str]] = []

    for region in payload:
        if not isinstance(region, dict):
            continue
        name = str(region.get("regionName") or "")
        rtype = str(region.get("regionType") or "")
        rid = str(region.get("regionId") or "")
        eng = str(region.get("regionEngName") or "")
        active = region.get("activeAlerts")
        alert_types = (
            [str(a.get("type") or "?") for a in active if isinstance(a, dict)]
            if isinstance(active, list) else []
        )
        kinds.update(alert_types)
        types = ",".join(sorted(set(alert_types))) if alert_types else "-"
        levels[rtype or "(absent)"] += 1

        refs, declined_names = table.resolve_prose_detail(name)
        wanted = unit_word_code(name)
        if len(refs) > 1:
            cell, detail = "ambig", f"{len(refs)} rows"
        elif not refs and declined_names:
            cell, detail = "declined", ",".join(declined_names)
        elif not refs:
            cell, detail = "miss", ""
        else:
            ref = refs[0]
            got = UNIT_NAME.get(ref.unit, ref.unit)
            if wanted is None or ref.unit == wanted:
                cell, detail = "ok", f"{ref.code} {got}"
            else:
                want = UNIT_NAME.get(wanted, wanted)
                cell = "LEVEL"
                detail = f"{ref.code} {got}, name says {want}, border {ref.border_interval}"
        cells[cell] += 1
        rows.append((cell, rid, rtype, name, types, detail, eng))

    print("\nalert types:")
    for kind, count in kinds.most_common():
        print(f"  {count:4d}  {kind}")

    print("\nregionType:")
    for level, count in levels.most_common():
        print(f"  {count:4d}  {level}")

    print("\njoin against tag_map.csv:")
    for cell in ("ok", "LEVEL", "declined", "miss", "ambig"):
        print(f"  {cells[cell]:4d}  {cell}")

    print("\nper region:")
    for cell, rid, rtype, name, types, detail, eng in sorted(rows, key=lambda r: (r[0], r[3])):
        print(f"  {cell:8s} {rid:>8s} {rtype:12s} {name:44s} {types:24s} {eng:28s} {detail}")

    print("\nNothing was written. This figure is outside the gate: it is a reading")
    print("of one moment and must not be pinned in any document as a property of")
    print("the system.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
