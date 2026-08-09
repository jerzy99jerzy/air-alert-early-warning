"""Run a rule over a history and score it against ground truth.

The same function is used by the backtest and, later, by the live shadow mode.
A separate backtest path would stop measuring what production does.
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from mavo.baserate import Contingency, GateVerdict, RuleAssessment, assess_rule, gate
from mavo.policy import DecisionPolicy, Regime
from mavo.rules import Rule
from mavo.schema import Provenance
from mavo.sources.fixture import Night


@dataclass(frozen=True, slots=True)
class RuleRun:
    """Everything one rule produced over one history."""

    assessment: RuleAssessment
    verdict: GateVerdict
    median_lead_time_s: float | None
    missed_nights: tuple[str, ...]

    def metrics_line(self) -> str:
        """Measurements only, with no verdict attached.

        Separate from ``summary`` because a rule inside a policy is gated against
        its allocated share of the budget, not against the default. Printing the
        default verdict beside the allocated one put two contradictory answers on
        the same rule (F5).
        """
        lead = (
            "unknown"
            if self.median_lead_time_s is None
            else f"{self.median_lead_time_s / 60.0:.1f} min"
        )
        return f"{self.assessment.summary()} lead={lead}"

    def summary(self) -> str:
        """Two lines: what was measured, then whether it may raise an alarm."""
        return f"{self.metrics_line()}\n  {self.verdict}"


def run_rule(rule_id: str, rule: Rule, nights: Sequence[Night]) -> RuleRun:
    """Score ``rule`` over ``nights``.

    Lead time is measured only on true positives: the time a rule would have
    bought on a night that mattered.
    """
    a = b = c = d = 0
    lead_times: list[float] = []
    missed: list[str] = []

    for night in nights:
        fired_at = rule(night)
        if fired_at is not None and night.had_crossing:
            a += 1
            lead = night.lead_time_s(fired_at)
            if lead is not None:
                lead_times.append(lead)
        elif fired_at is not None:
            b += 1
        elif night.had_crossing:
            c += 1
            missed.append(night.start.isoformat())
        else:
            d += 1

    table = Contingency(a=a, b=b, c=c, d=d)
    weeks = len(nights) / 7.0
    assessment = assess_rule(rule_id, table, weeks, provenance=Provenance.REPORTED)
    return RuleRun(
        assessment=assessment,
        verdict=gate(assessment),
        median_lead_time_s=statistics.median(lead_times) if lead_times else None,
        missed_nights=tuple(missed),
    )


@dataclass(frozen=True, slots=True)
class PolicyRun:
    """A policy scored as a whole, plus each regime scored on its own events."""

    per_regime: tuple[tuple[str, RuleRun, GateVerdict], ...]
    combined: RuleRun
    combined_verdict: GateVerdict
    unserved: tuple[tuple[str, int], ...]

    @property
    def has_coverage_gap(self) -> bool:
        """Whether any crossing kind is served by no regime at all."""
        return any(count > 0 for _, count in self.unserved)

    def summary(self) -> str:
        """Per-regime lines, then the combined line that actually binds."""
        lines: list[str] = []
        for label, run, verdict in self.per_regime:
            lines.append(f"{label}: {run.metrics_line()}")
            lines.append(f"  {verdict}")
        lines.append(f"POLICY combined: {self.combined.metrics_line()}")
        lines.append(f"  {self.combined_verdict}")
        for kind, count in self.unserved:
            if count:
                lines.append(
                    f"  COVERAGE GAP: {count} {kind} crossings served by no regime. "
                    f"Recall above is scoped to served regimes and says nothing about these."
                )
        return "\n".join(lines)


def run_regime(
    rule_id: str,
    rule: Rule,
    nights: Sequence[Night],
    regime: Regime,
) -> RuleRun:
    """Score ``rule`` against only the crossings its regime is accountable for.

    Nights that ended in a crossing of the *other* kind are excluded from the
    table rather than counted as negatives. A missile rule that stays silent on a
    drone night has not made an error; it has declined a job that is not its own.
    Excluding them costs sample size and is still the honest accounting.
    """
    relevant = [
        night
        for night in nights
        if not night.had_crossing or night.crossing_kind is regime.threat_kind
    ]
    return run_rule(rule_id, rule, relevant)


def run_policy(policy: DecisionPolicy, nights: Sequence[Night]) -> PolicyRun:
    """Score every regime rule on its own events, then the policy as a whole.

    The combined line is still computed separately rather than summed from the
    parts. It bound differently before 0.8.0.0, when each part carried a share of
    an attention budget; now it answers a plainer question, which is whether the
    policy taken as one predicate beats the calendar (D-014).
    """
    per_regime: list[tuple[str, RuleRun, GateVerdict]] = []
    for regime_rule in policy.rules:
        run = run_regime(regime_rule.rule_id, regime_rule.rule, nights, regime_rule.regime)
        per_regime.append(
            (
                f"{regime_rule.regime.value}/{regime_rule.rule_id}",
                run,
                gate(run.assessment),
            )
        )

    # Combined recall is scoped to the regimes the policy actually serves. A
    # policy that covers one regime should not be scored as if it had failed at
    # a job it never claimed, but the crossings it does not serve must be counted
    # and printed, because an unserved kind silently folded into a recall figure
    # is the same defect as unknown resolving to clear.
    served = {regime_rule.regime.threat_kind for regime_rule in policy.rules}
    in_scope = [
        night for night in nights if not night.had_crossing or night.crossing_kind in served
    ]
    unserved: dict[str, int] = {}
    for night in nights:
        if night.had_crossing and night.crossing_kind not in served:
            key = night.crossing_kind.value
            unserved[key] = unserved.get(key, 0) + 1

    combined = run_rule("policy", policy.fires_at, in_scope)
    return PolicyRun(
        per_regime=tuple(per_regime),
        combined=combined,
        combined_verdict=gate(combined.assessment),
        unserved=tuple(sorted(unserved.items())),
    )
