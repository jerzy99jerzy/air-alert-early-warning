"""Regime split: one rule per timing regime.

Sprint 2 measured a recall of 0.47 for the missile rule and recorded it as a
failure. Sprint 3 probed what that average hid: 7 of 7 on missile nights and 0 of
8 on drone nights. The rule was not mediocre, it was perfect at one job and blind
to another, and a single global threshold cannot express that.

**The shared alarm budget was removed at 0.8.0.0** (D-014). Until then a regime
rule carried an allocated share of two alarms per week and the policy refused
construction when the shares exceeded the total. The number was an assumption
about recipient behaviour that nobody had measured, and the arithmetic built on
it inherited that label all the way down. What remains is the part that was
always a measurement: each rule's firing rate is computed and reported, and the
gate refuses a rule whose firing carries no information rather than one that
fires often.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

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
    """A rule bound to the timing regime it is accountable for."""

    regime: Regime
    rule_id: str
    rule: Rule


@dataclass(frozen=True, slots=True)
class DecisionPolicy:
    """The full alarm-tier decision: one rule per regime.

    Construction no longer refuses anything. The refusal it used to carry was a
    budget over-allocation check, and with the budget gone there is nothing left
    for it to be right about (D-014).
    """

    rules: tuple[RegimeRule, ...]

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


def policy_of(rules: Sequence[tuple[Regime, str, Rule]]) -> DecisionPolicy:
    """Build a policy from regime, id and rule triples.

    Replaces ``equal_split``, whose whole job was dividing an attention budget
    that no longer exists. The name changed rather than the body being emptied,
    because a function called ``equal_split`` that splits nothing is a comment
    that lies (D-014).
    """
    return DecisionPolicy(
        rules=tuple(
            RegimeRule(regime=regime, rule_id=rule_id, rule=rule)
            for regime, rule_id, rule in rules
        )
    )
