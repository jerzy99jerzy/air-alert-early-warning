"""The three checks added at 0.35.0.0, each verified red as well as green.

A check that has only ever been observed passing is not evidence, which is F14
and the reason `harness_mutation.py` exists. These three were added because
three claims had been maintained by hand and drifted; testing them by running
them against the tree and watching them pass would repeat the mistake one
level up.

Each test plants the failure the check exists for and asserts the check finds
it, then removes it and asserts the check goes quiet.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import docs_audit  # noqa: E402
import precision_lint  # noqa: E402


@pytest.fixture
def status() -> dict[str, object]:
    return docs_audit._status()


def test_the_tree_passes_all_three_today(status: dict[str, object]) -> None:
    """The green direction, stated first so the red ones mean something."""
    assert docs_audit.check_every_cited_defect_has_an_entry(status) == []
    assert docs_audit.check_badge_alt_text_matches_the_badge(status) == []
    assert precision_lint.main() == 0


def test_a_defect_cited_without_an_entry_is_found(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, status: dict[str, object]) -> None:
    """The F108 shape: written into the changelog, never into the register."""
    root = _tree(tmp_path,
                 changelog="## 1.0\n\nRepaired F900, which nobody logged.\n",
                 register="### F107, 0.32.8.0. Something\n")
    monkeypatch.setattr(docs_audit, "ROOT", root)
    problems = docs_audit.check_every_cited_defect_has_an_entry(status)
    assert len(problems) == 1, problems
    assert "F900" in problems[0], problems


def test_a_defect_cited_and_registered_is_not_a_problem(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, status: dict[str, object]) -> None:
    """The other direction, so the check is not simply always red."""
    root = _tree(tmp_path,
                 changelog="## 1.0\n\nRepaired F900.\n",
                 register="### F900, 1.0. Something\n")
    monkeypatch.setattr(docs_audit, "ROOT", root)
    assert docs_audit.check_every_cited_defect_has_an_entry(status) == []


def test_a_frozen_identifier_that_gained_an_entry_is_reported(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, status: dict[str, object]) -> None:
    """A resolved item may not sit in the frozen list pretending to be open.

    Without this the list only ever grows, and a list that only grows is a
    place to put things rather than a record of what is owed.
    """
    root = _tree(tmp_path,
                 changelog="## 1.0\n\nF14 was cited here.\n",
                 register="### F14, 0.4.0.0. It has an entry now\n")
    monkeypatch.setattr(docs_audit, "ROOT", root)
    problems = docs_audit.check_every_cited_defect_has_an_entry(status)
    assert len(problems) == 1 and "F14" in problems[0], problems


def test_badge_alt_text_that_disagrees_with_its_badge_is_found(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, status: dict[str, object]) -> None:
    """The 0.33.0.2 shape: badge read 427, the words beside it read 410."""
    root = _tree(tmp_path, readme=(
        "[![tests 410](https://img.shields.io/badge/tests-427-brightgreen)](tests/)\n"))
    monkeypatch.setattr(docs_audit, "ROOT", root)
    problems = docs_audit.check_badge_alt_text_matches_the_badge(status)
    assert len(problems) == 1, problems
    assert "410" in problems[0] and "427" in problems[0], problems


def test_percent_encoding_is_decoded_before_the_comparison(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, status: dict[str, object]) -> None:
    """`%20` and `%25` carry digits of their own and are not claims.

    The first version of this check compared the raw path and reported every
    badge with a space in its label. A check that cries on a clean tree is
    removed by whoever is trying to ship, which is worse than not having it.
    """
    root = _tree(tmp_path, readme=(
        "[![coverage 96.75%](https://img.shields.io/badge/coverage-96.75%25-brightgreen)](Makefile)\n"
        "[![defects logged 88](https://img.shields.io/badge/defects%20logged-88-informational)](x)\n"
        "[![python 3.11 | 3.14](https://img.shields.io/badge/python-3.11%20%7C%203.14-blue)](y)\n"))
    monkeypatch.setattr(docs_audit, "ROOT", root)
    assert docs_audit.check_badge_alt_text_matches_the_badge(status) == []


def test_the_precision_pattern_ignores_versions_and_addresses() -> None:
    """A version string is four numbers, not a measurement with decimals."""
    assert precision_lint.FIGURE.findall("released 0.33.0.2 from 34.116.232.215") == []
    assert precision_lint.FIGURE.findall("the window is 7.84 days") == ["7.84"]
    assert precision_lint.FIGURE.findall("one decimal, 7.8 days") == []


def test_the_polish_pattern_reads_a_comma_as_a_decimal_and_not_as_thousands() -> None:
    """`96,61` is a figure and `38,521` is a count, and only the language says so."""
    assert precision_lint.FIGURE_PL.findall("pokrycie 96,61 procent") == ["96,61"]
    assert precision_lint.FIGURE_PL.findall("38,521 wiadomości") == []


def test_the_polish_pattern_is_not_applied_to_english_documents(tmp_path: Path) -> None:
    """Applied everywhere it would read every thousands group as false precision."""
    english = tmp_path / "BRIEF.md"
    english.write_text("38,521 messages\n", encoding="utf-8")
    polish = tmp_path / "BRIEF-PL.md"
    polish.write_text("96,61 procent\n", encoding="utf-8")
    assert precision_lint.count(english) == 0
    assert precision_lint.count(polish) == 1


def _tree(tmp_path: Path, changelog: str = "", register: str = "",
          readme: str = "") -> Path:
    """A minimal stand-in root, so a check can be run against a planted tree."""
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    (tmp_path / "docs" / "METHODOLOGY.md").write_text(register, encoding="utf-8")
    (tmp_path / "README.md").write_text(readme, encoding="utf-8")
    return tmp_path


def test_the_ceiling_table_names_only_tracked_documents() -> None:
    """A ceiling for a file that no longer exists is a rule guarding nothing."""
    tracked = {p.relative_to(precision_lint.ROOT).as_posix()
               for p in precision_lint.documents()}
    assert set(precision_lint.CEILINGS) <= tracked, set(precision_lint.CEILINGS) - tracked


def test_dated_records_are_outside_the_sweep() -> None:
    """`CHANGELOG.md` and the reviews say what was claimed at a release.

    Rounding a figure inside them would edit the record to make the present
    look tidier, which is the one edit this repository does not make.
    """
    names = [p.as_posix() for p in precision_lint.documents()]
    assert not any(re.search(r"CHANGELOG\.md$|docs/reviews/", n) for n in names), names
