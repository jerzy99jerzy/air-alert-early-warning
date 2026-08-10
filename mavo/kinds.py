"""T16. The means of attack, joined to alerts rather than read off them.

F25 recorded the shape in sprint 4 and nothing acted on it for five sprints:
`kind` is modelled as an attribute of an alert, and the channel emits it as its
own message, tied to a hromada, with its own lifetime. Measured on the twenty
real messages held as fixtures: 15 carry an alert state, 4 carry a kind marker,
**0 carry both**. So on live input every alert event has `kind = UNKNOWN`, and
every regime rule tests `event.kind is MISSILE` or `is DRONE`. The regime split
that separated a working missile rule from a failing drone one could not fire at
all outside the fixture generator. The same class as F65, one field over.

This module holds the second stream and the join.

## The three decisions in here, and their labels

**Join granularity is the oblast** [inference]. Declarations arrive for
hromadas, alerts for raions and oblasts. Joining at the coarse level is the same
choice T38 made for the border predicates, and it is an inference in one
direction: a kind declared for one hromada is treated as describing the oblast
it sits in. That is generous, and it is generous in the direction that produces
*more* known regimes rather than fewer, so it must be reported as inference
wherever it reaches a reader.

**A declaration expires** [assumption, unmeasured]. A lift message ends it; a
missing lift would otherwise leave the kind attached to the oblast forever,
which is worse than unknown because it is confidently wrong at an unbounded
distance from the evidence. The default of six hours is not measured. The
distribution of declaration-to-lift intervals is computable from the corpus and
`tools/kind_coverage.py` prints it; until that number exists this one is an
assumption carrying a label, not a measurement.

**Ambiguity resolves to unknown, never to a guess.** When two kinds are active
over the same oblast at the same moment, which happens in a mixed strike, the
join leaves the alert `UNKNOWN` and counts the case. Picking the first, the
newest or the more dangerous would each be a fabrication with a rationale.
"""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from mavo.schema import KindEvent, KindState, ThreatEvent, ThreatKind

# [assumption, unmeasured] See the module docstring. Replaced by measurement,
# not by argument: `tools/kind_coverage.py` prints the interval distribution.
DEFAULT_KIND_TTL = timedelta(hours=6)


@dataclass(frozen=True, slots=True)
class JoinReport:
    """What the join did, in numbers, so it can be audited rather than trusted.

    ``carried`` and ``joined`` were one counter called ``resolved`` in the
    first version, which mixed "the message stated its own kind" with "the join
    supplied one" and let ``coverage`` take credit for regimes the join never
    touched. Quoting that figure as the join's performance would have been the
    instrument reporting its own framing as a property of the channel. Two
    counters, two questions: how many alerts have a regime at all, and how many
    of the ones that needed one did the join actually deliver.
    """

    alerts: int = 0
    carried: int = 0
    joined: int = 0
    ambiguous: int = 0
    unknown: int = 0

    @property
    def resolved(self) -> int:
        """Alerts that came out with a regime, whichever way it got there."""
        return self.carried + self.joined

    @property
    def coverage(self) -> float:
        """Share of all alerts that came out with a regime. Zero alerts is zero."""
        return self.resolved / self.alerts if self.alerts else 0.0

    @property
    def join_coverage(self) -> float:
        """The join's own performance: of the alerts that arrived without a
        kind, the share it resolved to exactly one. This is the number to quote
        when the question is whether the join works; ``coverage`` answers a
        different question and is the larger of the two whenever any message
        states its own kind."""
        needed = self.alerts - self.carried
        return self.joined / needed if needed else 0.0

    def line(self) -> str:
        return (
            f"alerts={self.alerts} carried={self.carried} joined={self.joined} "
            f"ambiguous={self.ambiguous} unknown={self.unknown} "
            f"coverage={self.coverage:.3f} join_coverage={self.join_coverage:.3f}"
        )


