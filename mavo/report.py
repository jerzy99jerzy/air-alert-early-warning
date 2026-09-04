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
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path

from mavo.areas import AreaRef, AreaTable, oblast_slug
from mavo.obs import RunLog
from mavo.schema import (
    AlertState,
    AreaRole,
    ThreatEvent,
    ThreatKind,
    is_clear,
    state_precedence,
)

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

#: How far ahead of our own clock a source timestamp may sit and still count as
#: evidence that the pipeline is fresh (F120).
#:
#: Not a limit on what is stored, published or counted: a skewed row keeps its
#: own timestamp everywhere else in this file. It bounds one question only -
#: which observation the freshness of the picture may rest on - because a stamp
#: in the future passes every `age > valid_for_s` comparison and pins the feed
#: to `ok` while nothing arrives.
#:
#: Two seconds would be enough for the defect and would go blind on a healthy
#: host; a day would tolerate the defect. 120 s is chosen between them and is
#: **[assumption, unmeasured]**. The measurement that replaces it exists in
#: the store already: `ThreatEvent.latency_s` is `ts_ingest - ts_source` and
#: its *negative* tail is exactly this skew, so the number to set this to is a
#: percentile of that tail over a week on the host. T40's instrument collects
#: it and nothing has read it for this purpose. Until then the figure is a
#: margin rather than a finding, and it is labelled here rather than in a
#: document a reader of this module would not open.
SKEW_TOLERANCE_S = 120

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

#: The windows `history.json` carries, longest last (D-048). The shortest is
#: `DEFAULT_TRAILING_DAYS` and its two blocks are the same objects
#: `state.json` and `feed.json` publish: one fold, one moment, three lengths,
#: so a reader comparing the week with the quarter compares one arithmetic
#: applied twice and never two compositions that could disagree. A window
#: longer than the store has observed is published with that fact beside it
#: rather than as a quiet stretch; see `TrailingWindow.log_reaches_start`.
HISTORY_WINDOWS_DAYS: tuple[int, ...] = (7, 30, 90)


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
class KindStanding:
    """One threat kind's standing within one area (D-044).

    An area can carry several at once - artillery running since April under an
    air alert raised twenty minutes ago - and before D-044 the fold collapsed
    them onto the area, so the clear of one kind erased the area (F133). This
    is the unit the fold actually works in, published rather than discarded so
    a reader can see which threat ended and which did not.
    """

    kind: ThreatKind
    state: AlertState
    since: datetime

    def as_item(self) -> dict[str, object]:
        """The contract form, field names matching the area block it sits in."""
        return {
            "kind": self.kind.value,
            "alert": self.state.value,
            "since": self.since.isoformat(timespec="seconds"),
        }


@dataclass(frozen=True, slots=True)
class AreaPicture:
    """One area's current state, with everything a reader needs beside it."""

    area_id: str
    state: AlertState
    kind: ThreatKind
    since: datetime
    area: AreaRef | None
    #: Every kind not affirmatively cleared, loudest first (D-044). `state`,
    #: `kind` and `since` above are the headline drawn from this tuple by
    #: `state_precedence`, kept as their own fields so a consumer reading the
    #: v3 contract does not change on the day this one arrived. Defaulted, so a
    #: `Report` constructed directly by a tool that predates the field is still
    #: well formed rather than a TypeError at import time.
    kinds: tuple[KindStanding, ...] = ()

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
    """How much, and how often, one oblast was under alert over the window.

    Oblast granularity rather than raion, because the consumer shades whole
    oblasts and a raion-level count would be a finer number rendered at a
    coarser resolution: precision the display cannot carry and a reader would
    assume anyway.

    **Two quantities, because one of them collapses and the other does not
    (F114).** `alerts_count` counts stretches: it goes up only when the oblast
    goes from no raion under alert to at least one. Under sustained attack the
    raions overlap and the oblast never falls wholly quiet, so forty alerts
    over a week count as one - measured, and measured at exactly that ratio.
    The number is therefore *lowest where attack is heaviest*, which is the
    opposite of what a reader takes it for.

    `alert_seconds` is the union of the time any raion of this oblast spent
    under alert, clipped to the window at both ends. It does not collapse:
    forty overlapping alerts and forty spaced ones give nearly the same total.
    It is the quantity to shade a map by and the quantity to answer "how bad
    was this week here" with; `alerts_count` answers the different and
    narrower question of how many separate flare-ups there were.

    `open_at_as_of` says the oblast was still under alert when the picture was
    composed, which makes `alert_seconds` a lower bound that is still growing.
    An open stretch rendered identically to a closed one is the same collapse
    one layer out.
    """

    slug: str
    alerts_count: int
    last_alert_ended_at: datetime | None
    alert_seconds: int = 0
    open_at_as_of: bool = False


