"""Which declared level stands beside an open alarm, at a moment (D-063).

D-050 recorded the level as its own stream and kept it off the contract until
the rows had been read. This module is the rule a reader is shown, and the one
place it lives: `compose` asks it for the present, `timeline.area_layer` for
every instant of the week, and `report.area_picture` hands it every ACTIVE
kind and nothing else.

**The rule, in one sentence.** A kind that is ACTIVE at a moment wears the
newest declaration on its `(area_id, kind)` key that the source stamped at or
before that moment and whose newest listing is no older than the read in
effect at that moment; every other kind, and an ACTIVE kind with no such
declaration, wears none. Put the other way round: a declaration stands from
its own stamp until a read asked after its newest listing has its page in
hand.

**Why what the read listed, and not what the store holds.** The adapter hands
over, on every poll, the declaration the API lists as current for every open
key: the newest `createdAt` among the level records of every alert on it.
`alert_levels` keys a declaration on its word and its moment, so the same
declaration seen on a hundred polls is one row, and until 0.60.0.0 that row
could not say whether the latest poll still listed it. Three things went
wrong from that, each measured or reproduced in the review of 0.60.0.0: a
new alarm on a key wore the colour its predecessor ended on; an alarm that
outlived a spurious all-clear, re-asserted by observation (D-044), lost its
level for the rest of its life to a bound drawn at the re-assertion; and on a
key where two alerts of one kind stand together (an `AIR` and an
`URBAN_FIGHTS` alert both fold to `UNKNOWN`), the level of the one that ended
stayed on the map, because the API's current level falls back to the older
alert's record and that record is already a row. `last_read` (the newest read
that listed the declaration) says what the source still lists, so the rule
needs no bound drawn from the alert rows at all.

**Three clocks.** A declaration begins at its own `createdAt`, the clock the
alert rows use too: the alarm itself is dated by the source and drawn from
that moment, including rows that reached the store after an outage. Its end
is not in the payload: the API stops listing it, so the end is the first read
that did not list it, from the moment that read had its page in hand
(`started_at` plus `elapsed_s`, `in_hand`) rather than the moment it asked.
The all-clear a read derives is stamped between the two, when the page
arrived, so a read that spoke from its `started_at` would end the level of
every alarm it ended a second or two before the alarm itself, and the week
would carry, at the end of every levelled alarm, a sliver of an open alarm
the source "lists no level" for (F198). Before the first read that recorded
what it listed took effect, nothing says which declaration stood, and a
moment there is unrecorded, never unlevelled.

**One replay, one horizon.** The alert rows come from a replay and the
declarations from queries made after it, and `collect-api` may write in
between. It writes the declarations, then the rows, then the read
(`mavo.cli`), so a read on record has everything it wrote on record too. A
reader therefore takes the newest read on record *before* its replay
(`read_horizon`) and asks about no read after it: a later read's all-clears
may be missing from the replay, and the alarm such a read ended would be drawn
open beside a listing that no longer names it, without its level, for a cycle
(F198). The declarations are queried after the replay, so every alarm the
replay holds finds its own: a read writes its listing before its rows.

**What this rule cannot see.** `last_read` holds the newest listing, not every
listing: a declaration listed, then not listed, then listed again while its
alarm stayed open reads as listed in between. That needs one declaration to
leave and come back with no newer one in between, which a key whose alerts
only gain records does not do. An alarm that ends and another that begins on
the same key between two polls leaves no alert row (the key never left the
list), and its first declaration is its own from its own stamp.

**The word is verbatim and the vocabulary open.** `Red` and `Yellow` are the
two words the API had used when this was written (`docs/DEPLOYMENT.md`, the
first thirty rows, 2026-09-09). A word outside them is published as received
and ranks above both when an area's kinds disagree, so a new word reaches the
map's loudest slot instead of hiding behind a known colour; the consumer
renders it as an unrecognised level, never as the nearest colour it knows.
"""

from __future__ import annotations

import bisect
from collections.abc import Iterable, Mapping
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Protocol

from mavo.schema import ThreatKind

if TYPE_CHECKING:
    from mavo.store import EventStore

#: The feed whose reads decide presence: the API, which is the only writer of
#: `alert_levels`. Spelled here rather than imported from `mavo.cli`, which
#: imports this module.
LEVEL_FEED = "ukrainealarm"

#: The words the API has used, quietest first, in the order Ukraine's
#: resolution of 2026-09-04 gives them (red above yellow) `[reported; the
#: consumer's ROADMAP S7 cites the resolution]`. It decides only which of an
#: area's kinds names the area's level, never what a word means.
KNOWN_WORDS: tuple[str, ...] = ("Yellow", "Red")

#: Rank of a word no release has seen: above every known word, see the module
#: docstring.
UNRECOGNISED_RANK = len(KNOWN_WORDS) + 1

Key = tuple[str, ThreatKind]