class KindIndex:
    """Which means of attack were declared over an oblast at a given moment.

    Built once from a stream of `KindEvent`, queried per alert. Intervals are
    half-open and closed by whichever comes first: an explicit lift, or the TTL.
    """

    def __init__(
        self, events: Iterable[KindEvent], ttl: timedelta = DEFAULT_KIND_TTL
    ) -> None:
        self.ttl = ttl
        self._intervals: dict[tuple[str, ThreatKind], list[tuple[datetime, datetime]]] = {}
        self._starts: dict[tuple[str, ThreatKind], list[datetime]] = {}

        by_key: dict[tuple[str, ThreatKind], list[KindEvent]] = {}
        for event in events:
            if not event.oblast:
                # No oblast, no join. An unplaceable declaration is dropped from
                # the index rather than applied everywhere, and it is visible in
                # the store either way.
                continue
            by_key.setdefault((event.oblast, event.kind), []).append(event)

        for key, group in by_key.items():
            group.sort(key=lambda event: event.ts_source)
            intervals: list[tuple[datetime, datetime]] = []
            open_since: datetime | None = None
            for event in group:
                if event.state is KindState.DECLARED:
                    # A re-declaration while one is open extends it rather than
                    # nesting: the source repeating itself is not a second
                    # threat.
                    if open_since is None:
                        open_since = event.ts_source
                    else:
                        intervals.append((open_since, event.ts_source))
                        open_since = event.ts_source
                elif open_since is not None:
                    intervals.append((open_since, event.ts_source))
                    open_since = None
                # A lift with nothing open is not an error and not an interval:
                # the declaration was probably before the window this store
                # holds. It is counted nowhere and invents nothing.
            if open_since is not None:
                intervals.append((open_since, open_since + ttl))
            self._intervals[key] = intervals
            self._starts[key] = [start for start, _end in intervals]

    def active(self, oblast: str, moment: datetime) -> frozenset[ThreatKind]:
        """Kinds declared over ``oblast`` and not yet lifted or expired at ``moment``."""
        found = set()
        for (key_oblast, kind), intervals in self._intervals.items():
            if key_oblast != oblast:
                continue
            starts = self._starts[(key_oblast, kind)]
            index = bisect_right(starts, moment) - 1
            if index < 0:
                continue
            start, end = intervals[index]
            # No TTL cap here, deliberately. The TTL closes a declaration whose
            # lift never arrived; it does not overrule a lift that did. A source
            # saying the threat ran for nine hours is evidence, and an
            # assumption written in this file is not, so the assumption does not
            # get to shorten it. The cap was in the first draft of this method
            # and is recorded here because it reversed that order.
            if start <= moment < end:
                found.add(kind)
        return frozenset(found)


def apply_kinds(
    alerts: Sequence[ThreatEvent], index: KindIndex
) -> tuple[tuple[ThreatEvent, ...], JoinReport]:
    """Fill in each alert's regime from the kind stream, or leave it unknown.

    The join happens here, before the rules, so the rules stay exactly as they
    are: they read `event.kind` and know nothing about how it got there. An
    alert that already carries a kind is untouched, since the message said so
    itself and a message beats an inference.
    """
    out: list[ThreatEvent] = []
    carried = joined_count = ambiguous = unknown = 0
    for alert in alerts:
        if alert.kind is not ThreatKind.UNKNOWN:
            out.append(alert)
            carried += 1
            continue
        active = index.active(alert.oblast, alert.ts_source) if alert.oblast else frozenset()
        if len(active) == 1:
            out.append(
                ThreatEvent(
                    area_id=alert.area_id,
                    state=alert.state,
                    ts_source=alert.ts_source,
                    ts_ingest=alert.ts_ingest,
                    source_id=alert.source_id,
                    kind=next(iter(active)),
                    provenance=alert.provenance,
                    raw_fields=alert.raw_fields,
                    oblast=alert.oblast,
                    role=alert.role,
                )
            )
            joined_count += 1
            continue
        if len(active) > 1:
            ambiguous += 1
        else:
            unknown += 1
        out.append(alert)
    return tuple(out), JoinReport(
        alerts=len(alerts),
        carried=carried,
        joined=joined_count,
        ambiguous=ambiguous,
        unknown=unknown,
    )
