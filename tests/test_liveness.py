"""Pipe liveness, checked against the four episodes the production table holds.

Every fixture below is a real sequence measured on `vm-mavo` on 2026-09-08 and
named by its date, because a threshold justified by a distribution has to be
tested against the distribution and not against numbers chosen to pass.
"""


from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from mavo.liveness import (
    PRODUCTION_FEEDS,
    EventStamps,
    FeedSpec,
    PipeState,
    as_block,
    liveness,
    measure_feed,
    refusal_class,
)
from mavo.store import EventStore

API = FeedSpec(feed="ukrainealarm", source_id="ukrainealarm",
               role="primary", cadence_s=120.0)
CHANNEL = FeedSpec(feed="channel", source_id="telegram",
                   role="watchman", cadence_s=30.0)


@pytest.fixture()
def store(tmp_path):
    return EventStore(tmp_path / "events")


def poll(store: EventStore, feed: str, at: datetime, outcome: str = "read",
         detail: str | None = None) -> None:
    """One row in `feed_attempts`, through the public recorders."""
    if outcome == "read":
        store.record_read(feed, "https://example.invalid/", at, 1, 0)
    else:
        store.record_refusal(feed, "https://example.invalid/", at,
                             detail or "unreachable")


def run(store: EventStore, feed: str, start: datetime, count: int,
        cadence_s: float, outcome: str = "read",
        detail: str | None = None) -> datetime:
    """`count` polls at `cadence_s` spacing. Returns the last stamp used."""
    at = start
    for _ in range(count):
        poll(store, feed, at, outcome, detail)
        at = at + timedelta(seconds=cadence_s)
    return at - timedelta(seconds=cadence_s)


def test_a_feed_with_no_row_is_unknown_and_not_stalled(store):
    """Never switched on is not the same fact as stopped, and must not read so.

    `mavo-rso` has no unit on the host, so the `rso` feed exists in the CLI and
    has never been collected. Reporting it as `stalled` would announce the
    failure of something nobody started.
    """
    now = datetime(2026, 9, 8, 15, 0, tzinfo=UTC)
    row = measure_feed(store, API, as_of=now)
    assert row.state is PipeState.UNKNOWN
    assert row.last_attempt_at is None
    assert row.read_age_s is None
    assert row.attempt_age_s is None


def test_a_healthy_pipe_is_delivering(store):
    now = datetime(2026, 9, 8, 15, 0, tzinfo=UTC)
    run(store, "ukrainealarm", now - timedelta(seconds=600), 5, 120.0)
    row = measure_feed(store, API, as_of=now)
    assert row.state is PipeState.DELIVERING
    assert row.read_age_s == pytest.approx(120.0)


def test_2026_09_07_the_stopped_timer_reads_stalled(store):
    """The 28 h 30 min the page did not announce.

    Two 401s at 08:20:49 and 08:22:50, then the timer stopped at 08:24 and no
    row of any outcome existed until 12:55 the next day. Nothing was being
    emitted, so no external observer could have caught it either.
    """
    last = datetime(2026, 9, 7, 8, 18, 48, tzinfo=UTC)
    run(store, "ukrainealarm", last - timedelta(seconds=600), 6, 120.0)
    poll(store, "ukrainealarm", datetime(2026, 9, 7, 8, 20, 49, tzinfo=UTC),
         "refused", "HTTP Error 401: Unauthorized")
    poll(store, "ukrainealarm", datetime(2026, 9, 7, 8, 22, 50, tzinfo=UTC),
         "refused", "HTTP Error 401: Unauthorized")
    a_day_later = datetime(2026, 9, 8, 12, 55, tzinfo=UTC)
    row = measure_feed(store, API, as_of=a_day_later)
    assert row.state is PipeState.STALLED
    assert row.attempt_age_s > 100_000


def test_2026_09_07_two_refusals_are_caught_before_the_timer_was_stopped(store):
    """`refusing` at 08:22:50, ninety seconds before the operator intervened.

    This is the detection the deployed page did not have. The threshold is one
    constant - two cadences without a read - and it fires here on the second
    consecutive refusal without any second rule about counting them.
    """
    run(store, "ukrainealarm", datetime(2026, 9, 7, 8, 8, 48, tzinfo=UTC),
        6, 120.0)
    poll(store, "ukrainealarm", datetime(2026, 9, 7, 8, 20, 49, tzinfo=UTC),
         "refused", "HTTP Error 401: Unauthorized")
    poll(store, "ukrainealarm", datetime(2026, 9, 7, 8, 22, 50, tzinfo=UTC),
         "refused", "HTTP Error 401: Unauthorized")
    row = measure_feed(
        store, API, as_of=datetime(2026, 9, 7, 8, 22, 51, tzinfo=UTC)
    )
    assert row.state is PipeState.REFUSING
    assert row.refusal_status == 401
    assert row.as_item()["refusal_class"] == "rejected"


def test_2026_09_06_a_single_502_does_not_raise_anything(store):
    """One isolated refusal between successful polls is weather, not an outage.

    Measured baseline: nine refusals in 1 296 attempts over 72 h, two of them
    isolated. A rule that fired on one refusal would have raised twice in three
    days for nothing.
    """
    run(store, "ukrainealarm", datetime(2026, 9, 6, 11, 18, 27, tzinfo=UTC),
        4, 120.0)
    poll(store, "ukrainealarm", datetime(2026, 9, 6, 11, 26, 27, tzinfo=UTC),
         "refused", "HTTP Error 502: Bad Gateway")
    row = measure_feed(
        store, API, as_of=datetime(2026, 9, 6, 11, 26, 28, tzinfo=UTC)
    )
    assert row.state is PipeState.DELIVERING


