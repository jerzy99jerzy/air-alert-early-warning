"""The report: what the picture is right now, and how blind we are about it.

Sprint S8 in `docs/MVP.md`. Two outputs from one composition, so they cannot
disagree: a line a person reads at half past three, and the `state.json`
contract a separate web application consumes.

**Silence is a first-class output here.** D-015 revision 1 moved MAVO from a
reporting instrument to an element of warning infrastructure, and the
difference lands in this module. An instrument that goes quiet has missing
data; infrastructure that goes quiet is telling its reader the sky is calm.
So every report carries the moment it describes, the age of the newest
observation behind it, and an explicit feed state - and when the store is
empty or stale, the feed state says so rather than rendering a short list of
active areas as a calm night.

`docs/FEED-SPEC.md` section 4 was written about a Polish feed that does not
exist. It applies to this output too, and the heartbeat property is the reason
`state.json` is written on every cycle whether or not anything changed. A
consumer that has not seen a fresh `generated_at` inside `valid_for_s` knows
it is blind, and can say so instead of displaying calm.

The all-clear convention is deliberately asymmetric and matches the contract
the site already implements: an area that has been affirmatively cleared
leaves the list, an area whose state is unknown stays on it as `unknown`. The
two are not the same claim, and folding them would be the founding defect of
this repository with a JSON schema wrapped around it.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from mavo.areas import AreaRef, AreaTable
from mavo.schema import AlertState, ThreatEvent, ThreatKind, is_clear

# The contract version. Bumped when a consumer could break, never silently:
# FEED-SPEC section 3 property four is a requirement this project wrote for
# somebody else's feed, and owing it to our own consumers is the whole point.
SCHEMA_VERSION = 1

# How long a report may be trusted after the observation it rests on. Chosen
# rather than measured, and labelled as such: the poll interval that will
# produce these observations is S9's work, and T39 has not yet measured the
# rate the source tolerates. 600 s is five times the two-minute requirement
# derived from the page-window arithmetic in T39, which is a margin rather
# than a finding. [assumption, unmeasured]
DEFAULT_VALID_FOR_S = 600


class FeedState(Enum):
    """Health of the pipeline, never of the sky.

    Kept separate from `AlertState` on purpose. `AlertState.UNKNOWN` says the
    source told us nothing about one area; `FeedState.BLIND` says the pipeline
    itself cannot see. A reader needs both, and a design that carries only one
    ends up expressing an outage as a quiet map.
    """

    OK = "ok"
    DEGRADED = "degraded"  # observations exist and are older than they should be
    BLIND = "blind"        # nothing to report on at all


@dataclass(frozen=True, slots=True)
class AreaPicture:
    """One area's current state, with everything a reader needs beside it."""

    area_id: str
    state: AlertState
    kind: ThreatKind
    since: datetime
    area: AreaRef | None

    @property
    def oblast(self) -> str:
        """The oblast, or "unknown" - never an empty string in the output."""
        if self.area is not None and self.area.oblast:
            return self.area.oblast
        return "unknown"

    @property
    def border_interval(self) -> str:
        """Distance to the Polish border as an interval, or "unknown"."""
        return "unknown" if self.area is None else self.area.border_interval

    @property
    def is_western(self) -> bool:
        """False when the area is unknown to the map.

        Deliberately false rather than None-propagating: an area the table
        cannot resolve is not silently promoted into the western list, and it
        is still visible in `unresolved_areas` on the report, so it is dropped
        from a subset rather than from the output.
        """
        return self.area is not None and self.area.is_western


@dataclass(frozen=True, slots=True)
class Report:
    """The composed picture at one moment, with its own blindness measured."""

    as_of: datetime
    newest_observation: datetime | None
    valid_for_s: int
    areas: tuple[AreaPicture, ...]
    unresolved_areas: tuple[str, ...]

    @property
    def staleness_s(self) -> float | None:
        """Age of the newest observation, or None when there is none.

        None means unknown and prints as "unknown". It is never zero: a store
        with nothing in it is not a store that was updated this second, and
        the difference is the whole product.
        """
        if self.newest_observation is None:
            return None
        return (self.as_of - self.newest_observation).total_seconds()

    @property
    def feed_state(self) -> FeedState:
        """OK, degraded or blind, decided by the age of the evidence."""
        age = self.staleness_s
        if age is None:
            return FeedState.BLIND
        if age > self.valid_for_s:
            return FeedState.DEGRADED
        return FeedState.OK

    @property
    def active(self) -> tuple[AreaPicture, ...]:
        """Areas affirmatively reported as under alert."""
        return tuple(p for p in self.areas if p.state is AlertState.ACTIVE)

    @property
    def western_active(self) -> tuple[AreaPicture, ...]:
        """The 3.5% this project exists for, nearest border first.

        Sorted by the *lower* bound of the interval rather than the centre:
        the areas this ordering is most wrong about under a centre sort are
        exactly the ones that touch the border, which are the ones a reader
        near Hrubieszow cares about. An area with no distance sorts last
        rather than first, because unknown must not read as near.
        """
        def key(picture: AreaPicture) -> tuple[int, float, float]:
            area = picture.area
            if area is None or area.border_lower_km is None:
                return (1, 0.0, 0.0)
            # Upper bound breaks the tie, and the tie is not rare: every area
            # that touches the border has a lower bound of zero, which is most
            # of the ones this list exists to show. Without the second term the
            # order among them falls back to whatever the fold produced.
            return (0, area.border_lower_km, area.border_upper_km or 0.0)

        return tuple(sorted((p for p in self.active if p.is_western), key=key))

    @property
    def unknown_areas(self) -> tuple[AreaPicture, ...]:
        """Areas the source has told us nothing about. Reported, not omitted."""
        return tuple(p for p in self.areas if p.state is AlertState.UNKNOWN)

    @property
    def nearest_km(self) -> float | None:
        """Lower bound of the distance to the nearest western active area."""
        candidates = [
            p.area.border_lower_km
            for p in self.western_active
            if p.area is not None and p.area.border_lower_km is not None
        ]
        return min(candidates) if candidates else None


