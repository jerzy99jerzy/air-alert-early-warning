"""The five checks added at 0.39.1.0, each verified red as well as green.

Same rule as `test_gate_checks_0_35.py`: a check observed only passing is not
evidence. Each test plants the failure the check exists for, asserts the check
finds it, and asserts it goes quiet when the failure is removed - so a check
that is simply always red cannot pass here either.

The red fixture for the unit check is not invented. It is the sentence
`docs/DEPLOYMENT.md` carried at 0.32.7.0, which asserted `MAVO_LOG_FILE` sat on
one unit and not the other with nothing quoted, and which was wrong: that is
F106, and T64 named it as the text this check must fail against.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import adapter_lint  # noqa: E402
import docs_audit  # noqa: E402


@pytest.fixture
def status() -> dict[str, object]:
    return docs_audit._status()


def _deployment(tmp_path: Path, body: str) -> Path:
    root = tmp_path / "tree"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "DEPLOYMENT.md").write_text(body, encoding="utf-8")
    return root


def test_the_tree_passes_all_five_today(status: dict[str, object]) -> None:
    """The green direction, stated first so the red ones mean something."""
    assert docs_audit.check_unit_claims_quote_the_unit() == []
    assert docs_audit.check_the_host_version_row_matches_the_pin(status) == []
    assert docs_audit.check_the_host_release_distance_is_counted(status) == []
    assert docs_audit.check_the_coverage_floor_stays_a_ratchet(status) == []
    assert adapter_lint.main() == 0


# --------------------------------------------------------------- T64 ---

F106_TEXT = """## Units

`MAVO_LOG_FILE` sits on `mavo-collect.service` and belongs on
`mavo-report.service`, so a `systemctl edit` is scheduled to move it.
Environment=MAVO_LOG_FILE=/var/lib/mavo/run.jsonl is on the wrong unit.
"""


def test_an_unsourced_claim_about_a_unit_is_found(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """F106's own text, which reached a tag and scheduled a needless step."""
    monkeypatch.setattr(docs_audit, "ROOT", _deployment(tmp_path, F106_TEXT))
    problems = docs_audit.check_unit_claims_quote_the_unit()
    assert problems, "the F106 text must not pass the check written against it"
    assert all("T64" in problem for problem in problems), problems


