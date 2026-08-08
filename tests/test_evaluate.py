"""Scoring a rule over a history."""

from __future__ import annotations

from mavo.evaluate import run_rule
from mavo.rules import CANDIDATE_RULES, conjunction, r1_border_active
from mavo.sources.fixture import generate_history


def test_contingency_accounts_for_every_night() -> None:
    nights = generate_history(weeks=20)
    run = run_rule("R1", r1_border_active, nights)
    assert run.assessment.table.n == len(nights)


def test_history_is_deterministic_for_a_seed() -> None:
    first = generate_history(weeks=8, seed=42)
    second = generate_history(weeks=8, seed=42)
    assert [n.scenario for n in first] == [n.scenario for n in second]


def test_campaign_nights_dominate_the_history() -> None:
    # The fixture must not make the base-rate problem easier than it is.
    nights = generate_history(weeks=104)
    campaigns = sum(1 for n in nights if n.scenario == "campaign-no-crossing")
    assert 0.45 <= campaigns / len(nights) <= 0.65


def test_lead_time_is_measured_only_on_true_positives() -> None:
    nights = generate_history(weeks=104)
    run = run_rule("CONJ", conjunction, nights)
    assert run.median_lead_time_s is not None
    assert run.median_lead_time_s > 0


def test_no_candidate_rule_passes_the_gate_on_the_adversarial_history() -> None:
    # Recorded as a finding, not tuned away. A single rule cannot serve both the
    # missile and the drone regime; see docs/METHODOLOGY.md, sprint 2.
    nights = generate_history(weeks=208)
    passing = [
        rule_id
        for rule_id, rule in CANDIDATE_RULES.items()
        if run_rule(rule_id, rule, nights).verdict.passes
    ]
    assert passing == []


def test_summary_is_printable_for_every_rule() -> None:
    nights = generate_history(weeks=12)
    for rule_id, rule in CANDIDATE_RULES.items():
        assert rule_id in run_rule(rule_id, rule, nights).summary()