def word_rank(word: str) -> int:
    """1 for the quietest known word, `UNRECOGNISED_RANK` for any other."""
    try:
        return KNOWN_WORDS.index(word) + 1
    except ValueError:
        return UNRECOGNISED_RANK


@dataclass(frozen=True, slots=True)
class Listed:
    """One declaration and the newest read that listed it."""

    area_id: str
    kind: ThreatKind
    word: str
    level_at: datetime
    last_read: datetime


def in_hand(started: datetime, elapsed_s: float | None) -> datetime:
    """When a read had its page: `started_at` plus `elapsed_s`, none if unmeasured."""
    return started + timedelta(seconds=max(elapsed_s or 0.0, 0.0))


@dataclass(frozen=True, slots=True)
class Read:
    """One successful API read, as the rule uses it.

    `started` names the read: it is `feed_attempts.started_at`, and the stamp
    `alert_levels.first_read` and `last_read` carry. `in_hand` is when the
    collector had the page (the module docstring, "Three clocks").
    """

    started: datetime
    in_hand: datetime


@dataclass(frozen=True, slots=True)
class Horizon:
    """The newest API read on record when a replay began (D-063).

    `read` is None when no read was on record then. Every read a picture
    drawn beside that replay may use is at or before `read`.
    """

    read: datetime | None


@dataclass(frozen=True, slots=True)
class LevelIndex:
    """The declarations a set of moments can be drawn from, and the reads.

    **The read in effect at a moment** is the newest by `started` among the
    reads whose page was in hand by then: a read's listing is what the
    source said when it was asked, and a read asked later says something
    newer whichever page arrived first. As the moment advances it only moves
    forward.

    `reads` holds, oldest first, the read in effect at the earliest moment
    the index is asked about and every read started after it up to the
    latest, none after the horizon. `first_listing` is the stamp of the first
    read that recorded what it listed; `recorded_since` is when the presence
    record opened, published so a consumer can say from when it runs. Made
    by `build`, which derives the two sorted views the searches use.
    """

    listed: Mapping[Key, tuple[Listed, ...]]
    reads: tuple[Read, ...]
    first_listing: datetime | None
    recorded_since: datetime | None
    #: `started` of every read, ascending, and beside each the soonest
    #: `in_hand` of it and every read started after it.
    starts: tuple[datetime, ...]
    soonest: tuple[datetime, ...]
    #: `in_hand` of every read, ascending, and beside each the newest
    #: `started` among the reads in hand by then.
    hands: tuple[datetime, ...]
    newest: tuple[datetime, ...]

    @classmethod
    def build(cls, listed: Iterable[Listed],
              reads: Iterable[tuple[datetime, float | None]], *,
              first_listing: datetime | None,
              recorded_since: datetime | None) -> LevelIndex:
        """`reads` as `(started_at, elapsed_s)`; a read given twice counts once."""
        grouped: dict[Key, list[Listed]] = {}
        for item in listed:
            grouped.setdefault((item.area_id, item.kind), []).append(item)
        held: dict[datetime, Read] = {}
        for started, elapsed in reads:
            held[started] = Read(started, in_hand(started, elapsed))
        ordered = tuple(held[started] for started in sorted(held))
        soonest: list[datetime] = []
        for read in reversed(ordered):
            soonest.append(min(read.in_hand, soonest[-1]) if soonest else read.in_hand)
        by_hand = sorted(ordered, key=lambda read: (read.in_hand, read.started))
        newest: list[datetime] = []
        for read in by_hand:
            newest.append(max(read.started, newest[-1]) if newest else read.started)
        return cls(
            listed={key: tuple(sorted(items, key=lambda d: (d.level_at, d.word)))
                    for key, items in grouped.items()},
            reads=ordered,
            first_listing=first_listing,
            recorded_since=recorded_since,
            starts=tuple(read.started for read in ordered),
            soonest=tuple(reversed(soonest)),
            hands=tuple(read.in_hand for read in by_hand),
            newest=tuple(newest),
        )

    def read_at(self, at: datetime) -> datetime | None:
        """The `started` of the read in effect at `at`, or None."""
        index = bisect.bisect_right(self.hands, at) - 1
        return self.newest[index] if index >= 0 else None

    def overtaken(self, stamp: datetime) -> datetime | None:
        """When a read started after `stamp` first had its page, or None."""
        index = bisect.bisect_right(self.starts, stamp)
        return self.soonest[index] if index < len(self.starts) else None

    def opening(self) -> datetime | None:
        """When a read that recorded its listing first took effect, here."""
        if self.first_listing is None:
            return None
        index = bisect.bisect_left(self.starts, self.first_listing)
        return self.soonest[index] if index < len(self.starts) else None

    def standing(self, key: Key, at: datetime) -> Listed | None:
        """The declaration the module docstring's rule names at `at`, or None.

        None too while the read in effect is older than the presence record:
        there the rule cannot be asked, and `to_contract` says so with
        `recorded_since` rather than a level.
        """
        read = self.read_at(at)
        if read is None or self.first_listing is None or read < self.first_listing:
            return None
        found: Listed | None = None
        for item in self.listed.get(key, ()):
            if item.level_at <= at and item.last_read >= read:
                found = item  # sorted by (level_at, word): the last is the newest
        return found

    def instants(self, start: datetime, end: datetime) -> dict[datetime, set[str]]:
        """Every moment in `(start, end]` at which `standing` can change, by area.

        A declaration starts at its own stamp, or when the record opens if it
        is older, and stops when a read started after its newest listing
        first takes effect. The ACTIVE state that gates it is the alert
        rows', whose moments are the area layer's own.
        """
        found: dict[datetime, set[str]] = {}

        def add(moment: datetime | None, area_id: str) -> None:
            if moment is not None and start < moment <= end:
                found.setdefault(moment, set()).add(area_id)

        opening = self.opening()
        if opening is None:
            return found
        for (area_id, _kind), items in self.listed.items():
            for item in items:
                add(max(item.level_at, opening), area_id)
                add(self.overtaken(item.last_read), area_id)
        return found


