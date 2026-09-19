"""The Polish blocks, composed from the store (D-053).

Three kinds of evidence, kept apart because they prove different things.

**The port.** The rules are `mavosite/rso.py` and `mavosite/airspace.py` at
4.76.0.0. Their tests are ported here with the consumer's expected values, so a
rule that drifted in the move fails a named test.

**The oracle.** `tests/fixtures/pansa_uup_mavo_site_4760.geojson` is the file
the consumer committed as what its own module serves for the same fixture at
the same moment. The producer's `features` must equal its features exactly. It
is the one assertion here nobody in this repository wrote.

**The states.** Absent, `null`, empty and rows are four different claims, and
each is reached through a real `EventStore` rather than a hand-built dict, so a
table or column name that drifts fails here and not on the host (F154).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo import poland
from mavo.cli import main
from mavo.report import compose, to_contract
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind
from mavo.sources import pansa, rso
from mavo.store import EventStore

FIXTURES = Path(__file__).parent / "fixtures"
UUP = FIXTURES / "pansa_uup.json"
CONSUMER_GEOJSON = FIXTURES / "pansa_uup_mavo_site_4760.geojson"
#: The consumer's `AIRSPACE_NOW` (tools/render_harness.py) and `NOW` in its
#: `tests/test_airspace.py`: midday, EPEA07 closed at 09:00, EPTS9's second
#: window still open.
AIR_NOW = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
#: The consumer's `NOW` in `tests/test_rso.py`.
RSO_NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)

#: The consumer's test page, with the two changes the producer's parser needs.
#: Its root is the feed's `<newses>` (`tests/fixtures/rso_page.xml`), where the
#: consumer's page invented `<news_list>` and so could not tell a list from any
#: other document (F173). And every `<province>` carries a
#: `slug`, as all three provinces in the reduced page recorded from the live
#: endpoint do (`tests/fixtures/rso_page.xml`; three is the whole of the
#: evidence). The consumer read slugless provinces by their text; this parser
#: keeps a province by its slug, and D-053 names that difference and its cost.
PAGE = """<?xml version="1.0" encoding="UTF-8"?>
<newses>
  <news>
    <id>1</id>
    <title>Zagrożenie z powietrza</title>
    <valid_to>2099-01-01 00:00:00</valid_to>
    <provinces><province slug="malopolskie">Malopolskie</province></provinces>
  </news>
  <news>
    <id>2</id>
    <title>Dron nad województwem</title>
    <valid_to>2000-01-01 00:00:00</valid_to>
    <provinces><province slug="slaskie">slaskie</province></provinces>
  </news>
  <news>
    <id>3</id>
    <title>Naruszenie przestrzeni powietrznej</title>
    <valid_to></valid_to>
    <provinces>
      <province slug="malopolskie">malopolskie</province>
      <province slug="podkarpackie">Podkarpackie</province>
    </provinces>
  </news>
  <news>
    <id>4</id>
    <title>Ostrzeżenie meteorologiczne: upał</title>
    <valid_to>2099-01-01 00:00:00</valid_to>
    <provinces><province slug="mazowieckie">mazowieckie</province></provinces>
  </news>
  <news>
    <id>5</id>
    <title>Zła jakość powietrza</title>
    <valid_to>2099-01-01 00:00:00</valid_to>
    <provinces><province slug="lubelskie">lubelskie</province></provinces>
  </news>
  <news>
    <id>6</id>
    <title>Test syren alarmowych Warszawa</title>
    <shortcut>Ćwiczenia: testy systemu alarmowania syrenami.</shortcut>
    <content>Testy alarmowania. Sygnał: alarm powietrzny. Zachowaj spokój.</content>
    <rso_alarm>0</rso_alarm>
    <valid_from>2026-09-09 09:00:00</valid_from>
    <valid_to>2099-01-01 00:00:00</valid_to>
    <provinces><province slug="mazowieckie">mazowieckie</province></provinces>
  </news>
  <news>
    <id>7</id>
    <title>Ostrzeżenie meteorologiczne</title>
    <content>Silny wiatr.</content>
    <rso_alarm>1</rso_alarm>
    <valid_to>2099-01-01 00:00:00</valid_to>
    <provinces><province slug="pomorskie">pomorskie</province></provinces>
  </news>
</newses>
""".encode()


def _rows(page_bytes: bytes = PAGE) -> list[dict[str, object]]:
    """Communique rows in the shape the store hands back, without a store."""
    return [
        {
            "source_id": item.id,
            "provinces": [[p.slug, p.name, p.city] for p in item.provinces],
            "fields": item.fields,
        }
        for item in rso.parse_page(page_bytes).communiques
    ]


# ---- the port: which communique is about the air


def test_the_term_list_is_the_one_the_project_reviewed() -> None:
    assert poland.AIR_THREAT_TERMS == (
        "z powietrza", "powietrzn", "dron", "bezzałogow", "rakiet",
        "pocisk", "nalot", "obiekt lataj", "przestrzeni powietrznej",
        "alarm lotnicz",
    )


def test_the_exclusion_list_is_the_one_the_project_reviewed() -> None:
    assert poland.NOT_A_THREAT_TERMS == (
        "test syren", "testy syren", "testu syren", "próba syren",
        "próby syren", "ćwiczeni", "trening", "jakość powietrza",
        "jakości powietrza", "smog", "pył zawieszon", "pyłu zawieszon",
    )


@pytest.mark.parametrize("title,body", [
    ("Test syren alarmowych", "sygnał alarmu powietrznego"),
    ("Próba syren", "alarm powietrzny o 12:00"),
    ("Ćwiczenia obrony cywilnej", "symulowany atak powietrzny"),
    ("Trening", "alarm powietrzny"),
    ("UWAGA SMOG", "zagrożenie z powietrza dla płuc"),
])
def test_exclusions_beat_inclusions(title: str, body: str) -> None:
    assert poland.air_term(title, body) is None


@pytest.mark.parametrize("title", [
    "Zagrożenie z powietrza",
    "Atak powietrzny na zachód Ukrainy",
    "Bezzałogowy statek powietrzny nad granicą",
    "Rakieta w przestrzeni powietrznej RP",
    "Nalot na obwody zachodnie",
])
def test_air_threat_titles_match(title: str) -> None:
    assert poland.air_term(title, None) is not None


@pytest.mark.parametrize("title", [
    "Ostrzeżenie meteorologiczne", "Stan wody na Wiśle",
    "Utrudnienia drogowe", "Smog: zła jakość powietrza", "Zła jakość powietrza",
])
def test_other_notices_do_not_match(title: str) -> None:
    assert poland.air_term(title, None) is None


def test_the_body_is_read_as_well_as_the_title_and_the_term_is_named() -> None:
    assert poland.air_term("Komunikat RCB", "wykryto drony nad regionem") == "dron"
    assert poland.air_term("Komunikat RCB", "silny wiatr i burze") is None


def test_the_payload_carries_the_communiques_behind_each_name() -> None:
    """The consumer's 4.76.0.0 expectations, unchanged, plus `air_term`."""
    rows, cleared = poland.warnings_rows(_rows(), RSO_NOW)
    assert cleared == []
    assert [r["voivodeship"] for r in rows] == ["malopolskie", "podkarpackie"]
    by_name = {r["voivodeship"]: [c["id"] for c in r["communiques"]] for r in rows}
    assert by_name == {"malopolskie": ["1", "3"], "podkarpackie": ["3"]}
    first = rows[0]["communiques"][0]
    assert first["title"] == "Zagro\u017cenie z powietrza"
    assert first["valid_to"] == "2099-01-01T00:00:00+01:00"
    assert first["air_term"] == "z powietrza"
    assert set(first) == {"id", "title", "valid_from", "valid_to", "text", "air_term"}


