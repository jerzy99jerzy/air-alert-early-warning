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


class UnknownScenario(MavoRefusal):
    """A fixture scenario was requested that the generator does not define.

    Refused rather than returning an empty night, because an empty night is a
    valid input that would silently pass every downstream check.
    """

    code = "refusal.unknown_scenario"


class NaiveTimestamp(MavoRefusal):
    """An event carries a timestamp without a UTC offset.

    Refused at the store boundary rather than tolerated: the store orders by
    ISO text, and lexicographic order is chronological only when every stored
    timestamp shares one offset. A naive datetime has no offset to normalize,
    so accepting it converts the ordering contract into an accident (F52).
    """

    code = "refusal.naive_timestamp"


class SourceUnavailable(MavoRefusal):
    """A source could not be read. Distinct from a source reporting nothing."""

    code = "refusal.source_unavailable"
