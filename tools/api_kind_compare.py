"""P4. What the API calls the threat, against what the join concludes (T16).

`api.ukrainealarm.com` returns an `alert_type` per active alert. MAVO's kind
join reaches 17% of alerts and leaves the rest UNKNOWN. The obvious question is
whether that field covers what the join misses.

**It is not a second opinion, and the arithmetic below must not be read as
one.** `mavo/sources/ukrainealarm.py` opens by saying so: the API and
`alerts.in.ua` and the public channel all draw on the same upstream. The API's
`type` is therefore **another parser over the same text**, not another
observation of the same event. Agreement between them is evidence that two
parsers read one message the same way and is not evidence that the message was
right. Disagreement is the interesting half, because two readers of one text
producing different labels means at least one is wrong and the text can be read
to find out which.

## What this prints, and what each number decides

- **API alerts carrying a usable type**: if this is small, the whole line of
  work stops here and no map or parser change is worth making for it.
- **The type vocabulary**: the raw strings, counted. The API's vocabulary and
  `ThreatKind` were written independently and there is no reason to expect them
  to align. A type this tool cannot map is reported as itself rather than
  folded into `unknown`, because a vocabulary gap and an absent label are
  different findings.
- **Oblasts the API labels and the join leaves UNKNOWN**: the coverage the
  field would add, at oblast granularity, which is the granularity the join
  already uses.
- **Oblasts both label, and whether they agree**: the disagreement rate. This
  is the number worth carrying into a document even if the coverage answer is
  no.

## What this does not do

It does not write anything to the store, the contract or `state.json`, and it
must not: D-013 records why this API is a measurement instrument here and not a
source, and its access is revocable without cause. Nothing this prints is
allowed to reach a reader without a decision recorded first.

It also does not run in CI. It needs a key and a live endpoint, so its output
is a measurement pasted into `docs/METHODOLOGY.md` by hand with its date, the
same discipline as `tools/kind_coverage.py`.

## Usage

    MAVO_UKRAINEALARM_KEY=... PYTHONPATH=. python3 tools/api_kind_compare.py

Add `--state path/to/state.json` to compare against a contract file the
producer has already written, which is how the join's side of the comparison
arrives without re-running the pipeline.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from mavo.errors import SourceUnavailable
from mavo.sources.ukrainealarm import KEY_ENV, UkrainealarmProbe, read_key

#: The API's five categories against `ThreatKind`. **Four of the five map to
#: `unknown`, and that is the correct answer rather than a gap to be filled.**
#:
#: [reported, 2026-08-14, three independent descriptions: Ajax Systems' own
#: account of the Air Alert app it built, the Home Assistant integration's
#: sensor list, and the alerts.in.ua client library's typed accessors. Not yet
#: [measured]: no response from this key has been read.]
#:
#: The field is a **category of alert**, not a description of the means of
#: attack. `AIR` covers a drone, a glide bomb, a cruise missile, a ballistic
#: missile, a MiG-31K takeoff and a threat from the sea, all under one value.
#: The question this project wants answered - what is coming - is exactly the
#: question the field does not answer, and its shape gives no hint of that: a
#: category and a kind are both short enums hanging off an alert.
#:
#: `ARTILLERY` is the only value that lands on a real kind, and the channel
#: join already produces that kind from its own declarations. So the coverage
#: this field could add to `ThreatKind` is, at most, alerts the join missed in
#: the one category it already reads.
#:
#: `CHEMICAL`, `NUCLEAR` and `URBAN_FIGHTS` have no member here and are not
#: given one. A `ThreatKind` member exists when **the channel names the thing
#: and the schema cannot hold it** - that is why ARTILLERY was added at
#: 0.19.3.0, after F71 measured messages being rejected whole. Whether the
#: channel names chemical, radiological or street-fighting threats is
#: unmeasured. Adding members because another interface has them would be
#: letting an API that must never reach `state.json` decide the shape of the
#: contract.
TYPE_TO_KIND: dict[str, str] = {
    "AIR": "unknown",
    "ARTILLERY": "artillery",
    "URBAN_FIGHTS": "unknown",
    "CHEMICAL": "unknown",
    "NUCLEAR": "unknown",
}


def _load_join(path: Path) -> dict[str, str]:
    """Oblast slug to kind, read from a contract file the producer wrote.

    Reads `state.json` rather than re-running the pipeline, so the join's side
    of this comparison is exactly what the consumer was served and not a fresh
    computation that could differ from it.
    """
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    areas = payload.get("areas")
    if not isinstance(areas, list):
        raise SystemExit(f"{path} has no `areas` list; is this a v3 contract?")
    out: dict[str, str] = {}
    for area in areas:
        if not isinstance(area, dict):
            continue
        oblast = area.get("oblast")
        kind = area.get("kind")
        # Several raions per oblast. A known kind wins over UNKNOWN so the
        # comparison is against the join at its best rather than against
        # whichever raion happened to sort last.
        if (isinstance(oblast, str) and isinstance(kind, str)
                and out.get(oblast) in (None, "unknown")):
            out[oblast] = kind
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=None,
                        help="a state.json written by this producer. Without it "
                             "only the API side is reported, which answers the "
                             "vocabulary question but not the coverage one")
    parser.add_argument("--key-file", dest="key", type=Path, default=None,
                        help=f"a file holding the API key. Without it, {KEY_ENV} "
                             "is read from the environment")
    arguments = parser.parse_args()

    try:
        key = read_key(path=arguments.key)
    except SourceUnavailable as missing:
        print(f"api-kind-compare: {missing}")
        print("  Access is revocable without cause (D-013); this is a probe and "
              "nothing it prints may reach a reader without a decision first.")
        return 1

    try:
        alerts = UkrainealarmProbe(key).alerts()
    except SourceUnavailable as refused:
        print(f"api-kind-compare: {refused}")
        print("  A refusal is a result. It is not evidence about the type field.")
        return 1
    print(f"api-kind-compare: {len(alerts)} active alerts from the API")
    if not alerts:
        print("  Nothing active. This is a result, not a failure, and it means")
        print("  the comparison below has no rows rather than that it agrees.")
        return 0

    types: Counter[str] = Counter(alert.alert_type for alert in alerts)
    unmapped = sorted(set(types) - set(TYPE_TO_KIND))
    print()
    print("== the API's type vocabulary, as returned ==")
    for value, count in types.most_common():
        mapped = TYPE_TO_KIND.get(value, "NOT IN THIS TOOL'S TABLE")
        print(f"  {count:>5}  {value:<16} -> {mapped}")
    if unmapped:
        print()
        print(f"  {len(unmapped)} type string(s) this tool has no row for: "
              f"{', '.join(unmapped)}")
        print("  Each is a decision, not a defect: mapping it means asserting")
        print("  what the API means by it, which has not been read anywhere.")

    unplaceable = [a for a in alerts if a.oblast is None]
    print()
    print("== oblast resolution ==")
    print(f"  alerts whose region resolved to an oblast slug   "
          f"{len(alerts) - len(unplaceable):>5}")
    print(f"  alerts that did not                              {len(unplaceable):>5}")
    if unplaceable:
        names = Counter(a.region_name for a in unplaceable)
        for name, count in names.most_common(10):
            print(f"    {count:>4}  {name}")
        print("  These are not necessarily errors: Kyiv city has no oblast slug")
        print("  by design (F90, T44) and inventing one here is the thing that")
        print("  decision exists to prevent.")

    if arguments.state is None:
        print()
        print("api-kind-compare: no --state given, so the coverage and agreement")
        print("  questions are unanswered. The vocabulary above is the whole")
        print("  result of this run.")
        return 0

    join = _load_join(arguments.state)
    print()
    print(f"== against the join, from {arguments.state} ==")
    print(f"  oblasts in the contract: {len(join)}")

    both = 0
    agree = 0
    api_only = 0
    join_only = 0
    disagreements: list[tuple[str, str, str]] = []
    api_by_oblast: dict[str, str] = {}
    for alert in alerts:
        if alert.oblast is None:
            continue
        api_by_oblast.setdefault(alert.oblast, alert.alert_type)

    for oblast, api_type in sorted(api_by_oblast.items()):
        join_kind = join.get(oblast)
        api_kind = TYPE_TO_KIND.get(api_type)
        if join_kind is None:
            continue
        if api_kind is None:
            # No row in this tool's table. Not counted as agreement or
            # disagreement, because this tool does not know what it means.
            continue
        if join_kind == "unknown" and api_kind != "unknown":
            api_only += 1
        elif join_kind != "unknown" and api_kind == "unknown":
            join_only += 1
        elif join_kind != "unknown" and api_kind != "unknown":
            both += 1
            if join_kind == api_kind:
                agree += 1
            else:
                disagreements.append((oblast, join_kind, api_kind))

    print(f"  the API names a kind where the join says UNKNOWN   {api_only:>5}"
          "   <- the coverage this field would add")
    print(f"  the join names a kind where the API does not       {join_only:>5}")
    print(f"  both name a kind                                   {both:>5}")
    print(f"    of those, agreeing                               {agree:>5}")
    if disagreements:
        print()
        print("== disagreements, which are the finding ==")
        for oblast, join_kind, api_kind in disagreements:
            print(f"  {oblast:<24} join={join_kind:<12} api={api_kind}")
        print()
        print("  Two parsers over one upstream disagreeing means at least one is")
        print("  wrong about a message that can be read. Read them before")
        print("  changing anything on either side.")

    print()
    print("api-kind-compare: this is one moment, not a distribution. A single")
    print("  reading is an anecdote with counts on it; the coverage question")
    print("  needs repeated sampling across hours before any figure here is")
    print("  quoted as a rate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
