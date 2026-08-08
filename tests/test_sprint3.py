"""Sprint 3 regressions: regime split, shared budget, coverage gap.

Defect class: a single global threshold averaging two populations that behave
differently, and the downstream failures that follow from splitting them badly.

Three specific things must not return:

F6. A recall figure that averages a rule which is perfect at one job with the
    same rule being blind to another. Sprint 2 reported 0.47 and called it a
    mediocre rule; the truth was 7 of 7 and 0 of 8.
F7. Two rules each cleared at the full alarm budget, producing twice the budget.
    The budget belongs to the recipient, not to the rule.
F8. An unserved crossing kind excluded from the recall denominator without being
    reported, so a partial policy reads as complete. This is the same defect as
    unknown resolving to clear, in a different place.

Verified red against a scratch copy of 0.1.0: `run_regime`, `DecisionPolicy` and
the coverage-gap fields do not exist there, so every test in this file errors on
import, which is the required red.
"""

from __future__ import annotations

import pytest

from mavo.baserate import Contingency, assess_rule, gate
from mavo.errors import BudgetOverAllocated
from mavo.evaluate import run_policy, run_regime
from mavo.policy import DecisionPolicy, Regime, RegimeRule, equal_split
from mavo.rules import conjunction, drone_conjunction
from mavo.sources.fixture import generate_history

MISSILE_CANDIDATE = (Regime.MISSILE, "CONJ-missile", conjunction)
DRONE_CANDIDATE = (Regime.DRONE, "CONJ-drone", drone_conjunction)


def test_f6_global_recall_hides_a_perfect_rule_and_a_blind_one() -> None:
    nights = generate_history(weeks=208)
    on_missiles = run_regime("CONJ", conjunction, nights, Regime.MISSILE).assessment.recall
    on_drones = run_regime("CONJ", conjunction, nights, Regime.DRONE).assessment.recall
    assert on_missiles == 1.0
    assert on_drones == 0.0


def test_f7_budget_cannot_be_allocated_twice() -> None:
    with pytest.raises(BudgetOverAllocated, match="exceeds total"):
        DecisionPolicy(
            rules=(
                RegimeRule(Regime.MISSILE, "a", conjunction, 2.0),
                RegimeRule(Regime.DRONE, "b", drone_conjunction, 2.0),
            ),
            total_budget_per_week=2.0,
        )


def test_f7_gate_uses_the_allocated_share_not_the_default() -> None:
    assessment = assess_rule("busy", Contingency(a=10, b=250, c=0, d=1200), observation_weeks=200)
    assert gate(assessment).passes is True
    assert gate(assessment, alarm_budget=0.5).passes is False


def test_f8_partial_policy_reports_its_gap() -> None:
    run = run_policy(equal_split([MISSILE_CANDIDATE]), generate_history(weeks=208))
    assert run.has_coverage_gap is True
    assert "COVERAGE GAP" in run.summary()


def test_f8_full_policy_reports_no_gap() -> None:
    run = run_policy(equal_split([MISSILE_CANDIDATE, DRONE_CANDIDATE]), generate_history(weeks=208))
    assert run.has_coverage_gap is False