def compose(
    events: Iterable[ThreatEvent],
    *,
    as_of: datetime | None = None,
    table: AreaTable | None = None,
    valid_for_s: int = DEFAULT_VALID_FOR_S,
) -> Report:
    """Fold an event log into the current picture.

    Last write per area wins, ordered by source time, because a later
    observation about an area supersedes an earlier one. Ties broken by
    ingest time so that a re-read of the same moment does not depend on
    iteration order.

    Cleared areas are dropped from the list and unknown ones are kept. That
    asymmetry is the contract, and it is the reason this is a fold rather
    than a filter: an area that went ACTIVE and then CLEAR must disappear,
    while an area that went ACTIVE and then UNKNOWN must remain and say so.
    """
    table = table if table is not None else AreaTable.from_csv()
    latest: dict[str, ThreatEvent] = {}
    for event in events:
        current = latest.get(event.area_id)
        if current is None or (event.ts_source, event.ts_ingest) >= (
            current.ts_source, current.ts_ingest
        ):
            latest[event.area_id] = event

    pictures: list[AreaPicture] = []
    unresolved: list[str] = []
    for area_id, event in sorted(latest.items()):
        if is_clear(event.state):
            continue
        area = table.by_code(area_id)
        if area is None:
            unresolved.append(area_id)
        pictures.append(
            AreaPicture(
                area_id=area_id,
                state=event.state,
                kind=event.kind,
                since=event.ts_source,
                area=area,
            )
        )
    newest = max((e.ts_source for e in latest.values()), default=None)
    return Report(
        as_of=as_of if as_of is not None else datetime.now(UTC),
        newest_observation=newest,
        valid_for_s=valid_for_s,
        areas=tuple(pictures),
        unresolved_areas=tuple(unresolved),
    )


def render_text(report: Report) -> str:
    """The report as a person reads it. Blindness first, never last.

    Ordering is a safety property rather than a style choice. A reader who
    stops after one line must have read the part that says whether the picture
    can be trusted, so the feed state leads and the areas follow.
    """
    age = report.staleness_s
    age_text = "unknown" if age is None else f"{age:.0f}s"
    lines = [
        f"as of {report.as_of.isoformat(timespec='seconds')}  "
        f"feed={report.feed_state.value}  observation age={age_text}"
    ]
    if report.feed_state is FeedState.BLIND:
        lines.append("BLIND: no observation behind this report. "
                     "This is not an all-clear.")
    elif report.feed_state is FeedState.DEGRADED:
        lines.append(f"DEGRADED: newest observation is older than "
                     f"{report.valid_for_s}s. Treat the picture as stale.")
    western = report.western_active
    if western:
        lines.append(f"active in the west: {len(western)}")
        for picture in western:
            lines.append(
                f"  {picture.area_id}  {picture.oblast}  "
                f"kind={picture.kind.value}  border={picture.border_interval}  "
                f"since {picture.since.isoformat(timespec='seconds')}"
            )
    else:
        lines.append("active in the west: 0 reported. "
                     "Absence of a report is not an all-clear.")
    lines.append(f"active elsewhere: {len(report.active) - len(western)}")
    if report.unknown_areas:
        lines.append(f"unknown: {len(report.unknown_areas)} areas, "
                     "state not reported by the source")
    if report.unresolved_areas:
        lines.append(f"unresolved by the map: {len(report.unresolved_areas)} "
                     "areas, printed rather than dropped")
    lines.append("This reports a picture. It does not predict a crossing.")
    return "\n".join(lines)


