"""The Polish airspace use plan, read as a record of structures and their windows.

PAŻP (Polska Agencja Żeglugi Powietrznej, PANSA) publishes the updated plan,
UUP, as a list of GeoJSON features at `airspace.pansa.pl`. Each feature is one
airspace structure - a TSA, a TRA, a danger or restricted area - with the
reservations the agency holds on it: a window, vertical limits, the managing
unit, remarks and a status.

**Why this reader is here and not in `mavo-site` (D-053).** The consumer read
this endpoint from 4.75.0.0 and kept the last good reading and nothing else.
That was enough for a map of *now* and useless for anything else: the plan the
agency serves at 03:10 is replaced by 03:15 and no archive of it exists
anywhere this project can reach. The seven-day scrubber is to repaint the sky
as well as the alerts (decided 2026-09-16), so the readings have to be
recorded where the event store is, from the first day, or the scrubber's first
week is a week of nothing.

**The parser is a port and says where from.** `mavosite/airspace.py` at
4.76.0.0, whose schema was measured on `vm-site` on 2026-09-14 against the
live body: 382,154 bytes, `reservationStatus` PLANNED and ACTIVATED on UUP and
PLANNED alone on AUP, every stamp carrying `Z`. The rules for what the map
draws are not in this module. They are a presentation decision (D-S82) over
what was read, and they live in `mavo/polish.py` so that this file records
everything the plan said and decides nothing about it, which is D-034 applied
to a second Polish feed.

**What is deliberately not kept.** `popupHtml` is the agency's own interface
fragment and is never parsed or stored. `altitudeUnit` is a constant `FL`
beside values like `GND` and `A061`, so it describes nothing. `activeH24` and
`section` carried one value each across every feature measured. `centroid` is
derivable from the geometry and is not a claim the agency makes about
anything but its own drawing.

Three refusals, each because its alternative is silent:

* A body that is not the document **is not an empty plan.** HTML where JSON
  was expected, a top level that is neither a list nor a FeatureCollection,
  an oversized body, or a list in which nothing is readable raises
  `SourceUnavailable`. An empty list is a real answer and must never also be
  the answer to a question we failed to ask.
* A feature that cannot be read **is counted, not dropped**, on the page.
* A reservation stamp without an offset **is not a reservation.** It is
  refused and counted, because guessing a zone could move a window by two
  hours and nothing downstream would ever find out.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from mavo.errors import SourceUnavailable
from mavo.transport import Transport

#: What the store calls rows read from this endpoint.
FEED = "pansa"

#: The updated plan. **Not the day plan, and never as a fallback**: AUP carries
#: no ACTIVATED status at all [measured on `vm-site` 2026-09-14, 352 PLANNED
#: and 0 ACTIVATED against UUP's 202 and 75], so reading it when UUP fails
#: would answer a different question in the same words.
SOURCE_URL = "https://airspace.pansa.pl/map-configuration/uup"

#: Ten times the measured body. The ceiling exists so a redirected or replaced
#: endpoint is refused rather than parsed. `transport.MAX_BYTES` is the first
#: line of defence and this is the second, for the reason `rso.poll_once` gives.
MAX_BYTES = 4 * 1024 * 1024

#: The whole request, connect to last byte. The body is two orders larger than
#: an RSO page, and the consumer ran this read at twenty seconds without a
#: recorded timeout from 4.75.0.0 to 4.76.0.0 [reported, consumer journal not
#: re-read for this figure].
TIMEOUT_S = 20.0

_HTML = re.compile(r"<!DOCTYPE|<html", re.IGNORECASE)


@dataclass(frozen=True)
class Reservation:
    """One window on one structure, as the plan states it.

    Limits stay the feed's codes. `GND`, `A061` and `F245` are three notations
    in one field, and converting them here would be this module inventing a
    common unit; `mavo/polish.py` puts an approximation in metres *beside*
    them for a reader.
    """

    starts_at: datetime
    ends_at: datetime
    lower: str | None
    upper: str | None
    #: The managing unit's code (`EPDE`, `COP`, `MIL`), not a unit of measure.
    managed_by: str | None
    remarks: str
    status: str

    def as_record(self) -> dict[str, Any]:
        return {
            "starts_at": self.starts_at.astimezone(UTC).isoformat(timespec="seconds"),
            "ends_at": self.ends_at.astimezone(UTC).isoformat(timespec="seconds"),
            "lower": self.lower,
            "upper": self.upper,
            "managed_by": self.managed_by,
            "remarks": self.remarks,
            "status": self.status,
        }


@dataclass(frozen=True)
class Zone:
    """One structure: what it is, its outline, and every window held on it."""

    designator: str
    kind: str
    geometry: dict[str, Any]
    reservations: tuple[Reservation, ...]

    def geometry_text(self) -> str:
        """The outline as stored: canonical JSON, so equal shapes are equal text."""
        return json.dumps(
            {"type": self.geometry["type"], "coordinates": self.geometry["coordinates"]},
            sort_keys=True,
            separators=(",", ":"),
        )

    def geometry_digest(self) -> str:
        return hashlib.sha256(self.geometry_text().encode("utf-8")).hexdigest()

    def reservations_text(self) -> str:
        return json.dumps(
            [res.as_record() for res in self.reservations],
            sort_keys=True,
            ensure_ascii=False,
        )

    def digest(self) -> str:
        """Content hash over everything recorded, for idempotence on content.

        An activation changes one status inside one reservation and nothing
        else, and it must land as a new row; keying on the designator would
        overwrite the plan's history with its present.
        """
        payload = json.dumps(
            {
                "designator": self.designator,
                "kind": self.kind,
                "geometry": self.geometry_digest(),
                "reservations": [res.as_record() for res in self.reservations],
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Page:
    """One reading of the plan, with what it could not read counted."""

    zones: tuple[Zone, ...] = ()
    #: Features refused whole: no properties, no designator, a shape that is
    #: not a polygon.
    unreadable: int = 0
    #: Reservations refused inside features that were read, almost always for
    #: a stamp with no offset. Reported on the attempt row, never absorbed.
    reservations_refused: int = 0
    #: Every status seen, so a vocabulary change shows up as a number rather
    #: than as a map that silently went empty.
    statuses: dict[str, int] = field(default_factory=dict)


def _stamp(value: Any) -> datetime | None:
    """An offset-bearing ISO stamp, or None."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _reservation(raw: Any) -> Reservation | None:
    if not isinstance(raw, dict):
        return None
    starts, ends = _stamp(raw.get("startDate")), _stamp(raw.get("endDate"))
    if starts is None or ends is None or ends < starts:
        return None
    return Reservation(
        starts_at=starts,
        ends_at=ends,
        lower=_text(raw.get("lowerAltitude")),
        upper=_text(raw.get("upperAltitude")),
        managed_by=_text(raw.get("unit")),
        remarks=_text(raw.get("remarks")) or "",
        status=(_text(raw.get("reservationStatus")) or "?").upper(),
    )


