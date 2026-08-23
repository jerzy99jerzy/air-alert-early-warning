"""F114/F115: the trailing count collapses under overlap, the duration does not.

`trailing_counts` opens an episode when an oblast goes from no raion under
alert to at least one, and closes it only on an affirmative all-clear of the
last one. Under sustained attack the raions overlap and the oblast never falls
wholly quiet, so a week of alerts counts as one. Measured before this file
existed: forty single-raion alerts render as 40 when spaced and as 1 when
overlapping, and one raion whose all-clear never arrives erases nineteen
episodes out of twenty.

The docstrings said of that rule that "the count errs in the direction that
does not understate". That is true of the alert *state* and false of the
*count*, and the count is the number a reader sees. F115 is the sentence; F114
is the behaviour.

**Why the existing suite never went red on this.** `trailing_counts`' own
docstring records of F76 that "the regression that should have caught it used
one raion, so the mutation had nothing to bite". Every fixture below uses at
least two raions of one oblast, because a single-raion fixture is blind to
every property in this file by construction.

Each test names the mutation it was verified against.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from mavo.areas import AreaTable
from mavo.report import trailing_areas, trailing_counts
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind

NOW = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)
WINDOW_S = 7 * 24 * 3600

#: Two raions of one oblast. The pair is the point: one raion cannot express
#: overlap, and overlap is the whole subject.
SAMBIR = "UA46080000000017237"
YAVORIV = "UA46140000000036328"
OBLAST = "lviv"


def _table() -> AreaTable:
    return AreaTable.from_csv()


def _ev(code: str, state: AlertState, minutes_ago: float) -> ThreatEvent:
    ts = NOW - timedelta(minutes=minutes_ago)
    return ThreatEvent(
        area_id=code,
        state=state,
        ts_source=ts,
        ts_ingest=ts,
        source_id="test",
        kind=ThreatKind.UNKNOWN,
        provenance=Provenance.REPORTED,
    )


def _oblast(events: list[ThreatEvent], *, days: int = 7):
    rows = {r.slug: r for r in trailing_counts(
        events, as_of=NOW, days=days, table=_table())}
    return rows.get(OBLAST)


def test_one_unclosed_raion_erases_the_count_and_not_the_duration() -> None:
    """The Kharkiv shape, at two raions instead of eight.

    Ten separate alerts on one raion, each cleanly cleared. Then a second
    raion goes active and never receives an all-clear. The oblast's episode
    count falls from ten to one, because it never again goes from empty to
    non-empty, and *that is the defect*: the oblast became strictly more
    dangerous and its number went down.

    `alert_seconds` moves the other way, which is the whole reason it exists.

    Mutation: drop the `span_since` accumulation in the closing branch of
    `trailing_counts`, so the duration stops summing closed stretches.
    """
    spaced: list[ThreatEvent] = []
    minutes = WINDOW_S / 60 - 60
    for _ in range(10):
        spaced.append(_ev(SAMBIR, AlertState.ACTIVE, minutes))
        spaced.append(_ev(SAMBIR, AlertState.CLEAR, minutes - 120))
        minutes -= 600
    clean = _oblast(spaced)
    assert clean is not None
    assert clean.alerts_count == 10
    assert clean.open_at_as_of is False

    # The same ten alerts, plus one raion that never clears.
    pinned = [*spaced, _ev(YAVORIV, AlertState.ACTIVE, WINDOW_S / 60 - 30)]
    worse = _oblast(pinned)
    assert worse is not None

    assert worse.alerts_count < clean.alerts_count, (
        "the count is expected to collapse; if this ever stops being true the "
        "defect was fixed at the counter and this file needs rewriting"
    )
    assert worse.alert_seconds > clean.alert_seconds, (
        "an oblast under alert for the whole window must not report less time "
        "than one under ten short alerts"
    )
    assert worse.open_at_as_of is True


def test_the_oblast_duration_is_a_union_and_not_a_sum() -> None:
    """Two raions under alert for the same hour give the oblast one hour.

    Summing per-raion time would reproduce F76 in the new field: an oblast
    with more raions would report more hours for the same attack, so the
    quantity would measure subdivision again, wearing different clothes.

    Mutation: in `trailing_counts`, accumulate on every clear rather than only
    when `running` empties.
    """
    both = [
        _ev(SAMBIR, AlertState.ACTIVE, 300),
        _ev(YAVORIV, AlertState.ACTIVE, 300),
        _ev(SAMBIR, AlertState.CLEAR, 240),
        _ev(YAVORIV, AlertState.CLEAR, 240),
    ]
    row = _oblast(both)
    assert row is not None
    assert row.alert_seconds == 3600, row.alert_seconds

    areas = {a.code: a for a in trailing_areas(
        both, as_of=NOW, days=7, table=_table())}
    assert areas[SAMBIR].alert_seconds == 3600
    assert areas[YAVORIV].alert_seconds == 3600
    assert (areas[SAMBIR].alert_seconds + areas[YAVORIV].alert_seconds
            != row.alert_seconds), (
        "the per-area figures must not sum to the oblast figure, and a test "
        "that let them would be blessing the F76 arithmetic"
    )


def test_a_stretch_older_than_the_window_is_clipped_to_the_window() -> None:
    """An alert running for thirty days reports seven days, not thirty.

    The count already handles this (F85): the stretch is counted once as it
    crosses the cutoff. The duration has to be clipped at the same edge, or a
    share of the window would exceed one and the shading scale would have no
    ceiling.

    Mutation: seed `span_since` from the event's own timestamp rather than
    from `cutoff` in the pre-window pass.
    """
    long_run = [_ev(SAMBIR, AlertState.ACTIVE, 30 * 24 * 60)]
    row = _oblast(long_run)
    assert row is not None
    assert row.alerts_count == 1
    assert row.alert_seconds == WINDOW_S, row.alert_seconds
    assert row.open_at_as_of is True

    area = next(a for a in trailing_areas(
        long_run, as_of=NOW, days=7, table=_table()) if a.code == SAMBIR)
    assert area.alert_seconds == WINDOW_S
    assert area.open_at_as_of is True
    assert area.last_active_at < NOW - timedelta(days=7), (
        "last_active_at keeps the real opening time; only the duration is "
        "clipped, because reporting the cutoff there would invent a "
        "transition that never happened"
    )


def test_time_stamped_after_the_picture_was_composed_is_not_counted() -> None:
    """The source's clock is not ours, and T40 measured it disagreeing.

    A negative lag is a finding about the measurement rather than an outlier
    to tidy away, but no arithmetic may publish minutes that had not happened
    when the picture was composed.

    **The fixture has to be a closed pair to say anything.** A lone future
    `ACTIVE` is absorbed by the `max(0.0, ...)` guard whichever way the clamp
    goes, so a test built on one would pass against both implementations and
    prove nothing - which is the fixture defect this repository has logged six
    times. A future declaration *and* its future all-clear is the case where
    the two implementations differ.

    Mutation: `stamp = min(event.ts_source, as_of)` -> `stamp = event.ts_source`.
    """
    ahead = [
        _ev(SAMBIR, AlertState.ACTIVE, -600),  # ten hours after `as_of`
        _ev(SAMBIR, AlertState.CLEAR, -720),   # twelve hours after `as_of`
    ]
    row = _oblast(ahead)
    assert row is not None
    assert row.alert_seconds == 0, (
        "two hours that had not happened yet were published as observed"
    )

    # And the mixed case: an alert that opened for real and whose all-clear
    # carries a clock ahead of ours is counted only up to `as_of`.
    mixed = [
        _ev(SAMBIR, AlertState.ACTIVE, 60),
        _ev(SAMBIR, AlertState.CLEAR, -600),
    ]
    row = _oblast(mixed)
    assert row is not None
    assert row.alert_seconds == 3600, row.alert_seconds


def test_an_instantaneous_alert_reports_zero_seconds_and_one_episode() -> None:
    """A declaration and its all-clear at the same stamp is a real condition.

    It must not become a negative duration, and it must not disappear from the
    count: the source said something happened.

    Mutation: replace `max(0.0, ...)` with the raw subtraction and reverse the
    operand order.
    """
    flat = [
        _ev(SAMBIR, AlertState.ACTIVE, 100),
        _ev(SAMBIR, AlertState.CLEAR, 100),
    ]
    row = _oblast(flat)
    assert row is not None
    assert row.alerts_count == 1
    assert row.alert_seconds == 0
    assert row.open_at_as_of is False


def test_the_duration_travels_in_both_contract_files() -> None:
    """A quantity computed and not published is a quantity nobody can read.

    `state.json` carries the oblast figure the map shades by; `feed.json`
    carries the per-area figure the panel reads. Both carry the openness flag,
    because a growing number rendered as a total is the collapse this work
    exists to remove, one layer out.

    Mutation: delete `alert_seconds` from either `as_item` or the `recent_7d`
    comprehension.
    """
    from mavo.report import compose, to_contract, to_feed

    events = [
        _ev(SAMBIR, AlertState.ACTIVE, 300),
        _ev(SAMBIR, AlertState.CLEAR, 240),
        _ev(YAVORIV, AlertState.ACTIVE, 60),
    ]
    report = compose(events, as_of=NOW, table=_table())
    entry = next(e for e in to_contract(report)["recent_7d"]
                 if e["oblast"] == OBLAST)
    assert isinstance(entry["alert_seconds"], int)
    assert entry["alert_seconds"] > 0
    assert entry["still_under_alert"] is True
    assert entry["alert_seconds"] <= WINDOW_S

    areas = to_feed(report)["recent_7d_areas"]
    assert areas, "the per-area block must not be empty on this fixture"
    for item in areas:
        assert isinstance(item["alert_seconds"], int)
        assert isinstance(item["still_under_alert"], bool)
        assert 0 <= item["alert_seconds"] <= WINDOW_S
