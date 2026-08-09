"""Regime split and the policy gate.

Budget allocation left this file at 0.8.0.0 with the budget itself (D-014).
"""

from __future__ import annotations

from mavo.policy import Regime, policy_of
from mavo.rules import conjunction, drone_conjunction

MISSILE_CANDIDATE = (Regime.MISSILE, "CONJ-missile", conjunction)
DRONE_CANDIDATE = (Regime.DRONE, "CONJ-drone", drone_conjunction)


def test_for_regime_finds_a_served_regime() -> None:
    policy = policy_of([MISSILE_CANDIDATE, DRONE_CANDIDATE])
    found = policy.for_regime(Regime.DRONE)
    assert found is not None
    assert found.rule_id == "CONJ-drone"


def test_for_regime_returns_none_for_an_unserved_regime() -> None:
    # Unserved must be distinguishable from served-but-silent, in code as in the
    # state machine.
    assert policy_of([MISSILE_CANDIDATE]).for_regime(Regime.DRONE) is None
