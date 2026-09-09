"""The check added at 0.54.0.0, verified red as well as green.

Same rule as `test_gate_checks_0_35.py` and `test_gate_checks_0_39_1.py`: a
check observed only passing is not evidence. T84's acceptance asks for the red
direction by name - *verified red by leaving one behind* - so the red fixture
here is not invented. It is `tools/latency.py` as it stood at 0.53.5.1: a
module in `tools/` that opens the store with the same `sqlite3.connect` call
the shipped instrument uses.

The three quiet directions matter as much as the loud one. A forwarding shim
imports the moved module and must not read as an instrument; a tool that
*names* the store in a comment must not either, because `tools/manual_audit.py`
does exactly that and a substring check would have moved it; and a tool that
reads the tree is the case the decision explicitly leaves in `tools/`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import lint_domain

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import precision_lint  # noqa: E402

READS_THE_STORE = """
import sqlite3
from contextlib import closing


def read(store):
    with closing(sqlite3.connect(f"file:{store}?mode=ro", uri=True)) as conn:
        return conn.execute("SELECT ts_source FROM events").fetchall()
"""

IMPORTS_THE_STORE = """
from mavo.store import EventStore


def rows(path):
    return EventStore(path).tail(10)
"""

A_FORWARDING_SHIM = """
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mavo.latency import main  # noqa: E402,F401
"""

NAMES_THE_STORE_IN_A_COMMENT = """
# `report --store` and `fixture` construct an `EventStore`, which is why this
# audit knows the word and does not open one: sqlite3.connect is not called
# here, it is discussed.
TEXT = "EventStore"
"""

READS_THE_TREE = """
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def lines():
    return sum(len(p.read_text().splitlines()) for p in ROOT.glob("docs/*.md"))
"""


def _tree(tmp_path: Path, name: str, body: str) -> Path:
    root = tmp_path / "tree"
    (root / "tools").mkdir(parents=True, exist_ok=True)
    (root / "tools" / name).write_text(body, encoding="utf-8")
    return root


def test_the_tree_passes_today() -> None:
    """The green direction, stated first so the red one means something."""
    assert lint_domain.check_no_tool_reads_the_store() == []


def test_the_instrument_left_behind_is_found(tmp_path: Path) -> None:
    """T84's own fixture: `tools/latency.py` as it stood at 0.53.5.1."""
    root = _tree(tmp_path, "latency.py", READS_THE_STORE)
    problems = lint_domain.check_no_tool_reads_the_store(root)
    assert len(problems) == 1
    assert "tools/latency.py" in problems[0]
    assert "D-038" in problems[0]


def test_a_tool_importing_the_store_module_is_found(tmp_path: Path) -> None:
    """The other way in. A store reached through `EventStore` is still the store."""
    root = _tree(tmp_path, "audit.py", IMPORTS_THE_STORE)
    assert len(lint_domain.check_no_tool_reads_the_store(root)) == 1


def test_a_forwarding_shim_is_not_an_instrument(tmp_path: Path) -> None:
    """The shim imports the module that opens the store and opens nothing.

    If this were red the check would demand the removal of the forwarding
    address D-038 asks for, which is the decision arguing with itself.
    """
    root = _tree(tmp_path, "latency.py", A_FORWARDING_SHIM)
    assert lint_domain.check_no_tool_reads_the_store(root) == []


def test_naming_the_store_in_a_comment_is_not_opening_it(tmp_path: Path) -> None:
    """`tools/manual_audit.py`'s real shape, which a grep would have moved."""
    root = _tree(tmp_path, "manual_audit.py", NAMES_THE_STORE_IN_A_COMMENT)
    assert lint_domain.check_no_tool_reads_the_store(root) == []


def test_a_tool_that_reads_the_tree_stays_where_it_is(tmp_path: Path) -> None:
    """D-038's other half: the tree is `tools/`'s input and always was."""
    root = _tree(tmp_path, "figures.py", READS_THE_TREE)
    assert lint_domain.check_no_tool_reads_the_store(root) == []


def test_a_missing_tools_directory_is_reported_rather_than_skipped(
        tmp_path: Path) -> None:
    """A check that quietly passes when its input is absent is worse than none."""
    problems = lint_domain.check_no_tool_reads_the_store(tmp_path / "nothing")
    assert len(problems) == 1
    assert "not a directory" in problems[0]


# ------------------------------------------- the section-number exclusion ---

SECTIONED = """### 4.10 `mavo attempts` - BUILT

The record is audited by `mavo attempts` (4.10), and section 4.12 measures the
lag. The rate measured on the host was 9.94 requests a second.

### 4.12 `mavo latency` - BUILT
"""

UNANCHORED_REFERENCE = """### 4.10 `mavo attempts` - BUILT

The ratio was (7.84) and section 2.50 is nowhere in this document.
"""


def test_a_section_number_is_not_a_figure(tmp_path: Path) -> None:
    """Renumbering a manual must not read as five new claims of precision.

    Three of the four figure-shaped tokens here are section numbers - the two
    headings, the bracketed back-reference and the `section 4.12` reference -
    and exactly one is a measurement.
    """
    document = tmp_path / "MANUAL.md"
    document.write_text(SECTIONED, encoding="utf-8")
    assert precision_lint.count(document) == 1


def test_a_reference_to_a_heading_that_does_not_exist_still_counts(
        tmp_path: Path) -> None:
    """The exclusion cannot be used to hide a figure by putting it in brackets.

    Only numbers this document carries as headings are blanked, so `(7.84)`
    and a `section 2.50` naming nothing survive as the figures they are.
    """
    document = tmp_path / "MANUAL.md"
    document.write_text(UNANCHORED_REFERENCE, encoding="utf-8")
    assert precision_lint.count(document) == 2