EMPTY = LevelIndex.build((), (), first_listing=None, recorded_since=None)


def read_horizon(store: EventStore) -> Horizon:
    """The newest API read on record now. Taken *before* a replay (module docstring)."""
    stamp = store.newest_read_at(LEVEL_FEED)
    return Horizon(None if stamp is None else datetime.fromisoformat(stamp))


def _reads(store: EventStore, start: datetime, end: datetime,
           cap: datetime) -> list[tuple[datetime, float | None]]:
    """Every read started by `end`, none after `cap`, back to the one in effect at `start`.

    Read newest first, so the walk stops at the first read started by
    `start` whose page was in hand by then: by the rule in `LevelIndex` it
    is the read in effect there, and no older one is ever in effect later.
    """
    found: list[tuple[datetime, float | None]] = []
    with closing(store.iter_reads_back(LEVEL_FEED, min(end, cap))) as rows:
        for started, elapsed in rows:
            found.append((started, elapsed))
            if started <= start and in_hand(started, elapsed) <= start:
                break
    return found


def _recorded_since(store: EventStore, first: datetime, cap: datetime) -> datetime | None:
    """When the presence record opened, or None if not by the horizon.

    The soonest page in hand among the reads started from `first`, none after
    `cap`: the moment the read in effect is first one that recorded its
    listing. Only a read started before the soonest page found so far can
    still beat it, so the walk is short. The read `first` names may be missing
    from the log (its `record_read` failed after its listing was stored); the
    record then opens with a logged one.
    """
    soonest: datetime | None = None
    with closing(store.iter_reads_from(LEVEL_FEED, first)) as rows:
        for started, elapsed in rows:
            if started > cap or (soonest is not None and started >= soonest):
                break
            moment = in_hand(started, elapsed)
            soonest = moment if soonest is None else min(soonest, moment)
    return soonest


def _index(store: EventStore, horizon: Horizon, start: datetime, end: datetime,
           until: datetime | None) -> LevelIndex:
    cap = horizon.read
    if cap is None:
        return EMPTY
    first = store.levels_listed_since()
    if first is not None and first > cap:
        first = None
    since = None if first is None else _recorded_since(store, first, cap)
    reads = _reads(store, start, end, cap)
    rows = store.listed_levels(min(read for read, _ in reads), until=until) if reads else []
    return LevelIndex.build(
        (Listed(area_id, kind, word, level_at, last_read)
         for area_id, kind, word, level_at, last_read in rows),
        reads, first_listing=first, recorded_since=since,
    )


def live_index(store: EventStore, horizon: Horizon) -> LevelIndex:
    """What a report cycle asks: the declarations the horizon's read listed.

    The cycle's moment comes after the horizon was recorded, and a read is
    recorded after its page arrived, so the horizon's read is in effect then.
    """
    if horizon.read is None:
        return EMPTY
    return _index(store, horizon, horizon.read, horizon.read, None)


def index_at(store: EventStore, moment: datetime, horizon: Horizon) -> LevelIndex:
    """What a picture at one past moment is drawn from (`timeline --at`)."""
    return _index(store, horizon, moment, moment, moment)


def window_index(store: EventStore, start: datetime, end: datetime,
                 horizon: Horizon) -> LevelIndex:
    """What the week is drawn from: every read in it and the one in effect before it."""
    return _index(store, horizon, start, end, end)


class LevelReader(Protocol):
    """What a report cycle reads the level stream through (`report.publish`).

    Two steps because the order is the rule: `horizon` before the replay,
    `live` after it (the module docstring, "One replay, one horizon").
    """

    def horizon(self) -> Horizon: ...

    def live(self, horizon: Horizon) -> LevelIndex: ...


@dataclass(frozen=True, slots=True)
class StoreLevels:
    """The reader over one store, `read_horizon` and `live_index`."""

    store: EventStore

    def horizon(self) -> Horizon:
        return read_horizon(self.store)

    def live(self, horizon: Horizon) -> LevelIndex:
        return live_index(self.store, horizon)