@dataclass(frozen=True, slots=True)
class RecentArea:
    """How often one **area** was under alert over the trailing window.

    The raion-level counterpart of `RecentOblast`, and deliberately not a
    finer rendering of it. `RecentOblast.alerts_count` answers "how often was
    this oblast under attack"; this answers "how often was this raion under
    attack", and the two are different questions with different answers. One
    western episode lights every raion of an oblast at once, so summing
    `episodes` across an oblast's areas reproduces exactly the number F76 was
    logged for: how finely the oblast is subdivided, wearing the costume of
    how often it was attacked. **The field is named `episodes` rather than
    `alerts_count` for that reason** - a consumer that reaches for the
    familiar name gets a `KeyError` rather than a plausible sum.

    This block exists because the consumer has no geometry below the oblast:
    `geometry.json` carries 25 oblast outlines and nothing finer [reported,
    from the consumer, 2026-08-19]. A distance at raion granularity therefore
    cannot be computed downstream at all, and an oblast-level interval would
    not be the same quantity: its lower bound comes from one raion and its
    upper from another, so it describes no single place while carrying the
    same field names as the per-area interval that describes exactly one.
    Two quantities under one name is the defect this block is shaped to avoid.

    The interval is copied from the same `border_km.csv` row the live picture
    reads, so the weekly sentence and the live sentence are comparable by
    construction rather than by a consumer's assumption.
    """

    code: str
    name: str
    oblast_slug: str
    oblast_name: str
    episodes: int
    last_active_at: datetime
    last_ended_at: datetime | None
    border_lower_km: float | None
    border_upper_km: float | None
    is_western: bool
    #: Seconds this area spent under alert inside the window, clipped at both
    #: ends. `episodes` collapses when alerts overlap or when an all-clear
    #: never arrives (F114); this does not. Summing `alert_seconds` across an
    #: oblast's areas is still not the oblast's `alert_seconds`, for the same
    #: reason the counts do not sum: the oblast figure is a union over
    #: simultaneous raions, not a total.
    alert_seconds: int = 0
    #: Still under alert when the picture was composed, which makes
    #: `alert_seconds` a lower bound rather than a total.
    open_at_as_of: bool = False

    def as_item(self) -> dict[str, object]:
        """The contract form. Field names match `areas` where they overlap."""
        return {
            "katottg": self.code,
            "area_name": self.name,
            "oblast": self.oblast_slug,
            "oblast_name": self.oblast_name,
            "episodes": self.episodes,
            "last_active_at": self.last_active_at.isoformat(timespec="seconds"),
            "last_ended_at": (
                self.last_ended_at.isoformat(timespec="seconds")
                if self.last_ended_at is not None
                else None
            ),
            "border_km_lower": self.border_lower_km,
            "border_km_upper": self.border_upper_km,
            "west": self.is_western,
            "alert_seconds": self.alert_seconds,
            "still_under_alert": self.open_at_as_of,
        }


@dataclass(frozen=True, slots=True)
class TrailingWindow:
    """One trailing window at both granularities, with what the log can say.

    `oblasts` is the `trailing_counts` fold and `areas` the `trailing_areas`
    fold, both over the same replay at the same `as_of`, so the two blocks
    of one window agree by construction and the blocks of different windows
    differ only in their cutoff.

    **A window the store has not observed in full is not a quiet window.**
    `oldest_observation` is the earliest source stamp in the replayed log,
    and `log_reaches_start` says whether it lies at or before the window's
    start. When it does not, every count in the window is a count over the
    part the log covers, and a consumer that renders it as a full window
    renders the unobserved part as calm - which is the one thing this
    project's counters exist to refuse (F85's shape, one window out). The
    field is a boolean beside a stamp rather than a clipped window, because
    the question a reader asks is "does this cover ninety days", and the
    honest answer is the date it covers from.
    """

    days: int
    start: datetime
    oblasts: tuple[RecentOblast, ...]
    areas: tuple[RecentArea, ...]
    oldest_observation: datetime | None

    @property
    def log_reaches_start(self) -> bool:
        return (
            self.oldest_observation is not None
            and self.oldest_observation <= self.start
        )

    def as_block(self) -> dict[str, object]:
        """The contract form. `oblasts` matches `recent_7d` and `areas`
        matches `recent_7d_areas` field for field, so a consumer reads all
        three windows with the readers it already has."""
        return {
            "days": self.days,
            "window_start": self.start.isoformat(timespec="seconds"),
            "log_oldest_at": (
                self.oldest_observation.isoformat(timespec="seconds")
                if self.oldest_observation is not None
                else None
            ),
            "log_reaches_window_start": self.log_reaches_start,
            "oblasts": [_oblast_item(entry) for entry in self.oblasts],
            "areas": [entry.as_item() for entry in self.areas],
        }


