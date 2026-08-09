"""CLI smoke level: wiring exercised through its callees."""

from __future__ import annotations

from pathlib import Path

import pytest

from mavo.cli import main


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


def test_demand_allocation_exits_nonzero_when_the_budget_does_not_fit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The allocator refusing is a result, not a crash: exit code 1, no traceback.
    assert main(["policy", "--weeks", "208", "--allocation", "demand"]) == 1
    assert "exceeds the total budget" in capsys.readouterr().out


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
