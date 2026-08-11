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
import random
import sys
import tempfile
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path

from mavo.areas import AreaRef, AreaTable, oblast_slug
from mavo.obs import RunLog
from mavo.schema import AlertState, AreaRole, ThreatEvent, ThreatKind, is_clear

# The contract version. Bumped when a consumer could break, never silently:
# FEED-SPEC section 3 property four is a requirement this project wrote for
# somebody else's feed, and owing it to our own consumers is the whole point.
#
# v3 adds the event stream (T50, D-024). v2 carried the current picture and
# seven-day counts and no history, so a consumer could not build a feed of
# transitions from it however it was written.
SCHEMA_VERSION = 3

#: The short window carried inside `state.json`, fetched on every cycle.
#:
#: Twenty minutes rather than an hour, chosen by the operator on 2026-08-12:
#: a dead collector empties the panel three times faster, which is a signal
#: the page exists to deliver. The cost is that a reader whose phone slept for
#: longer than the window cannot tell a gap from a quiet stretch, which is why
#: `window_start` is published beside the items rather than left to be derived.
STREAM_WINDOW_S = 1200

#: The long window, written to a separate file and fetched on demand.
#:
#: A day, because "what happened tonight" is the question a feed panel exists
#: to answer. Measured at roughly 800 events a day across all of Ukraine, this
#: is about 18 KiB gzipped: cheap once, and not cheap every two minutes, which
#: is the whole reason it is a second file rather than a longer window in the
#: first one.
FEED_WINDOW_S = 86400

#: Safety net on either window, not a design parameter.
#:
#: The first proposal capped the stream at 200 events, on a figure that turned
#: out to describe western areas only while the stream carries all of Ukraine:
#: two denominators for one number, the shape of T49. At the observed rate a
#: cap of 5,000 binds only at an intensity more than six times anything
#: measured, so `truncated` firing is itself a finding about intensity rather
#: than a daily artefact.
STREAM_CAP = 5000

# How long a report may be trusted after the observation it rests on. Chosen
# rather than measured, and labelled as such: the poll interval that will
# produce these observations is S9's work, and T39 has not yet measured the
# rate the source tolerates. 600 s is five times the two-minute requirement
# derived from the page-window arithmetic in T39, which is a margin rather
# than a finding. [assumption, unmeasured]
DEFAULT_VALID_FOR_S = 600

#: Fractional spread on the poll interval (T27). Ten to twenty percent is what
#: `docs/OBSERVABILITY.md` and the task both name; fifteen sits in the middle
#: and the caller can move it. Zero is allowed and means a fixed period, which
#: is what a measurement of the upstream's tolerance would want.
DEFAULT_JITTER = 0.15

# The trailing window the consumer shades its map by. Seven days is the
# consumer's choice rather than a measurement, and it is published as a
# parameter (`window_days`) so a reader can see which window produced the
# counts instead of inferring one.
DEFAULT_TRAILING_DAYS = 7


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
        """The oblast's register name, or "unknown". For a human reader."""
        if self.area is not None and self.area.oblast:
            return self.area.oblast
        return "unknown"

    @property
    def oblast_slug(self) -> str:
        """The canonical ASCII slug, or "" when nothing resolves it.

        Two fields rather than one because they answer to different readers.
        The register name is what a person recognises; the slug is what a
        consumer joins on, and joining on a Cyrillic display name is how
        F74 happened: the site indexes its geometry by slug, every area
        arrived carrying `Львівська`, and the map drew nothing while the
        distance list drew everything.

        Empty is the unknown state and never a match, the same rule
        `oblast_slug()` follows in `mavo/areas.py` (T38).
        """
        if self.area is None or not self.area.oblast:
            return ""
        return oblast_slug(self.area.oblast)

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
class StreamEvent:
    """One transition as a consumer reads it, in the same vocabulary as `areas`.

    A projection of `ThreatEvent` rather than the event itself: the store's
    row carries ingest time, provenance and the raw message text, none of
    which a page renders and the last of which is somebody's words about a
    place being shelled. What crosses the contract is what gets displayed.

    `role` crosses too, deliberately. One message can clear an area and list
    five others as still under alert, and a stream carrying only the subject
    would drop the five that are still dangerous. This project has made that
    loss once already (4,064 continuation areas discarded before T37).
    """

    area_id: str
    oblast_slug: str
    oblast_name: str
    state: AlertState
    kind: ThreatKind
    role: AreaRole
    at: datetime
    is_western: bool

    def as_item(self) -> dict[str, object]:
        """The contract form. Field names match `areas` where they overlap."""
        return {
            "area_id": self.area_id,
            "oblast": self.oblast_slug,
            "oblast_name": self.oblast_name,
            "alert": self.state.value,
            "kind": self.kind.value,
            "role": self.role.value,
            "at": self.at.isoformat(timespec="seconds"),
            "west": self.is_western,
        }