def test_2026_09_06_five_consecutive_503s_are_caught_on_the_second(store):
    """The ten-minute vendor outage nobody knew about until this session."""
    run(store, "ukrainealarm", datetime(2026, 9, 6, 7, 40, 49, tzinfo=UTC),
        5, 120.0)
    at = datetime(2026, 9, 6, 7, 50, 49, tzinfo=UTC)
    states = []
    for _ in range(5):
        poll(store, "ukrainealarm", at, "refused",
             "HTTP Error 503: Service Unavailable")
        states.append(
            measure_feed(store, API, as_of=at + timedelta(seconds=1)).state
        )
        at = at + timedelta(seconds=121)
    assert states[0] is PipeState.DELIVERING
    assert states[1] is PipeState.REFUSING
    assert all(state is PipeState.REFUSING for state in states[1:])
    row = measure_feed(store, API, as_of=at)
    assert row.refusal_status == 503
    assert row.as_item()["refusal_class"] == "upstream"


def test_a_silent_publisher_on_a_healthy_pipe_still_reads_delivering(store):
    """The reason this module reads attempts and not events.

    On 2026-09-06 both feeds went quiet for 4 958 s at the same minute because
    the sky was quiet. An event-derived signal calls that an outage; the pipe
    was reading perfectly throughout and this must say so.
    """
    now = datetime(2026, 9, 6, 22, 23, tzinfo=UTC)
    run(store, "ukrainealarm", now - timedelta(seconds=5000), 41, 120.0)
    stale = now - timedelta(seconds=4958)
    row = measure_feed(
        store, API, as_of=now,
        events=EventStamps(by_ingest={"ukrainealarm": stale},
                           by_source={"ukrainealarm": stale}),
    )
    assert row.state is PipeState.DELIVERING
    assert row.last_event_ingest_at == stale


def test_the_watchman_cannot_hold_the_primary_count_up(store):
    """The defect that was live in production for 33 h 50 min.

    The channel polls a page nobody is writing to, perfectly, twice a minute.
    A plain count of delivering pipes reads one throughout an outage of the
    only source that matters, which is why the reader-facing number is
    `primary_delivering` and not `delivering`.
    """
    now = datetime(2026, 9, 8, 15, 0, tzinfo=UTC)
    run(store, "channel", now - timedelta(seconds=300), 10, 30.0)
    run(store, "ukrainealarm", now - timedelta(seconds=100_000), 5, 120.0)
    rows = liveness(store, (API, CHANNEL), as_of=now)
    block = as_block(rows, now)
    assert block["delivering"] == 1
    assert block["primary_delivering"] == 0
    assert block["primary_known"] == 1
    assert block["known"] == 2


def test_the_boundary_holds_the_weaker_claim(store):
    """`>` and not `>=`, the F-S72 direction.

    At exactly two cadences the pipe is still called delivering, because the
    sentence that asserts less about the source is the one to keep at the edge.
    """
    now = datetime(2026, 9, 8, 15, 0, tzinfo=UTC)
    poll(store, "ukrainealarm", now - timedelta(seconds=240))
    assert measure_feed(store, API, as_of=now).state is PipeState.DELIVERING
    store_at_241 = measure_feed(
        store, API, as_of=now + timedelta(seconds=1)
    )
    assert store_at_241.state is PipeState.STALLED


def test_every_field_is_present_on_every_entry(store):
    """An absent key and a null read alike to a careless consumer."""
    now = datetime(2026, 9, 8, 15, 0, tzinfo=UTC)
    item = measure_feed(store, API, as_of=now).as_item()
    expected = {
        "feed", "source_id", "role", "state", "cadence_s",
        "silence_is_an_outage_s", "last_attempt_at", "last_read_at",
        "read_age_s", "attempt_age_s", "last_event_ingest_at",
        "last_event_source_at", "refusal_status", "refusal_class",
    }
    assert set(item) == expected


def test_refusal_class_separates_the_three_operator_actions():
    assert refusal_class(401) == "rejected"
    assert refusal_class(403) == "rejected"
    assert refusal_class(503) == "upstream"
    assert refusal_class(502) == "upstream"
    assert refusal_class(404) == "client"
    assert refusal_class(None) == "unreachable"


def test_the_production_registry_maps_feeds_to_the_right_source_ids():
    """`channel` writes rows stamped `telegram`, and the two spaces differ.

    Confusing them is the one mistake this registry exists to prevent: the
    table calls the Telegram pipe `channel` and the rows it produces carry
    `source_id="telegram"`.
    """
    by_feed = {spec.feed: spec for spec in PRODUCTION_FEEDS}
    assert by_feed["channel"].source_id == "telegram"
    assert by_feed["ukrainealarm"].source_id == "ukrainealarm"
    assert by_feed["ukrainealarm"].role == "primary"
    assert by_feed["channel"].role == "watchman"
    assert "rso" not in by_feed


def test_the_threshold_comes_from_the_shared_constant():
    """Two cadences, imported from `attempts`, not restated here."""
    assert API.silence_is_an_outage_s == 240.0
    assert CHANNEL.silence_is_an_outage_s == 60.0


def test_a_stamp_without_an_offset_is_refused(store, tmp_path):
    """The store writes offsets; a row without one came from somewhere else."""
    import sqlite3

    now = datetime(2026, 9, 8, 15, 0, tzinfo=UTC)
    poll(store, "ukrainealarm", now)
    conn = sqlite3.connect(tmp_path / "events")
    conn.execute("UPDATE feed_attempts SET started_at = ?",
                 ("2026-09-08T15:00:00",))
    conn.commit()
    conn.close()
    with pytest.raises(ValueError, match="no UTC offset"):
        measure_feed(store, API, as_of=now)