def to_contract(report: Report) -> dict[str, object]:
    """The `state.json` payload, schema v1.

    Written here rather than reconstructed by a consumer. The site's adapter
    was reading MAVO's domain objects and guessing at attribute names, which
    made the contract a thing the consumer inferred instead of a thing the
    producer published (D-020). A schema owned by the producer is checkable by
    the producer's own gate; one inferred by the consumer breaks on a rename
    nobody flagged.
    """
    return {
        "v": SCHEMA_VERSION,
        "generated_at": report.as_of.isoformat(timespec="seconds"),
        "valid_for_s": report.valid_for_s,
        "state": report.feed_state.value,
        "observation_age_s": report.staleness_s,
        "areas": [
            {
                "katottg": picture.area.code if picture.area is not None else "",
                "area_id": picture.area_id,
                "oblast": picture.oblast,
                "alert": picture.state.value,
                "kind": picture.kind.value,
                "since": picture.since.isoformat(timespec="seconds"),
                "border_km_lower": (
                    picture.area.border_lower_km if picture.area is not None else None
                ),
                "border_km_upper": (
                    picture.area.border_upper_km if picture.area is not None else None
                ),
            }
            for picture in report.areas
        ],
    }


def write_contract(report: Report, path: Path) -> Path:
    """Write `state.json` atomically, every cycle, changed or not.

    Atomic because a consumer polling the file must never read half of it:
    written to a temporary file in the same directory, flushed, fsynced,
    then renamed over the target. Renaming within a directory is the atomic
    operation; writing in place is not.

    Written unconditionally because the heartbeat is the property whose
    absence is dangerous. A file that is only rewritten when the picture
    changes is indistinguishable, to its reader, from a pipeline that died
    during a quiet hour.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(to_contract(report), ensure_ascii=False, indent=1)
    # mkstemp rather than NamedTemporaryFile: the file must outlive the handle
    # so it can be renamed, and a context manager that deletes on close is the
    # opposite of what an atomic replace needs. Same directory as the target,
    # because rename is only atomic within a filesystem.
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=".state-", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as tmp:
            tmp.write(payload + "\n")
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
    return path


@dataclass(frozen=True, slots=True)
class PublishReport:
    """What one publishing run did, and why it stopped."""

    cycles: int
    written: int
    blind_cycles: int
    degraded_cycles: int
    reason: str

    def line(self) -> str:
        """One line for an operator, with every count named."""
        return (
            f"cycles={self.cycles} written={self.written} "
            f"blind={self.blind_cycles} degraded={self.degraded_cycles} "
            f"stopped: {self.reason}"
        )


def publish(
    load: Callable[[], Iterable[ThreatEvent]],
    path: Path,
    *,
    interval_s: float,
    max_cycles: int | None = None,
    valid_for_s: int = DEFAULT_VALID_FOR_S,
    table: AreaTable | None = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] | None = None,
    on_cycle: Callable[[Report], None] | None = None,
) -> PublishReport:
    """Write the contract on a fixed interval until a named condition stops it.

    This is the heartbeat, and it is the reason the loop exists at all rather
    than a cron line calling `mavo report --json`. Cron would work; what cron
    would not give is a single process that can say how many of its cycles were
    blind, which is the number an operator needs and the number a dead cron job
    cannot report about itself.

    Stops on the first of: ``max_cycles`` reached, a write that fails, or an
    operator interrupt. The reason is recorded either way, because a loop that
    ends without saying why has told its operator that everything is fine.
    F46 is the precedent: an interrupt travelled through `backfill` and a run
    that had retrieved 1150 pages reported a stack trace instead of a count.

    **A failure to read the store is not a reason to skip the write.** The
    picture becomes blind and the blind picture is published, because a
    consumer polling a file that stopped being written cannot distinguish a
    dead producer from a quiet night. That is the failure `docs/FEED-SPEC.md`
    section 4 spends a section on, and this is the one place in the codebase
    where it would be easiest to reintroduce.
    """
    table = table if table is not None else AreaTable.from_csv()
    clock = now if now is not None else (lambda: datetime.now(UTC))
    cycles = written = blind = degraded = 0
    reason = f"reached max_cycles={max_cycles}"
    try:
        while max_cycles is None or cycles < max_cycles:
            cycles += 1
            try:
                events: Iterable[ThreatEvent] = list(load())
            except Exception as failure:  # noqa: BLE001
                # Deliberately broad. Whatever went wrong reading the store,
                # the answer is the same: publish blindness rather than
                # nothing. Narrowing this would mean a new exception type
                # somewhere below turns the loop silent, and silence is the
                # one outcome this function exists to prevent.
                events = []
                if on_cycle is None:
                    print(f"[BLIND] store unreadable: {failure}")
            report = compose(
                events, as_of=clock(), table=table, valid_for_s=valid_for_s
            )
            if report.feed_state is FeedState.BLIND:
                blind += 1
            elif report.feed_state is FeedState.DEGRADED:
                degraded += 1
            try:
                write_contract(report, path)
            except OSError as failure:
                reason = f"write failed: {failure}"
                break
            written += 1
            if on_cycle is not None:
                on_cycle(report)
            if max_cycles is None or cycles < max_cycles:
                sleep(interval_s)
    except KeyboardInterrupt:
        reason = "interrupted by operator"
    return PublishReport(
        cycles=cycles,
        written=written,
        blind_cycles=blind,
        degraded_cycles=degraded,
        reason=reason,
    )
