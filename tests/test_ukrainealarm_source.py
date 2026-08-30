"""The API adapter: snapshots turned into transitions without inventing clears.

The channel stopped publishing on 2026-08-29 at 04:55 UTC and this project had
no second pipe to ask. These tests hold the three properties that make the
replacement safe rather than merely available: a first snapshot clears nothing,
a region leaving the snapshot clears exactly once, and a failed poll clears
nothing at all.

Payload shape is taken from a live response measured on 2026-08-30, not from a
reading of the parser: `regionId`, `regionType`, `regionName`, `lastUpdate` and
a nested `activeAlerts` carrying its own `type` and `lastUpdate`.
"""

from __future__ import annotations

import json

import pytest

from mavo.areas import AreaTable
from mavo.errors import SourceUnavailable
from mavo.schema import AlertState, ThreatKind
from mavo.sources.ukrainealarm_source import UkrainealarmSource


class SequenceTransport:
    """Returns each body in turn. `StubTransport` holds one; snapshots need a
    sequence, because the whole question is what changes between two polls."""

    def __init__(self, bodies: list[str]) -> None:
        self._bodies = list(bodies)
        self.calls = 0

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
        """Return the next canned body, repeating the last one when exhausted."""
        body = self._bodies[min(self.calls, len(self._bodies) - 1)]
        self.calls += 1
        return body


LVIV = "Львівський район"
VOLODYMYR = "Володимирський район"


def _snapshot(*regions: tuple[str, str]) -> str:
    """An API body listing each `(name, type)` as one active alert."""
    return json.dumps(
        [
            {
                "regionId": str(index),
                "regionType": "District",
                "regionName": name,
                "lastUpdate": "2026-08-30T13:19:40Z",
                "activeAlerts": [
                    {
                        "regionId": str(index),
                        "regionType": "District",
                        "type": kind,
                        "lastUpdate": "2026-08-30T13:19:40Z",
                    }
                ],
            }
            for index, (name, kind) in enumerate(regions, start=1)
        ]
    )


def _source(transport: SequenceTransport) -> UkrainealarmSource:
    return UkrainealarmSource("key", areas=AreaTable.from_csv(), transport=transport)


def test_first_poll_reports_alerts_and_clears_nothing() -> None:
    """A snapshot with no predecessor cannot say what ended.

    The first poll of a process sees areas alerting and knows nothing about the
    ones that are not: their absence is unobserved, not observed-absent. Issuing
    clears here would let a restart announce all-clears for a window during
    which this process saw nothing at all.
    """
    source = _source(SequenceTransport([_snapshot((LVIV, "AIR"))]))

    events = source.poll()

    assert [event.state for event in events] == [AlertState.ACTIVE]
    assert events[0].kind is ThreatKind.MISSILE
    assert events[0].oblast == "Львівська"


def test_an_area_leaving_the_snapshot_clears_once() -> None:
    """The API stops listing an alert instead of announcing its end.

    The all-clear is therefore a difference between two snapshots, and it is
    dated from the observation rather than from the start the alert carried:
    the API never says when it ended, and dating the clear from the start would
    report it as having happened hours before anything saw it.
    """
    transport = SequenceTransport(
        [_snapshot((LVIV, "AIR")), _snapshot(), _snapshot()]
    )
    source = _source(transport)

    first = source.poll()
    second = source.poll()
    third = source.poll()

    assert [event.state for event in first] == [AlertState.ACTIVE]
    assert [event.state for event in second] == [AlertState.CLEAR]
    assert second[0].oblast == "Львівська"
    assert second[0].ts_source == second[0].ts_ingest
    assert third == ()


def test_a_failed_poll_clears_nothing() -> None:
    """A refusal is silence, and silence is never an all-clear.

    This is the property the whole project rests on, one layer down: an absence
    only counts as evidence when the observation succeeded. A malformed body
    must leave the previous snapshot standing rather than emptying the map.
    """
    transport = SequenceTransport([_snapshot((LVIV, "AIR")), "not json at all"])
    source = _source(transport)
    source.poll()

    with pytest.raises(SourceUnavailable):
        source.poll()

    assert source._previous is not None
    assert len(source._previous) == 1


def test_a_renamed_border_raion_resolves() -> None:
    """Volodymyr raion reaches the contract, by the name the register uses.

    The map keys this row on the channel's tag, which keeps the pre-2021 name,
    while the API publishes the current one. It is a border raion in Volyn, so
    an adapter that could not resolve it would be silent about one of the few
    areas this project exists to watch.
    """
    source = _source(SequenceTransport([_snapshot((VOLODYMYR, "AIR"))]))

    events = source.poll()

    assert [event.state for event in events] == [AlertState.ACTIVE]
    assert events[0].oblast == "Волинська"


def test_a_region_the_map_does_not_know_is_counted_not_dropped() -> None:
    """An unresolvable region is a finding about the map, not a silent loss."""
    source = _source(SequenceTransport([_snapshot(("Марсіанський район", "AIR"))]))

    events = source.poll()

    assert events == ()
    assert source.unresolved == ("Марсіанський район",)
