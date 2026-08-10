"""Normalized event schema and the source adapter boundary.

Everything above this module is blind to which feed produced an event. That is
what makes a later switch to a Polish channel a new implementation of
``ThreatSource`` rather than a rewrite.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
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
    """Classified means of attack, driving which timing regime applies."""

    MISSILE = "missile"
    DRONE = "drone"
    GLIDE_BOMB = "glide_bomb"
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
        Deliberately still excludes ``kind`` and the
        raw text: identity means "this area entered this state at this moment
        according to this source", and a reclassification of the same transition
        is a better *reading*, not a new *event* - see D-013 for why re-reading
        happens by rebuilding a store from the raw corpus rather than by
        appending to an old one.
        """
        ts = self.ts_source
        stamp = (ts.astimezone(UTC) if ts.tzinfo is not None else ts).isoformat()
        payload = "|".join(
            [self.area_id, self.state.value, stamp, self.source_id, self.role.value]
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
