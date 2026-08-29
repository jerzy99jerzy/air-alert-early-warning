"""The RSO reader, and the four ways a feed like this reports nothing.

Every test below names the invariant it defends. The fixture is a reduced copy
of a page measured from the live endpoint on 2026-08-20, kept verbatim in its
empty elements: those are the evidence, and reflowing them into absent
elements would edit the thing under test.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo.errors import NaiveTimestamp, SchemaMismatch, SourceUnavailable
from mavo.sources.rso import (
    CATEGORIES,
    FEED,
    AmbiguousLocalTime,
    Communique,
    Page,
    Province,
    page_url,
    parse_page,
    poll_once,
    to_utc,
)
from mavo.store import EventStore
from mavo.transport import FailingTransport, StubTransport

FIXTURE = Path(__file__).parent / "fixtures" / "rso_page.xml"


@pytest.fixture
def page() -> Page:
    return parse_page(FIXTURE.read_bytes())


def test_the_page_reports_its_pagination_as_the_feed_stated_it(page: Page) -> None:
    """Seventeen items across pages of twenty, from the feed's own header."""
    assert page.items_on_page == 17, page
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
    assert page.items_on_page == 2, "the feed's own count survives our own losses"


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
    assert page.items_on_page is None, page
    assert page.items_per_page is None, page


def test_a_pagination_figure_that_is_not_a_number_is_unknown_not_zero() -> None:
    """Same rule one layer down: unreadable is not empty."""
    page = parse_page(b'<newses><pagination_info totalItems="many"/></newses>')
    assert page.items_on_page is None, page


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


# --- 0.38.0.0: the poll path, the table of its own, and the attempt log ------
#
# Everything below was written against a live reading of the endpoint on
# 2026-08-22 rather than against the fixture alone, and the numbers quoted in
# the assertions' messages are from that reading. The fixture is still what the
# tests run on; the measurements are why these particular invariants and not
# others.



def test_a_category_outside_the_published_vocabulary_is_refused() -> None:
    """A sixth slug is a change in the feed, not a string to interpolate."""
    with pytest.raises(SourceUnavailable) as refusal:
        page_url("powietrzne")
    assert "powietrzne" in str(refusal.value)
    assert "stany-wod" in str(refusal.value), "the refusal names the vocabulary it checked"


def test_every_published_category_builds_an_address() -> None:
    """Five slugs, measured from /kategorie, and each one resolves."""
    assert len(CATEGORIES) == 5, CATEGORIES
    for name in CATEGORIES:
        assert page_url(name, 3).endswith(f"/{name}/3?_format=xml"), name


def test_poll_reads_a_page_through_the_transport(page: Page) -> None:
    """The seam is the transport; the parser never opens a socket."""
    body = FIXTURE.read_text(encoding="utf-8")
    read, elapsed = poll_once(StubTransport(body), page_url("ogolne"))
    assert [c.id for c in read.communiques] == [c.id for c in page.communiques]
    assert elapsed >= 0.0


def test_poll_lets_a_refusal_through_rather_than_returning_an_empty_page() -> None:
    """An unreachable endpoint is not a quiet country, one layer up as well."""
    with pytest.raises(SourceUnavailable):
        poll_once(FailingTransport(), page_url("ogolne"))


def test_communiques_land_in_their_own_table(tmp_path: Path, page: Page) -> None:
    """F25's lesson in SQL: a communique is not an alert with a different state."""
    store = EventStore(tmp_path / "s.sqlite3")
    assert store.append_communiques(FEED, page.communiques) == 2
    assert store.count_communiques(FEED) == 2
    assert store.count() == 0, "nothing reached the alert table"
    rows = list(store.replay_communiques(FEED))
    # Set, not sequence. Both rows share an ingest timestamp, so the order
    # falls to the digest, and asserting a digest-derived order would be a
    # fixture arranged by the implementation rather than against it. What is
    # worth asserting is that the order is *stable*, which is why the tie is
    # broken by a column at all.
    assert {r["source_id"] for r in rows} == {"23260001", "23261045"}
    assert [r["source_id"] for r in store.replay_communiques(FEED)] == [
        r["source_id"] for r in rows
    ], "two replays of an unchanged store agree"
    by_id = {r["source_id"]: r for r in rows}
    assert by_id["23261045"]["provinces"] == [["podkarpackie", "Podkarpackie", None]]
    assert by_id["23261045"]["fields"]["rso_icon"] is None, (
        "empty and absent both read as nothing; measured empty 156/156 on 2026-08-22"
    )


def test_re_reading_the_same_page_adds_nothing(tmp_path: Path, page: Page) -> None:
    """Idempotence by content digest. The feed republishes; the store does not grow."""
    store = EventStore(tmp_path / "s.sqlite3")
    store.append_communiques(FEED, page.communiques)
    assert store.append_communiques(FEED, page.communiques) == 0
    assert store.count_communiques() == 2


