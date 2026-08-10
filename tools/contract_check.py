#!/usr/bin/env python3
"""The contract has a reader in the gate, not only in a procedure.

D-020 moved ownership of `state.json` to this repository on the argument that
the producer's gate can exercise the schema. Then nothing exercised it, and
F74 shipped: `oblast` carried a Cyrillic display name where the consumer joins
on an ASCII slug, and the consumer's map drew nothing while its distance list
drew everything. Ownership without a check is a claim.

This is the check. It composes a report from a synthetic store, writes the
contract, and asserts the properties a consumer relies on. It deliberately
does **not** import the consumer: that package lives in another repository
with its own gate, and depending on it here would rebuild the coupling D-020
removed. What it encodes instead is the consumer's *requirements*, each one
traceable to a line in `docs/WEBAPP.md`.

Run by `make verify`. A failure here means a page somewhere renders wrongly at
a moment nobody is watching a web page.
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mavo.areas import OBLAST_SLUGS, AreaTable  # noqa: E402
from mavo.report import SCHEMA_VERSION, compose, to_contract, write_contract  # noqa: E402
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind  # noqa: E402

# Every slug the register can produce. A consumer joins geometry on these, so a
# new one appearing without the consumer knowing is a marker that vanishes.
KNOWN_SLUGS = frozenset(OBLAST_SLUGS.values())

REQUIRED_TOP = ("v", "generated_at", "valid_for_s", "state", "observation_age_s",
                "source_last_message_at", "window_days", "recent_7d", "areas")
REQUIRED_AREA = ("katottg", "area_id", "oblast", "oblast_name", "alert", "kind",
                 "since", "border_km_lower", "border_km_upper")


def _event(code: str, state: AlertState, minutes: int, now: datetime) -> ThreatEvent:
    stamp = now - timedelta(minutes=minutes)
    return ThreatEvent(
        area_id=code,
        state=state,
        ts_source=stamp,
        ts_ingest=stamp,
        source_id="contract-check",
        kind=ThreatKind.MISSILE,
        provenance=Provenance.REPORTED,
    )


def check_contract() -> list[str]:
    """Compose, write, read back, and assert what a consumer needs."""
    table = AreaTable.from_csv()
    now = datetime(2026, 8, 10, 23, 41, tzinfo=UTC)
    western = [
        area
        for area in (table.resolve(tag) for tag in table.tags)
        if area is not None and area.is_western and area.border_lower_km is not None
    ]
    if not western:
        return ["no western area in the map to build a contract check on"]
    subject = western[0]
    events = [
        _event(subject.code, AlertState.ACTIVE, 5, now),
        _event("UA00000000000000000", AlertState.ACTIVE, 5, now),  # unresolvable
    ]
    report = compose(events, as_of=now, table=table)
    with tempfile.TemporaryDirectory() as directory:
        path = write_contract(report, Path(directory) / "state.json")
        payload = json.loads(path.read_text(encoding="utf-8"))

    problems: list[str] = []
    for key in REQUIRED_TOP:
        if key not in payload:
            problems.append(f"contract is missing top-level {key!r}")
    if payload.get("v") != SCHEMA_VERSION:
        problems.append(f"contract version {payload.get('v')} != {SCHEMA_VERSION}")

    for area in payload.get("areas", []):
        for key in REQUIRED_AREA:
            if key not in area:
                problems.append(f"area entry is missing {key!r}")
        slug = area.get("oblast", "")
        # F74. The join field must be a slug the consumer's geometry can carry,
        # or empty. A display name here is the whole defect.
        if slug and slug not in KNOWN_SLUGS:
            problems.append(
                f"area oblast {slug!r} is not a register slug; a consumer joins on this"
            )
        if slug and not slug.isascii():
            problems.append(f"area oblast {slug!r} is not ASCII")
        if area.get("alert") == "clear":
            problems.append("a cleared area must leave the list, not carry alert=clear")

    # An unresolvable area must still appear, with empty rather than guessed
    # identifiers: dropping it is what made the consumer's map disagree with
    # its own list before the site logged that defect.
    unresolved = [a for a in payload.get("areas", []) if not a.get("oblast")]
    if not unresolved:
        problems.append("an area the map cannot resolve was dropped from the contract")
    else:
        if unresolved[0].get("oblast_name") != "unknown":
            problems.append("an unresolvable oblast must print as unknown, not blank")

    # Nulls must survive as nulls. A consumer renders null as unknown and 0 as
    # a measurement, and the difference is the founding invariant.
    blind = to_contract(compose([], as_of=now, table=table))
    if blind.get("state") != "blind":
        problems.append("an empty store must publish state=blind")
    if blind.get("observation_age_s") is not None:
        problems.append("observation_age_s must be null when unknown, never 0")
    if blind.get("source_last_message_at") is not None:
        problems.append("source_last_message_at must be null when the source never spoke")
    if blind.get("areas") != []:
        problems.append("a blind report must publish an empty area list")

    return problems


def main() -> int:
    """Run the contract check. Returns a process exit code."""
    problems = check_contract()
    for problem in problems:
        print(f"contract-check: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"contract-check: state.json v{SCHEMA_VERSION} holds its shape")
    return 0


if __name__ == "__main__":
    sys.exit(main())
