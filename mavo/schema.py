"""Normalized event schema and the source adapter boundary.

Everything above this module is blind to which feed produced an event. That is
what makes a later switch to a Polish channel a new implementation of
``ThreatSource`` rather than a rewrite.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
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
    """Tri-state alert status for one administrative area.

    UNKNOWN is a distinct state and never resolves to CLEAR. A feed that goes
    silent has not told us the sky is empty.
    """

    ACTIVE = "active"
    CLEAR = "clear"
    UNKNOWN = "unknown"


def is_clear(state: AlertState) -> bool:
    """True only for an affirmatively reported all-clear.

    Written as a function rather than ``state != ACTIVE`` at every call site
    because the negation is the defect: it silently folds UNKNOWN into CLEAR.
    """
    return state is AlertState.CLEAR


def is_actionable(state: AlertState) -> bool:
    """True when the state may contribute to a warning decision.

    UNKNOWN is actionable for degradation reporting but never for an alarm; the
    decision layer must ask which, so both predicates exist.
    """
    return state is AlertState.ACTIVE


class ThreatKind(Enum):
    """Classified means of attack, driving which timing regime applies."""

    MISSILE = "missile"
    DRONE = "drone"
    GLIDE_BOMB = "glide_bomb"
    UNKNOWN = "unknown"


# Oblasts bordering Poland, and the second-order ring behind them.
BORDER_OBLASTS: frozenset[str] = frozenset({"volyn", "lviv", "zakarpattia"})
SECOND_RING_OBLASTS: frozenset[str] = frozenset({"rivne", "ternopil", "ivano-frankivsk"})


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

    @property
    def latency_s(self) -> float:
        """Seconds between the source timestamp and our ingest timestamp."""
        return (self.ts_ingest - self.ts_source).total_seconds()

    def content_hash(self) -> str:
        """Stable identity for idempotent writes.

        Excludes ``ts_ingest``: re-polling the same transition must not create a
        second row.
        """
        payload = "|".join(
            [self.area_id, self.state.value, self.ts_source.isoformat(), self.source_id]
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
