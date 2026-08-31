"""The figures generator, verified red as well as green.

Same rule as `test_gate_checks_0_39_1.py`: a check observed only passing is not
evidence. D-046 states the reopen condition itself - a generator nobody checks
is the ritual again with better manners - so the generator that replaced the
ritual gets the treatment the ritual never had.

The red fixtures are not invented. `Releases | 44` against a changelog holding
122 is F139 exactly, the figure that sat in the README's headline table under
sixteen checks; and the two-place drift is the fixed point that made release
convergence a manual two-pass dance.

These run against copies in `tmp_path`. The generator writes to the real tree
by design, so a test that let it touch `ROOT` would be a test that edits the
repository as a side effect of asserting things about it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import figures  # noqa: E402


@pytest.fixture
def tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A miniature tree with the files the generator counts and writes."""
    for relative in ("docs", "tests/harness", "mavo", "tools"):
        (tmp_path / relative).mkdir(parents=True, exist_ok=True)

    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n"
        "## 0.2.0.0 - 2026-08-06\nsecond\n\n"
        "## 0.1.0 - 2026-08-05\nfirst, three segments on purpose\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "METHODOLOGY.md").write_text(
        "# METHODOLOGY\n\n### F1, first\nbody\n\n### F2, second\nbody\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "DECISIONS.md").write_text(
        "# DECISIONS\n\n## D-001. one\nbody\n\n## D-002. two\nbody\n\n"
        "## D-003. three\nbody\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "harness" / "CATALOGUE.md").write_text("# x\n", encoding="utf-8")
    (tmp_path / "mavo" / "__init__.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "tools" / "t.py").write_text("y = 2\n", encoding="utf-8")
    (tmp_path / "tests" / "t_test.py").write_text("z = 3\n", encoding="utf-8")

    (tmp_path / "README.md").write_text(
        "# R\n\n"
        "[![tests 1](https://img.shields.io/badge/tests-1-brightgreen)](tests/)\n"
        "[![coverage 1.0%](https://img.shields.io/badge/coverage-1.0%25-brightgreen)](Makefile)\n"
        "[![defects logged 1](https://img.shields.io/badge/defects%20logged-1-informational)]"
        "(docs/METHODOLOGY.md)\n\n"
        "| | Files | Lines |\n| --- | --- | --- |\n"
        "| Package `mavo/` | 0 | 0 |\n| Tests | 0 | 0 |\n"
        "| Tools | 0 | 0 |\n| Documentation | 0 | 0 |\n\n"
        "| Tests | 1, of which 13 are scripted attacks |\n"
        "| Coverage | 1.0% against a floor of 95 |\n"
        "| Defects logged with their class | 1, the count pinned against the log itself |\n"
        "| Decisions recorded with reopen conditions | 1, counted from the log itself |\n"
        "| Releases | 44 in the changelog; tags are fewer |\n",
        encoding="utf-8",
    )
    (tmp_path / "STATUS.json").write_text(
        json.dumps({
            "version": "0.2.0.0",
            "measured": {"tests_passing": 1, "coverage_percent": 1.0},
            "statistics": {"package_files": 0, "package_lines": 0},
            "defects_logged": 1,
            "decisions_recorded": 1,
        }, indent=2) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(figures, "ROOT", tmp_path)
    monkeypatch.setattr(figures, "STATUS", tmp_path / "STATUS.json")
    monkeypatch.setattr(figures, "README", tmp_path / "README.md")
    return tmp_path


def status_of(tree: Path) -> dict[str, object]:
    return json.loads((tree / "STATUS.json").read_text(encoding="utf-8"))


def test_the_check_is_red_before_the_write_and_green_after(tree: Path) -> None:
    """The whole contract in one test: it finds drift, and it fixes it."""
    assert figures.main(["--check"]) == 1
    assert figures.main([]) == 0
    assert figures.main(["--check"]) == 0


def test_a_check_run_leaves_the_tree_exactly_as_it_found_it(tree: Path) -> None:
    """`--check` runs the generator to compare, so it must undo what it wrote.

    Without this the gate would silently repair the drift it is reporting, and
    a person running `make verify` twice would see a different answer the
    second time.
    """
    before_readme = (tree / "README.md").read_text(encoding="utf-8")
    before_status = (tree / "STATUS.json").read_text(encoding="utf-8")
    assert figures.main(["--check"]) == 1
    assert (tree / "README.md").read_text(encoding="utf-8") == before_readme
    assert (tree / "STATUS.json").read_text(encoding="utf-8") == before_status


def test_the_releases_count_is_counted_rather_than_carried(tree: Path) -> None:
    """F139. The fixture carries 44 against a changelog holding 2."""
    assert "| Releases | 44 in the changelog" in (tree / "README.md").read_text()
    figures.main([])
    text = (tree / "README.md").read_text(encoding="utf-8")
    assert "| Releases | 2 in the changelog" in text
    assert status_of(tree)["releases"] == 2


def test_the_oldest_three_segment_release_is_not_missed(tree: Path) -> None:
    """The first entry predates four-segment versions, so the pattern is by shape."""
    figures.main([])
    assert status_of(tree)["releases"] == 2


def test_defects_and_decisions_come_from_their_own_logs(tree: Path) -> None:
    figures.main([])
    status = status_of(tree)
    assert status["defects_logged"] == 2
    assert status["decisions_recorded"] == 3
    text = (tree / "README.md").read_text(encoding="utf-8")
    assert "| Defects logged with their class | 2," in text
    assert "| Decisions recorded with reopen conditions | 3," in text


def test_the_readme_line_count_settles_despite_counting_itself(tree: Path) -> None:
    """The fixed point, which is why the loop lives in the tool.

    `README.md` is inside the documentation group whose line count `README.md`
    prints, so a single pass can leave a number that its own write invalidated.
    After the generator runs, a second run must find nothing to do.
    """
    figures.main([])
    first = (tree / "README.md").read_text(encoding="utf-8")
    assert figures.main(["--check"]) == 0
    figures.main([])
    assert (tree / "README.md").read_text(encoding="utf-8") == first
    documented = int(str(status_of(tree)["statistics"]["documentation_lines"]))  # type: ignore[index]
    assert f"| Documentation | 5 | {documented:,} |" in first


def test_the_execution_figures_are_left_to_their_own_check(tree: Path) -> None:
    """D-046's boundary, and the first version of the generator broke it.

    `tests_passing` and `coverage_percent` describe a run, not a tree. Reading
    them here would make the gate red on every run that changed a test, since
    `make verify` writes `.gate` before this check reads it - the convergence
    dance this tool retires, reintroduced. They stay where `docs_audit` can
    police them, and this test fails if they ever migrate back.
    """
    gate = tree / ".gate"
    gate.mkdir()
    (gate / "coverage.json").write_text(
        json.dumps({"totals": {"percent_covered": 96.789}}), encoding="utf-8")
    (gate / "tests.xml").write_text(
        '<testsuite tests="7" failures="0"></testsuite>', encoding="utf-8")
    figures.main([])
    measured = status_of(tree)["measured"]
    assert isinstance(measured, dict)
    assert measured["tests_passing"] == 1
    assert measured["coverage_percent"] == 1.0


def test_existing_status_keys_keep_their_order(tree: Path) -> None:
    """A generator that reorders the file buries a real change in moved lines."""
    status = json.loads((tree / "STATUS.json").read_text(encoding="utf-8"))
    status["statistics"] = {"documentation_lines": 0, "package_files": 0}
    (tree / "STATUS.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    figures.main([])
    keys = list(status_of(tree)["statistics"])  # type: ignore[arg-type]
    assert keys[:2] == ["documentation_lines", "package_files"]


def test_the_real_tree_is_in_the_state_the_gate_expects() -> None:
    """The one test that touches the repository, and only to read it."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "figures.py"), "--check"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
