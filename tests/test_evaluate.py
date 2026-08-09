"""Scoring a rule over a history."""

from __future__ import annotations

from mavo.baserate import gate
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


def test_only_the_broad_rule_passes_the_gate_on_the_adversarial_history() -> None:
    """Recorded as it now measures, not as it used to.

    Through 0.7.x no candidate passed: the two rules with perfect recall were
    stopped by the alarm-rate condition. With that condition removed (D-014),
    `R1-border-active` passes on recall, lift and association, at 2.52
    alarms/week. This is a real consequence of the decision rather than a
    regression, so the test records the new state.

    Two cautions belong here rather than in a commit message. R1 clears the lift
    floor at 1.69 against a floor of 1.5, which is thin: one night either way
    moves it. And this is synthetic history, so a pass here is a statement about
    the machinery and about nothing in the world.
    """
    nights = generate_history(weeks=208)
    passing = [
        rule_id
        for rule_id, rule in CANDIDATE_RULES.items()
        if gate(run_rule(rule_id, rule, nights).assessment).passes
    ]
    assert passing == ["R1-border-active"]


def test_summary_is_printable_for_every_rule() -> None:
    nights = generate_history(weeks=12)
    for rule_id, rule in CANDIDATE_RULES.items():
        assert rule_id in run_rule(rule_id, rule, nights).summary()