def test_a_siren_test_a_heat_warning_and_an_alarm_flag_do_not_paint() -> None:
    names = [r["voivodeship"] for r in poland.warnings_rows(_rows(), RSO_NOW)[0]]
    assert "mazowieckie" not in names    # siren test with "alarm powietrzny" in its body
    assert "pomorskie" not in names      # rso_alarm=1 and not about the air
    assert "lubelskie" not in names      # air quality
    assert "slaskie" not in names        # expired


@pytest.mark.parametrize(("text", "iso"), [
    ("2026-09-16 08:00:00", "2026-09-16T08:00:00+02:00"),
    ("2026-01-16 08:00:00", "2026-01-16T08:00:00+01:00"),
    ("not a date", "not a date"),
    (None, None),
])
def test_the_feeds_stamp_becomes_iso_with_the_warsaw_offset(
    text: str | None, iso: str | None
) -> None:
    assert poland.feed_stamp_as_iso(text) == iso


def test_the_autumn_hour_reaches_the_reader_as_the_feed_wrote_it() -> None:
    """Difference 2. The consumer printed this as +02:00 without saying so."""
    assert poland.feed_stamp_as_iso("2026-10-25 02:30:00") == "2026-10-25 02:30:00"


def test_an_end_inside_the_autumn_hour_is_not_an_end() -> None:
    """At 00:45 UTC the consumer called this over (it read 02:30 as 00:30 UTC).

    If the publisher meant winter time the communique runs to 01:30 UTC, and
    ending it early is a warning taken off the map while it stands.
    """
    moment = datetime(2026, 10, 25, 0, 45, tzinfo=UTC)
    assert poland.is_expired("2026-10-25 02:30:00", moment) is False
    assert poland.is_expired("2026-10-25 01:30:00", moment) is True   # unambiguous, 23:30 UTC


def test_an_absent_or_unparseable_end_is_not_an_end() -> None:
    assert poland.is_expired(None, RSO_NOW) is False
    assert poland.is_expired("not a date", RSO_NOW) is False
    assert poland.is_expired("2000-01-01 00:00:00", RSO_NOW) is True


# ---- the port: which structure is drawn


def _zones() -> tuple[pansa.Zone, ...]:
    return pansa.parse(UUP.read_bytes()).zones


def test_only_what_is_switched_on_is_drawn() -> None:
    assert [z.designator for z, _ in poland.drawn(_zones(), AIR_NOW)] == [
        "EPTS9", "EPTR700", "EPD29"]


def test_the_window_ending_first_is_the_one_shown() -> None:
    ts9 = {z.designator: r for z, r in poland.drawn(_zones(), AIR_NOW)}["EPTS9"]
    assert ts9.ends_at == datetime(2026, 9, 14, 16, 0, tzinfo=UTC)
    assert (ts9.lower, ts9.upper) == ("GND", "F095")


@pytest.mark.parametrize("remarks, civil", [
    ("BSP/UAV", True), ("OATC/SUP09/26/BSP/UAV", True), ("PJE/CLN", True),
    ("C150 GLD PJE", True), ("M346/CLN/W", False), ("F16/W", False),
    ("NOT.D6513/26/ORZEL", False), ("", False),
])
def test_civil_marks_are_read_out_of_slash_joined_remarks(remarks: str, civil: bool) -> None:
    res = pansa.Reservation(starts_at=AIR_NOW, ends_at=AIR_NOW, lower=None, upper=None,
                            managed_by=None, remarks=remarks, status="ACTIVATED")
    assert poland.is_civil(res) is civil


def test_the_reasons_account_for_everything_switched_on() -> None:
    counts = poland.not_drawn(_zones(), AIR_NOW)
    assert counts == {"switched_on": 7, "drawn": 3, "kind_not_drawn": 1,
                      "civil": 2, "tra_not_called_up": 1}
    assert counts["switched_on"] == (counts["drawn"] + counts["kind_not_drawn"]
                                     + counts["civil"] + counts["tra_not_called_up"])


@pytest.mark.parametrize(("code", "metres"), [
    ("GND", 0), ("SFC", 0), ("A061", 1850), ("A030", 900), ("F095", 2900),
    ("F135", 4100), ("F245", 7450), ("f095", 2900), ("UNL", None), ("4500", None),
    ("", None), (None, None),
])
def test_a_vertical_limit_is_read_for_a_reader_in_metres(code: str | None,
                                                          metres: int | None) -> None:
    assert poland.altitude_metres(code) == metres


def test_the_features_equal_what_the_consumer_committed_for_the_same_moment() -> None:
    """The oracle. Written by the consumer's release, not by this one."""
    committed = json.loads(CONSUMER_GEOJSON.read_text(encoding="utf-8"))
    value = poland.airspace_value(_zones(), AIR_NOW, read_at=AIR_NOW,
                                  unreadable=2, stale_error=None)
    assert value["features"] == committed["features"]
    assert committed["read_at"] == value["read_at"]


