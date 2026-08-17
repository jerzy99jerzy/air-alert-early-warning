"""Two controls added at 0.32.5.0, and a test each that fails when they go.

Both exist because a number in this repository was wrong while the gate said
pins held. `check_the_pins_match_the_gate_run` closes the gap for the two
fields `check_measured_block_is_recomputed` deliberately left as typed claims;
`tools/check_manifest.py` closes the omission dimension `shasum -c` cannot see.
A control with no test that fails when it is removed is a preference, which is
this repository's standing phrasing and the reason this file exists.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import tools.check_manifest as check_manifest
import tools.docs_audit as docs_audit

_JUNIT = """<?xml version="1.0" encoding="utf-8"?>
<testsuites name="pytest tests"><testsuite name="pytest" errors="{errors}"
 failures="{failures}" skipped="0" tests="{tests}" time="1.0" /></testsuites>
"""


def _gate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    percent: float = 96.22,
    tests: int = 380,
    failures: int = 0,
    errors: int = 0,
    written: bool = True,
) -> None:
    gate = tmp_path / ".gate"
    gate.mkdir()
    if written:
        (gate / "coverage.json").write_text(
            json.dumps({"totals": {"percent_covered": percent}}), encoding="utf-8")
        (gate / "tests.xml").write_text(
            _JUNIT.format(tests=tests, failures=failures, errors=errors),
            encoding="utf-8")
    monkeypatch.setattr(docs_audit, "ROOT", tmp_path)
    monkeypatch.setattr(docs_audit, "GATE_COVERAGE", gate / "coverage.json")
    monkeypatch.setattr(docs_audit, "GATE_TESTS", gate / "tests.xml")


def _status(coverage: float = 96.22, tests: int = 380) -> dict[str, object]:
    return {"measured": {"coverage_percent": coverage, "tests_passing": tests}}


def test_pins_that_match_the_run_are_silent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _gate(monkeypatch, tmp_path)
    assert docs_audit.check_the_pins_match_the_gate_run(_status()) == []


def test_the_drift_this_release_found_is_reported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """96.17 pinned against 96.22 measured, the state at 0.32.4.0."""
    _gate(monkeypatch, tmp_path, percent=96.21936019941836)
    problems = docs_audit.check_the_pins_match_the_gate_run(_status(coverage=96.17))
    assert any("96.22%" in problem for problem in problems)


def test_a_drifted_test_count_is_reported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _gate(monkeypatch, tmp_path, tests=380)
    problems = docs_audit.check_the_pins_match_the_gate_run(_status(tests=373))
    assert any("collected 380" in problem for problem in problems)


def test_a_red_suite_cannot_satisfy_a_green_pin(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The collected count is platform-stable and says nothing about outcome.

    Comparing against it alone would let a suite with a failure in it agree
    with a pin named `tests_passing`, which is the kind of true-sounding number
    this file is here to prevent.
    """
    _gate(monkeypatch, tmp_path, failures=1)
    problems = docs_audit.check_the_pins_match_the_gate_run(_status())
    assert any("1 failures" in problem for problem in problems)


def test_a_missing_artefact_fails_rather_than_skips(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A check that passes quietly when its input is absent is worse than none."""
    _gate(monkeypatch, tmp_path, written=False)
    problems = docs_audit.check_the_pins_match_the_gate_run(_status())
    assert len(problems) == 2
    assert all("make coverage" in problem for problem in problems)


def test_the_gate_run_check_is_registered_in_the_audit() -> None:
    """The other tests call the function; this one holds that the gate calls it."""
    source = Path(docs_audit.__file__).read_text(encoding="utf-8")
    assert source.count("check_the_pins_match_the_gate_run(status)") == 1


def _repository(tmp_path: Path, files: dict[str, str]) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for name, body in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    return tmp_path


def _point_at(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(check_manifest, "ROOT", root)
    monkeypatch.setattr(check_manifest, "MANIFEST", root / "MANIFEST.sha256")


def test_a_regenerated_manifest_checks_clean(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _point_at(monkeypatch, _repository(tmp_path, {"a.txt": "one", "b/c.txt": "two"}))
    assert check_manifest.write() == 0
    assert check_manifest.check() == 0


def test_a_tracked_file_the_manifest_never_listed_is_reported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The dimension `shasum -c` is silent about, and the one nobody counted.

    Thirteen tracked files were in this state at 0.32.4.0. Asserted against
    `completeness` rather than `check`, because this is the half that has to
    hold on a tree under edit: it is what `verify` runs.
    """
    root = _repository(tmp_path, {"a.txt": "one"})
    _point_at(monkeypatch, root)
    check_manifest.write()
    (root / "new.txt").write_text("added", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    assert check_manifest.completeness() == 1
    assert check_manifest.check() == 1


def test_an_edited_file_does_not_fail_the_half_the_gate_runs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """F101, and the reason the control was split.

    At 0.32.5.0 both questions lived in one check inside `verify`, so editing
    any tracked file made the gate unrunnable until the manifest was
    regenerated - which is the act the tool's own error message forbids. The
    hash question is about a commit; a working tree under edit is supposed to
    differ from one. Red against the unsplit control.
    """
    root = _repository(tmp_path, {"a.txt": "one"})
    _point_at(monkeypatch, root)
    check_manifest.write()
    (root / "a.txt").write_text("edited while working", encoding="utf-8")
    assert check_manifest.completeness() == 0
    assert check_manifest.digests() == 1


def test_the_gate_does_not_run_the_digest_half(tmp_path: Path) -> None:
    """The placement is the repair, so the placement is what is held.

    A test of the functions alone would stay green if `verify` grew the digest
    target back, which is exactly the regression F101 is about.
    """
    makefile = (Path(check_manifest.__file__).resolve().parent.parent
                / "Makefile").read_text(encoding="utf-8")
    verify = next(line for line in makefile.splitlines()
                  if line.startswith("verify:"))
    assert "manifest-completeness" in verify
    assert " manifest " not in verify


def test_changed_content_is_reported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = _repository(tmp_path, {"a.txt": "one"})
    _point_at(monkeypatch, root)
    check_manifest.write()
    (root / "a.txt").write_text("edited", encoding="utf-8")
    assert check_manifest.check() == 1


def test_a_listed_file_that_stopped_being_tracked_is_reported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = _repository(tmp_path, {"a.txt": "one", "gone.txt": "bye"})
    _point_at(monkeypatch, root)
    check_manifest.write()
    subprocess.run(["git", "-C", str(root), "rm", "-q", "-f", "gone.txt"], check=True)
    assert check_manifest.check() == 1


def test_the_manifest_does_not_carry_its_own_digest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Writing the line would change the file the line describes."""
    root = _repository(tmp_path, {"a.txt": "one"})
    _point_at(monkeypatch, root)
    check_manifest.write()
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    assert "MANIFEST.sha256" not in check_manifest.MANIFEST.read_text(encoding="utf-8")
    assert check_manifest.check() == 0


def test_no_repository_is_not_a_pass(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Exit 2, the convention `check_no_private_artifacts.py` already uses.

    A control that cannot reach its evidence has not found the tree clean; it
    has found nothing, and returning zero would be the stronger of the two
    claims.
    """
    _point_at(monkeypatch, tmp_path)
    with pytest.raises(SystemExit) as raised:
        check_manifest.check()
    assert raised.value.code == 2
