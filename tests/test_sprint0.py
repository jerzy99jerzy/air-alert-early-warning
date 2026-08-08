"""Sprint 0 regressions: the gate itself.

Defect class: absence read as success. A fresh repository passes `make verify`
by default, because pytest treats "nothing collected" as green and an unset
coverage floor as satisfied. A gate that passes an empty repository is not a
gate, and this is the same failure class as unknown-resolves-safe in the domain
code.

No previous tag exists. These were verified red against a scratch copy of the
skeleton with the coverage floor removed and the CI steps restated inline.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _pyproject() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        result: dict[str, object] = tomllib.load(handle)
    return result


def test_coverage_floor_is_above_zero() -> None:
    tool = _pyproject()["tool"]
    assert isinstance(tool, dict)
    assert tool["coverage"]["report"]["fail_under"] > 0


def test_pytest_exit_code_for_no_tests_is_not_swallowed() -> None:
    # `-p no:cacheprovider` style suppression or `--exitfirst=0` tricks would
    # hide exit 5. The Makefile must not pass anything that ignores it.
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "--exitcode-on-no-tests" not in makefile
    assert "|| true" not in makefile


def test_ci_calls_the_single_gate_rather_than_restating_it() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "make verify" in workflow
    # If CI listed the steps itself it would drift the moment one is added.
    assert "pytest" not in workflow


def test_ci_matrix_includes_the_development_version() -> None:
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "3.11" in workflow and "3.14" in workflow


def test_verify_target_includes_every_lint() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    verify_line = next(line for line in makefile.splitlines() if line.startswith("verify:"))
    for target in ("coverage", "lint", "lint-limitations", "lint-hygiene", "lint-mermaid",
                   "lint-domain"):
        assert target in verify_line, f"{target} missing from the single gate"


def test_every_lint_script_is_present() -> None:
    for name in ("lint_limitations", "lint_hygiene", "lint_mermaid", "lint_domain"):
        assert (ROOT / "tests" / f"{name}.py").exists()
