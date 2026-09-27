"""The past week as intervals: what `timeline.json` carries (D-058).

**The question this answers is D-054's.** The store has recorded the Ukrainian
alerts since its first row, and the RCB communique list and the PAŻP plan since
0.55.2.0 was installed on 2026-09-19. What no file carried was that record, so
the site's seven-day slider had nothing to repaint from. This module writes it:
one file, the trailing week, **intervals rather than frames**. A frame every
few minutes repeats the same picture thousands of times; an interval list grows
with change and not with time.

**One rule, two implementations, and a test that they agree.** Nothing here
decides what a moment looked like. An area is named by `report.area_picture`,
the rule `compose` uses; the communique keys by `poland.warnings_verdict`, the
rule `warnings_blocks` uses; the airspace by `poland.airspace_reading` and
`poland.drawn`, the rules `airspace_block` uses; coverage by the threshold
`liveness.measure_feed` uses. What this module adds is *when to ask*: it finds
every instant at which one of those answers can change and asks there. The
store readers answer "at this moment" (`at=`); this module answers "over this
window", and `tests/test_timeline.py` holds the two to the same picture at
sampled instants. If a change point is missing, that test is where it shows.

**Two clocks, one per layer, each the only one its data has.** Areas change at
source time (`ts_source`): the picture at a moment is `compose` over every
event the source stamped at or before it, which is what the store now knows
about that moment, including rows that reached it later, after an outage. The
Polish layers change at read time: a list has no clock but the read that saw
it, so the picture at a moment is the newest list read at or before it. The
first is the better reconstruction of the sky; the second is the only one the
lists allow. Where the record at a moment was incomplete, `coverage` says so,
per pipe and by the rule the live `sources` block uses.

**What an interval means.** Half-open `[from, to)`; `to: null` is still open
when the file was written and never "ended". Stamps at the store's own
precision, microseconds included, because the rules compare at microsecond
precision and a boundary rounded to the second would put the two
implementations one tick apart. A state that began before the window carries
the window's start as its `from`: the file's scope is the week, and when a
standing began is the item's own `since`.
"""

from __future__ import annotations

import bisect
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from mavo import poland
from mavo.areas import AreaTable
from mavo.liveness import FeedSpec, PipeState, measure_feed
from mavo.poland import Block, Drawable
from mavo.report import DEFAULT_TRAILING_DAYS, area_item, area_picture, compose
from mavo.schema import ThreatEvent, ThreatKind
from mavo.sources import pansa, rso
from mavo.store import EventStore

#: The file's own version, apart from `state.json`'s: the two are read by
#: different code and change for different reasons.
TIMELINE_VERSION = 1

#: The window is the week the map shades by, so a slider and the shading
#: describe one week (D-048's argument, one file over).
WINDOW_DAYS = DEFAULT_TRAILING_DAYS

#: The finest step a `datetime` has. A rule that holds *through* an instant (a
#: communique valid until 23:59:00 is valid at 23:59:00) stops holding one tick
#: later, and that tick is where the half-open interval ends.
TICK = timedelta(microseconds=1)

#: The fields of an area item that belong to the place and not to the moment.
#: Carried once per area in `places` rather than once per interval.
PLACE_FIELDS: tuple[str, ...] = (
    "katottg", "oblast", "oblast_name", "border_km_lower", "border_km_upper",
)

#: What a layer the store never recorded reads as in a picture, as distinct
#: from `null` (recorded, and unreadable at that moment) and from an empty list.
ABSENT = "absent"


def _stamp(text: str) -> datetime:
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError(f"{text!r} has no offset; the store writes offsets")
    return parsed.astimezone(UTC)


def _optional_stamp(text: str | None) -> datetime | None:
    return None if text is None else _stamp(text)


