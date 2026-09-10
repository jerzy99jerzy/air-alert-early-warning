"""T77's close, and the rule that keeps the by-name exclusion from rotting.

`precision_lint` counts figures written to two or more decimals. Three
populations look exactly like such a figure and are not one: four-part version
strings, document versions in prose, and CPython interpreter tokens. The first
is excluded by shape, the second and third by context and by name.

T77's acceptance offered two branches: exclude by *shape*, or record a decision
that version-shaped tokens are counted deliberately. The tree took neither
literally - it excludes interpreters by name, on the argument written in the
module that a shape wide enough for `3.14` swallows a genuine `7.84`. D-052
records that third answer, and these regressions are what make it safe: a
by-name list is only as good as the thing that notices when the list falls
behind the matrix it names.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import precision_lint  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def test_an_interpreter_token_is_not_a_figure() -> None:
    """The red direction T77 named, and the green one beside it."""
    assert precision_lint.FIGURE.findall("failed on 3.14 and not on 3.12") == []
    assert precision_lint.FIGURE.findall("the window is 7.84 days") == ["7.84"]


def test_the_exclusion_covers_every_interpreter_the_matrix_names() -> None:
    """A by-name list rots the day the matrix moves, unless something reads both.

    This is the whole cost of choosing names over shape, and it is payable
    exactly once. When CI gains 3.15, `_INTERPRETERS` must gain it in the same
    commit or this fails, which is cheaper than a ceiling rising for a reason
    the module is not about.
    """
    workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    assert workflows, "no workflow to read the matrix from"
    versions: set[str] = set()
    for workflow in workflows:
        for line in workflow.read_text(encoding="utf-8").splitlines():
            if "python-version:" in line and "[" in line:
                versions |= set(re.findall(r'"(\d+\.\d+)"', line))
    assert versions, "the matrix line was found and no version was read from it"
    for version in sorted(versions):
        assert precision_lint.FIGURE.findall(f"measured on {version} today") == [], (
            f"CI runs {version} and precision_lint would count it as a figure; "
            "extend _INTERPRETERS with the release that added it"
        )


def test_a_version_shaped_token_that_is_not_an_interpreter_still_counts() -> None:
    """The exclusion is a list, not a licence for anything two digits long."""
    assert precision_lint.FIGURE.findall("a ratio of 3.15 to one") == ["3.15"]
    assert precision_lint.FIGURE.findall("a ratio of 4.20 to one") == ["4.20"]