def test_an_edited_communique_lands_beside_the_original(tmp_path: Path) -> None:
    """`updated_at` moves and the identifier does not, so both readings survive.

    Keying on the identifier would overwrite the earlier reading and lose the
    fact that the publisher changed its mind, which for a record rather than an
    alarm is the whole content.
    """
    store = EventStore(tmp_path / "s.sqlite3")
    def at(hour: str) -> Communique:
        return Communique(id="7", fields={"title": "Ostrzeżenie", "updated_at": hour})

    first, edited = at("2026-08-20 12:00:00"), at("2026-08-20 13:00:00")
    assert store.append_communiques(FEED, [first]) == 1
    assert store.append_communiques(FEED, [edited]) == 1
    assert store.count_communiques(FEED) == 2


def test_one_feed_does_not_count_another(tmp_path: Path, page: Page) -> None:
    """`feed` is stated by the caller, and the counts respect it."""
    store = EventStore(tmp_path / "s.sqlite3")
    store.append_communiques(FEED, page.communiques)
    assert store.count_communiques("some-other-feed") == 0
    assert list(store.replay_communiques("some-other-feed")) == []


def test_appending_nothing_writes_nothing(tmp_path: Path) -> None:
    """An empty page is a real answer and costs no row."""
    store = EventStore(tmp_path / "s.sqlite3")
    assert store.append_communiques(FEED, []) == 0


def test_a_refusal_and_an_empty_page_are_stored_differently(tmp_path: Path) -> None:
    """**The property this table exists for.**

    Zero means the publisher said there is nothing. NULL means we did not find
    out. Collapse them and an hour with a dead collector reads as a quiet
    country, which is section 4 of FEED-SPEC applied to our own consumer.
    """
    store = EventStore(tmp_path / "s.sqlite3")
    when = datetime(2026, 8, 22, 14, 0, tzinfo=UTC)
    store.record_read(FEED, "u/read", when, 0, 0)
    store.record_refusal(FEED, "u/refused", when, "connection timed out")

    rows = store.attempts(FEED)
    assert [r["outcome"] for r in rows] == ["read", "refused"]
    empty, refused = rows
    assert empty["items"] == 0, "a page that was read and held nothing"
    assert refused["items"] is None, "a poll that never found out"
    assert empty["items"] is not refused["items"], "the two must not collapse"
    assert refused["detail"] == "connection timed out"
    assert empty["detail"] is None


def test_the_attempt_log_is_kept_per_feed(tmp_path: Path) -> None:
    """One collector, several endpoints; a silence on one is not a silence on all."""
    store = EventStore(tmp_path / "s.sqlite3")
    when = datetime(2026, 8, 22, 14, 0, tzinfo=UTC)
    store.record_read(FEED, "u", when, 3, 0)
    assert len(store.attempts(FEED)) == 1
    assert store.attempts("elsewhere") == ()


def test_a_naive_timestamp_cannot_enter_the_attempt_log(tmp_path: Path) -> None:
    """The log orders by ISO text, which is chronological in one offset only."""
    store = EventStore(tmp_path / "s.sqlite3")
    with pytest.raises(NaiveTimestamp):
        store.record_read(FEED, "u", datetime(2026, 8, 22, 14, 0), 1, 0)


def test_a_recorded_table_missing_an_unknown_column_is_refused(
    tmp_path: Path,
) -> None:
    """A column this version cannot type is a refusal, not a silent accept.

    Built by hand rather than by an older version of this class, because there
    is no older version to run. The shape is what matters: a `communiques`
    table exists and lacks a column, which `CREATE TABLE IF NOT EXISTS` is
    silent about.

    **The remedy in the message is not D-013's.** `communiques` is a recorded
    table, so "rebuild from the raw corpus" would delete rows nothing can
    reconstruct (F124). The message says to copy the file aside, and this
    assertion holds it to that: the older wording asserted `Rebuild` here and
    was wrong about which table it was talking to.
    """
    path = tmp_path / "old.sqlite3"
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("CREATE TABLE communiques (digest TEXT PRIMARY KEY, feed TEXT)")
    with pytest.raises(SchemaMismatch) as refusal:
        EventStore(path)
    assert "communiques.source_id" in str(refusal.value)
    assert "copy the file aside" in str(refusal.value), "the refusal names the remedy"
    assert "Rebuild" not in str(refusal.value), (
        "a recorded table is not rebuilt from the corpus; naming that remedy here "
        "prescribes deleting the only copy of the evidence (F124)"
    )


