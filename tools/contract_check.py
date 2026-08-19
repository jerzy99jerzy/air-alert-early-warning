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

from mavo.areas import OBLAST_SLUGS, AreaTable, oblast_slug  # noqa: E402
from mavo.report import (  # noqa: E402
    FEED_WINDOW_S,
    SCHEMA_VERSION,
    STREAM_WINDOW_S,
    compose,
    to_contract,
    write_contract,
    write_feed,
)
from mavo.schema import (  # noqa: E402
    AlertState,
    AreaRole,
    Provenance,
    ThreatEvent,
    ThreatKind,
)

WEBAPP = Path(__file__).resolve().parent.parent / "docs" / "WEBAPP.md"

# Every slug the register can produce. A consumer joins geometry on these, so a
# new one appearing without the consumer knowing is a marker that vanishes.
KNOWN_SLUGS = frozenset(OBLAST_SLUGS.values())

REQUIRED_TOP = ("v", "generated_at", "valid_for_s", "state", "observation_age_s",
                "source_last_message_at", "window_days", "recent_7d", "areas",
                "events", "counts_24h")
REQUIRED_STREAM = ("window_start", "window_s", "truncated", "items")
REQUIRED_ITEM = ("area_id", "oblast", "oblast_name", "alert", "kind", "role",
                 "at", "west")
REQUIRED_AREA = ("katottg", "area_id", "oblast", "oblast_name", "alert", "kind",
                 "since", "border_km_lower", "border_km_upper")
# The trailing block had no key set here for eleven releases while every other
# block in the payload had one. `recent_7d` is the layer the consumer shades a
# whole oblast from, so a rename here repaints the map rather than emptying a
# list, and nothing on either side would have said so.
REQUIRED_RECENT = ("oblast", "alerts_count", "last_alert_ended_at")


