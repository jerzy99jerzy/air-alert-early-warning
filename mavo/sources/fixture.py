"""Synthetic scenario generator.

Shipped as a CLI command rather than a test helper, so the repository runs with
no credentials and no data of its own. The adversarial scenarios earn their keep;
the clean ones only ever confirm the obvious.

Nothing generated here is evidence about the real world. It validates the
machinery, not the hypothesis: a gate verdict computed on this history says the
gate works, not that any rule is any good.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from mavo.errors import UnknownScenario
from mavo.schema import (
    BORDER_OBLASTS,
    SECOND_RING_OBLASTS,
    AlertState,
    Provenance,
    ThreatEvent,
    ThreatKind,
)

EAST_TO_WEST: tuple[str, ...] = (
    "kyiv",
    "zhytomyr",
    "rivne",
    "ternopil",
    "lviv",
    "volyn",
)

SCENARIOS: tuple[str, ...] = (
    "quiet",
    "campaign-no-crossing",
    "clean-missile",
    "clean-drone",
    "degraded-feed",
    "poisoned-feed",
    "border-only",
)


@dataclass(frozen=True, slots=True)
class Night:
    """One observation window with its ground truth attached."""

    start: datetime
    scenario: str
    events: tuple[ThreatEvent, ...]
    crossing_at: datetime | None
    crossing_kind: ThreatKind = ThreatKind.UNKNOWN

    @property
    def had_crossing(self) -> bool:
        """Whether a border violation actually occurred that night."""
        return self.crossing_at is not None

    def lead_time_s(self, decision_at: datetime) -> float | None:
        """Seconds between a decision and the crossing. None when neither exists."""
        if self.crossing_at is None:
            return None
        return (self.crossing_at - decision_at).total_seconds()


def _event(
    area: str,
    state: AlertState,
    ts: datetime,
    kind: ThreatKind,
    latency_s: int = 30,
    source_id: str = "fixture",
) -> ThreatEvent:
    return ThreatEvent(
        area_id=area,
        state=state,
        ts_source=ts,
        ts_ingest=ts + timedelta(seconds=latency_s),
        source_id=source_id,
        kind=kind,
        provenance=Provenance.REPORTED,
        # The generator works at oblast granularity, so the two fields carry the
        # same slug here. On the live path they differ: `area_id` is a raion or
        # hromada register code and `oblast` is the coarse geography the rules
        # read (T38). Setting both keeps the fixture honest about which field
        # the rules are actually testing.
        oblast=area,
    )


def _escalation(
    start: datetime, kind: ThreatKind, reach_border: bool, step_min: int = 12
) -> list[ThreatEvent]:
    """Alerts lighting up east to west, optionally reaching the border oblasts."""
    chain = EAST_TO_WEST if reach_border else EAST_TO_WEST[:3]
    events: list[ThreatEvent] = []
    for index, area in enumerate(chain):
        ts = start + timedelta(minutes=index * step_min)
        events.append(_event(area, AlertState.ACTIVE, ts, kind))
    return events


def build_night(start: datetime, scenario: str, rng: random.Random) -> Night:
    """Construct one night of events for a named scenario."""
    events: list[ThreatEvent] = []
    crossing: datetime | None = None
    crossing_kind = ThreatKind.UNKNOWN

    if scenario == "quiet":
        pass

    elif scenario == "campaign-no-crossing":
        # The decisive world. Roughly 57% of nights look like this and none of
        # them ends in a crossing. Every alarm here is a false positive.
        #
        # A campaign night carries missile-classified alerts a third of the time.
        # Without that the missile rule scores perfect precision by construction,
        # which is a property of the fixture and not of the rule. Found by running
        # the gate, not by reading the generator (F1, see METHODOLOGY).
        kind = ThreatKind.MISSILE if rng.random() < 0.33 else ThreatKind.DRONE
        events = _escalation(start, kind, reach_border=rng.random() < 0.5)

    elif scenario == "clean-missile":
        events = _escalation(start, ThreatKind.MISSILE, reach_border=True, step_min=8)
        crossing = events[-1].ts_source + timedelta(minutes=6)
        crossing_kind = ThreatKind.MISSILE

    elif scenario == "clean-drone":
        events = _escalation(start, ThreatKind.DRONE, reach_border=True, step_min=20)
        crossing = events[-1].ts_source + timedelta(minutes=33)
        crossing_kind = ThreatKind.DRONE

    elif scenario == "degraded-feed":
        # One feed goes silent: UNKNOWN, which must never be read as all-clear.
        events = _escalation(start, ThreatKind.UNKNOWN, reach_border=True)
        for area in sorted(BORDER_OBLASTS):
            events.append(
                _event(area, AlertState.UNKNOWN, start + timedelta(minutes=70),
                       ThreatKind.UNKNOWN, latency_s=240, source_id="fixture-degraded")
            )

    elif scenario == "poisoned-feed":
        # Every area at once: a source claiming the whole country is alight.
        everywhere = sorted(set(EAST_TO_WEST) | BORDER_OBLASTS | SECOND_RING_OBLASTS)
        for index, area in enumerate(everywhere):
            ts = start + timedelta(seconds=index)
            events.append(_event(area, AlertState.ACTIVE, ts, ThreatKind.MISSILE))

    elif scenario == "border-only":
        # Wrong vector: only the far south-west lights up, nothing behind it.
        events = [_event("zakarpattia", AlertState.ACTIVE, start, ThreatKind.DRONE)]

    else:
        raise UnknownScenario(f"unknown scenario: {scenario}")

    return Night(
        start=start,
        scenario=scenario,
        events=tuple(events),
        crossing_at=crossing,
        crossing_kind=crossing_kind,
    )


DEFAULT_MIX: dict[str, float] = {
    "quiet": 0.34,
    "campaign-no-crossing": 0.55,
    "clean-missile": 0.005,
    "clean-drone": 0.005,
    "degraded-feed": 0.05,
    "poisoned-feed": 0.02,
    "border-only": 0.03,
}


def generate_history(
    weeks: int = 52,
    seed: int = 1968,
    start: datetime | None = None,
    mix: dict[str, float] | None = None,
) -> list[Night]:
    """Generate a synthetic history of nights.

    The default mix puts campaign nights at 55%, matching the measured share of
    days covered by massed strike campaigns. That number is the whole difficulty
    of the problem and the fixture must not make it easier than it is.
    """
    rng = random.Random(seed)
    weights = dict(DEFAULT_MIX if mix is None else mix)
    names = list(weights)
    probabilities = [weights[name] for name in names]
    # Aware UTC, not naive: the store refuses a timestamp without an offset
    # (F52), and the generator must produce what the store accepts.
    first = start or datetime(2025, 1, 1, 21, 0, 0, tzinfo=UTC)

    nights: list[Night] = []
    for day in range(weeks * 7):
        scenario = rng.choices(names, weights=probabilities, k=1)[0]
        nights.append(build_night(first + timedelta(days=day), scenario, rng))
    return nights


class FixtureSource:
    """A ``ThreatSource`` replaying a generated history."""

    source_id = "fixture"

    def __init__(self, nights: Sequence[Night]) -> None:
        self._pending: list[ThreatEvent] = [
            event for night in nights for event in night.events
        ]

    def poll(self) -> Sequence[ThreatEvent]:
        """Drain every generated event once."""
        drained = self._pending
        self._pending = []
        return drained