@dataclass(frozen=True, slots=True)
class EventWindow:
    """A bounded slice of the log, with its own left edge and its own honesty.

    `window_start` is published rather than derived because a consumer needs
    to compare it against its own last successful read: a page whose device
    slept through part of the window must not render what it received as a
    continuous stretch. Deriving it from `generated_at` would work only while
    the consumer's clock and the producer's agree, and the case that matters
    is exactly the one where the consumer has been away.

    `truncated` distinguishes a window the cap cut from a window nothing
    happened in. Without it the two are one empty-looking answer, which is
    the unknown-never-zero invariant wearing different clothes.
    """

    window_start: datetime
    window_s: int
    events: tuple[StreamEvent, ...]
    truncated: bool

    def as_block(self) -> dict[str, object]:
        """The contract form, shared by `state.json` and `feed.json`.

        One vocabulary so the consumer writes one reader for both files.
        """
        return {
            "window_start": self.window_start.isoformat(timespec="seconds"),
            "window_s": self.window_s,
            "truncated": self.truncated,
            "items": [event.as_item() for event in self.events],
        }


def event_window(
    events: Iterable[ThreatEvent],
    *,
    as_of: datetime,
    window_s: int,
    table: AreaTable,
    cap: int = STREAM_CAP,
) -> EventWindow:
    """Every transition in the trailing window, oldest first, newest kept.

    No filtering by area or by role: D-024 settled that the stream carries all
    of Ukraine and both roles, and that a reader near the border is entitled to
    see the east because a quiet twenty minutes in the west during a night the
    east is burning is a different fact from a quiet night.

    When the cap binds, the **newest** events survive. A reader opening a feed
    during a mass alert wants the last hour, not the first, and a truncation
    that kept the oldest would hand them the beginning of the night while the
    night was still happening.
    """
    edge = as_of - timedelta(seconds=window_s)
    inside = [event for event in events if edge <= event.ts_source <= as_of]
    inside.sort(key=lambda event: (event.ts_source, event.area_id))
    truncated = len(inside) > cap
    if truncated:
        inside = inside[-cap:]
    projected = []
    for event in inside:
        area = table.by_code(event.area_id)
        projected.append(
            StreamEvent(
                area_id=event.area_id,
                oblast_slug=oblast_slug(area.oblast) if area is not None and area.oblast else "",
                oblast_name=area.oblast if area is not None and area.oblast else "unknown",
                state=event.state,
                kind=event.kind,
                role=event.role,
                at=event.ts_source,
                # False rather than None-propagating for an area the map
                # cannot resolve, the same asymmetry `AreaPicture.is_western`
                # applies: unknown is not quietly promoted into the west.
                is_western=area is not None and area.is_western,
            )
        )
    return EventWindow(
        window_start=edge,
        window_s=window_s,
        events=tuple(projected),
        truncated=truncated,
    )