def test_a_derived_table_predating_this_version_is_refused_and_named_as_derived(
    tmp_path: Path,
) -> None:
    """D-013 survives for the tables it was written about.

    `events` is derived: every row is reproducible from the raw corpus, so a
    rebuild restores the store and an in-place migration would invent values
    no row ever carried. The refusal keeps that remedy and now says which
    tables it covers, because the previous wording offered it for all four.
    """
    path = tmp_path / "derived.sqlite3"
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("CREATE TABLE events (content_hash TEXT PRIMARY KEY, area_id TEXT)")
    with pytest.raises(SchemaMismatch) as refusal:
        EventStore(path)
    assert "Rebuild" in str(refusal.value)
    assert "events, kind_events" in str(refusal.value), (
        "the refusal states the scope of the remedy it prescribes"
    )


def test_a_recorded_table_gains_a_known_column_instead_of_losing_its_rows(
    tmp_path: Path,
) -> None:
    """F124, and the case that would have bricked the production host.

    A `feed_attempts` table written before 0.41.0.0 has every column but
    `elapsed_s`. Under the previous guard that store was unopenable and the
    documented repair - rebuild from the raw corpus - would have deleted every
    poll record on the machine, none of which is derivable from anything.

    Three assertions, and the row count is the one that matters: the migration
    is additive, the pre-existing row survives, and its new column reads NULL
    rather than a plausible number.
    """
    path = tmp_path / "attempts.sqlite3"
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute(
            "CREATE TABLE feed_attempts (started_at TEXT NOT NULL, feed TEXT NOT NULL, "
            "url TEXT NOT NULL, outcome TEXT NOT NULL, items INTEGER, "
            "unreadable INTEGER, detail TEXT)"
        )
        conn.execute(
            "INSERT INTO feed_attempts (started_at, feed, url, outcome, items, "
            "unreadable, detail) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("2026-08-20T18:19:43+00:00", FEED, "u/old", "read", 4, 0, None),
        )

    store = EventStore(path)
    assert store.migrations_applied == (
        "feed_attempts.elapsed_s",
        "feed_attempts.first_id",
        "feed_attempts.last_id",
    ), "a migration that leaves no trace is the silent repair this project refuses"
    rows = store.attempts(FEED)
    assert len(rows) == 1, "the row written before the column existed survives"
    assert rows[0]["elapsed_s"] is None, (
        "a row that predates the column was never timed; NULL is the honest value "
        "and any number here would be indistinguishable from a measurement"
    )
    assert rows[0]["last_id"] is None, "and it bounded no window either"
    assert EventStore(path).newest_page_id(FEED) is None, (
        "a store with no observed ids has no cursor, and 0 would claim the "
        "channel is at post zero"
    )


def test_an_ordinary_open_reports_no_migration(tmp_path: Path) -> None:
    """The trace is empty when nothing was changed.

    Without this the previous assertion passes against an implementation that
    reports a migration on every open, which would make the line in the
    journal noise and teach a reader to skip it.
    """
    store = EventStore(tmp_path / "fresh.sqlite3")
    assert store.migrations_applied == ()
    assert EventStore(store.path).migrations_applied == (), (
        "re-opening a store this version wrote changes nothing"
    )


def test_a_store_at_the_previous_release_gains_only_what_it_lacks(
    tmp_path: Path,
) -> None:
    """The migration is additive per column, not per release.

    A host that took 0.41.0.0 has `elapsed_s` and not the id bounds. It must
    gain two columns and not three, or the trace stops being a record of what
    changed and becomes a restatement of what this version wants.
    """
    path = tmp_path / "at041.sqlite3"
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute(
            "CREATE TABLE feed_attempts (started_at TEXT NOT NULL, feed TEXT NOT NULL, "
            "url TEXT NOT NULL, outcome TEXT NOT NULL, items INTEGER, "
            "unreadable INTEGER, detail TEXT, elapsed_s REAL)"
        )
    store = EventStore(path)
    assert store.migrations_applied == (
        "feed_attempts.first_id",
        "feed_attempts.last_id",
    )


def test_the_cursor_is_the_highest_id_seen_not_the_most_recent(
    tmp_path: Path,
) -> None:
    """A page that came back short must not move the cursor backwards.

    A retreating cursor reports the messages between as newly skipped and
    counts the same window twice, which is worse than reporting unknown: it is
    a measurement that is confidently wrong.
    """
    store = EventStore(tmp_path / "cursor.sqlite3")
    when = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)
    store.record_read(FEED, "u/1", when, 20, 0, 0.3, first_id=100, last_id=120)
    store.record_refusal(FEED, "u/2", when + timedelta(seconds=33), "timed out", 10.0)
    store.record_read(FEED, "u/3", when + timedelta(seconds=66), 5, 0, 0.3,
                      first_id=101, last_id=105)
    assert store.newest_page_id(FEED) == 120
    assert store.newest_page_id("nothing-polled-this") is None
