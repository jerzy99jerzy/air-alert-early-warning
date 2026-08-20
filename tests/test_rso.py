"""The RSO reader, and the four ways a feed like this reports nothing.

Every test below names the invariant it defends. The fixture is a reduced copy
of a page measured from the live endpoint on 2026-08-20, kept verbatim in its
empty elements: those are the evidence, and reflowing them into absent
elements would edit the thing under test.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from mavo.errors import SourceUnavailable
from mavo.sources.rso import (
    AmbiguousLocalTime,
    Communique,
    Page,
    Province,
    parse_page,
    to_utc,
)

FIXTURE = Path(__file__).parent / "fixtures" / "rso_page.xml"


@pytest.fixture
def page() -> Page:
    return parse_page(FIXTURE.read_bytes())


def test_the_page_reports_its_pagination_as_the_feed_stated_it(page: Page) -> None:
    """Seventeen items across pages of twenty, from the feed's own header."""
    assert page.total_items == 17, page
    assert page.items_per_page == 20, page
    assert len(page.communiques) == 2, page.communiques


def test_an_element_that_is_present_and_empty_reads_as_nothing(page: Page) -> None:
    """`<latitude></latitude>` is a field that said nothing, not a coordinate.

    This is the defect class the whole project is built around, arriving one
    layer earlier than usual: in the source data rather than in our own output.
    """
    first = page.communiques[0]
    assert first.value("latitude") is None, first.fields
    assert first.value("longitude") is None, first.fields
    assert first.value("river_name") is None, first.fields


def test_an_absent_element_and_an_empty_one_are_both_nothing(page: Page) -> None:
    """The second item omits `valid_from` entirely. Same answer, deliberately."""
    second = page.communiques[1]
    assert second.value("valid_from") is None, second.fields
    assert second.value("latitude") is None, second.fields


def test_a_field_that_carries_content_survives_verbatim(page: Page) -> None:
    """A reader that nulls empties must still hand back what was said."""
    first = page.communiques[0]
    assert first.value("created_at") == "2026-08-20 11:27:07", first.fields
    assert first.value("title") == "Gwałtowne wzrosty stanów wody", first.fields


def test_the_severity_marker_stays_text(page: Page) -> None:
    """`rso_alarm` reads `1` and its encoding is undocumented and unverified.

    Parsing it as an integer would assert that the levels are ordered and
    comparable, which is a claim about MSWiA's scheme that nobody here has
    measured.
    """
    assert page.communiques[0].value("rso_alarm") == "1"
    assert page.communiques[1].value("rso_alarm") == "0"
    assert not isinstance(page.communiques[0].value("rso_alarm"), int)


def test_scope_is_a_list_and_a_city_is_not_a_voivodeship(page: Page) -> None:
    """One communique can name several voivodeships, and may name a city."""
    assert page.communiques[0].provinces == (
        Province(slug="podkarpackie", name="Podkarpackie", city=None),
    )
    second = page.communiques[1].provinces
    assert [p.slug for p in second] == ["podkarpackie", "lubelskie"], second
    assert second[0].city == "Rzeszów", second
    assert second[1].city is None, second


def test_an_item_without_an_identifier_is_dropped_and_counted() -> None:
    """A row with no identity cannot be stored idempotently, so it is refused.

    Counted on the page rather than logged, because a caller reading only the
    list cannot tell a short page from a damaged one.
    """
    payload = b"""<newses>
      <pagination_info totalItems="2" itemsPerPage="20"/>
      <news><id></id><title>no identity</title></news>
      <news><id>7</id><title>has one</title></news>
    </newses>"""
    page = parse_page(payload)
    assert page.unreadable == 1, page
    assert [c.id for c in page.communiques] == ["7"], page.communiques
    assert page.total_items == 2, "the feed's own count survives our own losses"


def test_a_province_without_a_slug_does_not_become_a_scope() -> None:
    """An unnameable area is dropped rather than folded into its neighbours."""
    payload = b"""<newses><news><id>7</id><provinces>
      <province id="9" city="">Podkarpackie</province>
      <province id="6" slug="lubelskie">Lubelskie</province>
    </provinces></news></newses>"""
    page = parse_page(payload)
    assert [p.slug for p in page.communiques[0].provinces] == ["lubelskie"]


