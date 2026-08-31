"""0.49.0.0: the trailing counters learn the unit of alarm, and two debts pay.

The trailing tests were run against the unpatched 0.48.0.1 tree first and
asserted the failure exactly: `open_at_as_of=False`, `last_ended` set, and
18,900 seconds missing, all produced by the clear of one kind while another
ran (F138). The source tests exercise F135 and F136 against payloads shaped
like the API's own, via the injected transport the source's suite already
uses.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from mavo.areas import AreaTable
from mavo.report import trailing_areas, trailing_counts
from mavo.schema import AlertState, AreaRole, Provenance, ThreatEvent, ThreatKind
from mavo.sources.ukrainealarm_source import UkrainealarmSource
from tools.precision_lint import FIGURE

NOON = datetime(2026, 8, 30, 12, 0, 0, tzinfo=UTC)


def table_and_area() -> tuple[AreaTable, str]:
    table = AreaTable.from_csv()
    code = next(a.code for a in table._rows.values() if a.oblast)
    return table, code


def ev(code: str, state: AlertState, kind: ThreatKind, ts: datetime) -> ThreatEvent:
    return ThreatEvent(code, state, ts, ts, "ukrainealarm", kind=kind,
                       provenance=Provenance.REPORTED, raw_fields={},
                       oblast="x", role=AreaRole.SUBJECT)


# -- F138: the episode counters --------------------------------------------


def test_a_clear_of_one_kind_does_not_close_the_oblast_episode() -> None:
    """The measured shape: chronic artillery under an air alert that ends."""
    table, code = table_and_area()
    opened = NOON - timedelta(days=2)
    log = [ev(code, AlertState.ACTIVE, ThreatKind.ARTILLERY, opened),
           ev(code, AlertState.ACTIVE, ThreatKind.UNKNOWN, NOON),
           ev(code, AlertState.CLEAR, ThreatKind.UNKNOWN, NOON + timedelta(minutes=45))]
    as_of = NOON + timedelta(hours=6)
    (oblast,) = trailing_counts(log, as_of=as_of, table=table)
    assert oblast.open_at_as_of is True
    assert oblast.last_alert_ended_at is None
    assert oblast.alert_seconds == int((as_of - opened).total_seconds())


def test_a_clear_of_one_kind_does_not_close_the_area_episode() -> None:
    table, code = table_and_area()
    opened = NOON - timedelta(days=2)
    log = [ev(code, AlertState.ACTIVE, ThreatKind.ARTILLERY, opened),
           ev(code, AlertState.ACTIVE, ThreatKind.UNKNOWN, NOON),
           ev(code, AlertState.CLEAR, ThreatKind.UNKNOWN, NOON + timedelta(minutes=45))]
    as_of = NOON + timedelta(hours=6)
    (area,) = trailing_areas(log, as_of=as_of, table=table)
    assert area.open_at_as_of is True
    assert area.last_ended_at is None
    assert area.alert_seconds == int((as_of - opened).total_seconds())
    assert area.episodes == 1


def test_the_last_kind_clearing_closes_the_episode() -> None:
    """One episode, both directions: opened once, closed once, clock right."""
    table, code = table_and_area()
    opened = NOON - timedelta(hours=4)
    ended = NOON + timedelta(hours=1)
    log = [ev(code, AlertState.ACTIVE, ThreatKind.ARTILLERY, opened),
           ev(code, AlertState.ACTIVE, ThreatKind.UNKNOWN, NOON),
           ev(code, AlertState.CLEAR, ThreatKind.UNKNOWN, NOON + timedelta(minutes=30)),
           ev(code, AlertState.CLEAR, ThreatKind.ARTILLERY, ended)]
    as_of = NOON + timedelta(hours=6)
    (oblast,) = trailing_counts(log, as_of=as_of, table=table)
    assert oblast.open_at_as_of is False
    assert oblast.last_alert_ended_at == ended
    assert oblast.alerts_count == 1
    assert oblast.alert_seconds == int((ended - opened).total_seconds())
    (area,) = trailing_areas(log, as_of=as_of, table=table)
    assert area.last_ended_at == ended
    assert area.episodes == 1


def test_single_kind_episodes_are_byte_identical_to_before() -> None:
    """The healthy path may not move: one kind, two episodes, same numbers."""
    table, code = table_and_area()
    log = [ev(code, AlertState.ACTIVE, ThreatKind.MISSILE, NOON),
           ev(code, AlertState.CLEAR, ThreatKind.MISSILE, NOON + timedelta(hours=1)),
           ev(code, AlertState.ACTIVE, ThreatKind.MISSILE, NOON + timedelta(hours=3)),
           ev(code, AlertState.CLEAR, ThreatKind.MISSILE, NOON + timedelta(hours=4))]
    as_of = NOON + timedelta(hours=6)
    (oblast,) = trailing_counts(log, as_of=as_of, table=table)
    assert oblast.alerts_count == 2
    assert oblast.alert_seconds == 7200
    assert oblast.open_at_as_of is False
    (area,) = trailing_areas(log, as_of=as_of, table=table)
    assert area.episodes == 2
    assert area.alert_seconds == 7200


def test_a_pre_window_kind_survives_a_clear_inside_the_window() -> None:
    """The seeding loop carries the same repair as the main one."""
    table, code = table_and_area()
    days = 7
    as_of = NOON
    log = [ev(code, AlertState.ACTIVE, ThreatKind.ARTILLERY, NOON - timedelta(days=9)),
           ev(code, AlertState.ACTIVE, ThreatKind.UNKNOWN, NOON - timedelta(days=8)),
           ev(code, AlertState.CLEAR, ThreatKind.UNKNOWN, NOON - timedelta(hours=2))]
    (oblast,) = trailing_counts(log, as_of=as_of, days=days, table=table)
    assert oblast.open_at_as_of is True
    assert oblast.alert_seconds == int(timedelta(days=days).total_seconds())


# -- F135 and F136: the source's honesty about what it could not read ------


class OneBody:
    """The injected transport, per the source suite's own convention."""

    def __init__(self, body: str) -> None:
        self._body = body

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
        return self._body


