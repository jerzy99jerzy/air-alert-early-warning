"""The strike tally from page to contract: store, `mavo kpszsu`, `strike_tally`.

The reader has its own suite on the recordings (`tests/test_kpszsu.py`). This
one covers what 0.56.0.0 adds around it (D-056): the rows the store keeps, the
four states the contract key can be in and the one it never takes, the rule
that a flagged night is published as its headline alone, the catch-up that
walks back when the channel outran the timer, the backfill from a file, and
the guard that keeps a failure here from taking the rest of the contract down.

Every figure asserted below was read off the recordings by hand before this
code ran on them, the order that found the reader's seven defects.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mavo import strike
from mavo.cli import KPSZSU_MAX_PAGES, main
from mavo.errors import SourceUnavailable
from mavo.poland import Block
from mavo.report import compose, to_contract
from mavo.sources import kpszsu
from mavo.store import RECORDED_TABLES_0_56, EventStore

FIXTURES = Path(__file__).parent / "fixtures" / "kpszsu"
T0 = datetime(2026, 9, 22, 6, 0, tzinfo=UTC)


def _block(post: str) -> str:
    """One recorded post as the preview serves it inside a page."""
    return f'data-post="kpszsu/{post}"' + (FIXTURES / f"{post}.html").read_text(encoding="utf-8")


def _page(*posts: str) -> str:
    return "".join(_block(post) for post in posts)


def _reading(post: str) -> kpszsu.Reading:
    page = kpszsu.read_page(_block(post))
    assert len(page.readings) == 1, post
    return page.readings[0]


def _store(tmp_path: Path) -> EventStore:
    return EventStore(tmp_path / "events")


# --- the store -------------------------------------------------------------

def test_a_store_written_by_0_55_gains_the_table_and_says_so(tmp_path: Path) -> None:
    """Additive under D-036: an older store opens and is extended, never refused."""
    path = tmp_path / "events"
    EventStore(path)
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("DROP TABLE strike_tallies")
        conn.commit()
    reopened = EventStore(path)
    assert RECORDED_TABLES_0_56 == ("strike_tallies",)
    assert "strike_tallies (table)" in reopened.migrations_applied
    assert reopened.count_strike_tallies() == 0


def test_rows_are_idempotent_on_the_post_and_its_text(tmp_path: Path) -> None:
    store = _store(tmp_path)
    rows = strike.rows_of(kpszsu.read_page(_page("79268", "79455")))
    assert store.append_strike_tallies(rows) == 2
    assert store.append_strike_tallies(rows) == 0
    edited = replace(rows[1], raw_text=rows[1].raw_text + " ")
    assert store.append_strike_tallies([edited]) == 1, "an edited post must land beside the first"
    assert store.count_strike_tallies() == 3


def test_the_latest_night_is_chosen_by_night_not_by_post(tmp_path: Path) -> None:
    """A correction or a day tally posted later never displaces the night."""
    store = _store(tmp_path)
    store.append_strike_tallies(strike.rows_of(kpszsu.read_page(
        _page("79455", "79268", "78115", "72080"))))
    newest = store.newest_strike_night()
    assert newest is not None
    assert newest["night"] == "2026-09-22"
    assert newest["source_url"] == "https://t.me/kpszsu/79455"


def test_a_store_holding_only_a_correction_and_a_day_has_no_night(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.append_strike_tallies(strike.rows_of(kpszsu.read_page(_page("78115", "72080"))))
    assert store.count_strike_tallies() == 2
    assert store.newest_strike_night() is None


def test_a_refused_correction_is_stored_with_its_text_and_no_figures(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.append_strike_tallies([strike.row_of(_reading("72080"))])
    with closing(sqlite3.connect(tmp_path / "events")) as conn:
        kind, status, tally, checks, raw = conn.execute(
            "SELECT kind, status, tally, checks, raw_text FROM strike_tallies").fetchone()
    assert (kind, status, tally, checks) == (None, "refused", None, "[]")
    assert "Уточнена інформація" in raw


# --- the value --------------------------------------------------------------

def _row(post: str) -> dict[str, object]:
    row = strike.row_of(_reading(post))
    return {
        "night": row.night, "posted_at": row.posted_at.isoformat(), "status": row.status,
        "tally": row.tally, "source_url": row.source_url,
    }


def test_an_ok_night_is_published_with_its_breakdown() -> None:
    """79455, read by hand: 186 downed as 1 + 8 + 177; five launched classes,
    two of them unnumbered, so no launched total may be derived."""
    value = strike.value(_row("79455"), read_at=T0, stale_error=None)
    assert value["check"] == "ok"
    assert value["downed_total"] == 186
    downed = value["downed"]
    assert isinstance(downed, list)
    assert [(item["class"], item["count"]) for item in downed] == [
        ("cruise", 1), ("banderol", 8), ("drone", 177)]
    launched = value["launched"]
    assert isinstance(launched, list)
    assert [item["count"] for item in launched] == [None, None, 4, 8, 212]
    assert value["launched_sum"] is None, "two launched counts were not given"
    assert value["launched_total"] is None
    assert value["as_of"] == "2026-09-22T05:00:00+00:00"
    assert value["source_url"] == "https://t.me/kpszsu/79455"


def test_a_fully_numbered_night_carries_its_sum() -> None:
    """66637, read by hand: two anti-ship, six ballistic and 142 drones, every
    one numbered, so 150 is arithmetic on their figures alone."""
    value = strike.value(_row("66637"), read_at=T0, stale_error=None)
    assert value["check"] == "ok"
    launched = value["launched"]
    assert isinstance(launched, list)
    assert [(item["class"], item["count"]) for item in launched] == [
        ("anti_ship", 2), ("ballistic", 6), ("drone", 142)]
    assert value["launched_sum"] == 150
    assert value["downed_total"] == 132


def test_an_item_they_left_unnumbered_withholds_the_sum() -> None:
    """79268: 172 drones, `а також` a Banderol with no count. No total."""
    value = strike.value(_row("79268"), read_at=T0, stale_error=None)
    launched = value["launched"]
    assert isinstance(launched, list)
    assert [(item["class"], item["count"]) for item in launched] == [
        ("drone", 172), ("banderol", None)]
    assert value["launched_sum"] is None


def test_a_flagged_night_is_published_as_their_headline_alone() -> None:
    """72214 is the one night the corpus flags. Nothing of our reading goes out."""
    reading = _reading("72214")
    assert reading.status == "flagged"
    value = strike.value(_row("72214"), read_at=T0, stale_error=None)
    assert value["check"] == "flagged"
    assert value["downed_total"] is not None, "their headline is theirs and stands"
    for key in ("downed", "launched", "launched_total", "launched_sum"):
        assert value[key] is None, key


def test_the_headline_total_never_adds_up_our_items() -> None:
    """`kpszsu.downed_total` may sum numbered items; the contract may not."""
    tally = strike.tally_json(_reading("79455").tally or pytest.fail("no tally"))
    assert strike.headline_total(tally) == 186
    headless = dict(tally, headline={"total": None, "missiles": None, "drones": None,
                                     "unnumbered": []})
    assert strike.headline_total(headless) is None
    tally["headline"] = {"total": None, "missiles": 2, "drones": 111, "unnumbered": []}
    assert strike.headline_total(tally) == 113


# --- the block: absent, null, value, and never empty ------------------------

def test_the_key_is_absent_before_the_channel_was_ever_polled(tmp_path: Path) -> None:
    assert strike.block(_store(tmp_path), T0).published is False


def test_a_refusal_alone_publishes_null(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.record_refusal(strike.FEED, kpszsu.SOURCE_URL, T0, "HTTP Error 403")
    block = strike.block(store, T0)
    assert block.published and block.value is None


def test_a_read_with_no_night_publishes_null_and_never_an_empty_object(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.record_read(strike.FEED, kpszsu.SOURCE_URL, T0, 20, 0, first_id=1, last_id=20)
    block = strike.block(store, T0)
    assert block.published and block.value is None
    assert block.value != {}


def test_a_refusal_after_the_read_is_named_beside_the_old_night(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.append_strike_tallies([strike.row_of(_reading("79455"))])
    store.record_read(strike.FEED, kpszsu.SOURCE_URL, T0, 20, 0, first_id=1, last_id=20)
    store.record_refusal(strike.FEED, kpszsu.SOURCE_URL, T0 + timedelta(minutes=5),
                         "HTTP Error 429")
    value = strike.block(store, T0 + timedelta(minutes=6)).value
    assert value is not None
    assert value["night"] == "2026-09-22"
    assert value["read_at"] == T0.isoformat()
    assert value["stale_error"] == "HTTP Error 429"


def test_the_contract_carries_the_key_only_when_the_block_is_published() -> None:
    report = compose([], as_of=T0)
    assert "strike_tally" not in to_contract(report)
    published = replace(report, strike=Block(published=True, value=None))
    assert to_contract(published)["strike_tally"] is None
    absent = replace(report, strike=Block(published=False))
    assert "strike_tally" not in to_contract(absent)


# --- the command ------------------------------------------------------------

class _Pages:
    """A transport serving one body per address, and remembering what was asked."""

    def __init__(self, bodies: dict[str, str], refuse: bool = False) -> None:
        self.bodies = bodies
        self.refuse = refuse
        self.asked: list[str] = []

    def fetch(self, url: str) -> str:
        self.asked.append(url)
        if self.refuse:
            raise SourceUnavailable("HTTP Error 403: Forbidden")
        return self.bodies.get(url, "")


def _attempts(path: Path) -> list[tuple[object, ...]]:
    with closing(sqlite3.connect(path)) as conn:
        return conn.execute(
            "SELECT outcome, items, first_id, last_id, detail, elapsed_s FROM feed_attempts "
            "WHERE feed = 'kpszsu' ORDER BY rowid").fetchall()


def test_a_stubbed_page_is_stored_and_the_read_carries_its_bounds(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    stub = tmp_path / "page.html"
    stub.write_text(_page("79268", "79455"), encoding="utf-8")
    store = tmp_path / "events"
    assert main(["kpszsu", "--stub", str(stub), "--store", str(store)]) == 0
    out = capsys.readouterr().out
    assert "messages=2" in out and "summaries: ok=2" in out and "stored=2" in out
    [(outcome, items, first_id, last_id, detail, elapsed)] = _attempts(store)
    assert (outcome, items, first_id, last_id, detail) == ("read", 2, 79268, 79455, None)
    assert elapsed is not None


def test_a_refusal_is_logged_before_the_exit_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pages = _Pages({}, refuse=True)
    monkeypatch.setattr("mavo.cli.UrllibTransport", lambda *a, **k: pages)
    store = tmp_path / "events"
    assert main(["kpszsu", "--store", str(store)]) == 3
    [(outcome, items, first_id, last_id, detail, _)] = _attempts(store)
    assert (outcome, items, first_id, last_id) == ("refused", None, None, None)
    assert "403" in str(detail)


def _ids_page(first: int, last: int) -> str:
    """A page of plain posts with the given ids, none of them a summary."""
    return "".join(
        f'data-post="kpszsu/{n}"><div class="tgme_widget_message_text js-message_text">'
        f'post {n}</div><time datetime="2026-09-22T05:00:00+00:00"></time>'
        for n in range(first, last + 1)
    )


def test_the_command_walks_back_until_it_meets_what_it_saw(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The morning summary pushed off the first page between two reads."""
    store_path = tmp_path / "events"
    store = EventStore(store_path)
    store.record_read(strike.FEED, kpszsu.SOURCE_URL, T0, 20, 0, first_id=60, last_id=79)
    pages = _Pages({
        kpszsu.SOURCE_URL: _ids_page(120, 139),
        kpszsu.page_url(120): _ids_page(100, 119),
        kpszsu.page_url(100): _page("79455").replace("kpszsu/79455", "kpszsu/99")
        + _ids_page(80, 98),
    })
    monkeypatch.setattr("mavo.cli.UrllibTransport", lambda *a, **k: pages)
    assert main(["kpszsu", "--store", str(store_path)]) == 0
    assert pages.asked == [kpszsu.SOURCE_URL, kpszsu.page_url(120), kpszsu.page_url(100)]
    newest = _attempts(store_path)[-1]
    assert newest[:5] == ("read", 60, 80, 139, None), "bridged, so nothing is skipped"
    assert EventStore(store_path).count_strike_tallies() == 1


