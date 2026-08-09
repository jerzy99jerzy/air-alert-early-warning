"""Sprint 2 regressions: the fixture must not flatter the rules.

Defect class (F1 in docs/METHODOLOGY.md): an adversarial fixture that is not
adversarial on the dimension the rule uses. Campaign nights initially carried
only drone-classified alerts, so the missile rule scored precision 1.000 by
construction. Hardening the generator moved it to 0.054, a twenty-fold
overstatement that was invisible to reading and obvious to running.

Verified red against a scratch copy of `fixture.py` with the hardening reverted:
`test_missile_classification_appears_on_nights_without_a_crossing` fails and
`test_missile_rule_precision_is_not_perfect` fails with precision 1.0.
"""

from __future__ import annotations

from mavo.evaluate import run_rule
from mavo.rules import r3_border_missile
from mavo.schema import ThreatKind
from mavo.sources.fixture import generate_history


def test_campaign_nights_carry_missile_classification() -> None:
    # Scoped to campaign nights specifically. An earlier version of this test
    # asked only for a missile-classified night without a crossing, which the
    # poisoned-feed and degraded-feed scenarios already satisfied; it passed
    # against the buggy generator and therefore documented nothing. Caught by
    # running it against a reverted scratch copy rather than assuming it was red.
    nights = generate_history(weeks=104)
    decoys = [
        night
        for night in nights
        if night.scenario == "campaign-no-crossing"
        and any(event.kind is ThreatKind.MISSILE for event in night.events)
    ]
    assert decoys, "campaign nights are drone-only: the fixture flatters the missile rule"


def test_missile_rule_precision_is_not_perfect() -> None:
    run = run_rule("R3", r3_border_missile, generate_history(weeks=208))
    assert run.assessment.precision is not None
    assert run.assessment.precision < 0.5


def test_gate_records_the_finding_rather_than_being_relaxed() -> None:
    # The floors are the ones the README publishes. If a sprint moves them, that
    # is a scope change and the README table moves in the same commit.
    from mavo.baserate import MAX_P_VALUE, MIN_LIFT_LOWER_BOUND, MIN_RECALL

    # MAX_ALARMS_PER_WEEK left this tuple at 0.8.0.0 with the condition it
    # carried (D-014). MIN_LIFT_LOWER_BOUND took its place in the gate.
    assert (MIN_RECALL, MIN_LIFT_LOWER_BOUND, MAX_P_VALUE) == (0.9, 1.5, 0.05)
