"""Regime split: one rule per timing regime, one shared attention budget.

Sprint 2 measured a recall of 0.47 for the missile rule and recorded it as a
failure. Sprint 3 probed what that average hid: 7 of 7 on missile nights and 0 of
8 on drone nights. The rule was not mediocre, it was perfect at one job and blind
to another, and a single global threshold cannot express that.

The load-bearing constraint is that **the alarm budget belongs to the recipient,
not to the rule.** Two rules each cleared at two alarms per week produce four,
which is the number that destroys the channel. So a regime rule is gated against
its own share of the budget, and the policy as a whole is gated against the total.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from mavo.errors import BudgetOverAllocated
from mavo.rules import Rule
from mavo.schema import ThreatKind
from mavo.sources.fixture import Night


class Regime(Enum):
    """Timing regime a rule is responsible for.

    Regimes are defined by transit time, not by munition taxonomy: what matters
    is how many minutes a warning buys, and that differs by roughly a factor of
    five between the two.
    """

    MISSILE = "missile"
    DRONE = "drone"

    @property
    def threat_kind(self) -> ThreatKind:
        """The ground-truth crossing kind this regime is accountable for."""
        return ThreatKind.MISSILE if self is Regime.MISSILE else ThreatKind.DRONE


@dataclass(frozen=True, slots=True)
class RegimeRule:
    """A rule bound to a regime and to its share of the alarm budget."""

    regime: Regime
    rule_id: str
    rule: Rule
    alarm_budget_per_week: float


@dataclass(frozen=True, slots=True)
class DecisionPolicy:
    """The full alarm-tier decision: one rule per regime, one total budget.

    ``total_budget_per_week`` is not the sum of the parts by accident. It is the
    binding constraint, and the per-regime shares are an allocation of it.
    """

    rules: tuple[RegimeRule, ...]
    total_budget_per_week: float = 2.0

    def __post_init__(self) -> None:
        allocated = sum(rule.alarm_budget_per_week for rule in self.rules)
        if allocated > self.total_budget_per_week:
            raise BudgetOverAllocated(
                f"allocated budget {allocated:.2f}/week exceeds total "
                f"{self.total_budget_per_week:.2f}/week"
            )

    def fires_at(self, night: Night) -> datetime | None:
        """Earliest moment any regime rule would fire, or None.

        Earliest rather than latest: if two regimes both recognise a night, the
        recipient is warned once, at the first opportunity.
        """
        moments = [
            moment
            for moment in (regime_rule.rule(night) for regime_rule in self.rules)
            if moment is not None
        ]
        return min(moments) if moments else None

    def for_regime(self, regime: Regime) -> RegimeRule | None:
        """The rule bound to ``regime``, or None when the regime is unserved."""
        for regime_rule in self.rules:
            if regime_rule.regime is regime:
                return regime_rule
        return None


def equal_split(rules: Sequence[tuple[Regime, str, Rule]], total: float = 2.0) -> DecisionPolicy:
    """Build a policy that divides the total budget evenly across regimes.

    An even split is a starting allocation, not a finding. Once real lead-time
    data exists, the regime that buys more minutes should get the larger share.
    """
    share = total / len(rules) if rules else total
    return DecisionPolicy(
        rules=tuple(
            RegimeRule(regime=regime, rule_id=rule_id, rule=rule, alarm_budget_per_week=share)
            for regime, rule_id, rule in rules
        ),
        total_budget_per_week=total,
    )
