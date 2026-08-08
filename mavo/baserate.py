"""Base-rate correction: this project's null model.

This module exists as a top-level file rather than a helper inside the decision
layer because it holds the load-bearing lesson of the project. A rule that fires
on nights when something happens is worthless if it also fires on most nights
when nothing does. Massed strike campaigns against western Ukraine cover roughly
57% of days in the observed period, so coincidence with a campaign carries almost
no information on its own.

Popularity is the null hypothesis. One candidate variable is excluded rather than
merely unused; it is named in docs/DECISIONS.md as D-002 and deliberately not
named here, because ``tests/lint_limitations.py`` enforces its absence from the
package by term and the decision log is its single home.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from mavo.schema import Provenance


@dataclass(frozen=True, slots=True)
class Contingency:
    """2x2 table over observation windows.

    ``a`` fired and event occurred, ``b`` fired and no event, ``c`` did not fire
    and event occurred, ``d`` neither.
    """

    a: int
    b: int
    c: int
    d: int

    @property
    def n(self) -> int:
        """Total observation windows."""
        return self.a + self.b + self.c + self.d

    @property
    def fired(self) -> int:
        """Windows in which the rule fired."""
        return self.a + self.b

    @property
    def events(self) -> int:
        """Windows in which the outcome occurred."""
        return self.a + self.c


def base_rate(table: Contingency) -> float | None:
    """Unconditional probability of the outcome. None when there is no data."""
    if table.n == 0:
        return None
    return table.events / table.n


def precision(table: Contingency) -> float | None:
    """P(event | rule fired). None when the rule never fired.

    None rather than 0.0: a rule that never fired has undefined precision, and
    reporting zero would let a silent rule look like a bad one instead of an
    untested one. Unknown is never the safe state.
    """
    if table.fired == 0:
        return None
    return table.a / table.fired


def recall(table: Contingency) -> float | None:
    """P(rule fired | event). None when no event was observed."""
    if table.events == 0:
        return None
    return table.a / table.events


def lift(table: Contingency) -> float | None:
    """Precision divided by the base rate. None when either is undefined.

    A lift near 1.0 means the rule has told you nothing you did not already know
    from the calendar.
    """
    precision_value = precision(table)
    base = base_rate(table)
    if precision_value is None or base is None or base == 0.0:
        return None
    return precision_value / base


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float] | None:
    """Wilson score interval for a proportion. None when there are no trials.

    Used instead of the normal approximation because the counts here are small:
    a handful of positive events over several years.
    """
    if trials == 0:
        return None
    p_hat = successes / trials
    denominator = 1.0 + z * z / trials
    center = (p_hat + z * z / (2 * trials)) / denominator
    margin = (
        z
        * math.sqrt(p_hat * (1.0 - p_hat) / trials + z * z / (4.0 * trials * trials))
        / denominator
    )
    return (max(0.0, center - margin), min(1.0, center + margin))


def fisher_exact_greater(table: Contingency) -> float:
    """One-sided Fisher exact p-value for association stronger than chance.

    Implemented on ``math.comb`` rather than pulled from SciPy: a tool whose
    product is a measurement is weakened by a dependency tree nobody audits, and
    this is the only statistic the gate needs.
    """
    a, b, c, d = table.a, table.b, table.c, table.d
    row1, row2 = a + b, c + d
    col1 = a + c
    total = table.n
    if total == 0 or row1 == 0 or col1 == 0:
        return 1.0
    denominator = math.comb(total, col1)
    upper = min(row1, col1)
    tail = 0.0
    for k in range(a, upper + 1):
        if col1 - k > row2:
            continue
        tail += math.comb(row1, k) * math.comb(row2, col1 - k)
    return min(1.0, tail / denominator)


@dataclass(frozen=True, slots=True)
class RuleAssessment:
    """What a candidate rule is worth, with its epistemic label attached."""

    rule_id: str
    table: Contingency
    base_rate: float | None
    precision: float | None
    precision_ci: tuple[float, float] | None
    recall: float | None
    lift: float | None
    p_value: float
    alarm_rate_per_week: float | None
    provenance: Provenance

    def summary(self) -> str:
        """One line for a human, with unknowns printed as unknown."""

        def fmt(value: float | None) -> str:
            return "unknown" if value is None else f"{value:.3f}"

        return (
            f"{self.rule_id}: precision={fmt(self.precision)} recall={fmt(self.recall)} "
            f"lift={fmt(self.lift)} p={self.p_value:.4f} "
            f"alarms/week={fmt(self.alarm_rate_per_week)} [{self.provenance.name.lower()}]"
        )


def assess_rule(
    rule_id: str,
    table: Contingency,
    observation_weeks: float,
    provenance: Provenance = Provenance.REPORTED,
) -> RuleAssessment:
    """Score a candidate rule against the base rate.

    ``provenance`` is the label of the weakest input feeding the rule; the
    assessment inherits it rather than upgrading itself to measured.
    """
    return RuleAssessment(
        rule_id=rule_id,
        table=table,
        base_rate=base_rate(table),
        precision=precision(table),
        precision_ci=wilson_interval(table.a, table.fired),
        recall=recall(table),
        lift=lift(table),
        p_value=fisher_exact_greater(table),
        alarm_rate_per_week=(table.fired / observation_weeks if observation_weeks > 0 else None),
        provenance=Provenance.weakest([provenance]),
    )


@dataclass(frozen=True, slots=True)
class GateVerdict:
    """Outcome of the S2 go/no-go gate for one rule."""

    rule_id: str
    passes: bool
    reasons: tuple[str, ...]

    def __str__(self) -> str:
        verdict = "PASS" if self.passes else "FAIL"
        return f"[{verdict}] {self.rule_id}: " + "; ".join(self.reasons)


MIN_RECALL = 0.9
MAX_ALARMS_PER_WEEK = 2.0
MAX_P_VALUE = 0.05


def gate(assessment: RuleAssessment, alarm_budget: float = MAX_ALARMS_PER_WEEK) -> GateVerdict:
    """Decide whether a rule may drive a critical alarm.

    Three conditions, and failing any one is decisive. Alarm rate is a hard
    control rather than a quality metric: a rule that fires three times a week
    trains its audience to ignore it, which is a failure mode an adversary can
    induce deliberately.

    ``alarm_budget`` is a parameter rather than a constant because the budget
    belongs to the recipient, not to the rule. When several rules share one
    recipient, each is gated against its allocated share and the sum is gated
    separately. Two rules each cleared at the full budget produce twice the
    budget, which is the arithmetic that destroys the channel.
    """
    reasons: list[str] = []
    passes = True

    if assessment.recall is None:
        passes = False
        reasons.append("recall unknown (no positive events observed)")
    elif assessment.recall < MIN_RECALL:
        passes = False
        reasons.append(f"recall {assessment.recall:.2f} below floor {MIN_RECALL}")
    else:
        reasons.append(f"recall {assessment.recall:.2f} meets floor")

    if assessment.alarm_rate_per_week is None:
        passes = False
        reasons.append("alarm rate unknown (no observation window)")
    elif assessment.alarm_rate_per_week > alarm_budget:
        passes = False
        reasons.append(
            f"alarm rate {assessment.alarm_rate_per_week:.2f}/week exceeds "
            f"{alarm_budget:.2f}/week; demote to observation tier"
        )
    else:
        reasons.append(
            f"alarm rate {assessment.alarm_rate_per_week:.2f}/week within "
            f"budget {alarm_budget:.2f}/week"
        )

    if assessment.p_value > MAX_P_VALUE:
        passes = False
        reasons.append(
            f"association p={assessment.p_value:.3f} not distinguishable from base rate"
        )
    else:
        reasons.append(f"association p={assessment.p_value:.3f}")

    return GateVerdict(rule_id=assessment.rule_id, passes=passes, reasons=tuple(reasons))