def _zone(raw: Any) -> tuple[Zone | None, int]:
    """One feature as a zone, and how many of its reservations were refused."""
    if not isinstance(raw, dict):
        return None, 0
    props, geometry = raw.get("properties"), raw.get("geometry")
    if not isinstance(props, dict) or not isinstance(geometry, dict):
        return None, 0
    designator = _text(props.get("designator"))
    kind = _text(props.get("airspaceElementType"))
    if designator is None or kind is None:
        return None, 0
    if geometry.get("type") not in ("Polygon", "MultiPolygon"):
        return None, 0
    if not isinstance(geometry.get("coordinates"), list):
        return None, 0
    raws = props.get("airspaceReservations") or []
    if not isinstance(raws, list):
        raws = []
    read = [_reservation(item) for item in raws]
    reservations = tuple(res for res in read if res is not None)
    zone = Zone(
        designator=designator,
        kind=kind.upper(),
        geometry={"type": geometry["type"], "coordinates": geometry["coordinates"]},
        reservations=reservations,
    )
    return zone, len(read) - len(reservations)


def parse(payload: bytes) -> Page:
    """Read one UUP body. Refuses with `SourceUnavailable` what is not the document."""
    if len(payload) > MAX_BYTES:
        raise SourceUnavailable(
            f"UUP body is {len(payload)} bytes, over the {MAX_BYTES} ceiling")
    if _HTML.search(payload[:512].decode("utf-8", errors="replace")):
        raise SourceUnavailable("UUP answered with an HTML document where JSON was expected")
    try:
        data = json.loads(payload)
    except ValueError as bad:
        raise SourceUnavailable(f"UUP body is not JSON: {bad}") from bad
    if isinstance(data, list):
        features: list[Any] = data
    elif isinstance(data, dict) and isinstance(data.get("features"), list):
        features = data["features"]
    else:
        raise SourceUnavailable("UUP body is neither a list of features nor a FeatureCollection")
    zones: list[Zone] = []
    unreadable = refused = 0
    statuses: dict[str, int] = {}
    for raw in features:
        zone, dropped = _zone(raw)
        if zone is None:
            unreadable += 1
            continue
        refused += dropped
        zones.append(zone)
        for res in zone.reservations:
            statuses[res.status] = statuses.get(res.status, 0) + 1
    if features and not zones:
        raise SourceUnavailable(f"none of the {len(features)} UUP features were readable")
    return Page(
        zones=tuple(zones),
        unreadable=unreadable,
        reservations_refused=refused,
        statuses=dict(sorted(statuses.items())),
    )


def zone_from_record(record: dict[str, Any]) -> Zone:
    """Rebuild a zone from the row `EventStore.airspace_zones_by_digest` returns.

    The inverse of what `append_airspace_zones` writes, so the rules in
    `mavo/polish.py` run over the same objects whether the zone came off the
    wire a second ago or out of the store a week later. A stored window that
    no longer parses raises rather than disappearing: the store writes these
    stamps itself, and one it cannot read back was written by something else.
    """
    reservations = []
    for raw in record["reservations"]:
        starts = _stamp(raw["starts_at"])
        ends = _stamp(raw["ends_at"])
        if starts is None or ends is None:
            raise ValueError(
                f"stored reservation on {record['designator']!r} carries a stamp "
                "this module did not write")
        reservations.append(Reservation(
            starts_at=starts,
            ends_at=ends,
            lower=raw.get("lower"),
            upper=raw.get("upper"),
            managed_by=raw.get("managed_by"),
            remarks=raw.get("remarks") or "",
            status=str(raw.get("status") or "?"),
        ))
    geometry = record["geometry"]
    return Zone(
        designator=str(record["designator"]),
        kind=str(record["kind"]),
        geometry={"type": geometry["type"], "coordinates": geometry["coordinates"]},
        reservations=tuple(reservations),
    )


def poll_once(transport: Transport, url: str = SOURCE_URL) -> tuple[Page, float]:
    """Fetch the plan once and parse it. Returns the page and the seconds it took."""
    started = time.monotonic()
    body = transport.fetch(url, headers={"Accept": "application/json"})
    page = parse(body.encode("utf-8"))
    return page, time.monotonic() - started