def test_the_same_claim_beside_its_reading_is_not_a_problem(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Quoting the machine is the whole repair, so quoting must clear it."""
    sourced = F106_TEXT + "\n```\nsystemctl cat mavo-report.service\n```\n"
    monkeypatch.setattr(docs_audit, "ROOT", _deployment(tmp_path, sourced))
    assert docs_audit.check_unit_claims_quote_the_unit() == []


def test_systemd_discussed_in_general_is_not_a_claim_about_our_units(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The allow-list's job, done by scope rather than by a list of sentences.

    `Restart=always` in a paragraph explaining systemd to a reader is a fact
    about systemd. The same string beside one of our units is a claim about a
    file on our host, and only the second is this check's business.
    """
    generic = "## Identity\n\n`Restart=always` and `WatchdogSec` give a job an identity.\n"
    monkeypatch.setattr(docs_audit, "ROOT", _deployment(tmp_path, generic))
    assert docs_audit.check_unit_claims_quote_the_unit() == []


# --------------------------------------------------------------- F117 ---

def test_a_stale_main_row_is_found(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, status: dict[str, object]) -> None:
    """F117's shape: the row went two releases stale under an enforced date."""
    body = "## Host\n\n| | |\n| --- | --- |\n| `main` | 0.37.0.0, stale |\n"
    monkeypatch.setattr(docs_audit, "ROOT", _deployment(tmp_path, body))
    problems = docs_audit.check_the_host_version_row_matches_the_pin(status)
    assert len(problems) == 1, problems
    assert "0.37.0.0" in problems[0], problems


def test_a_current_main_row_is_not_a_problem(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, status: dict[str, object]) -> None:
    body = f"## Host\n\n| `main` | {status['version']}, the release this ships in |\n"
    monkeypatch.setattr(docs_audit, "ROOT", _deployment(tmp_path, body))
    assert docs_audit.check_the_host_version_row_matches_the_pin(status) == []


def test_a_missing_main_row_is_reported_rather_than_skipped(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, status: dict[str, object]) -> None:
    """A check that goes quiet when its subject disappears checks nothing."""
    monkeypatch.setattr(docs_audit, "ROOT", _deployment(tmp_path, "## Host\n\nNo table.\n"))
    problems = docs_audit.check_the_host_version_row_matches_the_pin(status)
    assert len(problems) == 1 and "no '| `main` |' row" in problems[0], problems


def _tree_with_changelog(tmp_path: Path, deployment: str, changelog: str) -> Path:
    root = tmp_path / "tree"
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "DEPLOYMENT.md").write_text(deployment, encoding="utf-8")
    (root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    return root


CHANGELOG = "## 9.9.9.9 - 2026-01-01\n\n## 0.39.1.0 - x\n\n## 0.39.0.1 - x\n\n## 0.39.0.0 - x\n"


def _host_table(installed: str, main: str, distance: str) -> str:
    return (f"## Host\n\n| | |\n| --- | --- |\n"
            f"| Installed | `air-alert-early-warning {installed}`, `/opt/mavo/venv` |\n"
            f"| `main` | {main}, the release this reading ships in |\n"
            f"| Behind by | {distance} releases, deferred |\n")


def test_a_release_distance_that_stopped_counting_is_found(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The row that went stale inside the release that logged F117 for it."""
    root = _tree_with_changelog(tmp_path, _host_table("0.39.0.0", "0.39.1.0", "one"), CHANGELOG)
    monkeypatch.setattr(docs_audit, "ROOT", root)
    problems = docs_audit.check_the_host_release_distance_is_counted({"version": "0.39.1.0"})
    assert len(problems) == 1, problems
    assert "counts 2" in problems[0], problems


def test_a_counted_release_distance_is_not_a_problem(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = _tree_with_changelog(tmp_path, _host_table("0.39.0.0", "0.39.1.0", "two"), CHANGELOG)
    monkeypatch.setattr(docs_audit, "ROOT", root)
    assert docs_audit.check_the_host_release_distance_is_counted({"version": "0.39.1.0"}) == []


def test_a_distance_stated_as_a_digit_is_read_the_same_way(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The wording is a style choice; the number is the claim."""
    root = _tree_with_changelog(tmp_path, _host_table("0.39.0.0", "0.39.1.0", "2"), CHANGELOG)
    monkeypatch.setattr(docs_audit, "ROOT", root)
    assert docs_audit.check_the_host_release_distance_is_counted({"version": "0.39.1.0"}) == []


def test_an_installed_version_the_changelog_does_not_know_is_reported(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Silence on an unknown input is how a check stops being one."""
    root = _tree_with_changelog(tmp_path, _host_table("0.1.2.3", "0.39.1.0", "two"), CHANGELOG)
    monkeypatch.setattr(docs_audit, "ROOT", root)
    problems = docs_audit.check_the_host_release_distance_is_counted({"version": "0.39.1.0"})
    assert len(problems) == 1 and "0.1.2.3" in problems[0], problems


# ----------------------------------------------------------------- T9 ---

def test_a_floor_that_stopped_following_the_measurement_is_found() -> None:
    """More than five points of slack means the floor enforces the past."""
    lax = {"version": "1.0.0.0",
           "measured": {"coverage_percent": 96.43, "coverage_floor_percent": 88}}
    problems = docs_audit.check_the_coverage_floor_stays_a_ratchet(lax)
    assert len(problems) == 1 and "T9" in problems[0], problems


def test_a_floor_inside_the_ratchet_is_not_a_problem() -> None:
    tight = {"version": "1.0.0.0",
             "measured": {"coverage_percent": 96.43, "coverage_floor_percent": 95}}
    assert docs_audit.check_the_coverage_floor_stays_a_ratchet(tight) == []


def test_the_ratchet_does_not_ask_coverage_to_rise() -> None:
    """A floor above the measurement is `--cov-fail-under`'s business, not this
    one's. Asserted so a later edit cannot quietly turn a ratchet into a
    target."""
    above = {"version": "1.0.0.0",
             "measured": {"coverage_percent": 90.0, "coverage_floor_percent": 95}}
    assert docs_audit.check_the_coverage_floor_stays_a_ratchet(above) == []


# ----------------------------------------------------------------- T4 ---

def test_an_adapter_without_a_hostile_suite_is_found(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The rule T4 was written for: the next adapter, not the one that bit."""
    root = tmp_path / "tree"
    (root / "mavo" / "sources").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "mavo" / "sources" / "newfeed.py").write_text(
        "import json\n\n\ndef read(raw: str) -> dict:\n    return json.loads(raw)\n",
        encoding="utf-8")
    (root / "tests" / "test_newfeed.py").write_text(
        "def test_newfeed_reads_a_well_formed_document():\n    assert True\n",
        encoding="utf-8")
    monkeypatch.setattr(adapter_lint, "SOURCES", root / "mavo" / "sources")
    monkeypatch.setattr(adapter_lint, "TESTS", root / "tests")
    assert adapter_lint.main() == 1


def test_the_same_adapter_with_a_hostile_suite_passes(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "tree"
    (root / "mavo" / "sources").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "mavo" / "sources" / "newfeed.py").write_text(
        "import json\n\n\ndef read(raw: str) -> dict:\n    return json.loads(raw)\n",
        encoding="utf-8")
    (root / "tests" / "test_newfeed.py").write_text(
        "def test_newfeed_does_not_raise_on_malformed_input():\n    assert True\n",
        encoding="utf-8")
    monkeypatch.setattr(adapter_lint, "SOURCES", root / "mavo" / "sources")
    monkeypatch.setattr(adapter_lint, "TESTS", root / "tests")
    assert adapter_lint.main() == 0
