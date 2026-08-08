"""Regime split, budget allocation, and the policy gate."""

from __future__ import annotations

import pytest

from mavo.errors import BudgetOverAllocated, BudgetOverrun
from mavo.evaluate import plan_policy, run_policy, run_regime
from mavo.policy import DecisionPolicy, Regime, RegimeRule, equal_split
from mavo.rules import conjunction, drone_conjunction
from mavo.schema import ThreatKind
from mavo.sources.fixture import generate_history

MISSILE_CANDIDATE = (Regime.MISSILE, "CONJ-missile", conjunction)
DRONE_CANDIDATE = (Regime.DRONE, "CONJ-drone", drone_conjunction)


def test_regime_maps_to_its_ground_truth_kind() -> None:
    assert Regime.MISSILE.threat_kind is ThreatKind.MISSILE
    assert Regime.DRONE.threat_kind is ThreatKind.DRONE


def test_policy_refuses_to_allocate_more_than_it_has() -> None:
    with pytest.raises(BudgetOverAllocated, match="exceeds total"):
        DecisionPolicy(
            rules=(
                RegimeRule(Regime.MISSILE, "a", conjunction, 1.5),
                RegimeRule(Regime.DRONE, "b", drone_conjunction, 1.5),
            ),
            total_budget_per_week=2.0,
        )


def test_equal_split_divides_the_total() -> None:
    policy = equal_split([MISSILE_CANDIDATE, DRONE_CANDIDATE], total=2.0)
    assert [rule.alarm_budget_per_week for rule in policy.rules] == [1.0, 1.0]


def test_policy_fires_at_the_earliest_of_its_rules() -> None:
    policy = equal_split([MISSILE_CANDIDATE, DRONE_CANDIDATE], total=2.0)
    nights = [night for night in generate_history(weeks=104) if night.had_crossing]
    for night in nights:
        moments = [rule.rule(night) for rule in policy.rules]
        fired = [moment for moment in moments if moment is not None]
        if fired:
            assert policy.fires_at(night) == min(fired)


def test_missile_regime_has_perfect_recall_on_its_own_events() -> None:
    # The global 0.47 measured in sprint 2 averaged a perfect rule with a blind
    # one. Scored against only the crossings it is accountable for, the missile
    # rule misses nothing.
    run = run_regime("CONJ-missile", conjunction, generate_history(weeks=208), Regime.MISSILE)
    assert run.assessment.recall == 1.0


def test_missile_rule_is_silent_on_drone_events() -> None:
    run = run_regime("CONJ-missile", conjunction, generate_history(weeks=208), Regime.DRONE)
    assert run.assessment.recall == 0.0


def test_regime_scoring_excludes_the_other_regimes_crossings() -> None:
    nights = generate_history(weeks=104)
    total = len(nights)
    other = sum(
        1 for n in nights if n.had_crossing and n.crossing_kind is not ThreatKind.MISSILE
    )
    run = run_regime("CONJ-missile", conjunction, nights, Regime.MISSILE)
    assert run.assessment.table.n == total - other


def test_even_allocation_fails_the_drone_regime() -> None:
    # Recorded, not tuned away: the drone regime needs roughly twice the missile
    # regime, so an even split fails a regime the total could afford.
    run = run_policy(equal_split([MISSILE_CANDIDATE, DRONE_CANDIDATE]), generate_history(weeks=208))
    verdicts = {label: verdict.passes for label, _, verdict in run.per_regime}
    assert verdicts["missile/CONJ-missile"] is True
    assert verdicts["drone/CONJ-drone"] is False


def test_combined_policy_recovers_full_recall() -> None:
    run = run_policy(equal_split([MISSILE_CANDIDATE, DRONE_CANDIDATE]), generate_history(weeks=208))
    assert run.combined.assessment.recall == 1.0
    assert run.combined_verdict.passes is True


def test_demand_allocation_refuses_rather_than_trimming() -> None:
    # The allocator must not silently shrink a share to make the sum fit; a
    # policy that passes its own gate while overrunning the recipient is worse
    # than one that refuses to be built.
    with pytest.raises(BudgetOverrun, match="exceeds the total budget"):
        plan_policy([MISSILE_CANDIDATE, DRONE_CANDIDATE], generate_history(weeks=208))


def test_missile_only_policy_fits_with_headroom_but_leaves_a_gap() -> None:
    # The trade the sprint actually found. One regime fits the budget with room
    # to spare and passes on the scope it claims, but the crossings it does not
    # serve do not disappear: they are counted and printed.
    nights = generate_history(weeks=208)
    policy = plan_policy([MISSILE_CANDIDATE], nights, total_budget=2.0)
    assert policy.rules[0].alarm_budget_per_week < 1.0

    run = run_policy(policy, nights)
    assert run.combined_verdict.passes is True
    assert run.has_coverage_gap is True
    assert dict(run.unserved)["drone"] > 0


def test_two_regime_policy_has_no_coverage_gap() -> None:
    run = run_policy(equal_split([MISSILE_CANDIDATE, DRONE_CANDIDATE]), generate_history(weeks=208))
    assert run.has_coverage_gap is False


def test_coverage_gap_is_printed_and_not_folded_into_recall() -> None:
    # The defect this guards: an unserved crossing kind quietly excluded from the
    # denominator, so a partial policy reports recall 1.00 and looks complete.
    nights = generate_history(weeks=208)
    run = run_policy(plan_policy([MISSILE_CANDIDATE], nights, total_budget=2.0), nights)
    assert run.combined.assessment.recall == 1.0
    assert "COVERAGE GAP" in run.summary()


def test_for_regime_finds_a_served_regime() -> None:
    policy = equal_split([MISSILE_CANDIDATE, DRONE_CANDIDATE])
    found = policy.for_regime(Regime.DRONE)
    assert found is not None
    assert found.rule_id == "CONJ-drone"


def test_for_regime_returns_none_for_an_unserved_regime() -> None:
    # Unserved must be distinguishable from served-but-silent, in code as in the
    # state machine.
    assert equal_split([MISSILE_CANDIDATE]).for_regime(Regime.DRONE) is None
