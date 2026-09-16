"""The Polish side of the contract: communiques and airspace, composed from the store.

**What moved, and why it moved here (D-053).** Until 0.55.0.0 `mavo-site` read
RSO and the PAŻP plan itself, on timers inside its web process, and merged
`pl_warnings` and `pl_airspace` into the payload it rendered. Its own server
was written to stand down the moment this repository published either key
(`mavosite/server.py`, `_picture`), so the handover needs nothing from the
consumer's release. Three things forced the move rather than suggested it: two
readers of one feed disagree without anybody noticing, which is how a contract
drifts; the seven-day scrubber is to repaint the airspace too (decided
2026-09-16), and a plan nobody recorded cannot be repainted; and the CAP
credentials MSWiA issued are bound to `vm-mavo`'s address, so the communique
channel's future is on this host whatever its present is.

**The classification moved with the reading, on the operator's decision of
2026-09-16.** Which communique paints the map is decided here, from the store,
so a painting can be reproduced from rows this project holds rather than from
a consumer's cache that forgets on every refresh.

**Behaviour is ported, and three differences are chosen and named.** Every
rule below is `mavosite/rso.py` or `mavosite/airspace.py` at 4.76.0.0, with the
consumer's tests ported beside them as the proof. What differs:

1. **The communique scope is the `ogolne` reading at page 0, not page 1.**
   The consumer read page one and said so as a cost: a communique still valid
   on page two was never painted. `mavo rso` asks for page 0, which the
   publisher's integration page describes as the reading with pagination
   suppressed `[reported, T67; the 461-communique count of 2026-08-22 was
   taken through it]`. If that description holds, the cost is gone; whether it
   holds on the host is a T85 reading and not a property of this module.
2. **An hour the autumn change maps twice is not converted.** The consumer
   gave such a stamp the summer offset without saying so, which ends a
   communique an hour early if the publisher meant winter time. Here the stamp
   reaches the reader as the feed wrote it, and an end that cannot be settled
   is not an end.
3. **A communique list older than an hour is not published as current.** The
   consumer kept the last good reading for ever, and its payload shape has no
   field for age, so a reading from yesterday rendered exactly like one from a
   minute ago - including an empty one, which is silence rendered as calm.
   Past `WARNINGS_VALID_FOR_S` the block is `null`, which the page already
   renders as *could not read*.

**The four states, as the consumer renders them and this module emits them.**
Key absent: this producer has never polled the feed, so the consumer's own
reading, if any, still stands. `null`: polled and cannot say. Empty list or
object with nothing switched on: read, and nothing to show. Rows: something to
show.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from mavo.errors import SourceUnavailable
from mavo.sources import pansa, rso
from mavo.store import EventStore

#: The feed's own zone, stated by the caller as `rso.to_utc` asks.
ZONE = "Europe/Warsaw"

#: The one RSO address whose communiques may paint the map: `ogolne`, unpaged.
#: The other four categories carry meteorological, hydrological, road and
#: water-level notices, and a voivodeship painted because a river is high would
#: be read on a map of air alerts as something it is not (consumer D-S80). They
#: are still read and recorded; this constant decides what is *shown*.
WARNINGS_URL = rso.page_url("ogolne", 0)

#: Past this, a communique list is not published as current (difference 3
#: above). The consumer's own `VALID_FOR_S` for the same feed, carried over:
#: four missed refreshes at the consumer's cadence, which is a failure and not a
#: slow day. At this producer's 900 s timer it is four missed polls as well.
WARNINGS_VALID_FOR_S = 3600.0

#: The terms that make a communique about the air, matched as substrings of
#: the lowercased title and body. `mavosite/rso.py` at 4.76.0.0, verbatim and in
#: order. `powietrzn` and not `powietrz`: the latter matches every air-quality
#: notice, which is exactly the notice that must not paint a map of air alerts.
AIR_THREAT_TERMS: tuple[str, ...] = (
    "z powietrza",
    "powietrzn",
    "dron",
    "bezza\u0142ogow",
    "rakiet",
    "pocisk",
    "nalot",
    "obiekt lataj",
    "przestrzeni powietrznej",
    "alarm lotnicz",
)

#: Terms that keep a communique off the map even when an air term matches.
#: Exclusion wins: a siren test writes "alarm powietrzny" in its body and is
#: not a threat. Verbatim from the consumer, in order.
NOT_A_THREAT_TERMS: tuple[str, ...] = (
    "test syren",
    "testy syren",
    "testu syren",
    "pr\u00f3ba syren",
    "pr\u00f3by syren",
    "\u0107wiczeni",
    "trening",
    "jako\u015b\u0107 powietrza",
    "jako\u015bci powietrza",
    "smog",
    "py\u0142 zawieszon",
    "py\u0142u zawieszon",
)

#: Switched on, in the plan's own vocabulary (consumer D-S82, decision A).
STATUS_ON = "ACTIVATED"

#: The structures the layer draws. ATZ (aerodrome traffic) and MRT (a military
#: route, a corridor rather than a closure) are outside it on purpose.
KINDS_DRAWN: frozenset[str] = frozenset({"TSA", "TRA", "D", "R", "NPZ", "ADHOC"})

#: Remark tokens marking sport or unmanned work. `CLN` is not one: measured on
#: `vm-site` 2026-09-14 it sits only beside `M346`, `W3` and `F16`.
CIVIL_MARKS: frozenset[str] = frozenset({"PJE", "GLD", "BSP", "UAV"})

#: A TRA is drawn only when its remarks reference a NOTAM or an AIP supplement.
TRA_CALLED_UP = ("NOT.", "SUP")

_ALTITUDE = re.compile(r"^([AF])(\d{3})$")
_METRES_PER_FOOT = 0.3048
_METRES_STEP = 50
_TOKEN = re.compile(r"[A-Z0-9.]+")


@dataclass(frozen=True, slots=True)
class Block:
    """One key of the contract: whether to publish it, and what it holds.

    `published` False means the key is absent, which is a claim about this
    producer (it has never polled the feed) and not about the feed. `value`
    None with `published` True is `null`: polled, and cannot say.
    """

    published: bool
    value: Any = None


UNPUBLISHED = Block(published=False)

#: What a cycle publishes when composing these blocks raised. Both keys `null`
#: rather than absent: absent hands the page back to whatever the consumer
#: reads itself, and a producer that failed to read its own store has not
#: stopped polling anything.
FAILED_BLOCK = Block(published=True, value=None)


@dataclass(frozen=True, slots=True)
class PolandBlocks:
    """Both Polish keys for one composed picture."""

    warnings: Block = UNPUBLISHED
    airspace: Block = UNPUBLISHED


FAILED = PolandBlocks(warnings=FAILED_BLOCK, airspace=FAILED_BLOCK)


def _parse_stored(stamp: str) -> datetime:
    parsed = datetime.fromisoformat(stamp)
    if parsed.tzinfo is None:
        raise ValueError(f"{stamp!r} has no offset; the store writes offsets")
    return parsed.astimezone(UTC)


# ---- communiques


def air_term(title: str | None, text: str | None) -> str | None:
    """The first air term a communique matches, or None when it is not about the air.

    None as well when an exclusion matches, whatever else does. The term is
    returned rather than a boolean so the contract can say *why* a voivodeship
    is painted, and a reviewer reading a false paint sees which word did it.
    """
    haystack = " ".join(part for part in (title, text) if part).lower()
    if any(term in haystack for term in NOT_A_THREAT_TERMS):
        return None
    for term in AIR_THREAT_TERMS:
        if term in haystack:
            return term
    return None


def is_expired(valid_to: str | None, as_of: datetime) -> bool:
    """Whether a communique has an end and that end is behind us.

    **An end that cannot be established is not an end.** Absent, unparseable,
    or inside the hour the autumn change maps twice: the communique stays,
    because dropping it would be this producer deciding a warning is over on
    the strength of a field it could not read.
    """
    if valid_to is None:
        return False
    try:
        end = rso.to_utc(valid_to, ZONE)
    except SourceUnavailable:
        return False
    return end < as_of


def feed_stamp_as_iso(value: str | None) -> str | None:
    """The feed's naive stamp as ISO 8601 with the Warsaw offset, or as it came.

    What does not convert - an ambiguous hour, a malformed stamp - reaches the
    reader as the feed's own text rather than as nothing and rather than as a
    guess. The consumer's clock renders non-ISO text escaped and verbatim.
    """
    if value is None:
        return None
    try:
        utc = rso.to_utc(value, ZONE)
    except SourceUnavailable:
        return value
    return utc.astimezone(ZoneInfo(ZONE)).isoformat()


def _body(fields: dict[str, Any]) -> str | None:
    return " ".join(
        part for part in (fields.get("shortcut"), fields.get("content")) if part
    ) or None


def _names(row: dict[str, Any]) -> tuple[str, ...]:
    """Voivodeship names as the consumer folds them: the element text, lowercased."""
    names: list[str] = []
    for entry in row["provinces"]:
        slug, name = entry[0], entry[1]
        folded = str(name or slug).lower()
        if folded not in names:
            names.append(folded)
    return tuple(names)


def _communique_item(row: dict[str, Any], term: str) -> dict[str, Any]:
    fields = row["fields"]
    return {
        "id": row["source_id"],
        "title": fields.get("title"),
        "valid_from": feed_stamp_as_iso(fields.get("valid_from")),
        "valid_to": feed_stamp_as_iso(fields.get("valid_to")),
        "text": _body(fields),
        "air_term": term,
    }


def warnings_rows(rows: list[dict[str, Any]], as_of: datetime) -> list[dict[str, Any]]:
    """The `pl_warnings` list from communique rows in feed order.

    Expired rows and rows not about the air are dropped; voivodeships are
    deduplicated and ordered by first appearance, and each carries the rows
    that named it, in feed order.
    """
    active: list[tuple[dict[str, Any], str]] = []
    for row in rows:
        fields = row["fields"]
        if is_expired(fields.get("valid_to"), as_of):
            continue
        term = air_term(fields.get("title"), _body(fields))
        if term is not None:
            active.append((row, term))
    order: list[str] = []
    for row, _term in active:
        for name in _names(row):
            if name not in order:
                order.append(name)
    return [
        {
            "voivodeship": name,
            "communiques": [
                _communique_item(row, term) for row, term in active if name in _names(row)
            ],
        }
        for name in order
    ]


def warnings_block(store: EventStore, as_of: datetime) -> Block:
    """`pl_warnings` for one moment, or the reason it is absent or null."""
    if store.newest_attempt_at(rso.FEED) is None:
        return UNPUBLISHED
    read = store.newest_read(rso.FEED, WARNINGS_URL)
    if read is None:
        return Block(published=True, value=None)
    age = (as_of - _parse_stored(str(read["started_at"]))).total_seconds()
    if age > WARNINGS_VALID_FOR_S:
        return Block(published=True, value=None)
    snapshot = store.newest_snapshot(rso.FEED, WARNINGS_URL)
    if snapshot is None:
        return Block(published=True, value=None)
    members = [str(member) for member in snapshot["members"]]
    held = store.communiques_by_digest(members)
    if any(member not in held for member in members):
        # A list naming a row nobody wrote is a store this cycle cannot read,
        # and a partial list would render as a complete one.
        return Block(published=True, value=None)
    return Block(published=True, value=warnings_rows([held[m] for m in members], as_of))


# ---- airspace


def altitude_metres(code: str | None) -> int | None:
    """A vertical limit as a reader's approximation in metres, or None.

    `GND` and `SFC` are 0, `Annn` is hundreds of feet, `Fnnn` a flight level,
    rounded to 50 m because a flight level is a pressure altitude. Anything
    else is None and the caller shows the code it has.
    """
    if not code:
        return None
    text = code.strip().upper()
    if text in ("GND", "SFC"):
        return 0
    found = _ALTITUDE.match(text)
    if not found:
        return None
    feet = int(found.group(2)) * 100
    return int(round(feet * _METRES_PER_FOOT / _METRES_STEP)) * _METRES_STEP


def is_civil(res: pansa.Reservation) -> bool:
    return bool(CIVIL_MARKS & set(_TOKEN.findall(res.remarks.upper())))


def _on_in_force(res: pansa.Reservation, now: datetime) -> bool:
    return res.status == STATUS_ON and res.starts_at <= now <= res.ends_at


def _called_up(zone: pansa.Zone, res: pansa.Reservation) -> bool:
    if zone.kind == "TRA":
        return any(mark in res.remarks.upper() for mark in TRA_CALLED_UP)
    return True


def drawn_now(zone: pansa.Zone, now: datetime) -> pansa.Reservation | None:
    """The reservation a zone is drawn for, or None; the one ending first wins."""
    if zone.kind not in KINDS_DRAWN:
        return None
    live = [
        res for res in zone.reservations
        if _on_in_force(res, now) and not is_civil(res) and _called_up(zone, res)
    ]
    return min(live, key=lambda res: res.ends_at) if live else None


def civil_now(zone: pansa.Zone, now: datetime) -> bool:
    if zone.kind not in KINDS_DRAWN:
        return False
    return any(_on_in_force(res, now) and is_civil(res) for res in zone.reservations)


def drawn(zones: tuple[pansa.Zone, ...], now: datetime
          ) -> list[tuple[pansa.Zone, pansa.Reservation]]:
    """The zones drawn now, nearest end first, designator second."""
    pairs = [(zone, res) for zone in zones if (res := drawn_now(zone, now)) is not None]
    pairs.sort(key=lambda pair: (pair[1].ends_at, pair[0].designator))
    return pairs


def not_drawn(zones: tuple[pansa.Zone, ...], now: datetime) -> dict[str, int]:
    """What is switched on and still not drawn, counted in zones, by reason.

    The reasons partition the remainder, so `switched_on` equals the drawn
    count plus the three below it; a test asserts that rather than trusting it.
    """
    on = [z for z in zones if any(_on_in_force(r, now) for r in z.reservations)]
    rest = [z for z in on if drawn_now(z, now) is None]
    return {
        "switched_on": len(on),
        "drawn": len(on) - len(rest),
        "kind_not_drawn": sum(1 for z in rest if z.kind not in KINDS_DRAWN),
        "civil": sum(1 for z in rest if civil_now(z, now)),
        "tra_not_called_up": sum(
            1 for z in rest
            if z.kind == "TRA" and not civil_now(z, now)
            and any(_on_in_force(r, now) for r in z.reservations)
        ),
    }


def properties(zone: pansa.Zone, res: pansa.Reservation) -> dict[str, Any]:
    return {
        "designator": zone.designator,
        "kind": zone.kind,
        "lower": res.lower,
        "upper": res.upper,
        "lower_m": altitude_metres(res.lower),
        "upper_m": altitude_metres(res.upper),
        "managed_by": res.managed_by,
        "until": res.ends_at.astimezone(UTC).isoformat(timespec="seconds"),
        "remarks": res.remarks or None,
    }


def airspace_value(
    zones: tuple[pansa.Zone, ...],
    now: datetime,
    *,
    read_at: datetime,
    unreadable: int,
    stale_error: str | None,
) -> dict[str, Any]:
    """The `pl_airspace` object: the consumer's text block plus the drawn outlines.

    `features` is the one addition. The consumer served the outlines from its
    own cache at `/airspace.json`; carried here, the text and the shapes come
    from one reading and cannot describe two different skies.
    """
    statuses: dict[str, int] = {}
    for zone in zones:
        for res in zone.reservations:
            statuses[res.status] = statuses.get(res.status, 0) + 1
    pairs = drawn(zones, now)
    return {
        "read_at": read_at.isoformat(timespec="seconds"),
        "switched_on": [properties(zone, res) for zone, res in pairs],
        "not_drawn": not_drawn(zones, now),
        "unreadable": unreadable,
        "statuses": dict(sorted(statuses.items())),
        "stale_error": stale_error,
        "features": [
            {"type": "Feature", "geometry": zone.geometry,
             "properties": properties(zone, res)}
            for zone, res in pairs
        ],
    }


def airspace_block(store: EventStore, as_of: datetime) -> Block:
    """`pl_airspace` for one moment, or the reason it is absent or null.

    **No age ceiling, unlike the communiques, and the asymmetry is the payload
    shape.** This object carries `read_at` and `stale_error`, and the page
    prints both, so an old reading is shown as old. The consumer did exactly
    this and it is kept.
    """
    if store.newest_attempt_at(pansa.FEED) is None:
        return UNPUBLISHED
    read = store.newest_read(pansa.FEED, pansa.SOURCE_URL)
    if read is None:
        return Block(published=True, value=None)
    snapshot = store.newest_snapshot(pansa.FEED, pansa.SOURCE_URL)
    if snapshot is None:
        return Block(published=True, value=None)
    members = [str(member) for member in snapshot["members"]]
    held = store.airspace_zones_by_digest(members)
    if any(member not in held for member in members):
        return Block(published=True, value=None)
    zones = tuple(pansa.zone_from_record(held[member]) for member in members)
    read_at = _parse_stored(str(read["started_at"]))
    newest_attempt = store.newest_attempt_at(pansa.FEED, pansa.SOURCE_URL)
    stale_error = None
    if newest_attempt is not None and _parse_stored(newest_attempt) > read_at:
        stale_error = store.newest_refusal_detail(pansa.FEED, pansa.SOURCE_URL)
    return Block(published=True, value=airspace_value(
        zones, as_of, read_at=read_at,
        unreadable=int(read["unreadable"] or 0), stale_error=stale_error,
    ))


def measure(store: EventStore, as_of: datetime) -> PolandBlocks:
    """Both Polish keys for one moment, from the store and nothing else."""
    return PolandBlocks(
        warnings=warnings_block(store, as_of),
        airspace=airspace_block(store, as_of),
    )
