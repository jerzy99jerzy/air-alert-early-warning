"""F72 regressions: a version pin nobody compares against the document.

``check_every_document_is_pinned`` compares the set of documents against the
tree, and its own docstring says a version marker "could drift, or it could
carry no marker at all, and every check here would still pass". It drifted.
On 0.16.1.0 nine documents disagreed with their pins, `docs/FEED-SPEC.md`
by three minor versions, while the gate printed that pins held.

These tests hold the reader in place. Verified red on a scratch copy carrying
the pre-repair headers.

The last test exists because the first attempt at this repair had the defect it
was repairing: the tests below import the check directly, so deleting its line
from `main` left them all green while the gate stopped running it. A check that
is not registered is a check that does not run.
"""

from __future__ import annotations

from pathlib import Path

from tools.docs_audit import check_document_versions_match_their_pins


def _status(pin: str) -> dict[str, object]:
    return {"documents": {"docs/METHODOLOGY.md": pin}}


def test_a_document_that_declares_a_different_version_than_its_pin_is_reported() -> None:
    """The exact 0.16.1.0 shape: the tree says one thing, STATUS.json another."""
    problems = check_document_versions_match_their_pins(_status("99.9"))
    assert problems, "a document three versions from its pin passed the gate"
    assert "docs/METHODOLOGY.md" in problems[0]
    assert "99.9" in problems[0]


def test_a_document_that_agrees_with_its_pin_is_silent() -> None:
    """Whatever the methodology's real version is, the tree is the reference."""
    head = Path("docs/METHODOLOGY.md").read_text(encoding="utf-8")[:1500]
    declared = head.split("version ")[1].split("\n")[0].strip()
    assert check_document_versions_match_their_pins(_status(declared)) == []


def test_a_document_with_no_version_marker_is_reported_rather_than_skipped() -> None:
    """A document that cannot drift also cannot be checked, and silence hides that.

    `LICENSE` carries no marker of this kind. Pinning it must produce a
    complaint, not a pass: skipping unmarked documents would rebuild the gap
    one level down.
    """
    problems = check_document_versions_match_their_pins({"documents": {"LICENSE": "1.0"}})
    assert problems and "no version marker" in problems[0]


def test_a_review_without_a_marker_is_out_of_scope() -> None:
    """Reviews are versioned by the release they review, not by a marker."""
    review = next(Path("docs/reviews").glob("*.md"))
    status = {"documents": {str(review).replace("\\", "/"): "1.0"}}
    assert check_document_versions_match_their_pins(status) == []


def test_every_document_in_the_tree_agrees_with_its_pin() -> None:
    """The gate check itself, run against the real STATUS.json.

    Duplicated here deliberately: `make verify` runs `docs_audit` as a process,
    so a failure there prints a message; a failure here names the test that
    covers it and fails with the suite.
    """
    import json

    status = json.loads(Path("STATUS.json").read_text(encoding="utf-8"))
    assert check_document_versions_match_their_pins(status) == []


def test_both_new_checks_are_registered_in_the_audit() -> None:
    """A check the gate does not call is decoration.

    Found while verifying this repair: unregistering either check from `main`
    left every test in this file green, because they call the functions
    directly. The registration is the part that runs on `make verify`, so the
    registration is what needs a reader.
    """
    source = Path("tools/docs_audit.py").read_text(encoding="utf-8")
    body = source.split("def main(")[1]
    for name in (
        "check_document_versions_match_their_pins",
        "check_readme_tables_match_the_pins",
    ):
        assert f"+ {name}(status)" in body, f"{name} is defined but never called by the gate"
