"""The source dimension in `state.json` (D-049).

The defect these pin: `compose` took its freshness from one `max()` over a pool
with no source dimension, so the loss of one feed was invisible while another
produced. Measured on production 2026-09-08: the channel had produced nothing
for 33 h 50 min while its pipe read perfectly twice a minute, and the page said
nothing because the API was delivering.
"""


from __future__ import annotations

from datetime import UTC, datetime, timedelta

from mavo.liveness import EventStamps, FeedLiveness, FeedSpec, PipeState
from mavo.report import compose, to_contract
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind

API = FeedSpec(feed="ukrainealarm", source_id="ukrainealarm",
               role="primary", cadence_s=120.0)
CHANNEL = FeedSpec(feed="channel", source_id="telegram",
                   role="watchman", cadence_s=30.0)
NOW = datetime(2026, 9, 8, 15, 0, tzinfo=UTC)


def event(source_id: str, ts: datetime, ingest: datetime | None = None):
    return ThreatEvent(
        area_id="UA05020030000000000",
        state=AlertState.ACTIVE,
        ts_source=ts,
        ts_ingest=ingest if ingest is not None else ts,
        source_id=source_id,
        kind=ThreatKind.UNKNOWN,
        provenance=Provenance.REPORTED,
        raw_fields={},
        oblast="vinnytsia",
    )


def row(spec: FeedSpec, state: PipeState, **kwargs) -> FeedLiveness:
    base = dict(
        last_attempt_at=NOW, last_read_at=NOW,
        last_event_ingest_at=None, last_event_source_at=None,
    )
    base.update(kwargs)
    return FeedLiveness(spec=spec, as_of=NOW, state=state, **base)


def test_without_the_callable_the_key_is_present_and_null():
    """Absent and null read alike to a consumer, and they are different facts.

    A producer that does not measure has to be distinguishable from a key
    somebody forgot, because on `null` the page keeps leaning on the
    observation-age heuristic and on a block it may stop.
    """
    report = compose([event("ukrainealarm", NOW)], as_of=NOW)
    assert report.sources is None
    payload = to_contract(report)
    assert "sources" in payload
    assert payload["sources"] is None


def test_the_block_carries_both_counts_and_they_differ():
    """The watchman must not hold the reader-facing number up.

    This is the production state of 2026-09-07 06:09 onward: the channel pipe
    perfect, the primary source gone, a plain count of delivering pipes at one.
    """
    rows = (row(API, PipeState.STALLED), row(CHANNEL, PipeState.DELIVERING))
    report = compose(
        [event("ukrainealarm", NOW)], as_of=NOW, sources=lambda _s, _m: rows
    )
    block = to_contract(report)["sources"]
    assert block["delivering"] == 1
    assert block["primary_delivering"] == 0
    assert block["known"] == 2
    assert block["primary_known"] == 1
    assert block["as_of"] == NOW.isoformat(timespec="seconds")


def test_compose_folds_both_stamps_per_source_and_passes_them_on():
    """`ts_ingest` and `ts_source` are two questions, and both are handed over.

    For the API `ts_source` is the alarm's own `began`, so a row recovered
    after an outage carries a stamp from while we were blind. Only `ts_ingest`
    says when this pipe last reached us.
    """
    seen: list[EventStamps] = []

    def capture(stamps: EventStamps, _moment: datetime):
        seen.append(stamps)
        return ()

    began = NOW - timedelta(days=140)
    compose(
        [
            event("ukrainealarm", began, ingest=NOW - timedelta(seconds=30)),
            event("telegram", NOW - timedelta(hours=33),
                  ingest=NOW - timedelta(hours=33)),
        ],
        as_of=NOW,
        sources=capture,
    )
    assert len(seen) == 1
    ingest, source = seen[0].for_source("ukrainealarm")
    assert source == began
    assert ingest == NOW - timedelta(seconds=30)
    assert seen[0].for_source("telegram")[0] == NOW - timedelta(hours=33)
    assert seen[0].for_source("rso") == (None, None)


def test_the_callable_is_handed_the_moment_the_picture_was_composed():
    """One moment for the whole picture, not two clocks a line apart."""
    moments: list[datetime] = []
    compose(
        [event("ukrainealarm", NOW)], as_of=NOW,
        sources=lambda _s, moment: moments.append(moment) or (),
    )
    assert moments == [NOW]


def test_the_schema_version_does_not_move():
    """Additive against v3, which is what lets the producer ship first.

    The consumer's validator checks the fields it requires and rejects none it
    did not expect. A bump here would make a deployed site refuse the file.
    """
    report = compose(
        [event("ukrainealarm", NOW)], as_of=NOW,
        sources=lambda _s, _m: (row(API, PipeState.DELIVERING),),
    )
    assert to_contract(report)["v"] == 3


def test_a_refusing_primary_reaches_the_contract_with_its_status():
    """401 and 503 take different operator actions and must not share a word."""
    rows = (row(API, PipeState.REFUSING, refusal_status=401),)
    report = compose(
        [event("ukrainealarm", NOW)], as_of=NOW, sources=lambda _s, _m: rows
    )
    entry = to_contract(report)["sources"]["feeds"][0]
    assert entry["state"] == "refusing"
    assert entry["refusal_status"] == 401
    assert entry["refusal_class"] == "rejected"


def test_an_empty_tuple_is_not_the_same_as_no_measurement():
    """Looked and found no feeds, against nobody looked."""
    report = compose(
        [event("ukrainealarm", NOW)], as_of=NOW, sources=lambda _s, _m: ()
    )
    block = to_contract(report)["sources"]
    assert block is not None
    assert block["known"] == 0
    assert block["primary_delivering"] == 0