def test_the_text_block_is_the_consumers_shape_with_features_added() -> None:
    value = poland.airspace_value(_zones(), AIR_NOW, read_at=AIR_NOW,
                                  unreadable=2, stale_error=None)
    assert set(value) == {"read_at", "switched_on", "not_drawn", "unreadable",
                          "statuses", "stale_error", "features"}
    assert value["statuses"] == {"ACTIVATED": 9, "PLANNED": 1}
    first = value["switched_on"][0]
    assert first["managed_by"] == "EPDE"
    assert (first["lower"], first["upper"], first["lower_m"], first["upper_m"]) == (
        "GND", "F095", 0, 2900)
    assert "popupHtml" not in json.dumps(value)


# ---- the states, through a real store


def _write_page(store: EventStore, url: str, at: datetime, page_bytes: bytes = PAGE) -> None:
    """Rows, the list, then the read: the order `mavo rso` writes them in."""
    page = rso.parse_page(page_bytes)
    store.append_communiques(rso.FEED, page.communiques)
    store.record_snapshot(rso.FEED, url, at, [item.digest() for item in page.communiques])
    store.record_read(rso.FEED, url, at, len(page.communiques), page.unreadable)


def test_a_feed_this_producer_never_polled_leaves_the_key_absent(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    blocks = poland.measure(store, RSO_NOW)
    assert blocks.warnings.published is False
    assert blocks.airspace.published is False


def test_a_read_of_another_category_is_not_a_read_of_the_map_scope(tmp_path: Path) -> None:
    """Five addresses under one feed name, and only one of them paints.

    The map scope was last read two hours ago; a weather category answered a
    minute ago. A freshness test that did not narrow to the address would see
    the minute-old read and publish the two-hour-old list as current, which
    is the first half of this test's reason to exist. The second half is the
    store with no map-scope read at all.
    """
    store = EventStore(tmp_path / "events")
    _write_page(store, poland.WARNINGS_URL, RSO_NOW - timedelta(hours=2))
    _write_page(store, rso.page_url("meteorologiczne", 0), RSO_NOW - timedelta(minutes=1))
    block = poland.warnings_block(store, RSO_NOW)
    assert block.published is True and block.value is None

    other = EventStore(tmp_path / "other")
    _write_page(other, rso.page_url("meteorologiczne", 0), RSO_NOW)
    assert poland.warnings_block(other, RSO_NOW) == poland.Block(published=True, value=None)


def test_a_fresh_reading_of_the_map_scope_publishes_rows(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    _write_page(store, poland.WARNINGS_URL, RSO_NOW - timedelta(minutes=10))
    block = poland.warnings_block(store, RSO_NOW)
    assert block.value == poland.warnings_rows(_rows(), RSO_NOW)[0]
    assert [r["voivodeship"] for r in block.value] == ["malopolskie", "podkarpackie"]


def test_a_reading_older_than_the_ceiling_is_null_and_not_the_last_list(tmp_path: Path) -> None:
    """Difference 3. The consumer kept this list, empty or not, for ever."""
    store = EventStore(tmp_path / "events")
    _write_page(store, poland.WARNINGS_URL, RSO_NOW - timedelta(hours=2))
    later = rso.page_url("ogolne", 0)
    store.record_refusal(rso.FEED, later, RSO_NOW - timedelta(minutes=5), "HTTP Error 503")
    block = poland.warnings_block(store, RSO_NOW)
    assert block.published is True and block.value is None


def test_the_ceiling_is_inclusive_of_its_own_edge(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    edge = RSO_NOW - timedelta(seconds=poland.WARNINGS_VALID_FOR_S)
    _write_page(store, poland.WARNINGS_URL, edge)
    assert poland.warnings_block(store, RSO_NOW).value is not None
    assert poland.warnings_block(store, RSO_NOW + timedelta(seconds=1)).value is None


def test_an_empty_page_is_an_empty_list_and_not_null(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    _write_page(store, poland.WARNINGS_URL, RSO_NOW, b"<newses/>")
    assert poland.warnings_block(store, RSO_NOW).value == []


def test_a_list_naming_a_row_nobody_wrote_is_null_not_partial(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    page = rso.parse_page(PAGE)
    store.record_read(rso.FEED, poland.WARNINGS_URL, RSO_NOW, 7, 0)
    store.append_communiques(rso.FEED, page.communiques[:1])
    store.record_snapshot(rso.FEED, poland.WARNINGS_URL, RSO_NOW,
                          [item.digest() for item in page.communiques])
    assert poland.warnings_block(store, RSO_NOW).value is None


def test_an_edited_communique_shows_only_the_edit_the_feed_serves_now(tmp_path: Path) -> None:
    """The store keeps both readings; the newest list decides which one is shown."""
    store = EventStore(tmp_path / "events")
    _write_page(store, poland.WARNINGS_URL, RSO_NOW - timedelta(minutes=20))
    edited = PAGE.replace("Zagrożenie z powietrza".encode(),
                          "Zagrożenie z powietrza: dron".encode())
    _write_page(store, poland.WARNINGS_URL, RSO_NOW - timedelta(minutes=5), edited)
    assert store.count_communiques(rso.FEED) == 8, "seven rows plus the edit"
    titles = [c["title"] for row in poland.warnings_block(store, RSO_NOW).value
              for c in row["communiques"] if c["id"] == "1"]
    assert titles == ["Zagrożenie z powietrza: dron"]


def _write_plan(store: EventStore, at: datetime) -> pansa.Page:
    page = pansa.parse(UUP.read_bytes())
    store.append_airspace_zones(pansa.FEED, page.zones)
    store.record_snapshot(pansa.FEED, pansa.SOURCE_URL, at,
                          [zone.digest() for zone in page.zones])
    store.record_read(pansa.FEED, pansa.SOURCE_URL, at, len(page.zones), page.unreadable)
    return page


def test_the_airspace_block_read_back_from_the_store_equals_the_one_composed_from_the_wire(
    tmp_path: Path,
) -> None:
    store = EventStore(tmp_path / "events")
    page = _write_plan(store, AIR_NOW)
    block = poland.airspace_block(store, AIR_NOW)
    assert block.published is True
    assert block.value == poland.airspace_value(page.zones, AIR_NOW, read_at=AIR_NOW,
                                                unreadable=2, stale_error=None)


def test_a_failed_read_after_a_good_one_keeps_the_reading_and_says_so(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    _write_plan(store, AIR_NOW - timedelta(minutes=10))
    store.record_refusal(pansa.FEED, pansa.SOURCE_URL, AIR_NOW - timedelta(minutes=5),
                         "HTTP Error 503: Service Unavailable")
    value = poland.airspace_block(store, AIR_NOW).value
    assert value["stale_error"] == "HTTP Error 503: Service Unavailable"
    assert value["read_at"] == "2026-09-14T11:50:00+00:00"
    _write_plan(store, AIR_NOW)
    assert poland.airspace_block(store, AIR_NOW).value["stale_error"] is None


def test_polled_and_never_read_is_null_for_the_airspace(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    store.record_refusal(pansa.FEED, pansa.SOURCE_URL, AIR_NOW, "unreachable")
    block = poland.airspace_block(store, AIR_NOW)
    assert block.published is True and block.value is None


# ---- the store: what one read served


def test_an_unchanged_list_is_not_written_twice_and_a_return_is(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    url = "https://example.invalid/list"
    t0 = datetime(2026, 9, 16, 10, 0, tzinfo=UTC)
    assert store.record_snapshot("x", url, t0, ["a", "b"]) is True
    assert store.record_snapshot("x", url, t0 + timedelta(minutes=5), ["a", "b"]) is False
    assert store.record_snapshot("x", url, t0 + timedelta(minutes=10), ["b"]) is True
    assert store.record_snapshot("x", url, t0 + timedelta(minutes=15), ["a", "b"]) is True
    assert store.count_snapshots("x") == 3, "A, B and back to A are three rows"
    at = store.newest_snapshot("x", url, at=t0 + timedelta(minutes=12))
    assert at is not None and at["members"] == ["b"]
    assert store.newest_snapshot("x", url)["members"] == ["a", "b"]  # type: ignore[index]
    assert store.newest_snapshot("x", url, at=t0 - timedelta(seconds=1)) is None


def test_order_is_part_of_the_list(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    t0 = datetime(2026, 9, 16, 10, 0, tzinfo=UTC)
    store.record_snapshot("x", "u", t0, ["a", "b"])
    assert store.record_snapshot("x", "u", t0 + timedelta(minutes=1), ["b", "a"]) is True


def test_an_empty_list_is_recorded_as_a_list(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    t0 = datetime(2026, 9, 16, 10, 0, tzinfo=UTC)
    assert store.record_snapshot("x", "u", t0, []) is True
    assert store.newest_snapshot("x", "u")["members"] == []  # type: ignore[index]


def test_a_shape_is_stored_once_however_many_times_its_windows_change(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    page = pansa.parse(UUP.read_bytes())
    assert store.append_airspace_zones(pansa.FEED, page.zones) == 10
    assert store.append_airspace_zones(pansa.FEED, page.zones) == 0
    with closing(sqlite3.connect(tmp_path / "events")) as conn:
        shapes = conn.execute("SELECT COUNT(*) FROM airspace_geometries").fetchone()[0]
    assert shapes == len({zone.geometry_digest() for zone in page.zones})


def test_the_tails_narrow_to_one_address(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    t0 = datetime(2026, 9, 16, 10, 0, tzinfo=UTC)
    store.record_read(rso.FEED, "u1", t0, 3, 0)
    store.record_refusal(rso.FEED, "u2", t0 + timedelta(minutes=1), "503")
    assert store.newest_read_at(rso.FEED, "u2") is None
    assert store.newest_read_at(rso.FEED) is not None
    assert store.newest_refusal_detail(rso.FEED, "u1") is None
    assert store.newest_refusal_detail(rso.FEED, "u2") == "503"
    assert store.newest_read(rso.FEED, "u1")["items"] == 3  # type: ignore[index]
    assert store.newest_attempt_at(rso.FEED, "u2") > store.newest_attempt_at(rso.FEED, "u1")  # type: ignore[operator]


def test_a_store_written_before_this_release_gains_three_tables_and_says_so(
    tmp_path: Path,
) -> None:
    path = tmp_path / "events"
    EventStore(path)
    with closing(sqlite3.connect(path)) as conn:
        for table in ("feed_snapshots", "airspace_zones", "airspace_geometries"):
            conn.execute(f"DROP TABLE {table}")
        conn.commit()
    reopened = EventStore(path)
    assert reopened.migrations_applied == (
        "feed_snapshots (table)", "airspace_zones (table)", "airspace_geometries (table)")
    assert EventStore(path).migrations_applied == ()


# ---- the contract


def _event() -> ThreatEvent:
    return ThreatEvent(area_id="UA05020030000000000", state=AlertState.ACTIVE,
                       ts_source=RSO_NOW, ts_ingest=RSO_NOW, source_id="ukrainealarm",
                       kind=ThreatKind.UNKNOWN, provenance=Provenance.REPORTED,
                       raw_fields={}, oblast="vinnytsia")


def test_without_the_callable_neither_key_is_published() -> None:
    payload = to_contract(compose([_event()], as_of=RSO_NOW))
    assert "pl_warnings" not in payload and "pl_airspace" not in payload


def test_each_key_is_published_on_its_own() -> None:
    blocks = poland.PolandBlocks(warnings=poland.Block(published=True, value=[]))
    payload = to_contract(compose([_event()], as_of=RSO_NOW, poland=lambda _m: blocks))
    assert payload["pl_warnings"] == []
    assert "pl_airspace" not in payload
    assert payload["v"] == 3


def test_a_failed_composition_publishes_both_keys_null() -> None:
    payload = to_contract(compose([_event()], as_of=RSO_NOW, poland=lambda _m: poland.FAILED))
    assert payload["pl_warnings"] is None and payload["pl_airspace"] is None


def test_the_callable_is_handed_the_moment_the_picture_was_composed() -> None:
    moments: list[datetime] = []

    def capture(moment: datetime) -> poland.PolandBlocks:
        moments.append(moment)
        return poland.PolandBlocks()

    compose([_event()], as_of=RSO_NOW, poland=capture)
    assert moments == [RSO_NOW]


# ---- the commands


def test_the_airspace_command_records_the_plan_once_and_the_list_on_change(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    store_path = tmp_path / "events"
    assert main(["airspace", "--stub", str(UUP), "--store", str(store_path)]) == 0
    assert "snapshot=changed" in capsys.readouterr().out
    assert main(["airspace", "--stub", str(UUP), "--store", str(store_path)]) == 0
    assert "snapshot=unchanged" in capsys.readouterr().out
    store = EventStore(store_path)
    assert store.count_airspace_zones() == 10
    assert store.count_snapshots(pansa.FEED) == 1
    attempts = store.attempts(pansa.FEED)
    assert [a["outcome"] for a in attempts] == ["read", "read"]
    assert attempts[0]["items"] == 10 and attempts[0]["unreadable"] == 2
    assert attempts[0]["detail"] == "reservations_refused=1"
    assert attempts[0]["elapsed_s"] is not None


def test_the_airspace_command_logs_a_refusal_and_exits_three(tmp_path: Path) -> None:
    blocked = tmp_path / "blocked.html"
    blocked.write_text("<!DOCTYPE html><html><body>1010</body></html>", encoding="utf-8")
    store_path = tmp_path / "events"
    assert main(["airspace", "--stub", str(blocked), "--store", str(store_path)]) == 3
    store = EventStore(store_path)
    (attempt,) = store.attempts(pansa.FEED)
    assert attempt["outcome"] == "refused" and attempt["items"] is None
    assert store.count_snapshots() == 0


def test_the_rso_command_records_what_each_address_served_in_order(tmp_path: Path) -> None:
    stub = FIXTURES / "rso_page.xml"
    store_path = tmp_path / "events"
    assert main(["rso", "--stub", str(stub), "--category", "ogolne",
                 "--store", str(store_path)]) == 0
    store = EventStore(store_path)
    snapshot = store.newest_snapshot(rso.FEED, poland.WARNINGS_URL)
    assert snapshot is not None
    served = rso.parse_page(stub.read_bytes()).communiques
    assert snapshot["members"] == [item.digest() for item in served]


def test_the_publishing_loop_carries_the_airspace_and_leaves_the_communiques_to_the_consumer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One timer switched on hands over one layer and not both."""
    monkeypatch.delenv("MAVO_LOG_FILE", raising=False)
    store_path = tmp_path / "events"
    assert main(["airspace", "--stub", str(UUP), "--store", str(store_path)]) == 0
    state = tmp_path / "state.json"
    assert main(["report", "--store", str(store_path), "--json", str(state),
                 "--watch", "--interval", "0", "--max-cycles", "1"]) == 0
    payload = json.loads(state.read_text(encoding="utf-8"))
    assert "pl_warnings" not in payload
    assert payload["pl_airspace"] is not None
    assert set(payload["pl_airspace"]) >= {"switched_on", "features", "read_at"}
    feeds = {row["feed"]: row for row in payload["sources"]["feeds"]}
    assert feeds["pansa"]["state"] == "delivering"
    assert feeds["rso"]["state"] == "unknown"
    assert payload["sources"]["primary_known"] == 1


def test_the_publishing_loop_survives_a_store_the_polish_blocks_cannot_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("MAVO_LOG_FILE", raising=False)
    store_path = tmp_path / "events"
    assert main(["airspace", "--stub", str(UUP), "--store", str(store_path)]) == 0

    def broken(_store: EventStore, _moment: datetime) -> poland.PolandBlocks:
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr("mavo.cli.measure_poland", broken)
    state = tmp_path / "state.json"
    assert main(["report", "--store", str(store_path), "--json", str(state),
                 "--watch", "--interval", "0", "--max-cycles", "1"]) == 0
    payload = json.loads(state.read_text(encoding="utf-8"))
    assert payload["pl_warnings"] is None and payload["pl_airspace"] is None
    assert "[POLAND-FAILED] disk I/O error" in capsys.readouterr().err


# ---- D-055: an all-clear ends the alert it cancels; `valid_to` does not

#: The pair's titles and texts, verbatim from the recorded body below. **The
#: provinces in `PAIR` are stand-ins**: the recorded pair names one voivodeship,
#: `lubelskie`, so no recorded row clears part of a threat's area, and the
#: three used here exist to exercise that rule `[measured: the recorded body]`.
ALERT = ("UWAGA! Rosyjski atak powietrzny na terenie Ukrainy.",
         "UWAGA! Rosyjski atak powietrzny na terenie Ukrainy. Sytuacja jest "
         "monitorowana. W przestrzeni RP operuje polskie lotnictwo. Oczekuj "
         "dalszych komunikatów.")
CLEAR = ("UWAGA! Zakończył się atak powietrzny na Ukrainę. Brak zagrożenia na "
         "terenie Polski.",
         "UWAGA! Zakończył się atak powietrzny na Ukrainę. Brak zagrożenia na "
         "terenie Polski.")


def _news(id_: str, title: str, shortcut: str, content: str, valid_from: str,
          slugs: tuple[str, ...], valid_to: str = "2026-09-16 23:59:00") -> str:
    provinces = "".join(f'<province id="1" slug="{s}" city="">{s.title()}</province>'
                        for s in slugs)
    return (f"<news><id>{id_}</id><title>{title}</title><shortcut>{shortcut}</shortcut>"
            f"<content>{content}</content><valid_from>{valid_from}</valid_from>"
            f"<valid_to>{valid_to}</valid_to><provinces>{provinces}</provinces></news>")


def _page(*items: str) -> bytes:
    return ('<?xml version="1.0" encoding="UTF-8"?><newses>' + "".join(items)
            + "</newses>").encode()


PAIR = _page(
    _news("23337898", "ALERT RCB- ODWOŁANIE ZAGROŻENIA", *CLEAR, "2026-09-16 07:36:00",
          ("lubelskie", "podkarpackie")),
    _news("23337896", "Alert RCB", *ALERT, "2026-09-16 07:05:00",
          ("lubelskie", "podkarpackie", "mazowieckie")),
)
MIDDAY = datetime(2026, 9, 16, 10, 0, tzinfo=UTC)


def test_a_partial_clearance_ends_the_threat_only_where_it_is_named() -> None:
    """Stand-in provinces: the rule for a clearance of part of an area has no recorded row."""
    painted, cleared = poland.warnings_rows(_rows(PAIR), MIDDAY)
    assert [r["voivodeship"] for r in painted] == ["mazowieckie"]
    assert [c["id"] for c in painted[0]["communiques"]] == ["23337896"]
    assert [r["voivodeship"] for r in cleared] == ["lubelskie", "podkarpackie"]
    for row in cleared:
        (item,) = row["communiques"]
        assert item["id"] == "23337898" and item["ended"] == ["23337896"]
        assert item["air_term"] == "odwołan"


# ---- F169's closing condition, on the recorded bytes of the pair

#: The unpaged `ogolne` body the operator recorded on 2026-09-16, byte for byte:
#: 40 records, one province each, the pair 23337896 and 23337898 among them.
#: The digest is the one read on the operator's disk and on upload
#: `[measured 2026-09-19, both sides]`; a fixture that has moved is a different
#: fixture, so this test fails before any other can pass on it.
RECORDED = FIXTURES / "rso_ogolne_2026-09-16.xml"
RECORDED_SHA256 = "40421bb37d35e5e0db06f0d3fbca726098563c71edb42280e50fb7b0b3da559c"


def _recorded() -> list[dict[str, object]]:
    return _rows(RECORDED.read_bytes())


def test_the_recorded_body_is_the_one_the_operator_holds() -> None:
    raw = RECORDED.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == RECORDED_SHA256
    assert raw.lstrip().startswith(b'<?xml version="1.0" encoding="utf-8"?>\n<newses>')
    assert len(_recorded()) == 40


def test_the_recorded_pair_paints_nothing_the_publisher_cleared() -> None:
    """F169 closes here: from the all-clear to 23:59 lubelskie is cleared, not painted."""
    for as_of in (datetime(2026, 9, 16, 5, 40, tzinfo=UTC), MIDDAY,
                  datetime(2026, 9, 16, 21, 58, tzinfo=UTC)):
        painted, cleared = poland.warnings_rows(_recorded(), as_of)
        assert painted == [], as_of
        (row,) = cleared
        assert (row["voivodeship"], row["slug"]) == ("lubelskie", "lubelskie")
        (item,) = row["communiques"]
        assert (item["id"], item["ended"]) == ("23337898", ["23337896"])
        assert item["air_term"] == "odwołan"
        assert item["valid_from"] == "2026-09-16T07:36:00+02:00"
    assert poland.warnings_rows(_recorded(), datetime(2026, 9, 16, 22, 0, tzinfo=UTC)) == ([], [])


def test_zero_five_five_zero_painted_the_cleared_voivodeship() -> None:
    """The defect, on the recorded bytes: the old rule read both rows as threats."""
    pair = [r for r in _recorded() if r["source_id"] in {"23337896", "23337898"}]
    fields = [r["fields"] for r in pair]
    assert [poland.air_term(f["title"], poland._body(f)) for f in fields] == [
        "powietrzn", "powietrzn"]
    assert [f["valid_to"] for f in fields] == ["2026-09-16 23:59:00"] * 2


def test_on_the_recorded_day_only_the_pair_is_about_the_air() -> None:
    """38 civic notices - water, a siren test, rail, hydrology, ozone, smog - stay off."""
    verdicts = {r["source_id"]: poland.classify(r["fields"]["title"], poland._body(r["fields"]))
                for r in _recorded()}
    about_the_air = {k: v for k, v in verdicts.items() if v is not None}
    assert about_the_air == {"23337896": ("threat", "powietrzn"),
                             "23337898": ("all_clear", "odwołan")}


def test_no_recorded_communique_prints_its_lead_twice() -> None:
    """F172: five of the forty carry the lead inside the content, one after a header."""
    whole = 0
    for row in _recorded():
        fields = row["fields"]
        lead, text = poland._folded(fields["shortcut"]), poland._folded(poland._body(fields) or "")
        assert text.count(lead) == 1, row["source_id"]
        whole += poland._body(fields) == fields["content"].strip()
    assert whole == 5


def test_the_recorded_body_names_eleven_voivodeships_four_of_them_with_letters() -> None:
    """Why the row carries two fields (D-055): name and slug differ for four."""
    names = dict(pair for row in _recorded() for pair in poland._names(row))
    assert len(names) == 11
    assert {s: n for s, n in names.items() if s != n} == {
        "dolnoslaskie": "dolnośląskie", "slaskie": "śląskie",
        "swietokrzyskie": "świętokrzyskie", "warminsko-mazurskie": "warmińsko-mazurskie"}


def test_an_all_clear_is_an_air_communique_first() -> None:
    assert poland.classify("Odwołanie ostrzeżenia hydrologicznego",
                           "Zakończono ostrzeżenie. Stan wody opada.") is None
    assert poland.classify("Alert RCB", "Na razie brak zagrożenia dla Polski. "
                           "Rosyjski atak powietrzny na Ukrainę.") == ("threat", "powietrzn")
    assert poland.classify("Test syren", "Odwołanie alarmu powietrznego - ćwiczenia") is None


def test_a_threat_issued_after_the_all_clear_is_a_new_threat() -> None:
    page = _page(
        _news("3", "Alert RCB", *ALERT, "2026-09-16 09:00:00", ("lubelskie",)),
        _news("2", "ALERT RCB- ODWOŁANIE ZAGROŻENIA", *CLEAR, "2026-09-16 07:36:00",
              ("lubelskie",)),
        _news("1", "Alert RCB", *ALERT, "2026-09-16 07:05:00", ("lubelskie",)),
    )
    painted, cleared = poland.warnings_rows(_rows(page), MIDDAY)
    assert [c["id"] for c in painted[0]["communiques"]] == ["3"]
    assert cleared[0]["communiques"][0]["ended"] == ["1"]


def test_an_unreadable_issue_stamp_keeps_the_warning_and_ends_nothing() -> None:
    page = _page(
        _news("2", "ALERT RCB- ODWOŁANIE ZAGROŻENIA", *CLEAR, "not a date", ("lubelskie",)),
        _news("1", "Alert RCB", *ALERT, "2026-09-16 07:05:00", ("lubelskie",)),
    )
    painted, cleared = poland.warnings_rows(_rows(page), MIDDAY)
    assert [c["id"] for c in painted[0]["communiques"]] == ["1"]
    assert cleared[0]["communiques"][0]["ended"] == []
    page = _page(
        _news("2", "ALERT RCB- ODWOŁANIE ZAGROŻENIA", *CLEAR, "2026-09-16 07:36:00",
              ("lubelskie",)),
        _news("1", "Alert RCB", *ALERT, "", ("lubelskie",)),
    )
    painted, _cleared = poland.warnings_rows(_rows(page), MIDDAY)
    assert [c["id"] for c in painted[0]["communiques"]] == ["1"]


def test_an_all_clear_with_nothing_to_end_is_still_published() -> None:
    page = _page(_news("2", "ALERT RCB- ODWOŁANIE ZAGROŻENIA", *CLEAR,
                       "2026-09-16 07:36:00", ("lubelskie",)))
    painted, cleared = poland.warnings_rows(_rows(page), MIDDAY)
    assert painted == []
    assert cleared[0]["communiques"][0]["ended"] == []


def test_valid_to_still_ends_a_row_the_publisher_never_cleared() -> None:
    painted, cleared = poland.warnings_rows(_rows(PAIR), datetime(2026, 9, 16, 22, 0, tzinfo=UTC))
    assert painted == [] and cleared == []


def test_the_lead_sentence_is_not_repeated() -> None:
    fields = {"shortcut": ALERT[0], "content": ALERT[1]}
    assert poland._body(fields) == ALERT[1]
    assert poland._body({"shortcut": "A.", "content": "B."}) == "A. B."
    assert poland._body({"shortcut": "A.", "content": None}) == "A."
    assert poland._body({"shortcut": "Lead\nwrapped.", "content": "Header.\n\nLead wrapped. Rest."}
                        ) == "Header.\n\nLead wrapped. Rest."
    assert poland._body({"shortcut": None, "content": None}) is None


def test_the_row_shows_the_feeds_name_and_joins_on_the_publishers_slug() -> None:
    """`voivodeship` is what a reader sees, `slug` is what anything joins on (D-055)."""
    page = _page(_news("1", "Alert RCB", *ALERT, "2026-09-16 07:05:00", ("x",)).replace(
        'slug="x" city="">X', 'slug="warminsko-mazurskie" city="">Warmińsko-Mazurskie'))
    painted, _ = poland.warnings_rows(_rows(page), MIDDAY)
    assert painted[0]["voivodeship"] == "warmińsko-mazurskie"
    assert painted[0]["slug"] == "warminsko-mazurskie"
    assert list(painted[0]) == ["voivodeship", "slug", "communiques"]


def test_an_empty_province_element_shows_the_slug() -> None:
    page = _page(_news("1", "Alert RCB", *ALERT, "2026-09-16 07:05:00", ("x",)).replace(
        'slug="x" city="">X', 'slug="slaskie" city="">'))
    painted, _ = poland.warnings_rows(_rows(page), MIDDAY)
    assert (painted[0]["voivodeship"], painted[0]["slug"]) == ("slaskie", "slaskie")
    # The parser already falls back to the slug; a stored row written with no
    # name reaches the same answer rather than the text "none".
    assert poland._names({"provinces": [["slaskie", None, None]]}) == (("slaskie", "slaskie"),)


def test_pairing_and_grouping_go_by_slug_not_by_the_text_shown() -> None:
    """An all-clear writing the name differently still ends the threat it names.

    Whether RCB ever spells one voivodeship two ways is `[nieustalone]`; the
    test pins that the key which decides a clearance is the one the publisher
    keeps constant, and that one voivodeship is one row whatever its spelling.
    """
    alert = _news("1", "Alert RCB", *ALERT, "2026-09-16 07:05:00", ("x",)).replace(
        'slug="x" city="">X', 'slug="slaskie" city="">Śląskie')
    second = _news("3", "Alert RCB", *ALERT, "2026-09-16 07:10:00", ("x",)).replace(
        'slug="x" city="">X', 'slug="slaskie" city="">slaskie')
    clear = _news("2", "ALERT RCB- ODWOŁANIE ZAGROŻENIA", *CLEAR, "2026-09-16 07:36:00",
                  ("x",)).replace('slug="x" city="">X', 'slug="slaskie" city="">ŚLĄSKIE')
    painted, cleared = poland.warnings_rows(_rows(_page(clear, second, alert)), MIDDAY)
    assert painted == []
    (row,) = cleared
    assert (row["voivodeship"], row["slug"]) == ("śląskie", "slaskie")
    assert row["communiques"][0]["ended"] == ["3", "1"]
    painted, _ = poland.warnings_rows(_rows(_page(second, alert)), MIDDAY)
    assert [(r["voivodeship"], r["slug"]) for r in painted] == [("slaskie", "slaskie")]
    assert [c["id"] for c in painted[0]["communiques"]] == ["3", "1"]


def test_the_third_key_travels_with_the_first(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events")
    _write_page(store, poland.WARNINGS_URL, MIDDAY - timedelta(minutes=5), PAIR)
    blocks = poland.measure(store, MIDDAY)
    assert [r["voivodeship"] for r in blocks.warnings.value] == ["mazowieckie"]
    assert [r["voivodeship"] for r in blocks.all_clear.value] == ["lubelskie", "podkarpackie"]
    assert all(r["slug"] == r["voivodeship"] for r in blocks.warnings.value)
    payload = to_contract(compose([_event()], as_of=MIDDAY, poland=lambda _m: blocks))
    assert set(payload) >= {"pl_warnings", "pl_all_clear"} and "pl_airspace" not in payload
    stale = poland.measure(store, MIDDAY + timedelta(hours=2))
    assert stale.warnings.value is None and stale.all_clear.value is None
    assert to_contract(compose([_event()], as_of=MIDDAY, poland=lambda _m: poland.FAILED)
                       )["pl_all_clear"] is None


# ---- F174 to F177, found by the review of 0.55.0.1


def test_a_change_night_end_ends_at_the_later_of_its_two_readings() -> None:
    """F177. Both ends below were never an end, which kept them painted for ever."""
    autumn = "2026-10-25 02:30:00"      # 00:30 or 01:30 UTC
    assert poland.is_expired(autumn, datetime(2026, 10, 25, 1, 30, tzinfo=UTC)) is False
    assert poland.is_expired(autumn, datetime(2026, 10, 25, 1, 31, tzinfo=UTC)) is True
    assert poland.is_expired(autumn, datetime(2027, 1, 1, tzinfo=UTC)) is True
    spring = "2026-03-29 02:30:00"      # a wall time the zone never shows
    assert poland.is_expired(spring, datetime(2026, 3, 29, 1, 30, tzinfo=UTC)) is False
    assert poland.is_expired(spring, datetime(2026, 3, 29, 1, 31, tzinfo=UTC)) is True


def test_a_lead_the_body_opens_with_is_printed_once() -> None:
    """F172 on wrapped text, which the recorded body does not exercise: its
    five leads match the content without folding. The recorded case is
    `test_no_recorded_communique_prints_its_lead_twice`."""
    lead = "Zdanie wiodace komunikatu."
    doubled = {"shortcut": lead, "content": "Zdanie  wiodace\nkomunikatu. Dalsza tresc."}
    assert poland._body(doubled) == doubled["content"]
    apart = {"shortcut": "podkarpackie, zlewnie", "content": "W obszarach wystepowania"}
    assert poland._body(apart) == "podkarpackie, zlewnie W obszarach wystepowania"
    assert poland._body({"shortcut": None, "content": None}) is None


@pytest.mark.parametrize("command", ["rso", "airspace"])
def test_a_store_failure_leaves_no_read_vouching_for_the_previous_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    """F176. The read row is the list's age, so it may exist only once the list does.

    Reproduced before the repair with one `\\ud800` escape in a UUP remark: every
    run exited 7, every run logged a fresh read, and `pl_airspace` published
    the previous plan under the new `read_at` with no `stale_error`.
    """
    store_path = tmp_path / "events"
    if command == "rso":
        argv = ["rso", "--stub", str(FIXTURES / "rso_page.xml"), "--category", "ogolne",
                "--store", str(store_path)]
        feed, url = rso.FEED, poland.WARNINGS_URL
    else:
        argv = ["airspace", "--stub", str(UUP), "--store", str(store_path)]
        feed, url = pansa.FEED, pansa.SOURCE_URL
    assert main(argv) == 0
    first = EventStore(store_path).newest_read(feed, url)
    assert first is not None

    def broken(*_args: object, **_kwargs: object) -> bool:
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(EventStore, "record_snapshot", broken)
    assert main(argv) == 7
    assert EventStore(store_path).newest_read(feed, url) == first


def _nested(depth: int) -> list[object]:
    value: list[object] = []
    for _ in range(depth):
        value = [value]
    return value


@pytest.mark.parametrize("value", [
    {"read_at": "x", "features": [{"coordinates": [float("nan"), 50.0]}]},
    {"read_at": "x", "features": [{"coordinates": _nested(2000)}]},
    {"read_at": "x", "remarks": "\ud800"},
], ids=["nan", "deep", "surrogate"])
def test_a_polish_value_the_writer_cannot_write_publishes_both_keys_null(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    value: dict[str, object],
) -> None:
    """F174. D-053 promises the Ukrainian picture survives the Polish side.

    Before the repair `deep` raised `RecursionError` in the writer's own
    `json.dumps`, outside every guard, and no `state.json` was written; `nan`
    was written as a token strict JSON readers refuse. **Whether 2000 levels
    are unwritable depends on the interpreter**: the indented writer refuses
    them on 3.11 and 3.12 and writes them on 3.13 and 3.14 `[measured
    2026-09-19 on 3.11.16, 3.12.3, 3.13.15, 3.14.7]`. What holds on every one
    is the promise: `state.json` is written, as strict JSON, and a value is
    either published or refused with every Polish key `null`.
    """
    monkeypatch.delenv("MAVO_LOG_FILE", raising=False)
    store_path = tmp_path / "events"
    EventStore(store_path)
    blocks = poland.PolandBlocks(airspace=poland.Block(published=True, value=value))
    monkeypatch.setattr("mavo.cli.measure_poland", lambda _store, _moment: blocks)
    state = tmp_path / "state.json"
    assert main(["report", "--store", str(store_path), "--json", str(state),
                 "--watch", "--interval", "0", "--max-cycles", "1"]) == 0

    def refuse(constant: str) -> object:
        raise ValueError(constant)

    payload = json.loads(state.read_text(encoding="utf-8"), parse_constant=refuse)
    if _this_interpreter_writes(value):
        assert payload["pl_airspace"] is not None
        assert "[POLAND-FAILED]" not in capsys.readouterr().err
    else:
        assert payload["pl_warnings"] is None and payload["pl_airspace"] is None
        assert "[POLAND-FAILED]" in capsys.readouterr().err


def _this_interpreter_writes(value: object) -> bool:
    """Whether this interpreter's `json` writes `value` under the writer's settings."""
    try:
        json.dumps(value, ensure_ascii=False, indent=1, allow_nan=False).encode("utf-8")
    except (RecursionError, ValueError, UnicodeEncodeError):
        return False
    return True


def test_an_unwritable_clearance_publishes_every_polish_key_null(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """F174 one key over: D-055 added `pl_all_clear` after the review read the guard.

    A lone surrogate in a clearance's text is refused by the UTF-8 encode; left
    outside the guard it stopped `state.json` exactly as the airspace did.
    """
    monkeypatch.delenv("MAVO_LOG_FILE", raising=False)
    store_path = tmp_path / "events"
    EventStore(store_path)
    row = {"voivodeship": "lubelskie", "slug": "lubelskie",
           "communiques": [{"id": "1", "text": "\ud800", "ended": []}]}
    blocks = poland.PolandBlocks(warnings=poland.Block(published=True, value=[]),
                                 all_clear=poland.Block(published=True, value=[row]))
    monkeypatch.setattr("mavo.cli.measure_poland", lambda _store, _moment: blocks)
    state = tmp_path / "state.json"
    assert main(["report", "--store", str(store_path), "--json", str(state),
                 "--watch", "--interval", "0", "--max-cycles", "1"]) == 0
    payload = json.loads(state.read_text(encoding="utf-8"))
    assert payload["pl_warnings"] is None and payload["pl_all_clear"] is None
    assert "[POLAND-FAILED]" in capsys.readouterr().err



# ---- R7: a negated drill word does not exclude

@pytest.mark.parametrize("text", [
    "UWAGA! Rosyjski atak powietrzny na terenie Ukrainy. To nie są ćwiczenia.",
    "UWAGA! Atak powietrzny. Nie są to ćwiczenia!",
    "Alarm lotniczy - to nie ćwiczenie.",
], ids=["nie-sa", "nie-sa-to", "nie"])
def test_a_threat_that_says_it_is_not_a_drill_is_painted(text: str) -> None:
    verdict = poland.classify("Alert RCB", text)
    assert verdict is not None and verdict[0] == "threat"


def test_the_exception_is_narrow() -> None:
    """Only the negated drill word is set aside; every other exclusion still wins."""
    assert poland.classify("Ćwiczenia", "Ćwiczenia obrony powietrznej w powiecie.") is None
    assert poland.classify("Test syren", "Alarm powietrzny. To nie są ćwiczenia.") is None
    assert poland.classify("Alert RCB", "To nie są ćwiczenia. Ćwiczenia z alarmem "
                           "powietrznym odbędą się jutro.") is None
    # `trening` is not the word R7 named, so its negation keeps excluding.
    assert poland.classify("Alert RCB", "Atak powietrzny. To nie jest trening.") is None
    assert poland.classify("ALERT RCB- ODWOŁANIE ZAGROŻENIA", "Zakończył się atak "
                           "powietrzny. To nie były ćwiczenia.") == ("all_clear", "odwołan")