@dataclass(frozen=True, slots=True)
class RecentOblast:
    """How often one oblast declared an alert over the trailing window.

    Oblast granularity rather than raion, because the consumer shades whole
    oblasts and a raion-level count would be a finer number rendered at a
    coarser resolution: precision the display cannot carry and a reader would
    assume anyway.
    """

    slug: str
    alerts_count: int
    last_alert_ended_at: datetime | None


@dataclass(frozen=True, slots=True)
class Report:
    """The composed picture at one moment, with its own blindness measured."""

    as_of: datetime
    newest_observation: datetime | None
    valid_for_s: int
    areas: tuple[AreaPicture, ...]
    unresolved_areas: tuple[str, ...]
    recent: tuple[RecentOblast, ...] = ()
    trailing_days: int = DEFAULT_TRAILING_DAYS
    #: The short window published inside `state.json` (T50).
    stream: EventWindow | None = None
    #: The day-long window published to `feed.json`, from the same fold.
    feed: EventWindow | None = None
    #: Transitions in the last 24 hours, split west and rest. The context that
    #: keeps a twenty-minute window from being a keyhole: a quiet stream during
    #: a night the east is burning is a different fact from a quiet night.
    counts_24h: tuple[int, int] = (0, 0)

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


def trailing_counts(
    events: Iterable[ThreatEvent],
    *,
    as_of: datetime,
    days: int = DEFAULT_TRAILING_DAYS,
    table: AreaTable,
) -> tuple[RecentOblast, ...]:
    """Alert *episodes* per oblast over the trailing window.

    An episode is one stretch during which the oblast had at least one raion
    under alert. It opens when the oblast goes from no raion active to one,
    and closes when the last active raion is affirmatively cleared.

    **This counts episodes rather than raion transitions, and the difference
    is not cosmetic (F76).** The first version of this function added one per
    transition into ACTIVE. A single western episode lights every raion in the
    oblast at once, so one alert over Lviv counted as seven, and 22 of the 81
    western episodes in the design window touched all 36 western raions
    simultaneously. The shading would then have measured how finely an oblast
    is subdivided rather than how often it was under attack, and oblasts with
    more raions would have rendered systematically darker. The regression that
    should have caught it used one raion, so the mutation had nothing to bite.

    **UNKNOWN does not close an episode.** A source that stops talking about a
    raion has not said the alert ended, and treating silence as the end of an
    episode would be unknown-resolves-to-clear inside a counter. Only an
    affirmative all-clear closes one, which means an episode left open by a
    feed outage stays open, and the count is conservative in the direction
    that does not understate.

    An oblast the register map cannot resolve is dropped from this count and
    **not** folded into another: a count quietly wrong for the oblast it lands
    in is worse than one visibly missing, and those areas are already reported
    as `unresolved_areas` beside this.

    **An episode that overlaps the window counts, wherever it opened (F85).**
    The first cutoff was a filter on events, and it broke the promise two
    paragraphs up at the window's edge: an episode opened before the cutoff
    had its opening event aged out, so an oblast under a single alert longer
    than the window rendered as the quietest on the map, and a close falling
    inside the window went unrecorded because the episode it closed had never
    been seen. The fold now replays the whole log: events before the cutoff
    move the running state without counting, episodes still open at the
    cutoff are counted once as they cross it, and only an episode both opened
    and affirmatively closed before the window is outside it.

    `last_alert_ended_at` is the most recent episode close, or None where no
    episode closed inside the window. None means unknown, and a consumer must
    not render it as "ended just now".
    """
    cutoff = as_of - timedelta(days=days)
    active: dict[str, set[str]] = {}
    episodes: dict[str, int] = {}
    last_close: dict[str, datetime] = {}
    ordered = sorted(events, key=lambda e: (e.ts_source, e.area_id))
    inside = next(
        (i for i, e in enumerate(ordered) if e.ts_source >= cutoff), len(ordered)
    )
    for event in ordered[:inside]:
        area = table.by_code(event.area_id)
        slug = oblast_slug(area.oblast) if area is not None else ""
        if not slug:
            continue
        running = active.setdefault(slug, set())
        if event.state is AlertState.ACTIVE:
            running.add(event.area_id)
        elif is_clear(event.state):
            running.discard(event.area_id)
    # Episodes open as the window begins: counted here, once, so the loop
    # below cannot count them again (`running` is already non-empty).
    for slug, running in active.items():
        if running:
            episodes[slug] = 1
    for event in ordered[inside:]:
        area = table.by_code(event.area_id)
        slug = oblast_slug(area.oblast) if area is not None else ""
        if not slug:
            continue
        running = active.setdefault(slug, set())
        if event.state is AlertState.ACTIVE:
            if not running:
                episodes[slug] = episodes.get(slug, 0) + 1
            running.add(event.area_id)
        elif is_clear(event.state):
            running.discard(event.area_id)
            if not running and slug in episodes:
                last_close[slug] = event.ts_source
    return tuple(
        RecentOblast(
            slug=slug,
            alerts_count=count,
            last_alert_ended_at=last_close.get(slug),
        )
        for slug, count in sorted(episodes.items())
    )