def poll_with(body: list[dict[str, object]]) -> UkrainealarmSource:
    return UkrainealarmSource(
        "key", areas=AreaTable.from_csv(), transport=OneBody(json.dumps(body))
    )


def region(name: str, alert_type: str, started: str | None) -> dict[str, object]:
    alert: dict[str, object] = {"regionId": "1", "regionType": "District",
                                "type": alert_type}
    if started is not None:
        alert["lastUpdate"] = started
    return {"regionId": "1", "regionType": "District", "regionName": name,
            "lastUpdate": "2026-08-30T13:19:40Z", "activeAlerts": [alert]}


LVIV = "Львівський район"


def test_a_sentinel_alert_on_a_named_region_is_counted_and_stored() -> None:
    """F135. A record the parser marks `unparsed` is not the absence of an
    alert: it lands under UNKNOWN, dated by the observation with the F136
    mark, and the recap counts it."""
    body = region(LVIV, "ARTILLERY", "2026-08-30T11:00:00Z")
    body["activeAlerts"] = ["not-a-dict"]
    source = poll_with([body])
    events = source.poll()
    assert source.unparsed == (LVIV,)
    assert len(events) == 1
    assert events[0].state is AlertState.ACTIVE
    assert events[0].kind is ThreatKind.UNKNOWN
    assert events[0].raw_fields.get("ts_source_origin") == "observed"


def test_an_unreadable_region_is_counted_and_lands_nowhere() -> None:
    source = poll_with(["garbage"])
    events = source.poll()
    assert source.unparsed == ("<unreadable region>",)
    assert events == ()


def test_a_missing_stamp_is_substituted_with_a_mark() -> None:
    """F136. The read time stands in, and the row says so."""
    source = poll_with([region(LVIV, "ARTILLERY", None)])
    before = datetime.now(UTC)
    (event,) = source.poll()
    assert event.raw_fields.get("ts_source_origin") == "observed"
    assert event.ts_source >= before


def test_a_carried_stamp_is_not_marked() -> None:
    source = poll_with([region(LVIV, "ARTILLERY", "2026-08-30T11:00:00Z")])
    (event,) = source.poll()
    assert "ts_source_origin" not in event.raw_fields


# -- T77: the figure counter and the interpreter tokens --------------------


def test_interpreter_tokens_are_not_figures() -> None:
    assert FIGURE.findall("appeared on 3.14 and vanished on 3.11") == []


def test_measurements_that_share_the_shape_still_count() -> None:
    assert FIGURE.findall("a genuine 7.84 measurement") == ["7.84"]
    assert FIGURE.findall("a future 3.140 is not 3.14") == ["3.140"]
    assert FIGURE.findall("13.14 is not an interpreter") == ["13.14"]
