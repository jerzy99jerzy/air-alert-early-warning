"""Regime split and the policy gate.

Budget allocation left this file at 0.8.0.0 with the budget itself (D-014).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from mavo.policy import Regime, policy_of
from mavo.rules import conjunction, drone_conjunction
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind
from mavo.sources.fixture import Night

MISSILE_CANDIDATE = (Regime.MISSILE, "CONJ-missile", conjunction)
DRONE_CANDIDATE = (Regime.DRONE, "CONJ-drone", drone_conjunction)

_T0 = datetime(2026, 8, 29, 22, 0, tzinfo=UTC)


def _westward_night(kind: ThreatKind) -> Night:
    """Three oblasts activating east to west, all carrying one kind.

    `rivne`, `lviv` and `volyn` are in `EAST_TO_WEST` in that order and the
    last two are border oblasts, so this clears the escalation requirement and
    the border one. Three areas is `ESCALATION_MIN_AREAS` and well under
    `POISON_AREA_THRESHOLD`, so nothing here is suppressed as implausible
    breadth.
    """
    return Night(
        start=_T0,
        scenario=f"westward-{kind.value}",
        events=tuple(
            ThreatEvent(
                area_id=oblast,
                state=AlertState.ACTIVE,
                ts_source=_T0 + timedelta(minutes=10 * index),
                ts_ingest=_T0 + timedelta(minutes=10 * index),
                source_id="test-policy",
                kind=kind,
                provenance=Provenance.REPORTED,
                oblast=oblast,
            )
            for index, oblast in enumerate(("rivne", "lviv", "volyn"))
        ),
        crossing_at=None,
    )


def test_for_regime_finds_a_served_regime() -> None:
    policy = policy_of([MISSILE_CANDIDATE, DRONE_CANDIDATE])
    found = policy.for_regime(Regime.DRONE)
    assert found is not None
    assert found.rule_id == "CONJ-drone"


def test_for_regime_returns_none_for_an_unserved_regime() -> None:
    # Unserved must be distinguishable from served-but-silent, in code as in the
    # state machine.
    assert policy_of([MISSILE_CANDIDATE]).for_regime(Regime.DRONE) is None


def test_a_glide_bomb_or_artillery_night_reaches_no_alarm_rule() -> None:
    """T47, item 3. Naming a kind is a reporting change, never an alarm one.

    The consumer gains labels for `glide_bomb` and `artillery` because three
    thousand declarations currently arrive named and render as unnamed. That
    is a rendering decision, and the risk it carries is that a kind which has
    a glyph starts looking like a kind which has a tier. It does not: `Regime`
    names MISSILE and DRONE, the conjunctions compare with `is`, and D-015
    keeps glide bombs and artillery in the reporting tier because neither
    reaches the Polish border.

    Constructed as the *hardest* case rather than an easy one. This night has
    everything an alarm needs except the kind: active alerts in a border
    oblast, a westward vector across three oblasts inside the escalation
    window, and no poisoning. A rule reading breadth or geography alone fires
    on it. Only the kind test stops it, which is the property under assertion.
    """
    kinds = (ThreatKind.GLIDE_BOMB, ThreatKind.ARTILLERY)
    for kind in kinds:
        night = _westward_night(kind)
        assert conjunction(night) is None, f"{kind.value} reached the missile alarm"
        assert drone_conjunction(night) is None, f"{kind.value} reached the drone alarm"
        policy = policy_of([MISSILE_CANDIDATE, DRONE_CANDIDATE])
        assert policy.fires_at(night) is None, f"{kind.value} raised an alarm"
        # The night is only evidence if the same shape fires when the kind is
        # one the alarm tier serves. Without this the assertions above pass
        # against a fixture that could never fire for any reason at all.
        assert conjunction(_westward_night(ThreatKind.MISSILE)) is not None


def test_the_alarm_tier_serves_exactly_two_regimes() -> None:
    """A third `Regime` member is loud on the day it is added.

    The test above enumerates the two kinds that exist today and would keep
    passing if a fifth `ThreatKind` gained a regime tomorrow. This one fails
    instead, which is the direction that surfaces the change rather than
    absorbing it.
    """
    assert {regime.value for regime in Regime} == {"missile", "drone"}
    assert {regime.threat_kind for regime in Regime} == {
        ThreatKind.MISSILE,
        ThreatKind.DRONE,
    }