def test_unparseable_bytes_refuse_rather_than_read_as_a_quiet_day() -> None:
    """The invariant this module exists for.

    An empty page is a real answer on a quiet day. If damaged bytes produced
    the same value, our blindness would render as a country with no warnings.
    """
    with pytest.raises(SourceUnavailable):
        parse_page(b"<newses><news><id>7</id>")


def test_a_doctype_is_refused_before_the_parser_sees_it() -> None:
    """`xml.etree` is documented as unsafe against entity expansion.

    The feed has never carried a doctype, so refusing the construct removes
    the class outright rather than bounding it.
    """
    bomb = (
        b'<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol">'
        b'<!ENTITY lol2 "&lol;&lol;&lol;">]><newses>&lol2;</newses>'
    )
    with pytest.raises(SourceUnavailable):
        parse_page(bomb)


def test_an_oversized_payload_is_refused_by_length_alone() -> None:
    """A replaced endpoint handing back a stream must not be parsed."""
    from mavo.sources import rso

    with pytest.raises(SourceUnavailable):
        parse_page(b"<newses/>" + b"x" * rso.MAX_BYTES)


def test_a_page_with_no_pagination_header_reports_unknown_not_zero() -> None:
    """Absent counts are unknown. Zero is a measurement nobody took."""
    page = parse_page(b"<newses><news><id>7</id></news></newses>")
    assert page.total_items is None, page
    assert page.items_per_page is None, page


def test_a_pagination_figure_that_is_not_a_number_is_unknown_not_zero() -> None:
    """Same rule one layer down: unreadable is not empty."""
    page = parse_page(b'<newses><pagination_info totalItems="many"/></newses>')
    assert page.total_items is None, page


def test_the_naive_timestamp_is_not_converted_by_the_parser(page: Page) -> None:
    """The zone is a decision about the publisher and is not made in a parser."""
    assert isinstance(page.communiques[0].value("created_at"), str)
    assert page.communiques[0].value("created_at") == "2026-08-20 11:27:07"


def test_to_utc_requires_the_zone_from_its_caller() -> None:
    """Summer and winter differ by an hour, and the feed states neither."""
    assert to_utc("2026-08-20 11:27:07", "Europe/Warsaw") == datetime(
        2026, 8, 20, 9, 27, 7, tzinfo=UTC
    )
    assert to_utc("2026-01-20 11:27:07", "Europe/Warsaw") == datetime(
        2026, 1, 20, 10, 27, 7, tzinfo=UTC
    )


def test_an_hour_the_zone_maps_twice_is_refused() -> None:
    """The autumn transition: one local hour, two possible instants.

    Picking the earlier one silently would be wrong for one hour of one night
    a year, which is the error profile nobody ever finds.
    """
    with pytest.raises(AmbiguousLocalTime):
        to_utc("2026-10-25 02:30:00", "Europe/Warsaw")


def test_a_timestamp_in_another_shape_refuses(page: Page) -> None:
    """A format change upstream must stop a run rather than shift every row."""
    with pytest.raises(SourceUnavailable):
        to_utc("2026-08-20T11:27:07Z", "Europe/Warsaw")


def test_the_content_digest_moves_with_content_and_not_with_reading_it() -> None:
    """Idempotence keys on content, because `updated_at` moves on a rewrite."""
    one = Communique(id="7", fields={"title": "a"})
    same = Communique(id="7", fields={"title": "a"})
    other = Communique(id="7", fields={"title": "b"})
    assert one.digest() == same.digest()
    assert one.digest() != other.digest()


def test_the_reader_is_not_wired_into_the_collector() -> None:
    """It has no `poll` and does not implement `ThreatSource`, deliberately.

    Where this data renders, if anywhere, is undecided. A reader that could be
    dropped into the collector by accident would make that decision by
    default.
    """
    from mavo.sources import rso

    assert not hasattr(rso, "poll")
    assert not any(hasattr(obj, "poll") for obj in (Page, Communique, Province))
