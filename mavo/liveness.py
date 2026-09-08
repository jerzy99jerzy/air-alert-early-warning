"""Which pipes are delivering, decided from `feed_attempts` and nothing else.

**The problem this exists for.** `report.compose` takes the newest observation
over one pool keyed `(area_id, kind)` with no source dimension, so as long as
*any* source is producing, the loss of another is invisible. On 2026-09-07 the
API stopped at 08:24 and stayed stopped for 28 h 30 min; on 2026-09-07 06:09
the channel stopped and was still stopped 33 h later while the page said
nothing, because the API was delivering. Two outages, neither announced.

**Why `feed_attempts` and not `events`.** A source that is alive and has
nothing to report produces no events, so an event-derived health signal calls a
healthy quiet feed dead. Measured, in the window 2026-08-31 to 2026-09-07:
both feeds went silent together for 4 958 s and again for 4 922 s on the
evening of 2026-09-06, at the same minute, because they are two delivery paths
of one Ukrainian system and the sky was quiet. An hour-long observation-age
threshold would have claimed an outage twice in nine days with both pipes at
full health. `feed_attempts` carries one row per poll whatever happened
(`store.py`), so absence of data is a fact rather than an inference, and over
the same window it produced 1 287 reads on the API and 7 852 on the channel
with exactly one gap, which was an operator stopping a timer.

**What this module refuses to do.** It will not guess a cadence. The timer
interval is configuration, it lives in the unit file, and inferring it from the
data would calibrate the gap detector on the gaps it is looking for - the same
refusal `mavo attempts` already makes and for the same reason. A feed whose
cadence the caller did not declare gets no state.

It also never decides a state from event stamps. `last_event_*` below is
reported beside the state and never inside it.
"""


from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from mavo.attempts import GAP_CADENCES
from mavo.store import EventStore


#: The name in `feed_attempts` is not the name in `events.source_id`, and the
#: two spaces have been confused once already in this project. `channel` polls
#: `t.me/s/air_alert_ua` and writes rows stamped `telegram`; the API polls and
#: writes rows stamped `ukrainealarm`. The mapping lives here, once, rather
#: than in every caller that needs to join a pipe to the rows it produced.
#:
#: `role` is D-040's vocabulary made executable. `docs/ARCHITECTURE.md` has
#: called the API the primary source and the channel the watchman since the
#: switchover; until this module the distinction lived only in prose, which is
#: why a reader-facing rule could not use it. A page cannot see when no
#: **primary** feed is delivering; a watchman going dark is an operator's
#: problem and not a reason to tell a reader the instrument is blind.
@dataclass(frozen=True, slots=True)
class FeedSpec:
    """One pipe: its name in the table, its name on the rows, its standing."""

    feed: str
    source_id: str
    role: str
    #: The timer interval in seconds, from the unit file. Declared by the
    #: caller, never measured from the table it is used to judge.
    cadence_s: float

    @property
    def silence_is_an_outage_s(self) -> float:
        """How long without a successful read before this pipe is not delivering.

        One cadence is the ordinary spacing between polls and cannot be an
        outage; a threshold at exactly one cadence would report jitter as
        blindness on every timer that has any. Two is the same margin
        `mavo attempts` uses to call a stretch unobserved, and the constant is
        imported rather than restated so the two instruments cannot drift.
        """
        return self.cadence_s * GAP_CADENCES


#: Production, measured 2026-09-08 from `systemctl cat`. `mavo-collect-api.timer`
#: is `OnUnitActiveSec=120` and `mavo-collect.timer` is `OnUnitActiveSec=30`
#: after its own override. `docs/DEPLOYMENT.md` records 121 s for the API; that
#: was an observed interval, which is the configured 120 plus the run, and the
#: number that belongs here is the configured one.
#:
#: RSO is absent deliberately: there is no `mavo-rso` unit on the host, so the
#: feed exists in `cli.py` and has never been collected. A spec for it would
#: publish `unknown` for ever and read as an outage of something that was never
#: switched on.
PRODUCTION_FEEDS: tuple[FeedSpec, ...] = (
    FeedSpec(feed="ukrainealarm", source_id="ukrainealarm",
             role="primary", cadence_s=120.0),
    FeedSpec(feed="channel", source_id="telegram",
             role="watchman", cadence_s=30.0),
)


