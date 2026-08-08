"""Candidate warning rules.

Rules are explicit predicates with tunable thresholds, not a learned model. The
reason is in docs/DECISIONS.md and it is not conservatism: the positive class
holds roughly a dozen events across four years, and any model fitted to that
would reproduce exactly the overfitting that invalidated the project's first
analysis.

A rule returns the moment it would fire, or None. Returning the timestamp rather
than a boolean is what makes lead time measurable.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timedelta

from mavo.schema import BORDER_OBLASTS, AlertState, ThreatEvent, ThreatKind
from mavo.sources.fixture import EAST_TO_WEST, Night

Rule = Callable[[Night], datetime | None]

# A source reporting this many areas within this window is not describing weather.
POISON_AREA_THRESHOLD = 8
POISON_WINDOW = timedelta(seconds=120)

ESCALATION_MIN_AREAS = 3
ESCALATION_WINDOW = timedelta(minutes=90)


def _active(events: Sequence[ThreatEvent]) -> list[ThreatEvent]:
    return [event for event in events if event.state is AlertState.ACTIVE]


def is_poisoned(night: Night) -> bool:
    """Whether the feed claims implausibly broad simultaneous activation.

    Suppression is a hard control, not a scoring penalty: an adversary who can
    induce alarms can exhaust the audience's attention, which costs nothing to
    attempt and disables the system for free.
    """
    active = sorted(_active(night.events), key=lambda event: event.ts_source)
    for index, anchor in enumerate(active):
        window = [
            event
            for event in active[index:]
            if event.ts_source - anchor.ts_source <= POISON_WINDOW
        ]
        if len({event.area_id for event in window}) >= POISON_AREA_THRESHOLD:
            return True
    return False


def r1_border_active(night: Night) -> datetime | None:
    """Any border oblast reports an active alert."""
    if is_poisoned(night):
        return None
    for event in sorted(_active(night.events), key=lambda e: e.ts_source):
        if event.area_id in BORDER_OBLASTS:
            return event.ts_source
    return None


def r3_border_missile(night: Night) -> datetime | None:
    """A border oblast reports an active alert classified as a missile threat."""
    if is_poisoned(night):
        return None
    for event in sorted(_active(night.events), key=lambda e: e.ts_source):
        if event.area_id in BORDER_OBLASTS and event.kind is ThreatKind.MISSILE:
            return event.ts_source
    return None


def r2_westward_escalation(night: Night) -> datetime | None:
    """Alerts activate across several areas trending west inside one window."""
    if is_poisoned(night):
        return None
    active = sorted(_active(night.events), key=lambda event: event.ts_source)
    order = {area: index for index, area in enumerate(EAST_TO_WEST)}
    seen: list[ThreatEvent] = []
    for event in active:
        seen = [
            candidate
            for candidate in seen
            if event.ts_source - candidate.ts_source <= ESCALATION_WINDOW
        ]
        seen.append(event)
        ranked = [candidate for candidate in seen if candidate.area_id in order]
        areas = {candidate.area_id for candidate in ranked}
        if len(areas) < ESCALATION_MIN_AREAS:
            continue
        positions = [order[candidate.area_id] for candidate in ranked]
        if positions[-1] > positions[0]:
            return event.ts_source
    return None


def r4_border_drone(night: Night) -> datetime | None:
    """A border oblast reports an active alert classified as a drone threat."""
    if is_poisoned(night):
        return None
    for event in sorted(_active(night.events), key=lambda e: e.ts_source):
        if event.area_id in BORDER_OBLASTS and event.kind is ThreatKind.DRONE:
            return event.ts_source
    return None


def drone_conjunction(night: Night) -> datetime | None:
    """Drone classification in a border oblast plus a westward vector.

    The drone-regime counterpart of ``conjunction``. It exists to be measured,
    not because it is expected to work: nothing in oblast-level alert state
    distinguishes a drone night that ends in a crossing from one that does not.
    """
    if is_poisoned(night):
        return None
    drone_at = r4_border_drone(night)
    escalation_at = r2_westward_escalation(night)
    if drone_at is None or escalation_at is None:
        return None
    return max(drone_at, escalation_at)


def conjunction(night: Night) -> datetime | None:
    """Border oblast, missile classification and a westward vector together.

    This is the only shape permitted to raise a critical alarm. Each conjunct
    exists to close one failure of the others: R1 alone fires on the majority of
    nights, R3 alone cannot distinguish a routine alert from an inbound raid, and
    R2 alone fires on campaigns that stop at the border.
    """
    if is_poisoned(night):
        return None
    missile_at = r3_border_missile(night)
    escalation_at = r2_westward_escalation(night)
    if missile_at is None or escalation_at is None:
        return None
    return max(missile_at, escalation_at)


CANDIDATE_RULES: dict[str, Rule] = {
    "R1-border-active": r1_border_active,
    "R2-westward-escalation": r2_westward_escalation,
    "R3-border-missile": r3_border_missile,
    "R4-border-drone": r4_border_drone,
    "CONJ-missile": conjunction,
    "CONJ-drone": drone_conjunction,
}
