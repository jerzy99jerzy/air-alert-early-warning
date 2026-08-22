"""CLI smoke level: wiring exercised through its callees."""

from __future__ import annotations

from pathlib import Path

import pytest

from mavo.cli import main
from mavo.store import EventStore


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