class PipeState(Enum):
    """What the collector for one feed is doing, in four distinguishable words.

    Named `PipeState` and not `FeedState` because `report.FeedState` already
    holds `ok`/`degraded`/`blind`, which describes the *picture*. This
    describes the *pipe*, and the whole defect this module repairs is that
    those two were folded into one.
    """

    #: A successful read inside the threshold. Says the pipe works. Says
    #: nothing about whether the publisher had anything to say.
    DELIVERING = "delivering"
    #: Polls are current and the far end is refusing them. Their fault or our
    #: credential; `refusal_status` says which.
    REFUSING = "refusing"
    #: No poll at all inside the threshold. The timer is not running. This is
    #: the state that covered 28 h 30 min on 2026-09-07 and the one no
    #: external observer could have caught, because nothing was being emitted.
    STALLED = "stalled"
    #: This feed has never left a row. Not zero, not dead: never seen.
    UNKNOWN = "unknown"


#: `HTTP Error 401: Unauthorized` and friends, as `transport` writes them into
#: `feed_attempts.detail`. Anchored on the literal the transport emits rather
#: than on a loose digit match, so a status inside a URL or a message cannot be
#: read as the status of the attempt.
_STATUS = re.compile(r"HTTP Error (\d{3})\b")


def refusal_class(status: int | None) -> str:
    """A coarse word for what kind of refusal this was.

    Reported, never decisive. The three classes take three different operator
    actions and collapsing them would put "their server is having a moment"
    and "we are banned" under one word. Measured on the production table over
    fourteen days: five consecutive 503, one 502, three 401, and **no 403 at
    any point** - the 403 with Cloudflare 1010 in the incident record was
    served to hand-made diagnostic requests, never to the collector.
    """
    if status is None:
        return "unreachable"
    if status in (401, 403):
        return "rejected"
    if 500 <= status < 600:
        return "upstream"
    if 400 <= status < 500:
        return "client"
    return "other"


@dataclass(frozen=True, slots=True)
class FeedLiveness:
    """One pipe's standing at one moment, plus the numbers behind it."""

    spec: FeedSpec
    as_of: datetime
    state: PipeState
    last_attempt_at: datetime | None
    last_read_at: datetime | None
    #: When a row attributable to this source was last **written by us**. This
    #: is `MAX(ts_ingest)`, not `MAX(ts_source)`, and the difference is not
    #: cosmetic: for the API `ts_source` is the alarm's own `began`, so a
    #: chronic artillery alarm running since April carries an April stamp and
    #: a batch recovered after an outage carries the stamps of alarms that
    #: started while we were blind. `ts_source` answers "when did this alarm
    #: begin"; only `ts_ingest` answers "when did we last hear from this pipe".
    last_event_ingest_at: datetime | None
    #: The newest `ts_source` on this source's rows, reported beside the one
    #: above because it is true and is a different claim.
    last_event_source_at: datetime | None
    #: HTTP status of the most recent refusal, when one can be read from
    #: `detail`. None when the newest refusal carried no status or there is
    #: no refusal on record.
    refusal_status: int | None = None

    @property
    def read_age_s(self) -> float | None:
        """Seconds since the last successful read, or None when there was none."""
        if self.last_read_at is None:
            return None
        return max(0.0, (self.as_of - self.last_read_at).total_seconds())

    @property
    def attempt_age_s(self) -> float | None:
        """Seconds since the last poll of any outcome, or None when there was none."""
        if self.last_attempt_at is None:
            return None
        return max(0.0, (self.as_of - self.last_attempt_at).total_seconds())

    @property
    def is_delivering(self) -> bool:
        return self.state is PipeState.DELIVERING

    def as_item(self) -> dict[str, object]:
        """This pipe as one entry of the contract's `sources` block.

        Every field is present on every entry, including the null ones. An
        absent key and a null read alike to a careless consumer, and the whole
        argument of this project is that unknown must not render as zero.
        """
        return {
            "feed": self.spec.feed,
            "source_id": self.spec.source_id,
            "role": self.spec.role,
            "state": self.state.value,
            "cadence_s": self.spec.cadence_s,
            "silence_is_an_outage_s": self.spec.silence_is_an_outage_s,
            "last_attempt_at": _iso(self.last_attempt_at),
            "last_read_at": _iso(self.last_read_at),
            "read_age_s": self.read_age_s,
            "attempt_age_s": self.attempt_age_s,
            "last_event_ingest_at": _iso(self.last_event_ingest_at),
            "last_event_source_at": _iso(self.last_event_source_at),
            "refusal_status": self.refusal_status,
            "refusal_class": (
                refusal_class(self.refusal_status)
                if self.state is PipeState.REFUSING
                else None
            ),
        }


def _iso(stamp: datetime | None) -> str | None:
    return None if stamp is None else stamp.isoformat(timespec="seconds")


def _parse(stamp: str | None) -> datetime | None:
    """Read a stored timestamp back, refusing one with no offset.

    The store normalises every timestamp to UTC on the way in, so a row
    without an offset was written by something that is not this package and
    must not be silently assumed to mean UTC.
    """
    if stamp is None:
        return None
    parsed = datetime.fromisoformat(stamp)
    if parsed.tzinfo is None:
        raise ValueError(
            f"{stamp!r} has no UTC offset; the store writes offsets and a row "
            "without one was written by something else"
        )
    return parsed.astimezone(UTC)


