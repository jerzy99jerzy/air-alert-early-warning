"""Normalized event schema and the source adapter boundary.

Everything above this module is blind to which feed produced an event. That is
what makes a later switch to a Polish channel a new implementation of
``ThreatSource`` rather than a rewrite.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum
from typing import Protocol, runtime_checkable


class Provenance(Enum):
    """Epistemic label carried by every load-bearing field.

    Ordered weakest-last: a composite inherits the weakest label of its inputs.
    """

    MEASURED = 0
    REPORTED = 1
    INFERENCE = 2
    SPECULATION = 3

    @classmethod
    def weakest(cls, labels: Iterable[Provenance]) -> Provenance:
        """Return the weakest label in ``labels``.

        An empty input is SPECULATION, not MEASURED: absence is never the
        flattering state.
        """
        materialized = list(labels)
        if not materialized:
            return cls.SPECULATION
        return max(materialized, key=lambda label: label.value)


class AlertState(Enum):
    """Alert status for one administrative area. Four states, not three.

    UNKNOWN is a distinct state and never resolves to CLEAR. A feed that goes
    silent has not told us the sky is empty.

    PARTIAL_CLEAR is the fourth, added in sprint 5 after real channel content
    showed a message that announces an all-clear and says in the same breath
    that the alert continues (F26). It is deliberately not folded into UNKNOWN:
    UNKNOWN means the source has told us nothing, PARTIAL_CLEAR means it has
    told us two things that do not agree. Collapsing them would lose the
    difference between silence and contradiction, and a contradiction is
    evidence while silence is not.
    """

    ACTIVE = "active"
    CLEAR = "clear"
    UNKNOWN = "unknown"
    PARTIAL_CLEAR = "partial_clear"


def is_clear(state: AlertState) -> bool:
    """True only for an affirmatively reported all-clear.

    Written as a function rather than ``state != ACTIVE`` at every call site
    because the negation is the defect: it silently folds UNKNOWN, and now
    PARTIAL_CLEAR, into CLEAR.
    """
    return state is AlertState.CLEAR


def is_actionable(state: AlertState) -> bool:
    """True when the state may contribute to a warning decision."""
    return state is AlertState.ACTIVE


#: How loudly each reading speaks, for choosing among concurrent kinds (D-044).
#: A table rather than an ordering on the enum, because ``AlertState`` has no
#: natural order: CLEAR is not "less" than ACTIVE, it is a different claim.
#: PARTIAL_CLEAR outranks UNKNOWN for the reason the enum's own docstring gives
#: one screen up - a contradiction is evidence and silence is not.
_STATE_PRECEDENCE = {
    AlertState.ACTIVE: 3,
    AlertState.PARTIAL_CLEAR: 2,
    AlertState.UNKNOWN: 1,
    AlertState.CLEAR: 0,
}


def state_precedence(state: AlertState) -> int:
    """Which of several concurrent readings an area is *named* by.

    Decides nothing about whether the area is clear. That is ``is_clear``
    applied to every kind the area carries, and one kind not clear is enough.
    This only picks which of the surviving kinds becomes the headline, so a
    reader sees the loudest live reading rather than the most recent one.
    """
    return _STATE_PRECEDENCE[state]


def _utc(ts: datetime) -> datetime:
    """UTC form for comparison. A naive stamp is read as UTC and never dated.

    The store refuses naive timestamps at the point of entry (``_stored_form``),
    so nothing that reaches here from a store carries one. Fixtures and direct
    constructions can, and a ``TypeError`` from comparing an aware stamp with a
    naive one would surface as an outage rather than as the modelling fault it
    is.
    """
    return ts if ts.tzinfo is not None else ts.replace(tzinfo=UTC)


def redate_reassertions(
    events: Iterable[ThreatEvent],
    newest_clears: Mapping[tuple[str, ThreatKind], datetime],
    observed_at: datetime,
) -> tuple[ThreatEvent, ...]:
    """Date a re-asserted alarm by the observation rather than by its source stamp.

    D-044 part 2. A snapshot API repeats the same ``lastUpdate`` for an alarm
    that never ended, so an ACTIVE re-emitted after a spurious clear is
    byte-identical to the row already stored and ``content_hash`` discards it.
    It also carries a stamp older than the clear that preceded it, so even were
    it stored the fold would still pick the clear and the area would render calm
    during an alarm. One repair answers both: an ACTIVE whose ``(area_id, kind)``
    already carries a stored CLEAR no older than the incoming stamp is dated by
    the moment it was observed.

    The source's own word is kept in ``raw_fields`` rather than discarded. This
    row is a claim about when we saw the alarm, not about when it started, and
    the two have to stay tellable apart by a later reader.

    **Deliberately not in an adapter.** The invariant is a property of the log
    and holds for every pipe: the channel path can emit an ACTIVE stamped from a
    message older than a ``reconcile`` closure and would reproduce the same
    defect by a second road. Pure - no store, no clock, ``observed_at`` passed
    rather than read - so the behaviour is a function of its arguments and the
    test needs neither a database nor a fixed clock.
    """
    redated: list[ThreatEvent] = []
    for event in events:
        cleared_at = newest_clears.get((event.area_id, event.kind))
        if (
            event.state is not AlertState.ACTIVE
            or cleared_at is None
            or _utc(event.ts_source) > _utc(cleared_at)
        ):
            redated.append(event)
            continue
        redated.append(
            replace(
                event,
                ts_source=observed_at,
                raw_fields={
                    **event.raw_fields,
                    "reported_at": _utc(event.ts_source).isoformat(),
                    "superseded_clear": _utc(cleared_at).isoformat(),
                },
            )
        )
    return tuple(redated)


def is_degraded(state: AlertState) -> bool:
    """True when the state must surface as degradation, never as an alarm.

    The third predicate. Until 0.6.0.0 the docstring above *claimed* a
    degradation path that no code implemented - a promise in prose, which is the
    claim-drift class the README lints exist to catch, living one file below
    them. Written by negation deliberately, and in the safe direction: a fifth
    state added tomorrow is degraded by default, so the new member is *loud*
    on the day it exists rather than silent. Negating toward CLEAR is the
    defect; negating toward "report this" is the guard.

    The consumer is the notification layer (docs/MOBILE.md): a degraded area is
    a "the system is blind here" message, which is a first-class output, because
    a warning channel that goes quiet when its feed dies has rebuilt
    unknown-resolves-to-clear one layer up.
    """
    return state not in (AlertState.ACTIVE, AlertState.CLEAR)


class ThreatKind(Enum):
    """Classified means of attack, driving which timing regime applies.

    ARTILLERY was added at 0.19.3.0 after F71 measured what the tables miss.
    The channel announces `Відбій загрози артобстрілу` and the parser rejected
    the whole message, because artillery had no member to resolve to: a means
    of attack the source names and the schema cannot hold is a message thrown
    away, not a message classified.

    It carries no timing regime and it is not meant to. `Regime` names MISSILE
    and DRONE explicitly and the rules compare with `is`, so an artillery
    declaration is reported and never reaches an alarm rule. That is correct
    rather than provisional: artillery is a front-line phenomenon at ranges
    that do not reach the Polish border, and giving it a regime would be
    inventing one for a threat this project cannot be warning anyone about.
    """

    MISSILE = "missile"
    DRONE = "drone"
    GLIDE_BOMB = "glide_bomb"
    ARTILLERY = "artillery"
    UNKNOWN = "unknown"


class KindState(Enum):
    """A threat-kind declaration is announced and later lifted (T16, F25).

    Its own lifecycle, separate from ``AlertState``. The channel declares
    "Загроза ударних БпЛА" for a hromada and later lifts it with "Відбій
    загрози", on messages that carry no alert state at all. Modelling this as an
    attribute of an alert, which is what the code did until 0.14.0.0, means the
    two can never meet: measured on the 20 real messages held as fixtures, 15
    carry an alert state, 4 carry a kind marker, and **none carry both**.
    """

    DECLARED = "declared"
    LIFTED = "lifted"


class AreaRole(Enum):
    """Why an area appears in the message that named it.

    Sprint 8, T37. An all-clear can carry a continuation list: the tag names the
    area that was cleared, and the list names areas where the alert is *still
    running*. Both are areas the source spoke about and both must reach the
    store, but reading them as one thing would announce an all-clear over a
    place the message called dangerous. The role is a field rather than a note
    in ``raw_fields`` because a consumer must be able to match on it.
    """

    SUBJECT = "subject"
    CONTINUATION = "continuation"


# Oblasts bordering Poland, and the second-order ring behind them.
#
# **These are oblast slugs, not area ids** (T38). Until 0.12.0.0 the rules below
# tested ``event.area_id`` against this set, and that comparison could only ever
# be false on a real event: ``classify`` emits a KATOTTG register code for a
# raion or hromada (``UA46060000000042587``) while these are coarse slugs, so
# every border predicate was silently unsatisfiable outside the fixture. Two
# vocabularies met at a set membership test and the answer was "no" forever.
#
# The split is now deliberate and typed: ``area_id`` identifies the reporting
# unit at whatever granularity the source names it, ``oblast`` is the coarse
# geography the rules reason about, and both live on the event.
BORDER_OBLASTS: frozenset[str] = frozenset({"volyn", "lviv", "zakarpattia"})
SECOND_RING_OBLASTS: frozenset[str] = frozenset({"rivne", "ternopil", "ivano-frankivsk"})


@dataclass(frozen=True, slots=True)
class KindEvent:
    """One declaration or lifting of a means of attack, for one area.

    A second stream beside the alert stream, with its own lifetime. The decision
    layer joins the two by area and time rather than reading the kind off the
    alert, because the source does not put them in the same message (T16).
    """

    area_id: str
    kind: ThreatKind
    state: KindState
    ts_source: datetime
    ts_ingest: datetime
    source_id: str
    oblast: str = ""
    raw_fields: dict[str, str] = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        """Identity: this kind entered this state for this area at this moment.

        Same construction as ``ThreatEvent.content_hash`` and for the same
        reason: a page re-read must not append the same declaration twice.
        """
        ts = self.ts_source
        stamp = (ts.astimezone(UTC) if ts.tzinfo is not None else ts).isoformat()
        payload = "|".join([self.area_id, self.kind.value, self.state.value, stamp, self.source_id])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ThreatEvent:
    """One observed state transition for one area, from one source.

    ``ts_source`` is when the source says it happened; ``ts_ingest`` is when we
    saw it. The difference is the feed latency that eats the warning budget, so
    it is stored rather than derived.
    """

    area_id: str
    state: AlertState
    ts_source: datetime
    ts_ingest: datetime
    source_id: str
    kind: ThreatKind = ThreatKind.UNKNOWN
    provenance: Provenance = Provenance.REPORTED
    raw_fields: dict[str, str] = field(default_factory=dict)
    # T38. The oblast this area sits in, as a canonical slug, or "" when the
    # source did not say and nothing could resolve it. Empty means unknown and
    # is never treated as a match: a rule asking "is this a border oblast" gets
    # "no" from an unknown, and the unknown is visible in the row rather than
    # dressed as a negative answer.
    oblast: str = ""
    # T37. Whether the message was about this area or listed it as still under
    # alert while clearing another.
    role: AreaRole = AreaRole.SUBJECT

    @property
    def latency_s(self) -> float:
        """Seconds between the source timestamp and our ingest timestamp."""
        return (self.ts_ingest - self.ts_source).total_seconds()

    def content_hash(self) -> str:
        """Stable identity for idempotent writes.

        Excludes ``ts_ingest``: re-polling the same transition must not create a
        second row. An offset-aware timestamp is normalized to UTC first, so the
        same instant reported as ``+02:00`` by one poll and ``+00:00`` by
        another hashes identically; two spellings of one moment are one
        transition, not two (F52). ``role`` is part of the identity from 0.12.0.0
        (T37): one message can name one area twice, clearing it and listing it
        as still under alert, and those are two transitions rather than one
        row overwriting the other. ``oblast`` stays out, because it is derived
        from ``area_id`` rather than an independent fact about the moment.

        ``kind`` is part of the identity from 0.48.0.0 (D-044), and this is not
        a reversal of D-013 but a consequence of it having been outgrown. D-013
        excluded ``kind`` on the premise that a transition is something an
        *area* undergoes, so a reclassification was a better reading of one
        event rather than a second one. D-044 measured that premise false: an
        area carries several threat kinds at once, they begin and end
        independently, and the fold now works in ``(area_id, kind)``. Under the
        old identity two kinds asserted for one area at one instant by one
        source collapsed into a single row and the second was silently
        discarded - which `reconcile --unmask` does by construction, since every
        row it writes carries the snapshot's own ``saved_at``.

        D-013's actual concern survives untouched: re-reading the raw corpus
        with a better parser still happens by rebuilding a store from raw rather
        than by appending to an old one.

        **Migration.** Old rows keep the hashes they were written with. A
        transition still live across the deploy will be re-polled, hash
        differently and land a second time; that duplicate carries the same
        area, kind, state and stamp as the original, so it folds to the same
        standing and renders identically. The cost is bounded by the number of
        alerts open at the moment of the deploy.

        The raw text stays out for the reason it always did.
        """
        ts = self.ts_source
        stamp = (ts.astimezone(UTC) if ts.tzinfo is not None else ts).isoformat()
        payload = "|".join(
            [
                self.area_id,
                self.state.value,
                stamp,
                self.source_id,
                self.role.value,
                self.kind.value,
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@runtime_checkable
class ThreatSource(Protocol):
    """The adapter boundary.

    A Polish feed, a Ukrainian feed and the fixture generator differ only in
    their implementation of this protocol.
    """

    source_id: str

    def poll(self) -> Sequence[ThreatEvent]:
        """Return events observed since the previous call.

        Implementations must not raise on malformed input. A parser that raises
        turns a hostile payload into an outage.
        """
        ...