def _oblast_item(entry: RecentOblast) -> dict[str, object]:
    """One `recent_7d` row. Shared by `to_contract` and `TrailingWindow` so
    the week in `state.json` and the week in `history.json` are one
    serialisation and cannot drift apart a field at a time."""
    return {
        "oblast": entry.slug,
        "alerts_count": entry.alerts_count,
        "last_alert_ended_at": (
            entry.last_alert_ended_at.isoformat(timespec="seconds")
            if entry.last_alert_ended_at is not None
            else None
        ),
        # F114/F115. `alerts_count` collapses under overlap and the
        # collapse is worst where attack is heaviest; these two carry
        # the quantity that does not. A consumer shading a map should
        # read `alert_seconds` over `window_days * 86400`, which is
        # bounded, needs no thresholds chosen against a distribution,
        # and cannot invert. `alerts_count` stays because "how many
        # separate flare-ups" is a real and different question.
        "alert_seconds": entry.alert_seconds,
        # A figure still growing must not render as a total.
        "still_under_alert": entry.open_at_as_of,
    }


@dataclass(frozen=True, slots=True)
class Report:
    """The composed picture at one moment, with its own blindness measured."""

    as_of: datetime
    #: The observation the freshness of this picture rests on: the newest
    #: source timestamp that is not further ahead of us than `SKEW_TOLERANCE_S`
    #: (F120). None means there is no datable observation, which is `blind`.
    newest_observation: datetime | None
    valid_for_s: int
    areas: tuple[AreaPicture, ...]
    unresolved_areas: tuple[str, ...]
    recent: tuple[RecentOblast, ...] = ()
    #: The same window at raion granularity (0.33.0.0). Published to
    #: `feed.json` rather than `state.json`: measured at 10.2 KiB for the west
    #: alone and 35.5 KiB for every area the map knows, against a `state.json`
    #: of 13,150 bytes polled every 30 s on the host [measured, 2026-08-19].
    #: The headline sentence the page needs from it is one object, and that
    #: one travels in `state.json` as `nearest_7d`.
    recent_areas: tuple[RecentArea, ...] = ()
    trailing_days: int = DEFAULT_TRAILING_DAYS
    #: Every window `history.json` publishes, shortest first (D-048). The
    #: entry whose `days` equals `trailing_days` holds the very tuples
    #: `recent` and `recent_areas` hold, not a recomputation of them.
    history: tuple[TrailingWindow, ...] = ()
    #: The short window published inside `state.json` (T50).
    stream: EventWindow | None = None
    #: The day-long window published to `feed.json`, from the same fold.
    feed: EventWindow | None = None
    #: Transitions in the last 24 hours, split west and rest. The context that
    #: keeps a twenty-minute window from being a keyhole: a quiet stream during
    #: a night the east is burning is a different fact from a quiet night.
    counts_24h: tuple[int, int] = (0, 0)
    #: The newest source timestamp as the source wrote it, unfiltered. Separate
    #: from `newest_observation` because the two answer different questions:
    #: this one is "when did the source last speak", which stays reportable
    #: even when the stamp is not usable as evidence of our own freshness.
    #: Defaults to None so a `Report` built directly - a handful of tests and
    #: tools predate this field - falls back to `newest_observation` rather
    #: than losing the line.
    newest_source_stamp: datetime | None = None
    #: How far ahead of `as_of` the newest source timestamp sits, in seconds,
    #: floored at zero. Published rather than absorbed: the reason the F120
    #: behaviour was invisible for the life of the project is that nothing
    #: recorded the disagreement between the two clocks. Zero is the ordinary
    #: value and is written out, because an absent key and a zero read alike.
    clock_skew_s: float = 0.0

    @property
    def staleness_s(self) -> float | None:
        """Age of the newest usable observation, or None when there is none.

        None means unknown and prints as "unknown". A store with nothing in it
        is not a store that was updated this second, and the difference is the
        whole product.

        **Floored at zero (F120).** An observation inside the skew tolerance
        can still sit a little ahead of our clock, and a negative age passes
        every freshness comparison a consumer could write - including the one
        in `feed_state` directly below. Zero here means "as fresh as this
        pipeline can tell", and the amount by which the two clocks disagree is
        published beside it as `clock_skew_s` rather than hidden in the sign of
        this number.
        """
        if self.newest_observation is None:
            return None
        return max(0.0, (self.as_of - self.newest_observation).total_seconds())

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


    @property
    def nearest_recent(self) -> RecentArea | None:
        """The nearest area that was under alert in the trailing window.

        None when nothing in the window has a distance, and None is unknown:
        a page rendering it as "nothing near" would be printing silence as
        calm, which is the one thing this project refuses everywhere.

        A reduction the producer performs rather than the consumer, because
        the page needs exactly this sentence in its headline and the block it
        would be reduced from travels in the other file. `recent_areas` is
        sorted nearest-first with unknowns last, so this is its head with the
        unknown case excluded rather than a second ordering that could
        disagree with the first.
        """
        for entry in self.recent_areas:
            if entry.border_lower_km is not None:
                return entry
        return None


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

    **The running set holds `(area_id, kind)`, not `area_id` (F138).** Until
    0.49.0.0 it held areas, so the clear of one threat kind discarded the whole
    area while another kind was live: an oblast under a chronic artillery alarm
    had its episode closed, its clock stopped and `open_at_as_of` extinguished
    by the end of a concurrent air alert - the quiet tail that nobody observed,
    forbidden two paragraphs down, produced by this function. F133's mechanism,
    one layer further out than D-044 reached, found by the probe D-044's own
    review said was owed.
    """
    cutoff = as_of - timedelta(days=days)
    active: dict[str, set[tuple[str, ThreatKind]]] = {}
    episodes: dict[str, int] = {}
    last_close: dict[str, datetime] = {}
    #: Start of the stretch currently open per oblast, already clipped to the
    #: window. Separate from `last_close` because a stretch that opened before
    #: the cutoff contributes from the cutoff, not from when it opened: the
    #: window is seven days and a figure inside it may not exceed seven days.
    span_since: dict[str, datetime] = {}
    seconds: dict[str, float] = {}
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
            running.add((event.area_id, event.kind))
        elif is_clear(event.state):
            running.discard((event.area_id, event.kind))
    # Episodes open as the window begins: counted here, once, so the loop
    # below cannot count them again (`running` is already non-empty). Their
    # clock starts at the cutoff for the same reason.
    for slug, running in active.items():
        if running:
            episodes[slug] = 1
            span_since[slug] = cutoff
    for event in ordered[inside:]:
        area = table.by_code(event.area_id)
        slug = oblast_slug(area.oblast) if area is not None else ""
        if not slug:
            continue
        # Clamped rather than trusted. `ts_source` is the source's clock and
        # T40 measured it disagreeing with ours in both directions; an event
        # stamped after `as_of` must not be able to make a duration longer
        # than the window it is reported inside.
        stamp = min(event.ts_source, as_of)
        running = active.setdefault(slug, set())
        if event.state is AlertState.ACTIVE:
            if not running:
                episodes[slug] = episodes.get(slug, 0) + 1
                span_since[slug] = stamp
            running.add((event.area_id, event.kind))
        elif is_clear(event.state):
            running.discard((event.area_id, event.kind))
            if not running and slug in episodes:
                last_close[slug] = event.ts_source
                opened = span_since.pop(slug, None)
                if opened is not None:
                    seconds[slug] = seconds.get(slug, 0.0) + max(
                        0.0, (stamp - opened).total_seconds()
                    )
    # Stretches still running when the picture was composed are counted up to
    # `as_of` and said to be open. Ending them silently at the last event
    # would report a quiet tail that nobody observed.
    for slug, opened in span_since.items():
        seconds[slug] = seconds.get(slug, 0.0) + max(
            0.0, (as_of - opened).total_seconds()
        )
    return tuple(
        RecentOblast(
            slug=slug,
            alerts_count=count,
            last_alert_ended_at=last_close.get(slug),
            alert_seconds=int(seconds.get(slug, 0.0)),
            open_at_as_of=slug in span_since,
        )
        for slug, count in sorted(episodes.items())
    )


def trailing_areas(
    events: Iterable[ThreatEvent],
    *,
    as_of: datetime,
    days: int = DEFAULT_TRAILING_DAYS,
    table: AreaTable,
) -> tuple[RecentArea, ...]:
    """Alert episodes per **area** over the trailing window, nearest first.

    The same episode rule as `trailing_counts`, applied one level down, and
    the same three invariants restated here rather than inherited, because a
    fold that reasons about a different key does not get them for free:

    **UNKNOWN does not close an episode.** A source that stops naming a raion
    has not said its alert ended. Only an affirmative all-clear closes one, so
    an episode left open by a feed outage stays open and the count errs in the
    direction that does not understate.

    **An episode that overlaps the window counts, wherever it opened (F85).**
    The whole log is replayed: events before the cutoff move the running state
    without counting, an area already active as the window opens is counted
    once as it crosses, and only an episode both opened and affirmatively
    closed before the window falls outside. A cutoff applied as a filter on
    events would age out the opening transition of a long alert and render the
    most persistently attacked area as the quietest.

    **An area the register cannot resolve is dropped, never folded.** It has
    no code to key on, no distance and no oblast, and attaching it to a
    neighbour would put a wrong number somewhere plausible. Those areas are
    already visible as `unresolved_areas` beside this.

    Ordered by the lower bound of the interval, nearest first, with unknown
    distances last: the same key `western_active` uses, for the same reason.
    An area with no distance must not sort as though it were near.

    **The open state is a set of kinds per area, not a flag (F138).** The same
    repair as `trailing_counts`, restated in code rather than inherited: an
    area's episode closes when its *last* live kind is affirmatively cleared,
    never when any one of them is.
    """
    cutoff = as_of - timedelta(days=days)
    open_since: dict[str, datetime] = {}
    kinds_open: dict[str, set[ThreatKind]] = {}
    episodes: dict[str, int] = {}
    last_active: dict[str, datetime] = {}
    last_close: dict[str, datetime] = {}
    #: The clipped twin of `open_since`. `open_since` keeps the real opening
    #: time because `last_active` is seeded from it and reporting the cutoff
    #: there would invent a transition that never happened; a duration inside
    #: a seven-day window may not exceed seven days, so it needs the other
    #: one. Two clocks, two purposes, named rather than shared.
    span_since: dict[str, datetime] = {}
    seconds: dict[str, float] = {}
    ordered = sorted(events, key=lambda e: (e.ts_source, e.area_id))
    edge = next(
        (i for i, e in enumerate(ordered) if e.ts_source >= cutoff), len(ordered)
    )
    for event in ordered[:edge]:
        if table.by_code(event.area_id) is None:
            continue
        if event.state is AlertState.ACTIVE:
            if not kinds_open.get(event.area_id):
                open_since.setdefault(event.area_id, event.ts_source)
            kinds_open.setdefault(event.area_id, set()).add(event.kind)
        elif is_clear(event.state):
            live = kinds_open.get(event.area_id)
            if live is not None:
                live.discard(event.kind)
                if not live:
                    open_since.pop(event.area_id, None)
    # Episodes already running as the window opens: counted here, once, so the
    # loop below cannot count them again (`open_since` is already populated).
    # `last_active` is seeded with the opening time, which predates the window
    # and is the honest answer: the area has been under alert since then, and
    # reporting the cutoff instead would invent a transition that never
    # happened.
    for code, since in open_since.items():
        episodes[code] = 1
        last_active[code] = since
        span_since[code] = cutoff
    for event in ordered[edge:]:
        if table.by_code(event.area_id) is None:
            continue
        stamp = min(event.ts_source, as_of)
        if event.state is AlertState.ACTIVE:
            if not kinds_open.get(event.area_id):
                episodes[event.area_id] = episodes.get(event.area_id, 0) + 1
                open_since[event.area_id] = event.ts_source
                span_since[event.area_id] = stamp
            kinds_open.setdefault(event.area_id, set()).add(event.kind)
            last_active[event.area_id] = event.ts_source
        elif is_clear(event.state):
            live = kinds_open.get(event.area_id)
            if live is not None:
                live.discard(event.kind)
            if not live and open_since.pop(event.area_id, None) is not None:
                last_close[event.area_id] = event.ts_source
                opened = span_since.pop(event.area_id, None)
                if opened is not None:
                    seconds[event.area_id] = seconds.get(event.area_id, 0.0) + max(
                        0.0, (stamp - opened).total_seconds()
                    )
    for code, opened in span_since.items():
        seconds[code] = seconds.get(code, 0.0) + max(
            0.0, (as_of - opened).total_seconds()
        )

    found: list[RecentArea] = []
    for code, count in episodes.items():
        area = table.by_code(code)
        if area is None:  # pragma: no cover - filtered in both loops above
            continue
        found.append(
            RecentArea(
                code=code,
                name=area.name,
                oblast_slug=oblast_slug(area.oblast) if area.oblast else "",
                oblast_name=area.oblast if area.oblast else "unknown",
                episodes=count,
                last_active_at=last_active[code],
                last_ended_at=last_close.get(code),
                border_lower_km=area.border_lower_km,
                border_upper_km=area.border_upper_km,
                is_western=area.is_western,
                alert_seconds=int(seconds.get(code, 0.0)),
                open_at_as_of=code in span_since,
            )
        )

    def key(entry: RecentArea) -> tuple[int, float, float, str]:
        if entry.border_lower_km is None:
            return (1, 0.0, 0.0, entry.code)
        return (0, entry.border_lower_km, entry.border_upper_km or 0.0, entry.code)

    return tuple(sorted(found, key=key))


def compose(
    events: Iterable[ThreatEvent],
    *,
    as_of: datetime | None = None,
    table: AreaTable | None = None,
    valid_for_s: int = DEFAULT_VALID_FOR_S,
    trailing_days: int = DEFAULT_TRAILING_DAYS,
    history_days: Sequence[int] = HISTORY_WINDOWS_DAYS,
) -> Report:
    """Fold an event log into the current picture.

    **`history_days` must contain `trailing_days` (D-048).** The week that
    `state.json` shades by and the week `history.json` lists are the same
    fold or they are two weeks, and the check is here rather than in the
    CLI because the CLI is one of several callers.

    **The fold works in `(area_id, kind)`, not in `area_id` (D-044).** Last
    write per *key* wins, ordered by source time, because a later observation
    about one threat kind supersedes an earlier one about that same kind and
    says nothing at all about the others. Ties broken by ingest time so that a
    re-read of the same moment does not depend on iteration order.

    An area is then not clear when **any** of its kinds is not clear, tested
    with `is_clear` and never with `!= ACTIVE`. Folding on `area_id` alone -
    which is what this did until 0.48.0.0 - made the clear of one threat kind
    erase the area: an artillery alarm running since April went calm the moment
    a concurrent air alert ended, and fifteen areas rendered calm during
    measured alarms on 2026-08-30 (F133).

    Which surviving kind *names* the area is `state_precedence`, ties to the
    later stamp. That is a headline, not a verdict: it decides the word beside
    the area, never whether the area appears at all.

    Cleared areas are dropped from the list and unknown ones are kept. That
    asymmetry is the contract, and it is the reason this is a fold rather
    than a filter: an area whose every kind went ACTIVE and then CLEAR must
    disappear, while an area that went ACTIVE and then UNKNOWN must remain and
    say so.
    """
    table = table if table is not None else AreaTable.from_csv()
    windows = tuple(sorted(set(history_days)))
    if trailing_days not in windows:
        raise ValueError(
            f"history_days {tuple(history_days)} must contain trailing_days "
            f"{trailing_days}: the window state.json shades by has to be one "
            "of the windows history.json lists, or the two are two weeks"
        )
    if any(days < 1 for days in windows):
        raise ValueError(f"history_days must be positive: {tuple(history_days)}")
    # Materialised once: the fold below and the trailing window both need the
    # whole log, and a generator consumed twice would silently give the second
    # reader nothing, which here would be an empty seven-day layer that looks
    # like a quiet week.
    replayed = list(events)
    latest: dict[tuple[str, ThreatKind], ThreatEvent] = {}
    for event in replayed:
        key = (event.area_id, event.kind)
        current = latest.get(key)
        if current is None or (event.ts_source, event.ts_ingest) >= (
            current.ts_source, current.ts_ingest
        ):
            latest[key] = event

    by_area: dict[str, list[ThreatEvent]] = {}
    for (area_id, _kind), event in latest.items():
        by_area.setdefault(area_id, []).append(event)

    pictures: list[AreaPicture] = []
    unresolved: list[str] = []
    for area_id in sorted(by_area):
        live = [event for event in by_area[area_id] if not is_clear(event.state)]
        if not live:
            continue
        headline = max(
            live,
            key=lambda event: (
                state_precedence(event.state),
                event.ts_source,
                event.ts_ingest,
            ),
        )
        area = table.by_code(area_id)
        if area is None:
            unresolved.append(area_id)
        pictures.append(
            AreaPicture(
                area_id=area_id,
                state=headline.state,
                kind=headline.kind,
                since=headline.ts_source,
                area=area,
                kinds=tuple(
                    sorted(
                        (
                            KindStanding(
                                kind=event.kind,
                                state=event.state,
                                since=event.ts_source,
                            )
                            for event in live
                        ),
                        key=lambda standing: (
                            -state_precedence(standing.state),
                            standing.kind.value,
                        ),
                    )
                ),
            )
        )
    moment = as_of if as_of is not None else datetime.now(UTC)
    # F120. Two quantities, deliberately not one. `raw_newest` is what the
    # source said and is reported as such; `newest` is the newest stamp this
    # pipeline may treat as evidence that it is not blind, which excludes
    # anything further ahead of us than the tolerance. Folding them - which is
    # what a single `max()` did until this release - lets one row stamped in
    # the future hold `feed_state` at `ok` while nothing arrives, because a
    # negative age passes `age > valid_for_s` forever.
    #
    # A store whose every row is past the horizon has no datable observation
    # at all, and the answer is `blind`: taking the newest of them would be
    # the same defect with a smaller number on it.
    stamps = [event.ts_source for event in latest.values()]
    raw_newest = max(stamps, default=None)
    horizon = moment + timedelta(seconds=SKEW_TOLERANCE_S)
    newest = max((stamp for stamp in stamps if stamp <= horizon), default=None)
    skew = (
        max(0.0, (raw_newest - moment).total_seconds())
        if raw_newest is not None
        else 0.0
    )
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
    # D-048. One fold per window per granularity, all over the same replay
    # at the same moment. The two blocks `state.json` and `feed.json` carry
    # are the entries of the `trailing_days` window, taken from this tuple
    # rather than computed beside it, so the week a reader sees on the map
    # and the week they open in the history are one object. The oldest stamp
    # is taken raw: a window's start is a question about the past of the log,
    # not about its freshness, so the skew filter above does not apply.
    oldest = min((event.ts_source for event in replayed), default=None)
    history = tuple(
        TrailingWindow(
            days=days,
            start=moment - timedelta(days=days),
            oblasts=trailing_counts(
                replayed, as_of=moment, days=days, table=table
            ),
            # Same log, same moment, same window as the block beside it. Two
            # compositions would be two weeks, and a page whose headline
            # named an area its own history block did not list would have no
            # way to say which half to believe.
            areas=trailing_areas(
                replayed, as_of=moment, days=days, table=table
            ),
            oldest_observation=oldest,
        )
        for days in windows
    )
    week = next(window for window in history if window.days == trailing_days)
    return Report(
        as_of=moment,
        newest_observation=newest,
        valid_for_s=valid_for_s,
        areas=tuple(pictures),
        unresolved_areas=tuple(unresolved),
        recent=week.oblasts,
        recent_areas=week.areas,
        trailing_days=trailing_days,
        history=history,
        stream=stream,
        feed=feed,
        # Counted off the day-long window rather than recomputed, so the two
        # cannot drift. The cap can bind here in principle; when it does,
        # `feed.truncated` says so in the same payload.
        counts_24h=(west, len(feed.events) - west),
        newest_source_stamp=raw_newest,
        clock_skew_s=skew,
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
    # F120. The raw stamp, falling back to the freshness basis for a `Report`
    # constructed directly by a caller that predates the field. These are the
    # same value on every healthy cycle and differ only when the two clocks do.
    newest = (
        report.newest_source_stamp
        if report.newest_source_stamp is not None
        else report.newest_observation
    )
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
        # F120. How far ahead of us the source's newest stamp sits, in seconds,
        # floored at zero and always present. A consumer needs it to explain
        # the one case where `source_last_message_at` is later than
        # `generated_at`, which without this field looks like a producer bug
        # rather than a clock disagreement. Above `SKEW_TOLERANCE_S` the stamp
        # stops counting as evidence of freshness and `state` says `blind`,
        # so a large value here beside a `blind` state is the whole diagnosis
        # in two fields.
        "clock_skew_s": report.clock_skew_s,
        "window_days": report.trailing_days,
        # One serialisation for this block and for the `oblasts` block of
        # every window in `history.json` (D-048); the field comments live on
        # `_oblast_item`.
        "recent_7d": [_oblast_item(entry) for entry in report.recent],
        # 0.33.0.0. The nearest area that was under alert in the window, at
        # **raion** granularity, so the weekly sentence and the live sentence
        # measure the same thing and a reader comparing them is comparing
        # like with like. `recent_7d` above deliberately carries no distance:
        # an oblast-level interval takes its lower bound from one raion and
        # its upper from another, describes no single place, and would carry
        # the same field names as the per-area interval that describes
        # exactly one. Two quantities under one name, one line apart.
        #
        # `null` is unknown and never "nothing near". The full block this
        # reduces travels in `feed.json`; see `RecentArea`.
        "nearest_7d": (
            report.nearest_recent.as_item()
            if report.nearest_recent is not None
            else None
        ),
        "areas": [
            {
                "katottg": picture.area.code if picture.area is not None else "",
                "area_id": picture.area_id,
                "oblast": picture.oblast_slug,
                "oblast_name": picture.oblast,
                "alert": picture.state.value,
                "kind": picture.kind.value,
                "since": picture.since.isoformat(timespec="seconds"),
                # D-044. Every kind not affirmatively cleared. `alert`, `kind`
                # and `since` above stay exactly what they were, so a consumer
                # reading v3 today reads the same fields tomorrow; this block
                # is what a consumer needs to stop treating one headline as the
                # whole of an area's standing. Never empty for a published
                # area: an area with no live kind is not published at all.
                "kinds": [standing.as_item() for standing in picture.kinds],
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
        # 0.33.0.0. The trailing window at raion granularity, nearest first.
        # Here rather than in `state.json` because it is measured at 10.2 KiB
        # for the west and 35.5 KiB for every area the map knows, against a
        # `state.json` of 13,150 bytes polled every thirty seconds
        # [measured, 2026-08-19]. This file is fetched when a reader opens the
        # panel, which is where a week of history belongs.
        #
        # Always present, empty or not, for the same reason the event block is.
        "window_days": report.trailing_days,
        "recent_7d_areas": [entry.as_item() for entry in report.recent_areas],
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


def to_history(report: Report) -> dict[str, object]:
    """The `history.json` payload: every trailing window, on demand (D-048).

    A third file rather than more blocks in `feed.json`, on the same cost
    argument that made `feed.json` a second file rather than a longer window
    in the first: a reader who opens the day panel pays for the day, and a
    reader who opens the quarter pays for the quarter. `recent_7d_areas`
    stays in `feed.json` for the consumer that reads it there; it is the
    same tuple as the seven-day entry here, and retiring the copy is a
    schema step this release does not take.

    Always every window, present and labelled, whether or not the store
    reaches its start: an absent quarter would be indistinguishable from a
    quiet one.
    """
    return {
        "v": SCHEMA_VERSION,
        "generated_at": report.as_of.isoformat(timespec="seconds"),
        "windows": [window.as_block() for window in report.history],
    }


def write_history(report: Report, path: Path) -> Path:
    """Write `history.json` atomically, every cycle, changed or not.

    Same guarantees as the other two files and for the same reasons. Every
    cycle rather than on change, because the quarter changes every cycle
    anyway: its start moves with the clock, and a file that is only rewritten
    on a new event would carry a `window_start` that stopped moving.
    """
    return _write_json(to_history(report), path, prefix=".history-")


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
    history_path: Path | None = None,
    history_days: Sequence[int] = HISTORY_WINDOWS_DAYS,
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
                events, as_of=clock(), table=table, valid_for_s=valid_for_s,
                history_days=history_days,
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
                # The third file rides the same cycle for the same reason
                # (D-048): a quarter frozen beside a moving week is the
                # same defect one file over.
                if history_path is not None:
                    write_history(report, history_path)
            except OSError as failure:
                reason = f"write failed: {failure}"
                break
            written += 1
            # T23. One line per cycle, and it is written here rather than
            # beside the interval draw for a reason the test that found this
            # states plainly: until 0.32.7.0 the only `log.line` in this loop
            # was `publish.interval`, emitted before sleeping. A cycle that did
            # not sleep - the last one of every run, and every run that ended
            # on a write failure - left no trace at all, so the record of the
            # loop was a record of its pauses. The sink was attached to the
            # sleep instead of to the work.
            #
            # `skipped` is deliberately absent rather than zero: this loop reads
            # a store, it does not poll, so it has no window to have missed and
            # a zero here would be a measurement nobody took.
            if log is not None:
                log.line(
                    "publish", "publish.cycle", cycle=cycle_id,
                    feed_state=report.feed_state.value,
                    as_of=report.as_of.isoformat(timespec="seconds"),
                    western_active=len(report.western_active),
                    events=len(report.areas),
                )
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
