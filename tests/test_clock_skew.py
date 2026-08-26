"""F120: one timestamp ahead of our clock disables the staleness machine.

`Report.staleness_s` subtracts the newest source timestamp from `as_of` and
`feed_state` compares the result against `valid_for_s`. A negative age passes
that comparison, so a single event stamped in the future pins the feed to `ok`
for as long as it is the newest row in the store. Measured before this file
existed, on a store whose real traffic stopped seven days earlier and which
carried one event stamped a year ahead: `state: "ok"`,
`observation_age_s: -31536000`, an empty `events` block, and
`source_last_message_at` in 2027. A consumer reading that renders a calm night,
which is the founding defect of this repository reached through a clock rather
than through a fold.

**The realistic path is not a hostile channel, it is our own host.** The
timestamp comes from the page's `<time datetime=...>` attribute, so any
backward drift of the collector's clock relative to the source makes *every*
event arrive in the future and makes DEGRADED unreachable. The comment in
`trailing_counts` already records that T40 measured the two clocks disagreeing
**in both directions**; the fold clamps for durations and the freshness basis
does not, so one module treats the skew as a hazard and the other treats it as
evidence.

**Why the suite never went red on this.** Every fixture in `test_sprint10.py`
and `test_trailing_duration.py` stamps its events at or before `as_of`, because
that is what a well-behaved source does. A fixture drawn from the well-behaved
case cannot see a guard that only fires outside it, which is the fixture class
this project has paid for twice (F76, F114).

**What is deliberately not asserted here.** The *content* fold is untouched: an
area whose newest row is a future event still publishes that row's state. That
is a separate question from whether the pipeline may call itself fresh, and
mixing them would make this file assert two things and pin neither.

Each test names the mutation it was verified against.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from mavo.areas import AreaTable
from mavo.report import (
    SKEW_TOLERANCE_S,
    FeedState,
    compose,
    to_contract,
)
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind

NOW = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
VALID_FOR_S = 600

#: Two raions of one oblast, the same pair the duration regressions use. The
#: area is incidental here; what matters is the stamp on the row.
SAMBIR = "UA46080000000017237"
YAVORIV = "UA46140000000036328"


def _table() -> AreaTable:
    return AreaTable.from_csv()


def _event(area_id: str, state: AlertState, ts: datetime) -> ThreatEvent:
    return ThreatEvent(
        area_id=area_id,
        state=state,
        ts_source=ts,
        ts_ingest=ts,
        source_id="test",
        kind=ThreatKind.UNKNOWN,
        provenance=Provenance.REPORTED,
        oblast="lviv",
    )


def test_a_future_stamped_event_does_not_refresh_a_dead_feed() -> None:
    """The measured case, inverted.

    Verified red against the tree at 0.39.1.0, where this composed as `ok` with
    an age of minus one year. Mutation: remove the horizon filter in `compose`
    and this returns to `ok`.
    """
    events = [
        _event(SAMBIR, AlertState.ACTIVE, NOW - timedelta(days=7)),
        _event(YAVORIV, AlertState.ACTIVE, NOW + timedelta(days=365)),
    ]
    report = compose(events, as_of=NOW, table=_table(), valid_for_s=VALID_FOR_S)
    assert report.feed_state is FeedState.DEGRADED, (
        "a store whose only recent row is stamped in the future has not been "
        "refreshed; the age of the newest row we can date is seven days"
    )
    assert report.staleness_s == 7 * 24 * 3600


def test_no_negative_age_crosses_the_contract() -> None:
    """`observation_age_s` is read by a consumer that compares it to a threshold.

    A negative number passes every freshness comparison a reader could write,
    so the field must not be able to carry one. `null` stays the unknown value
    and is unaffected. Mutation: drop the floor in `staleness_s`.
    """
    events = [_event(SAMBIR, AlertState.ACTIVE, NOW + timedelta(seconds=30))]
    payload = to_contract(compose(events, as_of=NOW, table=_table()))
    age = payload["observation_age_s"]
    assert age is not None
    assert isinstance(age, float)
    assert age >= 0.0


def test_a_small_forward_skew_is_tolerated_rather_than_called_blind() -> None:
    """The guard must not fire on the ordinary case it will meet every day.

    A collector a few seconds behind the source stamps every row in the future.
    Refusing those would turn a healthy pipeline blind, which is a louder
    failure than the one being fixed. Mutation: set the tolerance to zero and
    this goes blind.
    """
    events = [
        _event(SAMBIR, AlertState.ACTIVE, NOW + timedelta(seconds=SKEW_TOLERANCE_S - 30))
    ]
    report = compose(events, as_of=NOW, table=_table(), valid_for_s=VALID_FOR_S)
    assert report.feed_state is FeedState.OK


def test_a_feed_entirely_beyond_the_tolerance_is_blind_rather_than_fresh() -> None:
    """No datable observation is not a fresh observation.

    When every row sits past the horizon there is nothing to measure freshness
    against, and `blind` is the state that says so. Rendering the newest of
    them as the current moment would be the same defect with a smaller number.
    Mutation: fall back to the raw maximum and this reads `ok`.
    """
    ahead = timedelta(seconds=SKEW_TOLERANCE_S + 60)
    events = [
        _event(SAMBIR, AlertState.ACTIVE, NOW + ahead),
        _event(YAVORIV, AlertState.ACTIVE, NOW + ahead + timedelta(minutes=5)),
    ]
    report = compose(events, as_of=NOW, table=_table(), valid_for_s=VALID_FOR_S)
    assert report.feed_state is FeedState.BLIND
    assert report.staleness_s is None, "unknown, never zero"


def test_the_skew_is_published_rather_than_absorbed() -> None:
    """A clamp that leaves no trace is a measurement thrown away.

    The whole reason the old behaviour was invisible is that nothing recorded
    the disagreement between the two clocks. `clock_skew_s` is that record, and
    it is the field an operator greps when the panel and the channel disagree.
    Mutation: publish zero unconditionally.
    """
    events = [_event(SAMBIR, AlertState.ACTIVE, NOW + timedelta(seconds=45))]
    payload = to_contract(compose(events, as_of=NOW, table=_table()))
    assert payload["clock_skew_s"] == 45.0
    assert payload["source_last_message_at"] == (
        (NOW + timedelta(seconds=45)).isoformat(timespec="seconds")
    ), "the raw stamp is what the source said and is still reported as such"


def test_an_ordinary_report_publishes_a_zero_skew_rather_than_omitting_it() -> None:
    """Always present, empty or not.

    An absent key and a zero read alike to a careless consumer, and the common
    case is zero. The same rule the `events` block follows.
    """
    events = [_event(SAMBIR, AlertState.ACTIVE, NOW - timedelta(minutes=1))]
    payload = to_contract(compose(events, as_of=NOW, table=_table()))
    assert payload["clock_skew_s"] == 0.0


def test_the_staleness_basis_and_the_event_window_agree_about_the_future() -> None:
    """One payload, one reading of a skewed stamp.

    `event_window` has always excluded events stamped after `as_of`, so before
    this change a future row was absent from `events[]` and simultaneously the
    thing making `state` say `ok`: two answers about one row, one line apart in
    the same file. Mutation: let the window keep future events and this pair
    disagrees again.
    """
    events = [
        _event(SAMBIR, AlertState.ACTIVE, NOW - timedelta(minutes=3)),
        _event(YAVORIV, AlertState.ACTIVE, NOW + timedelta(days=2)),
    ]
    payload = to_contract(compose(events, as_of=NOW, table=_table()))
    window = payload["events"]
    assert isinstance(window, dict)
    items = window["items"]
    assert isinstance(items, list)
    assert [item["area_id"] for item in items] == [SAMBIR], (
        "the future row is outside the window, and the state must not rest on it"
    )
    assert payload["state"] == "ok"
    assert payload["observation_age_s"] == 180.0
