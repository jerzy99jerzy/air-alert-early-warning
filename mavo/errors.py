"""The refusal taxonomy.

There is no warning type in this codebase. A condition either refuses, with a
type a caller can match on and a harness can assert against, or it does not
exist. A warning is a refusal that nobody acted on, recorded in a place nobody
reads.

Convention adopted verbatim from `pirx`, where it was paid for in incidents.
"""

from __future__ import annotations


class MavoRefusal(Exception):
    """Base class. Every refusal in this codebase is a subclass."""

    code: str = "refusal.unspecified"


class BudgetOverrun(MavoRefusal):
    """Measured demand exceeds the recipient's total attention budget.

    Raised instead of trimming a share to fit. A policy that passes its own gate
    while overrunning the person it serves is worse than one that refuses to be
    built.
    """

    code = "refusal.budget_overrun"


class BudgetOverAllocated(MavoRefusal):
    """Allocated shares sum to more than the total they divide."""

    code = "refusal.budget_over_allocated"


class UnknownScenario(MavoRefusal):
    """A fixture scenario was requested that the generator does not define.

    Refused rather than returning an empty night, because an empty night is a
    valid input that would silently pass every downstream check.
    """

    code = "refusal.unknown_scenario"


class SourceUnavailable(MavoRefusal):
    """A source could not be read. Distinct from a source reporting nothing."""

    code = "refusal.source_unavailable"