def test_what_the_walk_could_not_bridge_is_written_as_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store_path = tmp_path / "events"
    EventStore(store_path).record_read(strike.FEED, kpszsu.SOURCE_URL, T0, 20, 0,
                                       first_id=1, last_id=10)
    bodies = {kpszsu.SOURCE_URL: _ids_page(1000, 1019)}
    for step in range(1, KPSZSU_MAX_PAGES):
        top = 1000 - 20 * (step - 1)
        bodies[kpszsu.page_url(top)] = _ids_page(top - 20, top - 1)
    pages = _Pages(bodies)
    monkeypatch.setattr("mavo.cli.UrllibTransport", lambda *a, **k: pages)
    assert main(["kpszsu", "--store", str(store_path)]) == 0
    assert len(pages.asked) == KPSZSU_MAX_PAGES
    newest = _attempts(store_path)[-1]
    assert newest[4] == "skipped_before=920"


def test_a_first_poll_reads_one_page(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No cursor, nothing to bridge: a fresh store is filled by `--from-file`."""
    pages = _Pages({kpszsu.SOURCE_URL: _ids_page(500, 519)})
    monkeypatch.setattr("mavo.cli.UrllibTransport", lambda *a, **k: pages)
    assert main(["kpszsu", "--store", str(tmp_path / "events")]) == 0
    assert pages.asked == [kpszsu.SOURCE_URL]


def test_a_page_that_does_not_move_back_stops_the_walk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store_path = tmp_path / "events"
    EventStore(store_path).record_read(strike.FEED, kpszsu.SOURCE_URL, T0, 20, 0,
                                       first_id=1, last_id=10)
    same = _ids_page(1000, 1019)
    pages = _Pages({kpszsu.SOURCE_URL: same, kpszsu.page_url(1000): same})
    monkeypatch.setattr("mavo.cli.UrllibTransport", lambda *a, **k: pages)
    assert main(["kpszsu", "--store", str(store_path)]) == 0
    assert len(pages.asked) == 2
    assert _attempts(store_path)[-1][4] == "skipped_before=1000"


# --- the backfill -----------------------------------------------------------

def test_the_corpus_backfills_as_measured(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The 98 summaries: 91 nights, 6 days, 1 correction, 72214 the one flag."""
    corpus = tmp_path / "summaries.jsonl"
    text = (FIXTURES / "summaries.jsonl").read_text(encoding="utf-8")
    corpus.write_text(text + "\nnot json\n{\"id\": 1}\n", encoding="utf-8")
    store_path = tmp_path / "events"
    assert main(["kpszsu", "--from-file", str(corpus), "--store", str(store_path)]) == 0
    out = capsys.readouterr().out
    assert "unreadable=2" in out
    assert "summaries: flagged=1 ok=96 refused=1" in out and "stored=98" in out
    with closing(sqlite3.connect(store_path)) as conn:
        kinds = dict(conn.execute(
            "SELECT COALESCE(kind, 'none'), COUNT(*) FROM strike_tallies GROUP BY kind"))
        flagged = conn.execute(
            "SELECT post_id FROM strike_tallies WHERE status = 'flagged'").fetchall()
    assert kinds == {"night": 91, "day": 6, "none": 1}
    assert flagged == [(72214,)]
    newest = EventStore(store_path).newest_strike_night()
    assert newest is not None and newest["night"] == "2026-09-22"
    assert _attempts(store_path) == [], "a file is not a read of the channel"


def test_a_missing_file_is_refused_with_its_own_code(tmp_path: Path) -> None:
    assert main(["kpszsu", "--from-file", str(tmp_path / "absent.jsonl")]) == 2


# --- the guard --------------------------------------------------------------

def test_a_failure_to_compose_the_tally_nulls_it_and_nothing_else(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("MAVO_LOG_FILE", raising=False)
    store_path = tmp_path / "events"
    EventStore(store_path)

    def broken(_store: EventStore, _moment: datetime) -> Block:
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr("mavo.cli.measure_strike", broken)
    state = tmp_path / "state.json"
    assert main(["report", "--store", str(store_path), "--json", str(state),
                 "--watch", "--interval", "0", "--max-cycles", "1"]) == 0
    payload = json.loads(state.read_text(encoding="utf-8"))
    assert payload["strike_tally"] is None
    assert "areas" in payload, "the Ukrainian picture must survive the tally"
    assert "[STRIKE-FAILED] disk I/O error" in capsys.readouterr().err


# --- failures that must leave a trace, or none --------------------------------

def test_a_store_that_cannot_be_opened_exits_7(tmp_path: Path) -> None:
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("x", encoding="utf-8")
    stub = tmp_path / "page.html"
    stub.write_text(_page("79455"), encoding="utf-8")
    assert main(["kpszsu", "--stub", str(stub), "--store", str(blocker / "events")]) == 7


def test_a_refusal_during_the_walk_keeps_what_was_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    store_path = tmp_path / "events"
    EventStore(store_path).record_read(strike.FEED, kpszsu.SOURCE_URL, T0, 20, 0,
                                       first_id=1, last_id=10)

    class _Refusing(_Pages):
        def fetch(self, url: str) -> str:
            if url != kpszsu.SOURCE_URL:
                self.asked.append(url)
                raise SourceUnavailable("HTTP Error 429")
            return super().fetch(url)

    pages = _Refusing({kpszsu.SOURCE_URL: _ids_page(1000, 1019)})
    monkeypatch.setattr("mavo.cli.UrllibTransport", lambda *a, **k: pages)
    assert main(["kpszsu", "--store", str(store_path)]) == 0
    assert "[CATCH-UP-REFUSED] HTTP Error 429" in capsys.readouterr().out
    newest = _attempts(store_path)[-1]
    assert newest[:5] == ("read", 20, 1000, 1019, "skipped_before=1000")


def test_a_store_that_fails_mid_write_leaves_no_read_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The read row is `read_at`; it must never vouch for rows that did not land."""
    def broken(self: EventStore, rows: object) -> int:
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(EventStore, "append_strike_tallies", broken)
    stub = tmp_path / "page.html"
    stub.write_text(_page("79455"), encoding="utf-8")
    store_path = tmp_path / "events"
    assert main(["kpszsu", "--stub", str(stub), "--store", str(store_path)]) == 7
    assert _attempts(store_path) == []
    corpus = tmp_path / "one.jsonl"
    corpus.write_text((FIXTURES / "summaries.jsonl").read_text(encoding="utf-8")
                      .splitlines()[0] + "\n", encoding="utf-8")
    assert main(["kpszsu", "--from-file", str(corpus), "--store", str(store_path)]) == 7



# --- the headline of a night that names one class (F187) --------------------

CORPUS = FIXTURES / "summaries.jsonl"


def _corpus_readings() -> tuple[kpszsu.Reading, ...]:
    """The 98 recorded summaries as readings, in the order the file holds them."""
    readings = []
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        message = kpszsu.Message(
            int(record["id"]),
            datetime.fromisoformat(str(record["posted_at"])).astimezone(UTC),
            str(record["text"]),
        )
        reading = kpszsu.read_message(message)
        if reading is not None:
            readings.append(reading)
    return tuple(readings)


def _corpus_nights() -> dict[str, kpszsu.Reading]:
    """One recording per night, by the night it covers."""
    return {
        reading.tally.night.isoformat(): reading
        for reading in _corpus_readings()
        if reading.tally is not None
        and reading.tally.kind == "night"
        and reading.tally.night is not None
    }


def _corpus_row(night: str) -> dict[str, object]:
    reading = _corpus_nights()[night]
    row = strike.row_of(reading)
    return {
        "night": row.night, "posted_at": row.posted_at.isoformat(),
        "status": row.status, "tally": row.tally, "source_url": row.source_url,
    }


def test_a_drone_only_headline_is_a_figure_they_published() -> None:
    """78455, read by hand: `ЗБИТО/ПОДАВЛЕНО 63 ВОРОЖІ БПЛА`, and below it 80
    launched. One class named, one figure stated, for the whole night. Until
    0.57.0.0 the contract answered `null` here and the page printed that no
    figure was given above a breakdown listing those same 63 drones."""
    value = strike.value(_corpus_row("2026-09-16"), read_at=T0, stale_error=None)
    assert value["downed_total"] == 63


def test_an_unnumbered_class_in_the_headline_withholds_the_single_figure() -> None:
    """66963: a Kh-59 `ТА 130 ВОРОЖИХ БПЛА`, the missile carrying no number.
    The night's total is not 130 and we do not know what it is."""
    value = strike.value(_row("66963"), read_at=T0, stale_error=None)
    assert value["downed_total"] is None


def test_the_repair_is_the_size_the_defect_log_claims() -> None:
    """91 nights recorded: 55 carried a headline figure under the two-branch
    rule, 90 carry one under this one. The difference is 35 nights, two in
    five, on which their own number was published as an unknown (F187)."""
    def two_branch(tally: dict[str, object]) -> int | None:
        head = tally["headline"]
        assert isinstance(head, dict)
        if head["total"] is not None:
            return int(head["total"])
        if head["missiles"] is not None and head["drones"] is not None:
            return int(head["missiles"]) + int(head["drones"])
        return None

    tallies = [strike.tally_json(reading.tally)
               for reading in _corpus_nights().values()
               if reading.tally is not None]
    assert len(tallies) == 91
    assert sum(two_branch(one) is not None for one in tallies) == 55
    assert sum(strike.headline_total(one) is not None for one in tallies) == 90


# --- the series the store keeps ---------------------------------------------

def test_the_series_keeps_the_latest_reading_of_each_night(tmp_path: Path) -> None:
    """A night re-read after an edit is one column of the chart, not two, and
    the column is the reading `newest_strike_night` publishes."""
    store = _store(tmp_path)
    first = strike.row_of(_reading("79455"))
    edited = replace(first, post_id=79456, raw_text=first.raw_text + " (уточнено)",
                     posted_at=first.posted_at + timedelta(hours=1))
    store.append_strike_tallies([first, edited])
    series = store.strike_nights_since("2026-09-01")
    assert [row["night"] for row in series] == ["2026-09-22"]
    assert series[0]["post_id"] == 79456
    newest = store.newest_strike_night()
    assert newest is not None and newest["post_id"] == series[-1]["post_id"]


def test_the_series_is_oldest_first_and_starts_where_it_was_told(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    store.append_strike_tallies(
        [strike.row_of(reading) for reading in _corpus_nights().values()])
    series = store.strike_nights_since("2026-09-16")
    nights = [row["night"] for row in series]
    assert nights == sorted(nights)
    assert nights[0] == "2026-09-16" and nights[-1] == "2026-09-22"


def test_a_day_tally_and_a_refusal_stay_out_of_the_series(tmp_path: Path) -> None:
    """The same filter as the block above it: a day is stored and not shown,
    and a correction carries no figures to draw."""
    store = _store(tmp_path)
    store.append_strike_tallies(
        [strike.row_of(_reading(post)) for post in ("78115", "69965", "79455")])
    assert [row["night"] for row in store.strike_nights_since("2026-01-01")] == [
        "2026-09-22"]


# --- the windows (D-057) ----------------------------------------------------

def _corpus_store(tmp_path: Path, read_at: datetime = T0) -> EventStore:
    store = _store(tmp_path)
    store.append_strike_tallies(
        [strike.row_of(reading) for reading in _corpus_readings()])
    store.record_read(strike.FEED, kpszsu.SOURCE_URL, read_at, 20, 0,
                      first_id=1, last_id=20)
    return store


def test_the_windows_are_absent_before_the_channel_was_ever_polled(
    tmp_path: Path,
) -> None:
    assert strike.history(_store(tmp_path), T0).published is False


def test_a_read_with_no_night_publishes_null_windows(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.record_read(strike.FEED, kpszsu.SOURCE_URL, T0, 20, 0,
                      first_id=1, last_id=20)
    block = strike.history(store, T0)
    assert block.published and block.value is None


def test_the_corpus_folds_into_the_three_windows_as_measured(
    tmp_path: Path,
) -> None:
    """Read off the recordings: seven nights to 22.09 give 842 shot down, the
    thirty to the same night 4300, and the ninety 12034 over 89 of 90 nights.
    The ninetieth is 01.07, whose headline names a missile without a number,
    so the window is complete in nights read and incomplete in figures - the
    two counts the page needs to choose its sentence."""
    value = strike.history(_corpus_store(tmp_path), T0).value
    assert value is not None
    assert value["latest_night"] == "2026-09-22"
    assert value["as_of_date"] == "2026-09-22"
    windows = {one["days"]: one for one in value["windows"]}
    assert sorted(windows) == [7, 30, 90]
    assert windows[7]["start"] == "2026-09-16" and windows[7]["end"] == "2026-09-22"
    assert windows[7]["downed"] == {
        "sum": 842, "nights": 7, "complete": True,
        "max": 186, "max_night": "2026-09-22"}
    assert windows[30]["downed"]["sum"] == 4300
    assert windows[30]["downed"]["complete"] is True
    assert windows[90]["start"] == "2026-06-25"
    assert windows[90]["nights_read"] == 90
    assert windows[90]["downed"] == {
        "sum": 12034, "nights": 89, "complete": False,
        "max": 524, "max_night": "2026-07-02"}
    assert len(value["nights"]) == 90, "the series spans the longest window"
    assert value["nights"][0]["night"] == "2026-06-25"
    assert value["nights"][-1]["night"] == "2026-09-22"


def test_the_night_with_no_figure_is_a_gap_and_never_a_zero(
    tmp_path: Path,
) -> None:
    value = strike.history(_corpus_store(tmp_path), T0).value
    assert value is not None
    gaps = [one for one in value["nights"] if one["downed"] is None]
    assert [one["night"] for one in gaps] == ["2026-07-01"]
    assert all(one["downed"] != 0 for one in value["nights"])


def test_launched_is_counted_only_where_they_gave_every_number(
    tmp_path: Path,
) -> None:
    """Three of the last seven nights carry a launched figure. The sum stands
    with the count beside it, so the page can say `at least` rather than pass
    off four unknown nights as nothing."""
    value = strike.history(_corpus_store(tmp_path), T0).value
    assert value is not None
    week = {one["days"]: one for one in value["windows"]}[7]
    assert week["launched"] == {
        "sum": 394, "nights": 3, "complete": False,
        "max": 176, "max_night": "2026-09-19"}


def test_a_flagged_night_keeps_its_headline_and_loses_its_launched(
    tmp_path: Path,
) -> None:
    """72214 is the one flagged night in the corpus. Its headline is theirs
    and stays in the series; everything our reading produced is withheld, as
    it is in the night's own block."""
    value = strike.history(_corpus_store(tmp_path), T0).value
    assert value is not None
    flagged = [one for one in value["nights"] if one["check"] == "flagged"]
    assert [one["night"] for one in flagged] == ["2026-08-10"]
    assert flagged[0]["downed"] == 96
    assert flagged[0]["launched"] is None


def test_an_empty_window_has_no_sum_rather_than_a_zero(tmp_path: Path) -> None:
    """A store holding one old night: the week is empty, and an empty week is
    not a week on which nothing was shot down."""
    store = _store(tmp_path)
    store.append_strike_tallies([strike.row_of(_reading("66440"))])
    store.record_read(strike.FEED, kpszsu.SOURCE_URL, T0, 20, 0,
                      first_id=1, last_id=20)
    value = strike.history(store, T0).value
    assert value is not None
    week = {one["days"]: one for one in value["windows"]}[7]
    assert week["nights_read"] == 0
    assert week["downed"] == {"sum": None, "nights": 0, "complete": False,
                              "max": None, "max_night": None}


def test_the_window_ends_on_the_night_a_summary_was_read_for(
    tmp_path: Path,
) -> None:
    """The night in progress has no summary until the morning. With today's
    reading held the window ends today; without it, yesterday - asked of the
    store rather than of a clock hour nobody could defend twice a year."""
    store = _corpus_store(tmp_path)
    value = strike.history(store, T0).value
    assert value is not None and value["windows"][0]["end"] == "2026-09-22"
    later = strike.history(store, T0 + timedelta(days=1)).value
    assert later is not None
    assert later["as_of_date"] == "2026-09-23"
    assert later["windows"][0]["end"] == "2026-09-22", "no reading for the 23rd"
    assert later["windows"][0]["start"] == "2026-09-16", "seven nights, not six"


def test_a_pipe_that_stopped_shows_the_days_it_missed(tmp_path: Path) -> None:
    """The window is seven days of the calendar and not seven days of ours.
    Four days after the last summary the week holds three nights, and the
    figure the page prints is a figure over three nights, marked as one."""
    store = _corpus_store(tmp_path)
    value = strike.history(store, T0 + timedelta(days=4)).value
    assert value is not None
    week = {one["days"]: one for one in value["windows"]}[7]
    assert week["end"] == "2026-09-25" and week["start"] == "2026-09-19"
    assert week["nights_read"] == 4
    assert week["downed"]["nights"] == 4 and week["downed"]["complete"] is False
    assert value["latest_night"] == "2026-09-22", "the tally above says the same"


def test_the_contract_carries_the_windows_only_when_published() -> None:
    report = compose([], as_of=T0)
    assert "strike_history" not in to_contract(report)
    published = replace(report, strike_history=Block(published=True, value=None))
    assert to_contract(published)["strike_history"] is None
    absent = replace(report, strike_history=Block(published=False))
    assert "strike_history" not in to_contract(absent)


def test_a_failure_to_fold_the_windows_leaves_the_night_standing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The night is the figure a reader came for. A fold over ninety nights
    has more ways to fail than a read of one, and its own guard is why the
    first cannot take the second down with it."""
    monkeypatch.delenv("MAVO_LOG_FILE", raising=False)
    store = _corpus_store(tmp_path)
    assert store.newest_strike_night() is not None

    def broken(_store: EventStore, _moment: datetime) -> Block:
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr("mavo.cli.measure_strike_history", broken)
    state = tmp_path / "state.json"
    assert main(["report", "--store", str(tmp_path / "events"),
                 "--json", str(state), "--watch", "--interval", "0",
                 "--max-cycles", "1"]) == 0
    payload = json.loads(state.read_text(encoding="utf-8"))
    assert payload["strike_history"] is None
    assert payload["strike_tally"] is not None, "the night survives the windows"
    assert "[STRIKE-HISTORY-FAILED] disk I/O error" in capsys.readouterr().err


def test_the_series_carries_a_column_for_every_night_of_the_window(
    tmp_path: Path,
) -> None:
    """Dense, and this is the property the chart rests on. Four days after the
    last summary the week still has seven entries: three of them are nights
    nobody read, and a series that simply left them out would draw four
    columns across seven days and look complete."""
    value = strike.history(_corpus_store(tmp_path), T0 + timedelta(days=4)).value
    assert value is not None
    week = {one["days"]: one for one in value["windows"]}[7]
    nights = [one["night"] for one in value["nights"]
              if week["start"] <= one["night"] <= week["end"]]
    assert nights == ["2026-09-19", "2026-09-20", "2026-09-21", "2026-09-22",
                      "2026-09-23", "2026-09-24", "2026-09-25"]
    unread = [one for one in value["nights"] if not one["read"]]
    assert [one["night"] for one in unread[-3:]] == [
        "2026-09-23", "2026-09-24", "2026-09-25"]
    assert all(one["downed"] is None and one["check"] is None for one in unread)
    assert week["nights_read"] == 4, "read nights, not entries"


def test_a_night_read_without_a_figure_is_not_a_night_nobody_read(
    tmp_path: Path,
) -> None:
    """Two kinds of blank, told apart by `read`. 01.07 was read and gave no
    figure the Air Force stated; a night after the last summary was not read
    at all. Both draw empty and they are different claims about us."""
    value = strike.history(_corpus_store(tmp_path), T0).value
    assert value is not None
    by_night = {one["night"]: one for one in value["nights"]}
    assert by_night["2026-07-01"] == {
        "night": "2026-07-01", "read": True, "downed": None,
        "launched": None, "check": "ok"}, (
        "read, and neither figure survives their own wording: a missile with "
        "no number stands in the headline and another in the launched list")
    assert all(one["read"] for one in value["nights"]), "the corpus has no hole"