def _iso(moment: datetime | None) -> str | None:
    return None if moment is None else moment.astimezone(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class Span:
    """`[start, end)`; `end` None is open at the window's end."""

    start: datetime
    end: datetime | None

    def holds(self, moment: datetime) -> bool:
        return self.start <= moment and (self.end is None or moment < self.end)

    def as_item(self) -> dict[str, str | None]:
        return {"from": _iso(self.start), "to": _iso(self.end)}


# ---- areas


@dataclass(frozen=True, slots=True)
class AreaSpan:
    area_id: str
    #: The area item's fields that change: `alert`, `kind`, `since`, `kinds`.
    standing: dict[str, Any]
    span: Span


@dataclass(frozen=True, slots=True)
class AreaLayer:
    oldest_observation: datetime | None
    places: dict[str, dict[str, Any]]
    spans: tuple[AreaSpan, ...]

    def reaches(self, start: datetime) -> bool:
        """Whether the log reaches back to `start`, so a quiet start is a quiet start."""
        return self.oldest_observation is not None and self.oldest_observation <= start


def _split(item: dict[str, object]) -> tuple[dict[str, Any], dict[str, Any]]:
    place = {name: item[name] for name in PLACE_FIELDS}
    standing = {
        name: value for name, value in item.items()
        if name not in PLACE_FIELDS and name != "area_id"
    }
    return place, standing


def area_layer(
    events: Iterable[ThreatEvent], start: datetime, end: datetime, table: AreaTable
) -> AreaLayer:
    """Every area's standing over `[start, end]`, changing at source time.

    The fold is `compose`'s: per `(area_id, kind)` the last write wins, ordered
    by `(ts_source, ts_ingest)`, ties to the later row in the order the log was
    handed over. Sorting stably by that pair and applying rows in turn gives,
    at every instant, the winner `compose` picks from the rows stamped at or
    before it. An event stamped after `end` is not in this file: the present
    belongs to `state.json`.
    """
    ordered = sorted(
        (event for event in events if event.ts_source <= end),
        key=lambda event: (event.ts_source, event.ts_ingest),
    )
    oldest = ordered[0].ts_source if ordered else None
    standing: dict[str, dict[ThreatKind, ThreatEvent]] = {}
    split = bisect.bisect_right([event.ts_source for event in ordered], start)
    for event in ordered[:split]:
        standing.setdefault(event.area_id, {})[event.kind] = event

    places: dict[str, dict[str, Any]] = {}
    current: dict[str, tuple[dict[str, Any], datetime]] = {}

    def picture(area_id: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
        found = area_picture(area_id, standing[area_id].values(), table)
        return None if found is None else _split(area_item(found))

    for area_id in sorted(standing):
        opened = picture(area_id)
        if opened is not None:
            places[area_id], state = opened
            current[area_id] = (state, start)

    spans: list[AreaSpan] = []
    index = split
    while index < len(ordered):
        instant = ordered[index].ts_source
        touched: set[str] = set()
        while index < len(ordered) and ordered[index].ts_source == instant:
            event = ordered[index]
            standing.setdefault(event.area_id, {})[event.kind] = event
            touched.add(event.area_id)
            index += 1
        for area_id in sorted(touched):
            found = picture(area_id)
            held = current.get(area_id)
            if held is not None and found is not None and held[0] == found[1]:
                continue
            if held is not None:
                spans.append(AreaSpan(area_id, held[0], Span(held[1], instant)))
                del current[area_id]
            if found is not None:
                places.setdefault(area_id, found[0])
                current[area_id] = (found[1], instant)
    for area_id, (standing_now, since) in sorted(current.items()):
        spans.append(AreaSpan(area_id, standing_now, Span(since, None)))
    spans.sort(key=lambda span: (span.area_id, span.span.start))
    named = {span.area_id for span in spans}
    return AreaLayer(
        oldest_observation=oldest,
        places={area_id: places[area_id] for area_id in sorted(named)},
        spans=tuple(spans),
    )


# ---- the Polish layers: shared helpers


def _newest_at(stamps: Sequence[datetime], moment: datetime) -> int | None:
    """Index of the last stamp at or before `moment` in a sorted list, or None."""
    found = bisect.bisect_right(stamps, moment) - 1
    return found if found >= 0 else None


def _reads(store: EventStore, feed: str, url: str, start: datetime,
           end: datetime) -> list[datetime]:
    """The newest read at or before `start`, then every read in `(start, end]`."""
    reads: list[datetime] = []
    prior = store.newest_read(feed, url, at=start)
    if prior is not None:
        reads.append(_stamp(str(prior["started_at"])))
    for row in store.iter_attempts(feed, since=start + TICK, until=end + TICK):
        if row["outcome"] == "read" and row["url"] == url:
            reads.append(_stamp(str(row["started_at"])))
    return reads


def _lists(store: EventStore, feed: str, url: str, start: datetime,
           end: datetime) -> list[tuple[datetime, list[str]]]:
    """The newest list at or before `start`, then every list recorded in `(start, end]`."""
    lists: list[tuple[datetime, list[str]]] = []
    prior = store.newest_snapshot(feed, url, at=start)
    if prior is not None:
        lists.append((_stamp(str(prior["observed_at"])),
                      [str(member) for member in prior["members"]]))
    for row in store.snapshots(feed, url, since=start + TICK, until=end + TICK):
        lists.append((_stamp(str(row["observed_at"])),
                      [str(member) for member in row["members"]]))
    return lists


def _inside(moment: datetime | None, start: datetime, end: datetime) -> bool:
    return moment is not None and start < moment <= end


# ---- communiques


@dataclass(frozen=True, slots=True)
class RcbSpan:
    warnings: Block
    all_clear: Block
    span: Span


@dataclass(frozen=True, slots=True)
class RcbLayer:
    recorded_since: datetime | None
    spans: tuple[RcbSpan, ...]


def rcb_layer(store: EventStore, start: datetime, end: datetime) -> RcbLayer:
    """`pl_warnings` and `pl_all_clear` over `[start, end]`, as `warnings_blocks` would say.

    The verdict can change at four kinds of instant and nowhere else: the first
    poll (absent to published), a list recorded (the members), a read that ends
    or a tick that starts a stretch older than `WARNINGS_VALID_FOR_S` (the age
    ceiling), and a communique's end passing (`is_expired`). The issue times
    the all-clear pairing compares are fixed by the rows and never by the
    moment, so they change nothing on their own.
    """
    first = _optional_stamp(store.oldest_attempt_at(rso.FEED))
    if first is None or first > end:
        return RcbLayer(recorded_since=first, spans=())
    reads = _reads(store, rso.FEED, poland.WARNINGS_URL, start, end)
    lists = _lists(store, rso.FEED, poland.WARNINGS_URL, start, end)
    list_stamps = [stamp for stamp, _members in lists]
    wanted = sorted({member for _stamp_, members in lists for member in members})
    held = store.communiques_by_digest(wanted)

    ceiling = timedelta(seconds=poland.WARNINGS_VALID_FOR_S)
    instants: set[datetime] = {max(start, first)}
    for index, read in enumerate(reads):
        before = reads[index - 1] if index else None
        if before is None or read - before > ceiling:
            instants.add(read)
        after = reads[index + 1] if index + 1 < len(reads) else None
        if after is None or after > read + ceiling + TICK:
            instants.add(read + ceiling + TICK)
    instants.update(list_stamps)
    for member in wanted:
        row = held.get(member)
        if row is None:
            continue
        valid_to = row["fields"].get("valid_to")
        expiry = poland.expiry_instant(valid_to if isinstance(valid_to, str) else None)
        if expiry is not None:
            instants.add(expiry + TICK)
    moments = sorted(moment for moment in instants
                     if max(start, first) <= moment <= end)

    spans: list[RcbSpan] = []
    for moment in moments:
        read_index = _newest_at(reads, moment)
        list_index = _newest_at(list_stamps, moment)
        warnings, cleared = poland.warnings_verdict(
            attempted=first <= moment,
            read_at=reads[read_index] if read_index is not None else None,
            members=lists[list_index][1] if list_index is not None else None,
            held=held,
            as_of=moment,
        )
        if spans and spans[-1].warnings == warnings and spans[-1].all_clear == cleared:
            continue
        if spans:
            last = spans[-1]
            spans[-1] = RcbSpan(last.warnings, last.all_clear, Span(last.span.start, moment))
        spans.append(RcbSpan(warnings, cleared, Span(moment, None)))
    return RcbLayer(recorded_since=first, spans=tuple(spans))


# ---- airspace


@dataclass(frozen=True, slots=True)
class ZoneSpan:
    designator: str
    kind: str
    geometry: str
    properties: dict[str, Any]
    span: Span


@dataclass(frozen=True, slots=True)
class AirspaceLayer:
    recorded_since: datetime | None
    #: Stretches in which `airspace_block` would publish `null`: polled, and
    #: no plan this module can draw from.
    unread: tuple[Span, ...]
    geometries: dict[str, dict[str, Any]]
    spans: tuple[ZoneSpan, ...]


def _drawn_now(zones: tuple[pansa.Zone, ...], moment: datetime
               ) -> dict[tuple[str, str, str, int], dict[str, Any]]:
    """The zones `poland.drawn` draws at `moment`, keyed so a zone keeps its span.

    The key is the designator, the kind and the outline, plus a count for the
    case of one plan listing the same structure twice, which nothing measured
    rules out; the count keeps both instead of letting one overwrite the other.
    """
    drawn: dict[tuple[str, str, str, int], dict[str, Any]] = {}
    for zone, res in poland.drawn(zones, moment):
        base = (zone.designator, zone.kind, zone.geometry_digest())
        count = sum(1 for key in drawn if key[:3] == base)
        drawn[(*base, count)] = poland.properties(zone, res)
    return drawn


def airspace_layer(store: EventStore, start: datetime, end: datetime) -> AirspaceLayer:
    """The zones `airspace_block` draws over `[start, end]`, per zone.

    Changes happen at the first poll, the first read, a recorded list, and the
    edges of every switched-on reservation in a list: `poland.drawn` asks
    `starts_at <= now <= ends_at` of a reservation with the switched-on status,
    and nothing else it asks depends on the moment. `read_at`, `statuses` and
    `stale_error` are the text block's and change at every read; the slider
    repaints outlines, and a stretch without reads is `coverage`'s to report.
    """
    first = _optional_stamp(store.oldest_attempt_at(pansa.FEED))
    if first is None or first > end:
        return AirspaceLayer(recorded_since=first, unread=(), geometries={}, spans=())
    reads = _reads(store, pansa.FEED, pansa.SOURCE_URL, start, end)
    lists = _lists(store, pansa.FEED, pansa.SOURCE_URL, start, end)
    list_stamps = [stamp for stamp, _members in lists]
    wanted = sorted({member for _stamp_, members in lists for member in members})
    held = store.airspace_zones_by_digest(wanted)

    begin = max(start, first)
    instants: set[datetime] = {begin, *list_stamps}
    if reads:
        instants.add(reads[0])
    for member in wanted:
        record = held.get(member)
        if record is None:
            continue
        for res in pansa.zone_from_record(record).reservations:
            if res.status == poland.STATUS_ON:
                instants.add(res.starts_at)
                instants.add(res.ends_at + TICK)
    moments = sorted(moment for moment in instants if begin <= moment <= end)

    readings: dict[tuple[bool, bool, int | None], Block | Drawable] = {}
    geometries: dict[str, dict[str, Any]] = {}
    current: dict[tuple[str, str, str, int], tuple[dict[str, Any], datetime]] = {}
    spans: list[ZoneSpan] = []
    unread: list[Span] = []
    unread_since: datetime | None = None

    def close(key: tuple[str, str, str, int], moment: datetime) -> None:
        properties, since = current.pop(key)
        spans.append(ZoneSpan(key[0], key[1], key[2], properties, Span(since, moment)))

    for moment in moments:
        attempted = first <= moment
        has_read = bool(reads) and reads[0] <= moment
        list_index = _newest_at(list_stamps, moment)
        epoch = (attempted, has_read, list_index)
        if epoch not in readings:
            readings[epoch] = poland.airspace_reading(
                attempted,
                {"started_at": _iso(reads[0]), "unreadable": 0} if has_read else None,
                lists[list_index][1] if list_index is not None else None,
                held,
            )
        reading = readings[epoch]
        if isinstance(reading, Block):
            drawn: dict[tuple[str, str, str, int], dict[str, Any]] = {}
            if reading.published and unread_since is None:
                unread_since = moment
        else:
            drawn = _drawn_now(reading.zones, moment)
            for zone in reading.zones:
                digest = zone.geometry_digest()
                if any(key[2] == digest for key in drawn):
                    geometries.setdefault(digest, zone.geometry)
            if unread_since is not None:
                unread.append(Span(unread_since, moment))
                unread_since = None
        for key in [key for key in current if drawn.get(key) != current[key][0]]:
            close(key, moment)
        for key, properties in drawn.items():
            if key not in current:
                current[key] = (properties, moment)
    for key in sorted(current):
        properties, since = current[key]
        spans.append(ZoneSpan(key[0], key[1], key[2], properties, Span(since, None)))
    if unread_since is not None:
        unread.append(Span(unread_since, None))
    spans.sort(key=lambda span: (span.designator, span.kind, span.geometry, span.span.start))
    return AirspaceLayer(
        recorded_since=first,
        unread=tuple(unread),
        geometries={digest: geometries[digest] for digest in sorted(geometries)},
        spans=tuple(spans),
    )


# ---- coverage


@dataclass(frozen=True, slots=True)
class FeedCoverage:
    spec: FeedSpec
    recorded_since: datetime | None
    #: Stretches after the first poll in which `measure_feed` would not say
    #: `delivering`: refusing or stalled, which a reader sees alike as an
    #: incomplete record and an operator reads apart in the journal.
    gaps: tuple[Span, ...]


def feed_coverage(store: EventStore, spec: FeedSpec, start: datetime,
                  end: datetime) -> FeedCoverage:
    """Where one pipe was not delivering in `[start, end]`, by the live rule.

    `measure_feed` calls a pipe delivering while its newest read is at most
    `silence_is_an_outage_s` old, the edge included. So each read covers
    `[read, read + threshold]`, the edge one tick short of the next half-open
    interval, and a gap is whatever of the window after the first poll no
    read covers.
    """
    first = _optional_stamp(store.oldest_attempt_at(spec.feed))
    if first is None or first > end:
        return FeedCoverage(spec=spec, recorded_since=first, gaps=())
    reach = timedelta(seconds=spec.silence_is_an_outage_s) + TICK
    reads: list[datetime] = []
    prior = _optional_stamp(store.newest_read_at(spec.feed, at=start))
    if prior is not None:
        reads.append(prior)
    for row in store.iter_attempts(spec.feed, since=start + TICK, until=end + TICK):
        if row["outcome"] == "read":
            reads.append(_stamp(str(row["started_at"])))
    begin = max(start, first)
    gaps: list[Span] = []
    cursor = begin
    for read in reads:
        covered_until = read + reach
        if covered_until <= cursor:
            continue
        if read > cursor:
            gaps.append(Span(cursor, read))
        cursor = covered_until
    if cursor <= end:
        gaps.append(Span(cursor, None))
    return FeedCoverage(spec=spec, recorded_since=first, gaps=tuple(gaps))


# ---- the file


def to_timeline(
    areas: AreaLayer,
    rcb: RcbLayer,
    airspace: AirspaceLayer,
    coverage: Sequence[FeedCoverage],
    *,
    start: datetime,
    end: datetime,
    days: int,
) -> dict[str, object]:
    """The `timeline.json` payload, version `TIMELINE_VERSION`."""
    return {
        "v": TIMELINE_VERSION,
        "generated_at": _iso(end),
        "window": {"start": _iso(start), "days": days},
        "areas": {
            "oldest_observation": _iso(areas.oldest_observation),
            "log_reaches_window_start": areas.reaches(start),
            "places": areas.places,
            "intervals": [
                {"area_id": span.area_id, **span.standing, **span.span.as_item()}
                for span in areas.spans
            ],
        },
        "rcb": {
            "recorded_since": _iso(rcb.recorded_since),
            "intervals": [
                {"pl_warnings": span.warnings.value,
                 "pl_all_clear": span.all_clear.value,
                 **span.span.as_item()}
                for span in rcb.spans
            ],
        },
        "airspace": {
            "recorded_since": _iso(airspace.recorded_since),
            "unread": [span.as_item() for span in airspace.unread],
            "geometries": airspace.geometries,
            "intervals": [
                {"designator": span.designator, "kind": span.kind,
                 "geometry": span.geometry, "properties": span.properties,
                 **span.span.as_item()}
                for span in airspace.spans
            ],
        },
        "coverage": {
            entry.spec.feed: {
                "role": entry.spec.role,
                "silence_is_an_outage_s": entry.spec.silence_is_an_outage_s,
                "recorded_since": _iso(entry.recorded_since),
                "gaps": [span.as_item() for span in entry.gaps],
            }
            for entry in coverage
        },
    }


def build(
    store: EventStore,
    events: Iterable[ThreatEvent],
    end: datetime,
    *,
    table: AreaTable,
    feeds: Sequence[FeedSpec],
    days: int = WINDOW_DAYS,
) -> dict[str, object]:
    """The whole file for the week ending at `end`, from one replay and the store."""
    start = end - timedelta(days=days)
    return to_timeline(
        area_layer(events, start, end, table),
        rcb_layer(store, start, end),
        airspace_layer(store, start, end),
        [feed_coverage(store, spec, start, end) for spec in feeds],
        start=start,
        end=end,
        days=days,
    )


def interval_counts(payload: Mapping[str, Any]) -> dict[str, int]:
    """How many intervals each layer of a payload carries, and how many gaps."""
    return {
        "areas": len(payload["areas"]["intervals"]),
        "rcb": len(payload["rcb"]["intervals"]),
        "airspace": len(payload["airspace"]["intervals"]),
        "gaps": sum(len(entry["gaps"]) for entry in payload["coverage"].values()),
    }


# ---- one moment, both ways: the check the file is held to


def _feature_entry(feature: Mapping[str, Any]) -> dict[str, Any]:
    geometry = feature["geometry"]
    zone = pansa.Zone(designator="", kind="", geometry=geometry, reservations=())
    properties = dict(feature["properties"])
    return {"designator": properties["designator"], "kind": properties["kind"],
            "geometry": zone.geometry_digest(), "properties": properties}


def _zone_order(entry: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (entry["designator"], entry["kind"], entry["geometry"],
            str(entry["properties"].get("until")))


def picture_from_store(
    store: EventStore,
    events: Iterable[ThreatEvent],
    moment: datetime,
    *,
    table: AreaTable,
    feeds: Sequence[FeedSpec],
) -> dict[str, object]:
    """What the live rules say about one moment, asked directly: the reference.

    `compose` over the events stamped at or before it, the two composers at
    it, and each pipe's liveness at it. This is what `mavo timeline --at`
    prints, and what the file is compared with.
    """
    # Only the areas are read off the report, and they do not depend on the
    # history windows, so only the week is folded; the fold is `compose`'s.
    report = compose([event for event in events if event.ts_source <= moment],
                     as_of=moment, table=table, history_days=(DEFAULT_TRAILING_DAYS,))
    warnings, cleared = poland.warnings_blocks(store, moment)
    air = poland.airspace_block(store, moment)
    zones: object
    if not air.published:
        zones = ABSENT
    elif air.value is None:
        zones = None
    else:
        zones = sorted((_feature_entry(feature) for feature in air.value["features"]),
                       key=_zone_order)
    pipes: dict[str, str] = {}
    for spec in feeds:
        state = measure_feed(store, spec, as_of=moment).state
        pipes[spec.feed] = (
            "unrecorded" if state is PipeState.UNKNOWN
            else "delivering" if state is PipeState.DELIVERING
            else "gap"
        )
    return {
        "at": _iso(moment),
        "areas": [area_item(picture) for picture in report.areas],
        "rcb": (
            {"pl_warnings": warnings.value, "pl_all_clear": cleared.value}
            if warnings.published else ABSENT
        ),
        "airspace": zones,
        "coverage": pipes,
    }


def _holding(items: Iterable[Mapping[str, Any]], moment: datetime) -> list[Mapping[str, Any]]:
    return [
        item for item in items
        if _stamp(str(item["from"])) <= moment
        and (item["to"] is None or moment < _stamp(str(item["to"])))
    ]


def _recorded(since: object, moment: datetime) -> bool:
    return isinstance(since, str) and _stamp(since) <= moment


def picture_from_file(payload: Mapping[str, Any], moment: datetime) -> dict[str, object]:
    """What a `timeline.json` says about one moment: selection, and nothing decided.

    The shape `picture_from_store` returns, built only by choosing the
    intervals that hold `moment`. The consumer does the same in its own code;
    this copy exists so the producer can hold its file to its own rules.

    A moment outside the file's window is refused rather than answered: the
    file holds no interval there, and an empty selection would read as a
    quiet map.
    """
    start = _stamp(str(payload["window"]["start"]))
    end = _stamp(str(payload["generated_at"]))
    if not start <= moment <= end:
        raise ValueError(
            f"{_iso(moment)} is outside the file's window "
            f"{_iso(start)} to {_iso(end)}"
        )
    areas_block = payload["areas"]
    places = areas_block["places"]
    areas = []
    for interval in sorted(_holding(areas_block["intervals"], moment),
                           key=lambda item: str(item["area_id"])):
        standing = {name: value for name, value in interval.items()
                    if name not in ("from", "to")}
        areas.append({**standing, **places[interval["area_id"]]})

    rcb_block = payload["rcb"]
    rcb: object = ABSENT
    if _recorded(rcb_block["recorded_since"], moment):
        held = _holding(rcb_block["intervals"], moment)
        rcb = ({"pl_warnings": held[0]["pl_warnings"],
                "pl_all_clear": held[0]["pl_all_clear"]} if held else ABSENT)

    air_block = payload["airspace"]
    zones: object = ABSENT
    if _recorded(air_block["recorded_since"], moment):
        if _holding(air_block["unread"], moment):
            zones = None
        else:
            zones = sorted(
                ({"designator": item["designator"], "kind": item["kind"],
                  "geometry": item["geometry"], "properties": item["properties"]}
                 for item in _holding(air_block["intervals"], moment)),
                key=_zone_order,
            )

    pipes: dict[str, str] = {}
    for feed, entry in payload["coverage"].items():
        if not _recorded(entry["recorded_since"], moment):
            pipes[feed] = "unrecorded"
        elif _holding(entry["gaps"], moment):
            pipes[feed] = "gap"
        else:
            pipes[feed] = "delivering"
    return {"at": _iso(moment), "areas": areas, "rcb": rcb, "airspace": zones,
            "coverage": pipes}


#: What `publish` calls each cycle: the replayed log and the moment in, the
#: payload out, or None when this cycle has no file to write.
TimelineBuilder = Callable[[Sequence[ThreatEvent], datetime], dict[str, object] | None]
