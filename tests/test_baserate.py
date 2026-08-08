"""The null model: every branch of the gate, both directions."""

from __future__ import annotations

from mavo.baserate import (
    Contingency,
    assess_rule,
    base_rate,
    fisher_exact_greater,
    gate,
    lift,
    precision,
    recall,
    wilson_interval,
)
from mavo.schema import Provenance


def test_precision_of_a_rule_that_never_fired_is_unknown_not_zero() -> None:
    # Zero would make an untested rule look merely bad. Unknown is never safe.
    assert precision(Contingency(a=0, b=0, c=3, d=97)) is None


def test_recall_without_events_is_unknown() -> None:
    assert recall(Contingency(a=0, b=10, c=0, d=90)) is None


def test_base_rate_of_empty_history_is_unknown() -> None:
    assert base_rate(Contingency(0, 0, 0, 0)) is None


def test_lift_near_one_means_the_rule_added_nothing() -> None:
    # Fires on 57% of nights, events occur on 57% of the nights it fires.
    table = Contingency(a=57, b=43, c=0, d=0)
    value = lift(table)
    assert value is not None
    assert abs(value - 1.0) < 1e-9


def test_lift_is_unknown_when_the_rule_never_fired() -> None:
    assert lift(Contingency(a=0, b=0, c=1, d=9)) is None


def test_wilson_interval_brackets_the_estimate() -> None:
    interval = wilson_interval(2, 40)
    assert interval is not None
    low, high = interval
    assert low < 0.05 < high


def test_wilson_interval_without_trials_is_unknown() -> None:
    assert wilson_interval(0, 0) is None


def test_fisher_matches_a_hand_checked_table() -> None:
    # Margins 3/4 by 4/3 over n=7. The only table at least as extreme has
    # k=3, so p = C(3,3)*C(4,1)/C(7,4) = 4/35. Checked against an independent
    # exact-fraction computation, not against the implementation.
    p = fisher_exact_greater(Contingency(a=3, b=0, c=1, d=3))
    assert abs(p - 4.0 / 35.0) < 1e-12


def test_fisher_of_a_degenerate_table_is_one() -> None:
    assert fisher_exact_greater(Contingency(0, 0, 0, 0)) == 1.0


def test_gate_fails_a_rule_that_fires_too_often() -> None:
    # Perfect recall, useless in practice: this is the whole point of the gate.
    assessment = assess_rule("noisy", Contingency(a=8, b=400, c=0, d=300), observation_weeks=100)
    verdict = gate(assessment)
    assert verdict.passes is False
    assert any("alarm rate" in reason for reason in verdict.reasons)


def test_gate_fails_a_rule_that_misses_events() -> None:
    assessment = assess_rule("blind", Contingency(a=4, b=2, c=6, d=700), observation_weeks=100)
    verdict = gate(assessment)
    assert verdict.passes is False
    assert any("recall" in reason and "below floor" in reason for reason in verdict.reasons)


def test_gate_fails_when_recall_is_unknown() -> None:
    assessment = assess_rule("silent", Contingency(a=0, b=5, c=0, d=700), observation_weeks=100)
    verdict = gate(assessment)
    assert verdict.passes is False
    assert any("recall unknown" in reason for reason in verdict.reasons)


def test_gate_fails_when_the_observation_window_is_missing() -> None:
    assessment = assess_rule("windowless", Contingency(a=5, b=1, c=0, d=10), observation_weeks=0)
    verdict = gate(assessment)
    assert verdict.passes is False
    assert any("alarm rate unknown" in reason for reason in verdict.reasons)


def test_gate_fails_an_association_no_better_than_chance() -> None:
    assessment = assess_rule("chance", Contingency(a=5, b=45, c=5, d=45), observation_weeks=100)
    verdict = gate(assessment)
    assert verdict.passes is False
    assert any("not distinguishable" in reason for reason in verdict.reasons)


def test_gate_passes_a_rule_that_clears_all_three_conditions() -> None:
    assessment = assess_rule("good", Contingency(a=10, b=40, c=0, d=1400), observation_weeks=200)
    verdict = gate(assessment)
    assert verdict.passes is True
    assert str(verdict).startswith("[PASS]")


def test_assessment_summary_prints_unknowns_as_unknown() -> None:
    assessment = assess_rule("silent", Contingency(a=0, b=0, c=0, d=10), observation_weeks=1)
    assert "unknown" in assessment.summary()


def test_assessment_inherits_the_weakest_input_label() -> None:
    assessment = assess_rule(
        "derived", Contingency(a=1, b=1, c=1, d=1), 1.0, provenance=Provenance.INFERENCE
    )
    assert assessment.provenance is Provenance.INFERENCE
