"""The check T22 asked for, verified in both directions.

F55 is what it closes: `docs/COMPUTATION.md` cited a constant that did not
exist, in the document whose subject is that figures come from measurement
rather than from memory. The acceptance names the red direction - *verified red
by citing a fabricated symbol in a scratch copy* - so the fabrications below are
the point of the file rather than decoration.

The quiet directions matter as much. A check on backticked names in thirty-one
documents will meet Python builtins, environment variables, another platform's
constants and the name of a symbol this project deliberately removed, and it has
to stay silent on all four or it will be switched off within a release.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import docs_audit  # noqa: E402


def _scratch(tmp_path: Path, body: str, name: str = "SCRATCH.md") -> Path:
    """A tree with one document in it, and no README."""
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / name).write_text(body, encoding="utf-8")
    return tmp_path


def test_the_tree_passes_today() -> None:
    """Green first, so red means something."""
    assert docs_audit.check_cited_identifiers_exist() == []


def test_a_fabricated_call_is_caught(tmp_path: Path) -> None:
    root = _scratch(tmp_path, "The loop calls `reconcile_everything()` each cycle.\n")
    problems = docs_audit.check_cited_identifiers_exist(root)
    assert len(problems) == 1
    assert "reconcile_everything" in problems[0]


def test_a_fabricated_constant_is_caught(tmp_path: Path) -> None:
    """F55's own shape, in one line."""
    root = _scratch(tmp_path, "The ceiling is `MAX_ALARMS_PER_NIGHT` in the package.\n")
    problems = docs_audit.check_cited_identifiers_exist(root)
    assert len(problems) == 1
    assert "MAX_ALARMS_PER_NIGHT" in problems[0]
    assert "CITED_BUT_NOT_OURS" in problems[0]


def test_a_fabricated_module_path_is_caught(tmp_path: Path) -> None:
    root = _scratch(tmp_path, "See `mavo.delivery.push_state` for the transport.\n")
    problems = docs_audit.check_cited_identifiers_exist(root)
    assert len(problems) == 1
    assert "mavo.delivery.push_state" in problems[0]


def test_a_real_module_path_is_quiet(tmp_path: Path) -> None:
    """`mavo.obs.from_environment` exists and must not be reported."""
    root = _scratch(tmp_path, "The sink comes from `mavo.obs.from_environment`.\n")
    assert docs_audit.check_cited_identifiers_exist(root) == []


def test_a_name_bound_only_by_an_import_alias_is_quiet(tmp_path: Path) -> None:
    """The first version of this check reported `sink_from_environment()`.

    It is bound in `mavo/cli.py` by `import ... as`, which binds a name without
    defining one, and a checker that reads only definitions cannot see it. The
    repair was to read aliases too rather than to allow-list the symptom.
    """
    root = _scratch(tmp_path, "The loop builds it with `sink_from_environment()`.\n")
    assert docs_audit.check_cited_identifiers_exist(root) == []


def test_a_builtin_is_not_a_citation(tmp_path: Path) -> None:
    """`max()` in prose about arithmetic is not a claim about this package."""
    root = _scratch(tmp_path, "The bound is `max()` of the two, never `next()`.\n")
    assert docs_audit.check_cited_identifiers_exist(root) == []


def test_an_environment_variable_is_not_a_symbol(tmp_path: Path) -> None:
    """`MAVO_LOG_FILE` is set by a unit file and bound by nothing in the tree."""
    root = _scratch(tmp_path, "The unit carries `MAVO_LOG_FILE` and `MAVO_RUN_ID`.\n")
    assert docs_audit.check_cited_identifiers_exist(root) == []


def test_an_allow_listed_name_is_quiet(tmp_path: Path) -> None:
    """Including a symbol this project removed on purpose.

    A defect register that could not name what is gone would be a register of
    only the present, which is the opposite of its job.
    """
    root = _scratch(
        tmp_path,
        "It cited `MAX_ALARMS_PER_WEEK`, which was removed, and the consumer's "
        "`SLUG_ALIASES`, and Android's `IMPORTANCE_HIGH`.\n",
    )
    assert docs_audit.check_cited_identifiers_exist(root) == []


def test_a_short_call_is_below_the_pattern(tmp_path: Path) -> None:
    """`f()` in a formula is not a citation, and the floor is stated in code."""
    root = _scratch(tmp_path, "Write the rate as `f()` over the window.\n")
    assert docs_audit.check_cited_identifiers_exist(root) == []


def test_every_allow_list_entry_carries_a_reason() -> None:
    """An allow-list is where a check goes to die, so entries are policed too.

    Not a style rule: an entry with an empty reason is indistinguishable from a
    failure somebody silenced, and this check exists because a document said
    something nobody could verify.
    """
    for name, reason in docs_audit.CITED_BUT_NOT_OURS.items():
        assert reason and len(reason) > 20, name