def compose(
    events: Iterable[ThreatEvent],
    *,
    as_of: datetime | None = None,
    table: AreaTable | None = None,
    valid_for_s: int = DEFAULT_VALID_FOR_S,
    trailing_days: int = DEFAULT_TRAILING_DAYS,
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
    # Materialised once: the fold below and the trailing window both need the
    # whole log, and a generator consumed twice would silently give the second
    # reader nothing, which here would be an empty seven-day layer that looks
    # like a quiet week.
    replayed = list(events)
    latest: dict[str, ThreatEvent] = {}
    for event in replayed:
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
    moment = as_of if as_of is not None else datetime.now(UTC)
    # Both windows come from one fold of one log, so the feed cannot describe
    # a moment the contract does not. Two compositions would be two pictures,
    # and a consumer rendering history that contradicts the present would have
    # no way to tell which half to believe.
    feed = event_window(
        replayed, as_of=moment, window_s=FEED_WINDOW_S, table=table
    )
    stream = event_window(
        replayed, as_of=moment, window_s=STREAM_WINDOW_S, table=table
    )
    west = sum(1 for event in feed.events if event.is_western)
    return Report(
        as_of=moment,
        newest_observation=newest,
        valid_for_s=valid_for_s,
        areas=tuple(pictures),
        unresolved_areas=tuple(unresolved),
        recent=trailing_counts(
            replayed, as_of=moment, days=trailing_days, table=table
        ),
        trailing_days=trailing_days,
        stream=stream,
        feed=feed,
        # Counted off the day-long window rather than recomputed, so the two
        # cannot drift. The cap can bind here in principle; when it does,
        # `feed.truncated` says so in the same payload.
        counts_24h=(west, len(feed.events) - west),
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
    newest = report.newest_observation
    return {
        "v": SCHEMA_VERSION,
        "generated_at": report.as_of.isoformat(timespec="seconds"),
        "valid_for_s": report.valid_for_s,
        "state": report.feed_state.value,
        "observation_age_s": report.staleness_s,
        # When the source last said anything, as distinct from when this
        # picture was composed. A consumer showing only `generated_at` would
        # tell a reader the page is fresh while the feed behind it is hours
        # old, which is the staleness failure one level up.
        "source_last_message_at": (
            newest.isoformat(timespec="seconds") if newest is not None else None
        ),
        "window_days": report.trailing_days,
        "recent_7d": [
            {
                "oblast": entry.slug,
                "alerts_count": entry.alerts_count,
                "last_alert_ended_at": (
                    entry.last_alert_ended_at.isoformat(timespec="seconds")
                    if entry.last_alert_ended_at is not None
                    else None
                ),
            }
            for entry in report.recent
        ],
        "areas": [
            {
                "katottg": picture.area.code if picture.area is not None else "",
                "area_id": picture.area_id,
                "oblast": picture.oblast_slug,
                "oblast_name": picture.oblast,
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
        # v3. Always present, empty or not: an absent block and an empty one
        # read identically to a careless consumer, and with roughly eleven
        # events per twenty minutes the empty case is the common case at four
        # in the morning. Nothing happened is an answer and has to look like
        # one.
        "events": (
            report.stream.as_block()
            if report.stream is not None
            else _empty_block(report, STREAM_WINDOW_S)
        ),
        "counts_24h": {
            "west": report.counts_24h[0],
            "rest": report.counts_24h[1],
            "total": sum(report.counts_24h),
        },
    }


def _empty_block(report: Report, window_s: int) -> dict[str, object]:
    """The window a report composed before v3 would have had.

    Reports are constructed directly in a few tests and tools that predate the
    stream. They get a well-formed empty window rather than a missing key,
    because the consumer's contract says the block is always there.
    """
    return EventWindow(
        window_start=report.as_of - timedelta(seconds=window_s),
        window_s=window_s,
        events=(),
        truncated=False,
    ).as_block()


def to_feed(report: Report) -> dict[str, object]:
    """The `feed.json` payload: the day-long window, fetched on demand.

    A separate file rather than a longer window inside `state.json` because
    the two have different costs. `state.json` is re-read on every cycle, so
    what it carries is a recurring cost on a phone that may be on one bar;
    the day of history is fetched when a reader opens the panel and then obeys
    ordinary HTTP caching. Measured against the same budget the geometry was
    measured against: roughly 18 KiB gzipped on a typical day, 46 KiB on a
    campaign night [estimate, from 800 and 2,000 events respectively].

    Same item vocabulary as the block inside `state.json`, so the consumer
    writes one reader for both.
    """
    block = (
        report.feed.as_block()
        if report.feed is not None
        else _empty_block(report, FEED_WINDOW_S)
    )
    return {
        "v": SCHEMA_VERSION,
        "generated_at": report.as_of.isoformat(timespec="seconds"),
        **block,
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
    return _write_json(to_contract(report), path, prefix=".state-")


def write_feed(report: Report, path: Path) -> Path:
    """Write `feed.json` atomically, every cycle, changed or not.

    Same guarantees as the contract and for the same reasons, because a
    consumer polling this file has the same problem: a half-written day of
    history is worse than yesterday's, and a file that stops being refreshed
    must not be indistinguishable from a quiet night.
    """
    return _write_json(to_feed(report), path, prefix=".feed-")


def _write_json(payload: dict[str, object], path: Path, *, prefix: str) -> Path:
    """The atomic write both files use. One implementation, one guarantee."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, indent=1)
    # mkstemp rather than NamedTemporaryFile: the file must outlive the handle
    # so it can be renamed, and a context manager that deletes on close is the
    # opposite of what an atomic replace needs. Same directory as the target,
    # because rename is only atomic within a filesystem.
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=prefix, suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as tmp:
            tmp.write(body + "\n")
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
    #: Every interval actually waited, in order. T27 asks that the recorded
    #: distribution match the configured range over 72 hours, and a distribution
    #: nobody kept is a distribution nobody can check.
    intervals: tuple[float, ...] = ()
    # F84. The observer hook failed and was disabled; the loop kept writing.
    # Counted rather than absorbed, because a console that went quiet
    # mid-run needs an explanation the operator can find.
    callback_failures: int = 0

    def line(self) -> str:
        """One line for an operator, with every count named."""
        base = (
            f"cycles={self.cycles} written={self.written} "
            f"blind={self.blind_cycles} degraded={self.degraded_cycles} "
            f"stopped: {self.reason}"
        )
        if self.callback_failures:
            base += (
                f" (callback failed {self.callback_failures}x and was disabled;"
                " publishing continued)"
            )
        return base


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
    jitter: float = DEFAULT_JITTER,
    draw: Callable[[float, float], float] | None = None,
    log: RunLog | None = None,
    feed_path: Path | None = None,
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
    pick = draw if draw is not None else random.uniform
    intervals: list[float] = []
    cycles = written = blind = degraded = callback_failures = 0
    reason = f"reached max_cycles={max_cycles}"
    try:
        while max_cycles is None or cycles < max_cycles:
            cycles += 1
            cycle_id = log.cycle_id() if log is not None else ""
            try:
                events: Iterable[ThreatEvent] = list(load())
            except Exception as failure:  # noqa: BLE001
                # Deliberately broad. Whatever went wrong reading the store,
                # the answer is the same: publish blindness rather than
                # nothing. Narrowing this would mean a new exception type
                # somewhere below turns the loop silent, and silence is the
                # one outcome this function exists to prevent.
                events = []
                # F83. Unconditionally, and on stderr. The old guard printed
                # the cause only when no callback was installed, and the CLI
                # always installs one, so in the one mode anybody runs the
                # operator saw `feed=blind` with the reason discarded. stderr
                # so a redirected stdout still carries only the announcements.
                print(f"[BLIND] store unreadable: {failure}",
                      file=sys.stderr, flush=True)
            report = compose(
                events, as_of=clock(), table=table, valid_for_s=valid_for_s
            )
            if report.feed_state is FeedState.BLIND:
                blind += 1
            elif report.feed_state is FeedState.DEGRADED:
                degraded += 1
            try:
                write_contract(report, path)
                # The feed rides the same cycle and the same failure. A run
                # that kept publishing the picture while silently failing to
                # refresh the history would leave a consumer reading a feed
                # frozen at some earlier hour beside a present that keeps
                # moving, with nothing in either file saying so.
                if feed_path is not None:
                    write_feed(report, feed_path)
            except OSError as failure:
                reason = f"write failed: {failure}"
                break
            written += 1
            if on_cycle is not None:
                # F84. The observer is not the product; the file is. A
                # BrokenPipeError from an announce print (stdout piped to a
                # reader that went away) used to propagate out of this loop as
                # a stack trace with no PublishReport - F46's shape,
                # reintroduced through the observability hook - and stopped
                # the one output a consumer depends on. The callback is
                # disabled after its first failure, the failure is printed and
                # counted, and the heartbeat keeps beating. KeyboardInterrupt
                # is not caught here: an operator interrupt during a callback
                # is still an operator interrupt.
                try:
                    on_cycle(report)
                except Exception as failure:  # noqa: BLE001
                    callback_failures += 1
                    on_cycle = None
                    print(f"[CALLBACK-DISABLED] on_cycle raised: {failure}; "
                          "publishing continues without announcements",
                          file=sys.stderr, flush=True)
            if max_cycles is None or cycles < max_cycles:
                # T27. The interval is drawn per cycle, not fixed. A fixed
                # period is a beacon profile to anyone watching the traffic and
                # a perfectly regular load on an upstream with which there is no
                # agreement. It goes in now rather than later because adding it
                # later would invalidate every interval measurement taken before
                # it, and those measurements are the evidence that would justify
                # tightening the poll.
                spread = interval_s * jitter
                waited = pick(interval_s - spread, interval_s + spread)
                intervals.append(waited)
                if log is not None:
                    log.line(
                        "publish", "publish.interval", cycle=cycle_id,
                        base_s=interval_s, jitter=jitter, waited_s=round(waited, 3),
                    )
                sleep(waited)
    except KeyboardInterrupt:
        reason = "interrupted by operator"
    return PublishReport(
        cycles=cycles,
        written=written,
        blind_cycles=blind,
        degraded_cycles=degraded,
        reason=reason,
        callback_failures=callback_failures,
        intervals=tuple(intervals),
    )