def _event(
    code: str,
    state: AlertState,
    minutes: int,
    now: datetime,
    role: AreaRole = AreaRole.SUBJECT,
) -> ThreatEvent:
    stamp = now - timedelta(minutes=minutes)
    return ThreatEvent(
        area_id=code,
        state=state,
        ts_source=stamp,
        ts_ingest=stamp,
        source_id="contract-check",
        kind=ThreatKind.MISSILE,
        provenance=Provenance.REPORTED,
        role=role,
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
    # A third area, in an oblast neither live one occupies, so its entry in the
    # trailing block is the closed episode and nothing else.
    live_slugs = {oblast_slug(area.oblast) for area in western[:2]}
    closed = next(
        (area for area in western if oblast_slug(area.oblast) not in live_slugs),
        western[-1],
    )
    events = [
        _event(subject.code, AlertState.ACTIVE, 5, now),
        _event("UA00000000000000000", AlertState.ACTIVE, 5, now),  # unresolvable
        # A continuation, so the role check above has something to find. A
        # fixture that carried only subjects would make that check unable to
        # fail, which is F44's rule: a probe whose negative result is
        # indistinguishable from its positive one is not a probe.
        _event(western[1].code if len(western) > 1 else subject.code,
               AlertState.ACTIVE, 4, now, role=AreaRole.CONTINUATION),
        # An episode that opens and affirmatively closes inside the window, so
        # `last_alert_ended_at` is non-null on at least one entry. Without it
        # every entry carries null, the null-or-timestamp check below passes on
        # a payload that could never produce a timestamp, and the check cannot
        # fail. Same rule as the continuation event above (F44).
        _event(closed.code, AlertState.ACTIVE, 400, now),
        _event(closed.code, AlertState.CLEAR, 300, now),
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

    # The trailing block. Per **oblast**, while `areas` above is per raion, and
    # the two are joined by nothing: an oblast is the parent of the areas, not
    # a coarser measurement of the same place. The checks below hold that line
    # rather than assume it.
    recent = payload.get("recent_7d")
    if not isinstance(recent, list):
        problems.append("recent_7d must be a list, present even when empty")
    else:
        if not recent:
            problems.append(
                "the trailing block was empty on a fixture that declares three "
                "alerts inside the window; the checks below would all vacate"
            )
        seen_slugs: set[str] = set()
        closed_seen = False
        for entry in recent:
            for key in REQUIRED_RECENT:
                if key not in entry:
                    problems.append(f"recent_7d entry is missing {key!r}")
            slug = entry.get("oblast", "")
            # F74 again, one block over. The consumer shades geometry from this
            # slug, so a display name here paints nothing and says nothing.
            if not slug:
                problems.append(
                    "a trailing entry carried no oblast slug; an oblast the "
                    "register cannot resolve is dropped from this count, never "
                    "published with an empty join key"
                )
            elif slug not in KNOWN_SLUGS:
                problems.append(f"recent_7d oblast {slug!r} is not a register slug")
            elif slug in seen_slugs:
                # One entry per oblast is what makes `alerts_count` an episode
                # count. Two entries for one oblast would let a consumer sum
                # them, and the sum is the F76 number: how finely the oblast is
                # subdivided, rendered as how often it was attacked.
                problems.append(f"recent_7d carries {slug!r} more than once")
            seen_slugs.add(slug)
            count = entry.get("alerts_count")
            if not isinstance(count, int) or isinstance(count, bool) or count < 1:
                problems.append(
                    f"recent_7d alerts_count {count!r} is not a positive integer; "
                    "an oblast with no episode leaves the block rather than "
                    "appearing with a zero"
                )
            ended = entry.get("last_alert_ended_at")
            if ended is None:
                continue
            closed_seen = True
            if not isinstance(ended, str):
                problems.append(
                    f"recent_7d last_alert_ended_at {ended!r} is neither null nor "
                    "a timestamp; null is unknown and must not render as ended"
                )
        if recent and not closed_seen:
            problems.append(
                "no trailing entry carried a close, though the fixture closes "
                "one episode inside the window; the null branch is the only one "
                "being exercised"
            )
        # The granularity guard. `areas` is per raion and `recent_7d` is per
        # oblast, so the two lists cannot be read as one vocabulary and a
        # consumer that prints a number from each in one sentence is printing
        # two different quantities. Checked rather than documented, because a
        # rule without a gate check is a preference.
        area_ids = {area.get("area_id") for area in payload.get("areas", [])}
        if area_ids & {entry.get("oblast") for entry in recent}:
            problems.append(
                "an identifier appears both as an area_id and as a trailing "
                "oblast slug; the two blocks are at different granularities and "
                "must not share a key space"
            )

    # v3. The stream is a contract of its own and gets its own reading.
    stream = payload.get("events")
    if not isinstance(stream, dict):
        problems.append("the event stream must be an object, present even when empty")
    else:
        for key in REQUIRED_STREAM:
            if key not in stream:
                problems.append(f"event stream is missing {key!r}")
        if stream.get("window_s") != STREAM_WINDOW_S:
            problems.append(
                f"stream window {stream.get('window_s')} != {STREAM_WINDOW_S}"
            )
        for item in stream.get("items", []):
            for key in REQUIRED_ITEM:
                if key not in item:
                    problems.append(f"stream item is missing {key!r}")
            slug = item.get("oblast", "")
            # Same join as `areas`, and the same defect if it is a display
            # name: a consumer colouring a feed row by oblast joins on this.
            if slug and slug not in KNOWN_SLUGS:
                problems.append(f"stream item oblast {slug!r} is not a register slug")
            if item.get("role") not in ("subject", "continuation"):
                problems.append(f"stream item role {item.get('role')!r} is not a role")
        # The stream carries both roles by decision (D-024). A build that
        # filtered to subjects would pass every shape check above and drop the
        # areas a message says are still under alert.
        roles = {item.get("role") for item in stream.get("items", [])}
        if "continuation" not in roles:
            problems.append(
                "the stream carried no continuation event; the check's own "
                "fixture provides one, so this means they are being filtered"
            )

    counts = payload.get("counts_24h")
    if not isinstance(counts, dict):
        problems.append("counts_24h must be an object")
    elif counts.get("total") != counts.get("west", 0) + counts.get("rest", 0):
        problems.append("counts_24h total does not equal west plus rest")

    # `feed.json` is a second file with the same vocabulary, so a consumer
    # writes one reader. A divergence here would be discovered by the consumer
    # rather than by this gate, which is the arrangement D-020 exists to avoid.
    with tempfile.TemporaryDirectory() as directory:
        feed_path = write_feed(report, Path(directory) / "feed.json")
        feed = json.loads(feed_path.read_text(encoding="utf-8"))
    for key in REQUIRED_STREAM:
        if key not in feed:
            problems.append(f"feed is missing {key!r}")
    if feed.get("window_s") != FEED_WINDOW_S:
        problems.append(f"feed window {feed.get('window_s')} != {FEED_WINDOW_S}")
    if feed.get("v") != SCHEMA_VERSION:
        problems.append(f"feed version {feed.get('v')} != {SCHEMA_VERSION}")
    if feed.get("generated_at") != payload.get("generated_at"):
        problems.append(
            "the feed and the contract describe different moments; they must "
            "come from one composition"
        )

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


def check_every_kind_is_documented() -> list[str]:
    """Every `ThreatKind` member appears in the contract's documentation.

    T47. MAVO classifies four kinds; the consumer knows three strings and
    renders the rest as "unknown", so three thousand declarations arrive named
    and display as unnamed. The producer cannot fix the consumer's labels, and
    it can stop adding a member without telling anyone: a kind that exists in
    the enum and nowhere in the contract's documentation is a value a consumer
    will meet for the first time in production.
    """
    if not WEBAPP.exists():
        return ["docs/WEBAPP.md is missing; the contract has no documentation"]
    text = WEBAPP.read_text(encoding="utf-8")
    missing = [
        kind.value for kind in ThreatKind if f"`{kind.value}`" not in text
    ]
    return [
        f"ThreatKind.{name.upper()} is not named in docs/WEBAPP.md; a consumer "
        f"would meet it first in production" for name in missing
    ]


def main() -> int:
    """Run the contract check. Returns a process exit code."""
    problems = check_contract() + check_every_kind_is_documented()
    for problem in problems:
        print(f"contract-check: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"contract-check: state.json v{SCHEMA_VERSION} holds its shape")
    return 0


if __name__ == "__main__":
    sys.exit(main())
