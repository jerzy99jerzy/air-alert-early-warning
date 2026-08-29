"""CLI smoke level: wiring exercised through its callees."""

from __future__ import annotations

from pathlib import Path

import pytest

from mavo.cli import main
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
    import os
    out = tmp_path / "corpus"
    out.mkdir()
    # The parent process: alive, and not us. pid+1 is usually neither, and a
    # lock naming a dead holder is taken over by design.
    (out / ".backfill.lock").write_text(str(os.getppid()), encoding="utf-8")
    page = tmp_path / "page.html"
    page.write_text("<html></html>", encoding="utf-8")
    assert main(["backfill", "--out", str(out), "--pages", "1", "--delay", "0",
                 "--stub", str(page)]) == 6
    assert "REFUSED" in capsys.readouterr().out


def test_backfill_releases_the_lock_when_it_finishes(tmp_path: Path) -> None:
    # A lock left behind by a clean exit is a lock the next run has to reason
    # about, which is how a control becomes a nuisance and then gets deleted.
    out = tmp_path / "corpus"
    page = tmp_path / "page.html"
    page.write_text("<html></html>", encoding="utf-8")
    main(["backfill", "--out", str(out), "--pages", "1", "--delay", "0",
          "--stub", str(page)])
    assert not (out / ".backfill.lock").exists()


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
    code = main(["rso", "--stub", str(stub), "--store", str(tmp_path / "s.sqlite3")])
    out = capsys.readouterr().out
    assert code == 0
    for name in ("ogolne", "meteorologiczne", "hydrologiczne",
                 "informacje-drogowe", "stany-wod"):
        assert f"/{name}/" in out, f"{name} was not read"
    assert "/wszystkie/wszystkie/" not in out, "the partial scope must not be used"


def test_rso_stores_each_communique_once_across_the_walk(tmp_path: Path) -> None:
    """Five reads of one page are two rows, and the count says which is which."""
    fixture = Path("tests/fixtures/rso_page.xml").read_text(encoding="utf-8")
    stub = tmp_path / "page.xml"
    stub.write_text(fixture, encoding="utf-8")
    store_path = tmp_path / "s.sqlite3"
    assert main(["rso", "--stub", str(stub), "--store", str(store_path)]) == 0
    store = EventStore(store_path)
    assert store.count_communiques("rso") == 2
    assert len(store.attempts("rso")) == 5, "one logged attempt per category"


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
    assert "refused=5/5" in out

    # Every refusal left a row, and each row says we did not find out rather
    # than that the publisher had nothing.
    attempts = EventStore(store_path).attempts("rso")
    assert len(attempts) == 5
    assert all(a["outcome"] == "refused" for a in attempts)
    assert all(a["items"] is None for a in attempts)


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
