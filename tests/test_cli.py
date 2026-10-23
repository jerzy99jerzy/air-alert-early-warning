"""CLI smoke level: wiring exercised through its callees."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from mavo.cli import main
from mavo.errors import SourceUnavailable
from mavo.poland import AIR_URL, WARNINGS_URL
from mavo.schema import AlertState, ThreatEvent
from mavo.sources.rso import ALL_SCOPE_URL as RSO_ALL_SCOPE_URL
from mavo.store import EventStore
from mavo.transport import FailingTransport


def test_fixture_command_writes_a_store(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "fixture.sqlite"
    assert main(["fixture", "--out", str(out), "--weeks", "4"]) == 0
    assert out.exists()
    assert "events_added=" in capsys.readouterr().out


def test_gate_command_reports_every_candidate(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["gate", "--weeks", "20"]) == 0
    output = capsys.readouterr().out
    assert "R1-border-active" in output
    assert "validates the gate, not any hypothesis" in output


def test_no_subcommand_is_an_error() -> None:
    with pytest.raises(SystemExit):
        main([])


def test_policy_command_reports_both_regimes(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["policy", "--weeks", "40"]) == 0
    output = capsys.readouterr().out
    assert "missile/CONJ-missile" in output
    assert "POLICY combined" in output


def test_collect_save_raw_writes_the_fetched_body_verbatim(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # T19. The corpus for the sprint-5 redesign can only be built forward in
    # time, so the snapshot is taken before parsing and byte-identical to what
    # the transport returned.
    page = tmp_path / "page.html"
    page.write_text("<html>verbatim body, parsed or not</html>", encoding="utf-8")
    raw_dir = tmp_path / "corpus"
    assert main(["collect", "--stub", str(page), "--save-raw", str(raw_dir)]) == 0
    saved = list(raw_dir.glob("channel-*.html"))
    assert len(saved) == 1
    assert saved[0].read_text(encoding="utf-8") == page.read_text(encoding="utf-8")
    assert "snapshot=" in capsys.readouterr().out


def test_collect_save_raw_failure_refuses_loudly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A snapshot that silently fails to land is a quiet loss of the evidence the
    # redesign needs. Exit 4, distinct from unreachable (3) and from success.
    page = tmp_path / "page.html"
    page.write_text("<html></html>", encoding="utf-8")
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("a file where the snapshot directory should be", encoding="utf-8")
    assert main(["collect", "--stub", str(page), "--save-raw", str(blocker)]) == 4
    assert "[SNAPSHOT-FAILED]" in capsys.readouterr().out


def test_backfill_reports_a_contiguous_corpus(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    page = tmp_path / "page.html"
    page.write_text(
        '<div class="tgme_widget_message" data-post="air_alert_ua/900">'
        '<time datetime="2026-08-01T21:00:00+00:00"></time>'
        '<div class="tgme_widget_message_text js-message_text">Львівська область<br/>'
        "Повітряна тривога</div></div>",
        encoding="utf-8",
    )
    out = tmp_path / "corpus"
    assert main(["backfill", "--out", str(out), "--pages", "1", "--delay", "0",
                 "--stub", str(page)]) == 0
    printed = capsys.readouterr().out
    assert "CONTIGUITY: no gaps" in printed
    assert "stopped:" in printed


def test_backfill_exits_nonzero_when_the_corpus_has_a_hole(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A hole is a finding, not a warning. The exit code carries it so a wrapper
    # script cannot read an incomplete corpus as a complete one.
    out = tmp_path / "corpus"
    out.mkdir()
    (out / "page-000000001-000000020.html").write_text("", encoding="utf-8")
    (out / "page-000000100-000000120.html").write_text("", encoding="utf-8")
    page = tmp_path / "page.html"
    page.write_text("<html>no posts</html>", encoding="utf-8")
    assert main(["backfill", "--out", str(out), "--pages", "1", "--delay", "0",
                 "--stub", str(page)]) == 5
    assert "missing 21..99 (79 posts)" in capsys.readouterr().out


def test_backfill_resume_starts_below_what_is_already_on_disk(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "corpus"
    out.mkdir()
    (out / "page-000000100-000000119.html").write_text("", encoding="utf-8")
    page = tmp_path / "page.html"
    page.write_text("<html>no posts</html>", encoding="utf-8")
    main(["backfill", "--out", str(out), "--pages", "1", "--delay", "0",
          "--resume", "--stub", str(page)])
    assert "resuming below id 100" in capsys.readouterr().out


def test_backfill_refuses_resume_and_before_together(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Two cursors, one loop. Picking one silently would make the printed start
    # point depend on an argument the reader cannot see in the output.
    page = tmp_path / "page.html"
    page.write_text("<html></html>", encoding="utf-8")
    assert main(["backfill", "--out", str(tmp_path / "c"), "--pages", "1",
                 "--resume", "--before", "500", "--stub", str(page)]) == 2
    assert "REFUSED" in capsys.readouterr().out


def test_backfill_resume_on_an_empty_directory_says_so(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    page = tmp_path / "page.html"
    page.write_text("<html></html>", encoding="utf-8")
    main(["backfill", "--out", str(tmp_path / "fresh"), "--pages", "1", "--delay", "0",
          "--resume", "--stub", str(page)])
    assert "nothing on disk yet" in capsys.readouterr().out


def test_backfill_refuses_a_directory_another_run_holds(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from mavo.backfill import DirectoryLock

    out = tmp_path / "corpus"
    out.mkdir()
    # Rewritten at 0.54.4.0. This test used to write a live pid into the lock
    # file and expect a refusal, which tested the *mechanism* - a number in a
    # file - rather than the property. When T26 replaced that mechanism with
    # `flock`, the test failed while the behaviour it names got stronger. A
    # regression that breaks because the implementation improved was written
    # against the implementation; it now holds a real lock and asserts what an
    # operator cares about, which is that the second run does not start.
    held = DirectoryLock(out)
    held.acquire()
    try:
        page = tmp_path / "page.html"
        page.write_text("<html></html>", encoding="utf-8")
        assert main(["backfill", "--out", str(out), "--pages", "1", "--delay", "0",
                     "--stub", str(page)]) == 6
        assert "REFUSED" in capsys.readouterr().out
    finally:
        held.release()


def test_backfill_releases_the_lock_when_it_finishes(tmp_path: Path) -> None:
    # Rewritten at 0.54.6.0 (F162). This used to assert the lock *file* was
    # gone, on the reasoning that a leftover file is one the next run has to
    # reason about - true while the file was the lock, and the reason the
    # first `flock` version kept an `unlink` that let two holders exist at
    # once. Under `flock` the file is inert. What the test was after is that
    # the next run is not blocked, and that is what it now asserts.
    from mavo.backfill import DirectoryLock

    out = tmp_path / "corpus"
    page = tmp_path / "page.html"
    page.write_text("<html></html>", encoding="utf-8")
    main(["backfill", "--out", str(out), "--pages", "1", "--delay", "0",
          "--stub", str(page)])
    after = DirectoryLock(out)
    after.acquire()
    after.release()


# --- 0.38.0.0: `mavo rso` ----------------------------------------------------


def test_rso_walks_every_category_rather_than_trusting_wszystkie(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """**Measured 2026-08-22: `wszystkie` returns 156 of 461 communiques.**

    The five categories are disjoint and hold 461 between them; the endpoint's
    own all-scope drops the 305 in `stany-wod` and says so nowhere. A default
    that read it would produce a partial answer shaped like a complete one, so
    the command reads the list and this test is what keeps it doing so.
    """
    fixture = Path("tests/fixtures/rso_page.xml").read_text(encoding="utf-8")
    stub = tmp_path / "page.xml"
    stub.write_text(fixture, encoding="utf-8")
    store_path = tmp_path / "s.sqlite3"
    code = main(["rso", "--stub", str(stub), "--store", str(store_path)])
    out = capsys.readouterr().out
    assert code == 0
    for name in ("ogolne", "meteorologiczne", "hydrologiczne",
                 "informacje-drogowe", "stany-wod", "atak-z-powietrza"):
        assert f"/{name}/" in out, f"{name} was not read"
    # D-065. The partial scope is read, as a canary, and is never a list.
    [scope_line] = [line for line in out.splitlines() if "/wszystkie/wszystkie/" in line]
    assert " canary " in scope_line
    assert EventStore(store_path).newest_snapshot("rso", RSO_ALL_SCOPE_URL) is None, (
        "the partial scope must never be recorded as a list")


def test_rso_stores_each_communique_once_across_the_walk(tmp_path: Path) -> None:
    """Seven reads of one page are two rows, and the count says which is which."""
    fixture = Path("tests/fixtures/rso_page.xml").read_text(encoding="utf-8")
    stub = tmp_path / "page.xml"
    stub.write_text(fixture, encoding="utf-8")
    store_path = tmp_path / "s.sqlite3"
    assert main(["rso", "--stub", str(stub), "--store", str(store_path)]) == 0
    store = EventStore(store_path)
    assert store.count_communiques("rso") == 2
    assert len(store.attempts("rso")) == 7, "one logged attempt per category and the canary"


def test_rso_refuses_a_category_outside_the_published_vocabulary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """argparse rejects it before any address is built."""
    with pytest.raises(SystemExit):
        main(["rso", "--category", "powietrzne"])


def test_rso_exits_three_when_any_category_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A partial reading must not exit 0.

    One category refusing is not the feed refusing, so the walk continues and
    the others are still read and stored. But the exit code carries the fact
    that the reading is incomplete, because a wrapper reading only stdout would
    otherwise record a short day as a quiet one.
    """
    broken = tmp_path / "broken.xml"
    broken.write_text("<newses><news><id>1</id>", encoding="utf-8")
    store_path = tmp_path / "s.sqlite3"
    code = main(["rso", "--stub", str(broken), "--store", str(store_path)])
    assert code == 3, "a partial reading is not a successful one"
    out = capsys.readouterr().out
    assert "[UNREACHABLE]" in out
    assert "refused=7/7" in out

    # Every refusal left a row, and each row says we did not find out rather
    # than that the publisher had nothing.
    attempts = EventStore(store_path).attempts("rso")
    assert len(attempts) == 7
    assert all(a["outcome"] == "refused" for a in attempts)
    assert all(a["items"] is None for a in attempts)


