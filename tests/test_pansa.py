"""The UUP reader: what it keeps, what it refuses, and what it counts.

The fixture is `mavo-site`'s `fixtures/airspace-harness.json` at 4.76.0.0,
copied byte for byte into `tests/fixtures/pansa_uup.json`. Its own docstring
states that it mirrors the schema measured on `vm-site` on 2026-09-14 field for
field, including the three fields that carry nothing and the one that must
never be stored. It is **a stand-in and not a recorded body**: the first body
this reader parses from `vm-mavo` is owed as a deployment reading (T85), and
until then these tests prove the port, not the feed.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from mavo.errors import SourceUnavailable
from mavo.sources import pansa
from mavo.transport import FailingTransport, StubTransport

FIXTURE = Path(__file__).parent / "fixtures" / "pansa_uup.json"
READABLE = 10
REFUSED_FEATURES = 2       # the Point, and the feature with no properties
REFUSED_RESERVATIONS = 1   # EPD53A's window, whose stamps carry no offset


def _page() -> pansa.Page:
    return pansa.parse(FIXTURE.read_bytes())


def test_features_that_cannot_be_read_are_counted_not_dropped() -> None:
    page = _page()
    assert len(page.zones) == READABLE
    assert page.unreadable == REFUSED_FEATURES


def test_a_stamp_without_an_offset_is_refused_and_counted() -> None:
    """Guessing a zone would move the window by two hours and nobody would know."""
    page = _page()
    naive = next(zone for zone in page.zones if zone.designator == "EPD53A")
    assert naive.reservations == ()
    assert page.reservations_refused == REFUSED_RESERVATIONS


def test_every_status_seen_is_counted() -> None:
    assert _page().statuses == {"ACTIVATED": 9, "PLANNED": 1}


def test_an_empty_list_is_a_quiet_plan_not_a_refusal() -> None:
    page = pansa.parse(b"[]")
    assert (page.zones, page.unreadable, page.statuses) == ((), 0, {})


def test_a_feature_collection_is_read_like_a_list() -> None:
    features = json.loads(FIXTURE.read_text(encoding="utf-8"))
    wrapped = json.dumps({"type": "FeatureCollection", "features": features}).encode()
    assert len(pansa.parse(wrapped).zones) == READABLE


@pytest.mark.parametrize("body, reason", [
    (b"<!DOCTYPE html><html><body>blocked</body></html>", "HTML"),
    (b'{"not": "features"}', "neither"),
    (b"not json at all", "not JSON"),
    (b'[{"type":"Feature","geometry":null,"properties":{}}]', "none of the 1"),
    (b'[{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[1,2],', "not JSON"),
    (b"x" * (pansa.MAX_BYTES + 1), "ceiling"),
])
def test_hostile_bodies_are_refused_rather_than_read_as_an_empty_plan(
    body: bytes, reason: str
) -> None:
    """Malformed, truncated, oversized, garbage and an HTML block page."""
    with pytest.raises(SourceUnavailable, match=reason):
        pansa.parse(body)


def test_garbage_reservations_inside_a_readable_feature_are_counted() -> None:
    body = json.dumps([{
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [[[1, 2], [2, 2], [2, 3], [1, 2]]]},
        "properties": {
            "designator": "EPX9", "airspaceElementType": "tsa",
            "airspaceReservations": [
                "garbage",
                {"startDate": "2026-09-14T10:00:00Z", "endDate": "2026-09-14T08:00:00Z"},
                {"startDate": "2026-09-14T10:00:00Z", "endDate": "2026-09-14T12:00:00Z",
                 "reservationStatus": "activated", "remarks": None},
            ],
        },
    }]).encode()
    page = pansa.parse(body)
    assert page.reservations_refused == 2, "a string and a window that ends before it starts"
    (zone,) = page.zones
    assert zone.kind == "TSA"
    (res,) = zone.reservations
    assert res.status == "ACTIVATED" and res.remarks == ""


def test_the_agency_interface_fragment_is_never_stored() -> None:
    assert b"popupHtml" in FIXTURE.read_bytes()
    for zone in _page().zones:
        stored = zone.geometry_text() + zone.reservations_text()
        assert "popupHtml" not in stored and "modal-item" not in stored


def test_the_digest_moves_when_a_reservation_is_activated_and_the_shape_does_not() -> None:
    """An activation is one status inside one window, and it is a new record."""
    zone = next(z for z in _page().zones if z.designator == "EPR134")
    planned = zone.reservations[0]
    activated = pansa.Zone(
        designator=zone.designator, kind=zone.kind, geometry=zone.geometry,
        reservations=(pansa.Reservation(
            starts_at=planned.starts_at, ends_at=planned.ends_at, lower=planned.lower,
            upper=planned.upper, managed_by=planned.managed_by,
            remarks=planned.remarks, status="ACTIVATED"),),
    )
    assert planned.status == "PLANNED"
    assert activated.digest() != zone.digest()
    assert activated.geometry_digest() == zone.geometry_digest()


def test_a_digest_is_stable_across_two_parses() -> None:
    first = [zone.digest() for zone in _page().zones]
    second = [zone.digest() for zone in _page().zones]
    assert first == second
    assert len(set(first)) == READABLE


def test_a_stored_zone_reads_back_as_the_zone_that_was_stored() -> None:
    for zone in _page().zones:
        record = {
            "designator": zone.designator,
            "kind": zone.kind,
            "reservations": json.loads(zone.reservations_text()),
            "geometry": json.loads(zone.geometry_text()),
        }
        back = pansa.zone_from_record(record)
        assert back.digest() == zone.digest()


def test_a_stored_stamp_this_module_did_not_write_is_refused_on_the_way_back() -> None:
    record = {
        "designator": "EPX1", "kind": "D",
        "geometry": {"type": "Polygon", "coordinates": []},
        "reservations": [{"starts_at": "2026-09-14 10:00", "ends_at": "2026-09-14T12:00:00Z"}],
    }
    with pytest.raises(ValueError, match="did not write"):
        pansa.zone_from_record(record)


def test_the_day_plan_is_never_the_address() -> None:
    """AUP carries no ACTIVATED at all [measured on vm-site 2026-09-14]."""
    assert pansa.SOURCE_URL.endswith("/uup")
    assert "aup" not in pansa.SOURCE_URL


def test_poll_once_asks_for_json_through_the_transport() -> None:
    transport = StubTransport(FIXTURE.read_text(encoding="utf-8"))
    page, elapsed = pansa.poll_once(transport)
    assert transport.calls == 1
    assert transport.last_headers == {"Accept": "application/json"}
    assert len(page.zones) == READABLE and elapsed >= 0


def test_an_unreachable_endpoint_raises_rather_than_returning_an_empty_plan() -> None:
    with pytest.raises(SourceUnavailable):
        pansa.poll_once(FailingTransport())


def test_reservation_records_are_normalised_to_utc() -> None:
    zone = next(z for z in _page().zones if z.designator == "EPTS9")
    record = zone.reservations[0].as_record()
    assert record["starts_at"].endswith("+00:00")
    assert datetime.fromisoformat(record["starts_at"]).tzinfo is not None
    assert datetime.fromisoformat(record["ends_at"]) > datetime(2026, 9, 14, tzinfo=UTC)


@pytest.mark.parametrize("feature", [
    {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[1, 2]]]},
     "properties": {"designator": ["EPX"], "airspaceElementType": {"k": 1},
                    "airspaceReservations": {"not": "a list"}}},
    {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[1, 2]]]},
     "properties": {"designator": 12, "airspaceElementType": None}},
    {"type": "Feature", "geometry": {"type": "MultiPolygon", "coordinates": "text"},
     "properties": {"designator": "EPX", "airspaceElementType": "D"}},
    {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[1, 2]]]},
     "properties": {"designator": "EPX", "airspaceElementType": "D",
                    "airspaceReservations": [{"startDate": 5, "endDate": [],
                                              "lowerAltitude": {}, "unit": 3,
                                              "remarks": 9, "reservationStatus": []}]}},
    {"type": "Feature", "geometry": [], "properties": []},
    42,
    None,
])
def test_json_of_the_wrong_shape_is_counted_and_never_escapes_as_another_exception(
    feature: object,
) -> None:
    """`_cmd_airspace` catches `SourceUnavailable` and nothing else, so a shape
    that raised `TypeError` or `KeyError` here would take the collector down
    with a traceback and no attempt row - F110's shape, one adapter over."""
    body = json.dumps([feature]).encode()
    try:
        page = pansa.parse(body)
    except SourceUnavailable:
        return
    assert page.unreadable + len(page.zones) == 1