def measure_feed(
    store: EventStore,
    spec: FeedSpec,
    *,
    as_of: datetime,
    events: EventStamps | None = None,
) -> FeedLiveness:
    """One pipe's standing, from three indexed reads and no scan.

    **The decision, in this order.** No attempt on record is `unknown`, which
    is not `stalled`: a feed nobody has switched on has not failed. A
    successful read inside the threshold is `delivering`. Past that, the
    question is only *why* there is no fresh data, and the answer is whether
    anything was even tried: an attempt inside the threshold means the far end
    is saying no (`refusing`), and no attempt means nothing is asking
    (`stalled`).

    **`>` and not `>=`.** At exactly the threshold the weaker claim holds, the
    same direction F-S72 chose on the consumer for the same reason: the
    sentence that asserts less about the source is the one to keep at the edge.
    """
    last_attempt = _parse(store.newest_attempt_at(spec.feed))
    if last_attempt is None:
        return FeedLiveness(
            spec=spec, as_of=as_of, state=PipeState.UNKNOWN,
            last_attempt_at=None, last_read_at=None,
            last_event_ingest_at=None, last_event_source_at=None,
        )
    last_read = _parse(store.newest_read_at(spec.feed))
    ingest, source = (events or EventStamps()).for_source(spec.source_id)
    threshold = spec.silence_is_an_outage_s
    read_age = (
        None if last_read is None
        else max(0.0, (as_of - last_read).total_seconds())
    )
    attempt_age = max(0.0, (as_of - last_attempt).total_seconds())

    if read_age is not None and read_age <= threshold:
        state = PipeState.DELIVERING
        status = None
    elif attempt_age <= threshold:
        state = PipeState.REFUSING
        status = _newest_refusal_status(store, spec.feed)
    else:
        state = PipeState.STALLED
        status = None
    return FeedLiveness(
        spec=spec, as_of=as_of, state=state,
        last_attempt_at=last_attempt, last_read_at=last_read,
        last_event_ingest_at=ingest, last_event_source_at=source,
        refusal_status=status,
    )


def _newest_refusal_status(store: EventStore, feed: str) -> int | None:
    detail = store.newest_refusal_detail(feed)
    if detail is None:
        return None
    found = _STATUS.search(detail)
    return int(found.group(1)) if found else None


@dataclass(frozen=True, slots=True)
class EventStamps:
    """Newest ingest and source stamp per `source_id`, folded by the caller.

    Passed in rather than queried, because the one caller that needs it -
    `report.compose` - already holds every event in memory for the fold it is
    doing anyway, and a second pass over the log to recover two maxima per
    source would be a scan bought for nothing. An empty instance reports
    unknown for every source, which is what a caller that did not fold gets:
    not zero, not "no events", unknown.
    """

    by_ingest: dict[str, datetime] | None = None
    by_source: dict[str, datetime] | None = None

    def for_source(self, source_id: str) -> tuple[datetime | None, datetime | None]:
        return (
            (self.by_ingest or {}).get(source_id),
            (self.by_source or {}).get(source_id),
        )


def liveness(
    store: EventStore,
    specs: tuple[FeedSpec, ...] = PRODUCTION_FEEDS,
    *,
    as_of: datetime | None = None,
    events: EventStamps | None = None,
) -> tuple[FeedLiveness, ...]:
    """Every declared pipe's standing, in the order the specs were declared."""
    moment = as_of if as_of is not None else datetime.now(UTC)
    return tuple(
        measure_feed(store, spec, as_of=moment, events=events) for spec in specs
    )


def as_block(rows: tuple[FeedLiveness, ...], as_of: datetime) -> dict[str, object]:
    """The `sources` block of `state.json`.

    **Additive, and that is deliberate.** The consumer's validator checks for
    the fields it requires and never rejects one it did not expect
    (`contract.py`), so this block reaches a deployed site without a schema
    bump and without a coordinated release. The producer can go first.

    `primary_delivering` is the number a reader-facing rule should read.
    `delivering` counts every pipe and is the operator's number: on this
    deployment the watchman polls a frozen page perfectly and would hold a
    plain count at one throughout an outage of the only source that matters.
    """
    primary = [row for row in rows if row.spec.role == "primary"]
    return {
        "as_of": as_of.isoformat(timespec="seconds"),
        "feeds": [row.as_item() for row in rows],
        "delivering": sum(1 for row in rows if row.is_delivering),
        "known": len(rows),
        "primary_delivering": sum(1 for row in primary if row.is_delivering),
        "primary_known": len(primary),
    }
