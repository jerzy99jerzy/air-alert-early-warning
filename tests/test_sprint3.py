"""Sprint 3 regressions: regime split, shared budget, coverage gap.

Defect class: a single global threshold averaging two populations that behave
differently, and the downstream failures that follow from splitting them badly.

Three specific things must not return:

F6. A recall figure that averages a rule which is perfect at one job with the
    same rule being blind to another. Sprint 2 reported 0.47 and called it a
    mediocre rule; the truth was 7 of 7 and 0 of 8.
F7. Two rules each cleared at the full alarm budget, producing twice the budget.
    **The regression for this defect was retired at 0.8.0.0** together with the
    budget it defended (D-014). The defect and its class stay in the log; what
    is gone is the control, so a test asserting the refusal would pass only by
    asserting that a removed feature is still removed.
F8. An unserved crossing kind excluded from the recall denominator without being
    reported, so a partial policy reads as complete. This is the same defect as
    unknown resolving to clear, in a different place.

Verified red against a scratch copy of 0.1.0: `run_regime`, `DecisionPolicy` and
the coverage-gap fields do not exist there, so every test in this file errors on
import, which is the required red.
"""

from __future__ import annotations

from mavo.evaluate import run_policy
from mavo.policy import Regime, policy_of
from mavo.rules import conjunction, drone_conjunction
from mavo.sources.fixture import generate_history

MISSILE_CANDIDATE = (Regime.MISSILE, "CONJ-missile", conjunction)
DRONE_CANDIDATE = (Regime.DRONE, "CONJ-drone", drone_conjunction)


def test_f8_partial_policy_reports_its_gap() -> None:
    run = run_policy(policy_of([MISSILE_CANDIDATE]), generate_history(weeks=208))
    assert run.has_coverage_gap is True
    assert "COVERAGE GAP" in run.summary()


def test_f8_full_policy_reports_no_gap() -> None:
    run = run_policy(policy_of([MISSILE_CANDIDATE, DRONE_CANDIDATE]), generate_history(weeks=208))
    assert run.has_coverage_gap is False