def _rso_body(*ids: str) -> str:
    """A list holding one bare communique per id, the shape the feed serves."""
    items = "".join(
        f"<news><id>{one}</id><title>t{one}</title>"
        "<provinces><province slug=\"lubelskie\">Lubelskie</province></provinces></news>"
        for one in ids)
    return (f"<newses><pagination_info totalItems=\"{len(ids)}\" itemsPerPage=\"20\"/>"
            f"{items}</newses>")


def _rso_feed(monkeypatch: pytest.MonkeyPatch, bodies: dict[str, str | None]) -> None:
    """The live transport, answering each address with its own body; None refuses."""
    from mavo.sources.rso import page_url

    by_url = {(RSO_ALL_SCOPE_URL if name == "*" else page_url(name, 0)): body
              for name, body in bodies.items()}

    class Feed:
        def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
            body = by_url.get(url, _rso_body())
            if body is None:
                raise SourceUnavailable("refused in the test")
            return body

    monkeypatch.setattr("mavo.cli.UrllibTransport", Feed)


def test_rso_a_communique_in_no_known_category_vouches_for_no_list(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """F203, D-065. The two days of 2026-10-21 replayed against the canary.

    The publisher lists 23441746 in a category the walk does not read. Every
    address answers, so until 0.62.0.0 every read was recorded and the page
    said RCB had been quiet. The run now names the communique, exits 3, and
    leaves no read row for any address, so no list of it can be shown as
    current; the lists and the rows are still kept.
    """
    _rso_feed(monkeypatch, {"*": _rso_body("1", "23441746"), "ogolne": _rso_body("1"),
                            "atak-z-powietrza": _rso_body()})
    store_path = tmp_path / "s.sqlite3"
    code = main(["rso", "--store", str(store_path)])
    out = capsys.readouterr().out
    assert code == 3, "a walk the canary cannot vouch for is a partial reading"
    assert "[UNKNOWN-CATEGORY] 1 communique(s)" in out and "23441746" in out
    store = EventStore(store_path)
    attempts = store.attempts("rso")
    assert len(attempts) == 7
    assert all(a["outcome"] == "refused" for a in attempts), "a list was vouched for"
    assert all("[UNKNOWN-CATEGORY]" in str(a["detail"]) for a in attempts)
    assert store.newest_snapshot("rso", WARNINGS_URL) is not None, "the list itself is kept"
    assert store.count_communiques("rso") == 2, "the canary's rows are kept as evidence"


@pytest.mark.parametrize(("bodies", "said"), [
    ({"*": None}, "the all-categories scope was not read"),
    ({"*": _rso_body("1"), "ogolne": _rso_body("1"), "stany-wod": None}, "1 address(es) refused"),
])
def test_rso_a_comparison_that_could_not_be_made_vouches_for_no_list(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
    bodies: dict[str, str | None], said: str,
) -> None:
    """D-065. Not compared is not compared clean, and it is worded apart from a find."""
    _rso_feed(monkeypatch, bodies)
    store_path = tmp_path / "s.sqlite3"
    assert main(["rso", "--store", str(store_path)]) == 3
    out = capsys.readouterr().out
    assert f"[UNVOUCHED] {said}" in out
    assert "[UNKNOWN-CATEGORY]" not in out
    assert all(a["outcome"] == "refused" for a in EventStore(store_path).attempts("rso"))


def test_rso_a_walk_the_canary_agrees_with_reads_every_list(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-065, the other side. Every communique the scope lists was walked, so
    every address gets its read and the run exits 0; the scope's own read is
    recorded too, and it never becomes a list."""
    _rso_feed(monkeypatch, {"*": _rso_body("1", "2"), "ogolne": _rso_body("1"),
                            "atak-z-powietrza": _rso_body("2")})
    store_path = tmp_path / "s.sqlite3"
    assert main(["rso", "--store", str(store_path)]) == 0
    out = capsys.readouterr().out
    assert "[UNVOUCHED]" not in out and "[UNKNOWN-CATEGORY]" not in out
    store = EventStore(store_path)
    assert [a["outcome"] for a in store.attempts("rso")] == ["read"] * 7
    assert store.newest_read("rso", AIR_URL) is not None
    assert store.newest_snapshot("rso", RSO_ALL_SCOPE_URL) is None


def test_rso_a_later_page_is_not_set_beside_the_unpaged_canary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The review's D3. Page 2 of every category is empty past the end; set
    beside the unpaged canary it read as a walk short of everything."""
    from mavo.sources.rso import page_url

    body = _rso_body("1")

    class Feed:
        def fetch(self, url: str, headers: dict[str, str] | None = None) -> str:
            return body if url in (RSO_ALL_SCOPE_URL, page_url("ogolne", 0)) else _rso_body()

    monkeypatch.setattr("mavo.cli.UrllibTransport", Feed)
    store_path = tmp_path / "s.sqlite3"
    assert main(["rso", "--page", "2", "--store", str(store_path)]) == 0
    out = capsys.readouterr().out
    assert "canary" not in out and "[UNKNOWN-CATEGORY]" not in out
    assert [a["outcome"] for a in EventStore(store_path).attempts("rso")] == ["read"] * 6


def test_rso_a_rejected_walk_leaves_the_last_vouched_list_on_the_map(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The review's D1 through the command: a vouched walk with an alert in the
    air category, then a walk whose canary finds it moved again. The map keeps
    the vouched list, not the rejected walk's empty one, until its hour ends."""
    from mavo.poland import warnings_blocks

    alert = _rso_body("23441700").replace("<title>t23441700</title>",
                                          "<title>Zagrożenie z powietrza</title>")
    _rso_feed(monkeypatch, {"*": alert, "atak-z-powietrza": alert})
    store_path = tmp_path / "s.sqlite3"
    assert main(["rso", "--store", str(store_path)]) == 0
    _rso_feed(monkeypatch, {"*": alert})
    assert main(["rso", "--store", str(store_path)]) == 3
    capsys.readouterr()
    now = datetime.now(UTC)
    shown, _cleared = warnings_blocks(EventStore(store_path), now)
    assert shown.published and shown.value, "a rejected walk's empty list was shown"
    assert [item["id"] for row in shown.value for item in row["communiques"]] == ["23441700"]


def test_rso_one_address_on_request_makes_no_claim_about_the_feed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--category` skips the canary: one address asked for is read and recorded."""
    _rso_feed(monkeypatch, {"*": _rso_body("9"), "ogolne": _rso_body("1")})
    store_path = tmp_path / "s.sqlite3"
    assert main(["rso", "--category", "ogolne", "--store", str(store_path)]) == 0
    assert [a["outcome"] for a in EventStore(store_path).attempts("rso")] == ["read"]


def test_rso_times_every_attempt_it_logs(tmp_path: Path) -> None:
    """F183. A read and a refusal both carry their duration, as PAŻP's rows do.

    `elapsed_s` is NULL only where the caller did not time itself. The RSO path
    timed itself and dropped the figure, so every RSO row on the host read NULL
    beside airspace rows written by the same kind of loop.
    """
    good = tmp_path / "page.xml"
    good.write_text(Path("tests/fixtures/rso_page.xml").read_text(encoding="utf-8"),
                    encoding="utf-8")
    broken = tmp_path / "broken.xml"
    broken.write_text("<newses><news><id>1</id>", encoding="utf-8")
    for stub, outcome in ((good, "read"), (broken, "refused")):
        store_path = tmp_path / f"{outcome}.sqlite3"
        main(["rso", "--stub", str(stub), "--category", "ogolne", "--store", str(store_path)])
        (attempt,) = EventStore(store_path).attempts("rso")
        assert attempt["outcome"] == outcome
        assert attempt["elapsed_s"] is not None and attempt["elapsed_s"] >= 0.0


def test_collect_records_the_poll_it_made(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """T71 under D-036: a successful poll leaves a row saying it happened.

    The counts are the page's, not the store's: `items` is what the channel
    served and `unreadable` what the parser refused, so a page that arrived
    and was half-understood is distinguishable from a short page. `elapsed_s`
    is present rather than NULL, because this caller does time itself.
    """
    fixture = Path("tests/fixtures/channel.html").read_text(encoding="utf-8")
    stub = tmp_path / "page.html"
    stub.write_text(fixture, encoding="utf-8")
    store_path = tmp_path / "s.sqlite3"
    assert main(["collect", "--stub", str(stub), "--store", str(store_path)]) == 0

    attempts = EventStore(store_path).attempts("channel")
    assert len(attempts) == 1, "one poll, one row"
    row = attempts[0]
    assert row["outcome"] == "read"
    assert row["items"] is not None and row["items"] > 0
    assert row["unreadable"] is not None, (
        "a page read and not fully understood is not a page that was not read"
    )
    assert row["elapsed_s"] is not None, "this caller times itself"


def test_collect_records_a_refusal_before_it_exits_three(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The row that separates blindness from a quiet sky.

    Until 0.41.0.0 this path returned 3 having written nothing, so an hour the
    collector could not reach the channel and an hour the channel said nothing
    were the same empty set of rows. `items` stays NULL: we did not find out,
    which is a different fact from the publisher having had nothing.
    """
    store_path = tmp_path / "s.sqlite3"
    # `--stub` reads a file eagerly, so it cannot express an unreachable
    # source; the transport is replaced instead, which is the same
    # `SourceUnavailable` the network raises and needs no network to raise it.
    monkeypatch.setattr("mavo.cli.UrllibTransport", FailingTransport)
    code = main(["collect", "--store", str(store_path)])
    assert code == 3
    out = capsys.readouterr().out
    assert "[UNREACHABLE]" in out
    assert "[ATTEMPT-UNLOGGED]" not in out

    attempts = EventStore(store_path).attempts("channel")
    assert len(attempts) == 1, "a refusal is an attempt and leaves a row"
    assert attempts[0]["outcome"] == "refused"
    assert attempts[0]["items"] is None, (
        "NULL is not zero: zero means the channel said nothing, NULL means we "
        "did not find out"
    )
    assert attempts[0]["elapsed_s"] is not None, "T55, in the table as in the line"


def test_collect_without_a_store_records_nothing_and_still_polls(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--store` is what turns a poll into a record, and it stays optional."""
    fixture = Path("tests/fixtures/channel.html").read_text(encoding="utf-8")
    stub = tmp_path / "page.html"
    stub.write_text(fixture, encoding="utf-8")
    assert main(["collect", "--stub", str(stub)]) == 0
    assert "messages=" in capsys.readouterr().out


def _page(ids: tuple[int, ...]) -> str:
    """A minimal channel page carrying the given post ids and one message each."""
    blocks = "".join(
        f'<div class="tgme_widget_message" data-post="air_alert_ua/{post}">'
        f'<div class="tgme_widget_message_text">Повітряна тривога '
        f'#Львівський_район</div>'
        f'<time datetime="2026-08-29T20:0{index}:00+00:00"></time></div>'
        for index, post in enumerate(ids)
    )
    return f"<html><body>{blocks}</body></html>"


def test_two_collect_invocations_measure_the_window_between_them(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """F123, and it is the acceptance production could never reach.

    `mavo-collect.service` is a `oneshot`, so the cursor on the source object
    died with every process and `skipped` read `unknown` on every poll the host
    has ever made. T18 was recorded done against an in-process baseline that
    production does not have.

    Two separate `main()` calls, two separate sources, one store. The second
    page starts eight posts past the end of the first, so five went unseen.
    """
    store_path = tmp_path / "s.sqlite3"
    first = tmp_path / "p1.html"
    first.write_text(_page((100, 101, 102)), encoding="utf-8")
    second = tmp_path / "p2.html"
    second.write_text(_page((108, 109)), encoding="utf-8")

    assert main(["collect", "--stub", str(first), "--store", str(store_path)]) == 0
    out = capsys.readouterr().out
    assert "skipped=unknown" in out, "the first poll has no baseline and says so"
    assert "no earlier page bound" in out

    assert main(["collect", "--stub", str(second), "--store", str(store_path)]) == 0
    out = capsys.readouterr().out
    assert "skipped=5" in out, (
        "posts 103 to 107 passed between the two polls and were never seen"
    )
    assert "skipped=unknown" not in out

    rows = EventStore(store_path).attempts("channel")
    assert [(row["first_id"], row["last_id"]) for row in rows] == [(100, 102), (108, 109)]


def test_a_refusal_between_two_reads_does_not_break_the_window(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The count is messages unseen, not messages unseen since the last attempt.

    A refusal carries no page and no bounds, so the baseline has to survive it.
    Reading the most recent row instead of the highest observed id would find
    NULL here and report `unknown`, turning one refusal into a permanently
    lost window.
    """
    store_path = tmp_path / "s.sqlite3"
    first = tmp_path / "p1.html"
    first.write_text(_page((200, 201)), encoding="utf-8")
    third = tmp_path / "p3.html"
    third.write_text(_page((205,)), encoding="utf-8")

    assert main(["collect", "--stub", str(first), "--store", str(store_path)]) == 0
    monkeypatch.setattr("mavo.cli.UrllibTransport", FailingTransport)
    assert main(["collect", "--store", str(store_path)]) == 3
    monkeypatch.undo()
    capsys.readouterr()
    assert main(["collect", "--stub", str(third), "--store", str(store_path)]) == 0
    assert "skipped=3" in capsys.readouterr().out, "202, 203 and 204 went unseen"


def test_a_page_with_no_post_ids_says_which_unknown_it_is(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Three causes of `unknown`, and a note that names only one is a claim.

    The old text asserted "a single poll has no baseline" on every unknown,
    including the case where a baseline exists and the page arrived without
    ids - which is what a restructured or hostile page looks like and is the
    one worth waking up for.
    """
    store_path = tmp_path / "s.sqlite3"
    good = tmp_path / "p1.html"
    good.write_text(_page((300, 301)), encoding="utf-8")
    idless = tmp_path / "p2.html"
    idless.write_text("<html><body><div>nothing this parser knows</div></body></html>",
                      encoding="utf-8")

    assert main(["collect", "--stub", str(good), "--store", str(store_path)]) == 0
    capsys.readouterr()
    assert main(["collect", "--stub", str(idless), "--store", str(store_path)]) == 0
    out = capsys.readouterr().out
    assert "skipped=unknown" in out
    assert "carried no post ids at all" in out
    assert "the baseline is post 301" in out.lower()

    row = EventStore(store_path).attempts("channel")[-1]
    assert (row["first_id"], row["last_id"]) == (None, None)


def _api_body(*names: str) -> str:
    """An API snapshot listing each name as one active AIR alert."""
    import json

    return json.dumps([
        {
            "regionId": str(i),
            "regionType": "District",
            "regionName": name,
            "lastUpdate": "2026-08-30T13:19:40Z",
            "activeAlerts": [{
                "regionId": str(i), "regionType": "District",
                "type": "AIR", "lastUpdate": "2026-08-30T13:19:40Z",
            }],
        }
        for i, name in enumerate(names, start=1)
    ])


def test_collect_api_without_a_key_attempts_nothing(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing key is a configuration fault, not an outage.

    Its own exit code, and no attempt row: writing a refusal here would put a
    line in the table saying the sky was not observed, when in fact nothing
    reached the sky at all. The two are different and the table is the one
    place that must not confuse them.
    """
    monkeypatch.delenv("MAVO_UKRAINEALARM_KEY", raising=False)

    assert main(["collect-api"]) == 2
    assert "[NO-KEY]" in capsys.readouterr().out


def test_collect_api_stores_events_and_the_attempt(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """A poll that reads leaves both the events and the record that it read.

    The attempt row carries this feed's own name, so a store holding the
    channel and the API can say which pipe an observation came down rather
    than presenting one cadence for two.
    """
    from mavo import cli
    from mavo.store import EventStore

    class _Stub:
        source_id = "ukrainealarm"
        unresolved: tuple[str, ...] = ()
        declined: tuple[str, ...] = ()
        unparsed: tuple[str, ...] = ()
        informational: tuple[str, ...] = ()
        unmapped_types: dict[str, tuple[str, ...]] = {}
        overlapping: dict[tuple[str, str], int] = {}
        unknown_keys: dict[str, int] = {}
        levels: tuple[object, ...] = ()
        snapshot_state = "disabled"
        snapshot_age_s: float | None = None

        def __init__(self, key: str, snapshot: Path | None = None) -> None:
            self.key = key
            self.snapshot = snapshot

        def save_snapshot(self) -> None:
            return None

        def poll(self) -> tuple[ThreatEvent, ...]:
            return (ThreatEvent(
                area_id="UA46060000000000000",
                state=AlertState.ACTIVE,
                ts_source=datetime(2026, 8, 30, 13, 19, tzinfo=UTC),
                ts_ingest=datetime(2026, 8, 30, 13, 20, tzinfo=UTC),
                source_id="ukrainealarm",
                oblast="Львівська",
            ),)

    monkeypatch.setenv("MAVO_UKRAINEALARM_KEY", "k")
    monkeypatch.setattr(cli, "UkrainealarmSource", _Stub)
    store = tmp_path / "events"

    assert main(["collect-api", "--store", str(store)]) == 0

    out = capsys.readouterr().out
    assert "active=1 cleared=0" in out
    assert "stored=1 new events" in out
    # The production-shaped invocation - a store, no snapshot - names its own
    # defect on every run. The failure it warns about is invisible on the map,
    # which is exactly why the warning cannot be.
    assert "[NO-SNAPSHOT]" in out
    assert EventStore(store).newest_page_id("ukrainealarm") is None


def test_collect_api_records_a_refusal_and_says_the_source_was_unreachable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unreachable API is exit 3 and leaves a refusal row, never a quiet poll."""
    from mavo import cli

    class _Refusing:
        unresolved: tuple[str, ...] = ()
        declined: tuple[str, ...] = ()
        unparsed: tuple[str, ...] = ()
        informational: tuple[str, ...] = ()
        unmapped_types: dict[str, tuple[str, ...]] = {}
        overlapping: dict[tuple[str, str], int] = {}
        unknown_keys: dict[str, int] = {}
        levels: tuple[object, ...] = ()
        snapshot_state = "disabled"
        snapshot_age_s: float | None = None

        def __init__(self, key: str, snapshot: Path | None = None) -> None:
            pass

        def poll(self) -> tuple[ThreatEvent, ...]:
            raise SourceUnavailable("api: injected failure")

    monkeypatch.setenv("MAVO_UKRAINEALARM_KEY", "k")
    monkeypatch.setattr(cli, "UkrainealarmSource", _Refusing)

    assert main(["collect-api", "--store", str(tmp_path / "e")]) == 3
    assert "[UNREACHABLE]" in capsys.readouterr().out


def test_collect_api_reads_the_key_from_a_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file is offered because an environment variable is readable from
    `/proc/<pid>/environ` by anything running as the same user."""
    from mavo import cli

    seen: dict[str, str] = {}

    class _Capturing:
        unresolved: tuple[str, ...] = ()
        declined: tuple[str, ...] = ()
        unparsed: tuple[str, ...] = ()
        informational: tuple[str, ...] = ()
        unmapped_types: dict[str, tuple[str, ...]] = {}
        overlapping: dict[tuple[str, str], int] = {}
        unknown_keys: dict[str, int] = {}
        levels: tuple[object, ...] = ()
        snapshot_state = "disabled"
        snapshot_age_s: float | None = None

        def __init__(self, key: str, snapshot: Path | None = None) -> None:
            seen["key"] = key

        def save_snapshot(self) -> None:
            return None

        def poll(self) -> tuple[ThreatEvent, ...]:
            return ()

    monkeypatch.delenv("MAVO_UKRAINEALARM_KEY", raising=False)
    monkeypatch.setattr(cli, "UkrainealarmSource", _Capturing)
    key_file = tmp_path / "key"
    key_file.write_text("secret-from-file\n", encoding="utf-8")

    assert main(["collect-api", "--key-file", str(key_file)]) == 0
    assert seen["key"] == "secret-from-file"


def test_collect_api_names_an_unmapped_type_and_persists_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """T83: a type string outside the vocabulary is named on stdout and lands
    in `feed_attempts.detail`, not only in a journal."""
    import sqlite3

    from mavo import cli

    class _Novel:
        unresolved: tuple[str, ...] = ()
        declined: tuple[str, ...] = ()
        unparsed: tuple[str, ...] = ()
        informational: tuple[str, ...] = ("Львівський район",)
        unmapped_types: dict[str, tuple[str, ...]] = {"BALLISTIC": ("Володимирський район",)}
        overlapping: dict[tuple[str, str], int] = {}
        unknown_keys: dict[str, int] = {}
        levels: tuple[object, ...] = ()
        snapshot_state = "disabled"
        snapshot_age_s: float | None = None

        def __init__(self, key: str, snapshot: Path | None = None) -> None:
            pass

        def save_snapshot(self) -> None:
            return None

        def poll(self) -> tuple[ThreatEvent, ...]:
            return ()

    monkeypatch.setenv("MAVO_UKRAINEALARM_KEY", "k")
    monkeypatch.setattr(cli, "UkrainealarmSource", _Novel)
    store = tmp_path / "e"
    assert main(["collect-api", "--store", str(store)]) == 0
    out = capsys.readouterr().out
    assert "informational=1 unmapped_types=1" in out
    assert "unmapped: BALLISTIC on 1 region(s)" in out
    with sqlite3.connect(store) as conn:
        rows = conn.execute(
            "SELECT outcome, detail FROM feed_attempts"
        ).fetchall()
    conn.close()
    assert rows == [("read", "unmapped types: BALLISTIC")]


def test_collect_api_records_the_declarations_it_saw_and_counts_only_new_ones(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """D-050, the second half, on the command: the recap says how many
    declarations were observed and how many the store had not seen, and the
    second run of the same picture stores none."""
    from mavo import cli
    from mavo.schema import LevelEvent, ThreatKind
    from mavo.store import EventStore

    class _Stub:
        source_id = "ukrainealarm"
        unresolved: tuple[str, ...] = ()
        declined: tuple[str, ...] = ()
        unparsed: tuple[str, ...] = ()
        informational: tuple[str, ...] = ()
        unmapped_types: dict[str, tuple[str, ...]] = {}
        overlapping: dict[tuple[str, str], int] = {}
        unknown_keys: dict[str, int] = {}
        snapshot_state = "disabled"
        snapshot_age_s: float | None = None

        def __init__(self, key: str, snapshot: Path | None = None) -> None:
            self.levels: tuple[LevelEvent, ...] = ()

        def save_snapshot(self) -> None:
            return None

        def poll(self) -> tuple[ThreatEvent, ...]:
            self.levels = (LevelEvent(
                area_id="UA46060000000000000", kind=ThreatKind.UNKNOWN, level="Yellow",
                level_at=datetime(2026, 9, 8, 17, 22, 35, tzinfo=UTC),
                ts_ingest=datetime(2026, 9, 8, 17, 24, tzinfo=UTC),
                source_id="ukrainealarm", oblast="Львівська",
            ),)
            return (ThreatEvent(
                area_id="UA46060000000000000",
                state=AlertState.ACTIVE,
                ts_source=datetime(2026, 9, 8, 17, 22, 35, tzinfo=UTC),
                ts_ingest=datetime(2026, 9, 8, 17, 24, tzinfo=UTC),
                source_id="ukrainealarm",
                oblast="Львівська",
            ),)

    monkeypatch.setenv("MAVO_UKRAINEALARM_KEY", "k")
    monkeypatch.setattr(cli, "UkrainealarmSource", _Stub)
    store = tmp_path / "events"

    assert main(["collect-api", "--store", str(store)]) == 0
    assert "levels=1 new declaration(s) (observed=1;" in capsys.readouterr().out
    assert main(["collect-api", "--store", str(store)]) == 0
    assert "levels=0 new declaration(s) (observed=1;" in capsys.readouterr().out
    assert EventStore(store).count_levels() == 1


def test_rso_a_long_find_is_named_in_part_and_counted_in_full() -> None:
    """Ten identifiers and the count of the rest, so one journal line stays a line."""
    from mavo.cli import _rso_unvouched
    from mavo.sources.rso import parse_page

    scope = parse_page(_rso_body(*(str(n) for n in range(12))).encode("utf-8"))
    line = _rso_unvouched(scope, set(), 0)
    assert line is not None
    assert line.startswith("[UNKNOWN-CATEGORY] 12 communique(s)")
    assert line.endswith("0, 1, 2, 3, 4, 5, 6, 7, 8, 9 and 2 more")
