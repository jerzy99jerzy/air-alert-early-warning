#!/usr/bin/env python3
"""Documentation consistency audit.

Pins in STATUS.json must match what the tree and the documents declare. A
version marker that drifts past a bump is the specific failure this catches: the
README says one thing, the package says another, and both look plausible.

Convention borrowed from `pirx/tools/docs_audit.py`.
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _status() -> dict[str, object]:
    with (ROOT / "STATUS.json").open(encoding="utf-8") as handle:
        result: dict[str, object] = json.load(handle)
    return result


def check_version_pins(status: dict[str, object]) -> list[str]:
    """STATUS.json, pyproject, the package and the changelog agree."""
    problems: list[str] = []
    pinned = status["version"]

    with (ROOT / "pyproject.toml").open("rb") as handle:
        declared = tomllib.load(handle)["project"]["version"]
    if declared != pinned:
        problems.append(f"pyproject version {declared} != STATUS.json {pinned}")

    init = (ROOT / "mavo" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', init)
    if match and match.group(1) != pinned:
        problems.append(f"__version__ {match.group(1)} != STATUS.json {pinned}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    headings = re.findall(r"^##\s*([0-9][0-9A-Za-z.\-]*)", changelog, re.M)
    if headings and headings[0] != pinned:
        problems.append(f"CHANGELOG head {headings[0]} != STATUS.json {pinned}")

    if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", str(pinned)):
        problems.append(f"version {pinned} is not four-segment; the portfolio uses X.Y.Z.W")
    return problems


def check_every_sprint_file_is_named(status: dict[str, object]) -> list[str]:
    """Every sprint the field lists has the regression file the field means.

    The field was called ``shipped_sprints`` until 0.28.2.0, which is the name
    F93 was logged against: it means "a test file exists", it was read as
    "the sprint met its exit criterion", and the reconciliation lived in the
    defect log while the misleading name stayed in the artefact a reader opens
    first. A defect entry is not a repair.
    """
    sprints = status["sprint_test_files"]
    assert isinstance(sprints, list)
    return [
        f"sprint {number} declared shipped but tests/test_sprint{number}.py is missing"
        for number in sprints
        if not (ROOT / f"tests/test_sprint{number}.py").exists()
    ]


def check_threat_model_numbering(status: dict[str, object]) -> list[str]:
    """Threat rows are numbered MT1..MTn with no gaps, and the count is pinned."""
    text = (ROOT / "docs" / "THREAT-MODEL.md").read_text(encoding="utf-8")
    found = sorted({int(number) for number in re.findall(r"\bMT(\d+)\b", text)})
    problems: list[str] = []
    if not found:
        return ["docs/THREAT-MODEL.md has no numbered MT rows"]
    expected = list(range(1, found[-1] + 1))
    missing = sorted(set(expected) - set(found))
    if missing:
        problems.append(f"threat model numbering has gaps: MT{missing}")
    if len(found) != status["threat_model_rows"]:
        problems.append(
            f"threat model has {len(found)} rows, STATUS.json pins {status['threat_model_rows']}"
        )
    return problems


def check_harness_catalogue(status: dict[str, object]) -> list[str]:
    """Every catalogued attack has a test, and the count is pinned."""
    catalogue = ROOT / "tests" / "harness" / "CATALOGUE.md"
    if not catalogue.exists():
        return ["tests/harness/CATALOGUE.md is missing"]
    text = catalogue.read_text(encoding="utf-8")
    rows = sorted({int(number) for number in re.findall(r"\bA(\d+)\b", text)})
    tests = (ROOT / "tests" / "harness" / "test_attacks.py").read_text(encoding="utf-8")
    problems = [f"A{number} is catalogued but has no test" for number in rows
                if f"def test_a{number}_" not in tests]
    if len(rows) != status["harness_attacks"]:
        problems.append(
            f"catalogue has {len(rows)} attacks, STATUS.json pins {status['harness_attacks']}"
        )
    return problems


def check_contents_anchors_resolve() -> list[str]:
    """Every in-document link points at a heading that exists.

    Six documents now carry a contents index, which is six new surfaces for
    class-1 drift: a renamed section leaves a link that renders as a link and
    goes nowhere. GitHub's anchor rules are reimplemented here rather than
    assumed, and the reimplementation is the risk this check carries.
    """
    problems: list[str] = []
    for document in sorted(ROOT.glob("docs/*.md")) + [ROOT / "README.md"]:
        text = document.read_text(encoding="utf-8")
        headings = {
            "#" + re.sub(r"[^a-z0-9 -]", "", heading.lower()).replace(" ", "-")
            for heading in re.findall(r"^#{1,4} (.+)$", text, re.M)
        }
        for link in set(re.findall(r"\]\((#[a-z0-9-]+)\)", text)):
            if link not in headings:
                problems.append(f"{document.name} links to {link}, which is not a heading in it")
    return problems


def check_measured_block_is_recomputed(status: dict[str, object]) -> list[str]:
    """Two fields in STATUS.json that are results, not counts, are re-derived.

    `candidate_rules_passing_gate` sat at 0 for three releases after D-014 made
    it 1, and nothing noticed: the badge checks cover counts of files and rows,
    and this block is the one place the repository states an *outcome*. Same
    class as F31, in the block a reader is most likely to quote.

    Only the two fields that can be recomputed cheaply and deterministically are
    checked here. The rest of the block stays a typed claim, which is stated so
    the guarantee is not read as wider than it is.
    """
    import sys as _sys
    _sys.path.insert(0, str(ROOT))
    from mavo.baserate import gate
    from mavo.cli import DEFAULT_POLICY
    from mavo.evaluate import run_policy, run_rule
    from mavo.rules import CANDIDATE_RULES
    from mavo.sources.fixture import generate_history

    nights = generate_history(weeks=208)
    passing = sum(
        1 for rule_id, rule in CANDIDATE_RULES.items()
        if gate(run_rule(rule_id, rule, nights).assessment).passes
    )
    rate = run_policy(DEFAULT_POLICY, nights).combined.assessment.alarm_rate_per_week
    measured = status.get("measured", {})
    assert isinstance(measured, dict)
    problems: list[str] = []
    if measured.get("candidate_rules_passing_gate") != passing:
        problems.append(
            f"candidate_rules_passing_gate recomputes to {passing}, "
            f"STATUS.json states {measured.get('candidate_rules_passing_gate')}"
        )
    pinned_rate = float(measured.get("policy_combined_alarms_per_week", -1))
    if rate is not None and abs(pinned_rate - rate) > 0.005:
        problems.append(
            f"policy_combined_alarms_per_week recomputes to {rate:.2f}, "
            f"STATUS.json states {measured.get('policy_combined_alarms_per_week')}"
        )
    return problems


def check_statistics_match_the_tree(status: dict[str, object]) -> list[str]:
    """The size block in STATUS.json is recomputed, not remembered.

    The README says these numbers are measured at each release and pinned. That
    sentence was true of the intent and false of the mechanism: nothing checked
    them, and at 0.6.2.0 all four rows were a release or two stale while reading
    as authoritative. F31's shape exactly, in the one block that describes the
    repository to a reader who will not open it.

    Counted definition, stated because a count without one drifts by
    reinterpretation: `.py` files under the package, `tests/` and `tools/`
    recursively, and for documentation every `.md` under `docs/` recursively
    plus the top-level authored markdown and the harness catalogue.
    """
    top_level_docs = ["README.md", "CHANGELOG.md", "ENGINEERING.md", "SECURITY.md",
                      "TODO.md", "CONTRIBUTING.md"]
    groups = {
        "package": sorted((ROOT / "mavo").rglob("*.py")),
        "test": sorted((ROOT / "tests").rglob("*.py")),
        "tool": sorted((ROOT / "tools").rglob("*.py")),
        "documentation": (
            sorted((ROOT / "docs").rglob("*.md"))
            + [ROOT / name for name in top_level_docs]
            + [ROOT / "tests" / "harness" / "CATALOGUE.md"]
        ),
    }
    statistics = status.get("statistics", {})
    assert isinstance(statistics, dict)
    problems: list[str] = []
    for label, paths in groups.items():
        present = [path for path in paths if path.exists()]
        counted = {
            f"{label}_files": len(present),
            f"{label}_lines": sum(
                len(path.read_text(encoding="utf-8").splitlines()) for path in present
            ),
        }
        for key, value in counted.items():
            if statistics.get(key) != value:
                problems.append(
                    f"{key} is {value} in the tree, STATUS.json pins {statistics.get(key)}"
                )
    return problems


def check_readme_links_resolve() -> list[str]:
    """Every relative link in the README points at something that exists.

    The documentation table is the map a reader uses before they trust anything
    else, and a dead link there is a claim about the repository that the
    repository does not honour. Cheap to check, and the alternative is finding
    out from someone else's browser.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    problems: list[str] = []
    for target in re.findall(r"\]\((?!https?://|#)([^)]+)\)", readme):
        if not (ROOT / target).exists():
            problems.append(f"README links to {target}, which does not exist")
    return problems


def check_corpus_measurements_carry_an_inventory(status: dict[str, object]) -> list[str]:
    """A measurement over the corpus requires an inventory of that corpus.

    F68. On 2026-08-09 the corpus was lost: sixty thousand posts, one copy, no
    checksum, no inventory, and every published measurement derived from it. The
    tree carried a `MANIFEST.sha256` over its own source files and nothing at
    all over the data those files exist to analyse.

    The re-collection is possible because Telegram addresses posts by id, so the
    same id range yields the same pages. That is also the trap: without an
    inventory, "the second copy is the first one" is an assumption, in the one
    place this project refuses them. So the rule is executable rather than
    remembered - any figure naming the design window in `STATUS.json` requires
    `data/aggregates/corpus_manifest.csv` to exist and to agree with the
    `corpus` block beside those figures.

    Same class as F64, one layer further out: a claim about something the gate
    could not see.
    """
    measured = status.get("measured")
    if not isinstance(measured, dict):
        return ["STATUS.json has no measured block"]
    # Both spellings: `design_window_messages` and
    # `western_episodes_design_window`. The first draft matched only the
    # suffix and would have let half the corpus-derived figures through a
    # check written to catch exactly them.
    derived = sorted(key for key in measured if "design_window" in key)
    if not derived:
        return []

    manifest = ROOT / "data" / "aggregates" / "corpus_manifest.csv"
    if not manifest.exists():
        return [
            f"{len(derived)} measurement(s) are derived from the corpus "
            f"({derived[0]} and others) and {manifest.relative_to(ROOT)} does not exist. "
            "A measurement whose data cannot be identified is not reproducible (F68)"
        ]

    header = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            break
        parts = line.lstrip("# ").split(None, 1)
        if len(parts) == 2:
            header[parts[0]] = parts[1].strip()

    corpus = status.get("corpus")
    if not isinstance(corpus, dict):
        return [
            "STATUS.json carries corpus-derived measurements and no corpus block. "
            "The inventory exists and nothing pins it (F68)"
        ]

    problems = []
    for key, field in (("pages", "pages"), ("messages", "messages"),
                       ("id_range", "id_range"), ("digest", "digest")):
        pinned, found = corpus.get(key), header.get(field)
        if found is None:
            problems.append(f"corpus_manifest.csv header has no {field}")
        elif str(pinned) != found:
            problems.append(
                f"corpus {key} is {found} in the inventory, STATUS.json pins {pinned}"
            )
    return problems


def check_every_document_is_pinned(status: dict[str, object]) -> list[str]:
    """Every document in the tree appears in the ``documents`` block, and vice versa.

    The block was a hand-maintained list that nothing compared against the tree,
    so a document could be added and be invisible to this gate: its version
    marker could drift, or it could carry no marker at all, and every check here
    would still pass. A pin nobody checks is the same shape as a README claim the
    code does not implement, which is the one thing this repository says it will
    not ship (F66). Raised by the reader of `docs/reviews/0.11.1.0.md` on the
    release that added that very document.

    Top-level documents are deliberately out of scope: they are versioned by the
    release rather than by a marker of their own.
    """
    documents = status.get("documents")
    if not isinstance(documents, dict):
        return ["STATUS.json has no documents block"]
    on_disk = {
        str(path.relative_to(ROOT)) for path in sorted((ROOT / "docs").rglob("*.md"))
    }
    pinned = set(documents)
    problems = [
        f"{name} is in the tree and not pinned in STATUS.json"
        for name in sorted(on_disk - pinned)
    ]
    problems += [
        f"{name} is pinned in STATUS.json and not in the tree"
        for name in sorted(pinned - on_disk)
    ]
    return problems


def check_readme_tables_match_the_pins(status: dict[str, object]) -> list[str]:
    """The numbers in the README's own tables equal the pins beside them.

    0.6.2.0 added `check_statistics_match_the_tree` and the README says so, in
    the paragraph directly above the size table: recounted on every run,
    "a gate failure rather than a typo". Only one edge of that triangle was
    ever closed. STATUS.json is compared against the tree; the README is
    compared against nothing, and by 0.16.1.0 every row of both tables was
    stale while the badges twelve lines higher were current and enforced. The
    same document therefore stated two different test counts, and the checked
    one was not the one a reader reaches first.

    A sentence claiming a check exists, in a document the check does not read,
    is the F66 shape aimed at this repository's own front page. Rows are
    located by label rather than by position so that reordering the table does
    not silently drop a row from the audit; a label that stops matching is
    reported as missing rather than skipped.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    statistics = status.get("statistics")
    measured = status.get("measured")
    corpus = status.get("corpus")
    if not (isinstance(statistics, dict) and isinstance(measured, dict)):
        return ["STATUS.json is missing the statistics or measured block"]
    expected: dict[str, list[object]] = {
        r"\| Package `mavo/` \|": [statistics["package_files"], statistics["package_lines"]],
        r"\| Tests \| \d": [statistics["test_files"], statistics["test_lines"]],
        r"\| Tools \|": [statistics["tool_files"], statistics["tool_lines"]],
        r"\| Documentation \| \d": [
            statistics["documentation_files"], statistics["documentation_lines"],
        ],
        r"\| Tests \| \*?\*?\d+,": [measured["tests_passing"], status["harness_attacks"]],
        r"\| Coverage \|": [measured["coverage_percent"]],
        r"\| Threat-model rows \|": [status["threat_model_rows"]],
        r"\| Defects logged with their class \|": [status["defects_logged"]],
        r"\| Decisions recorded with reopen conditions \|": [status["decisions_recorded"]],
    }
    if isinstance(corpus, dict) and "messages" in corpus:
        expected[r"\| Corpus \|"] = [corpus["messages"]]
    problems: list[str] = []
    for pattern, values in expected.items():
        rows = [line for line in readme.splitlines() if re.match(pattern, line)]
        if not rows:
            problems.append(f"README has no row matching {pattern!r} for the gate to read")
            continue
        row = rows[0]
        digits = {figure.replace(",", "") for figure in re.findall(r"\d[\d,]*\.?\d*", row)}
        for value in values:
            if str(value) not in digits:
                problems.append(f"README row {row.strip()!r} does not carry the pin {value}")
    return problems


def check_document_versions_match_their_pins(status: dict[str, object]) -> list[str]:
    """The version marker inside a document equals the version pinned for it.

    ``check_every_document_is_pinned`` compares the *set* of documents against
    the tree and says so in its own docstring: a marker "could drift, or it
    could carry no marker at all, and every check here would still pass". It
    did drift. On 0.16.1.0 nine documents disagreed with their pins, up to
    three minor versions apart (`docs/FEED-SPEC.md` header 1.0 against pin 1.3),
    while the gate reported that pins held. A prediction written into a
    docstring and left unguarded is a pin without a reader (F64) with a note
    attached, which is worse than one without: the failure was foreseen and the
    check was still not written. This is that check.

    Two marker styles exist in the tree and both are read here: the fenced
    ``Document:  docs/X.md, version N.N`` block used by the older documents,
    and the ``Version: N.N / date`` line used by the ones written since
    0.12.0.0. A document carrying neither is reported rather than skipped,
    because a document with no marker cannot drift and cannot be checked, and
    silence about it would be the same gap one level down.
    """
    documents = status.get("documents")
    if not isinstance(documents, dict):
        return []  # the pinning check beside this one reports the missing block
    problems: list[str] = []
    for name, pinned in sorted(documents.items()):
        path = ROOT / name
        if not path.exists():
            continue  # reported by check_every_document_is_pinned
        head = path.read_text(encoding="utf-8")[:1500]
        match = re.search(rf"Document:\s+{re.escape(name)}, version (\d+\.\d+)", head)
        if match is None:
            match = re.search(r"^Version:\s+(\d+\.\d+)", head, re.M)
        if match is None:
            if name.startswith("docs/reviews/"):
                continue  # a review is versioned by the release it reviews
            problems.append(f"{name} carries no version marker, STATUS.json pins {pinned}")
            continue
        if match.group(1) != pinned:
            problems.append(
                f"{name} declares version {match.group(1)}, STATUS.json pins {pinned}"
            )
    return problems


# D-021. Major releases only: the second component moving. At five releases in
# an afternoon, one review per release is a rule that cannot be followed, and a
# rule that cannot be followed is not narrower than this one, it is absent.
UNREVIEWED = frozenset({
    "0.1.0", "0.2.0.0", "0.7.0.0", "0.8.0.0", "0.9.0.0", "0.10.0.0",
    "0.11.0.0", "0.12.0.0", "0.14.0.0", "0.16.0.0", "0.17.0.0", "0.18.0.0",
    # 0.19.0.0 was the first of a five-release run worked in one sitting. The
    # code it introduced is reviewed in `docs/reviews/0.20.0.0.md`, which read
    # the whole run; writing a separate file for the first release of the run
    # would be splitting one reading into two documents to satisfy a counter.
    "0.19.0.0",
})


def check_major_releases_carry_a_review() -> list[str]:
    """Every major release has a file in `docs/reviews/`, or is named as lacking one.

    F79. Four documents said this directory held one review per release while
    it held nine for fifty, and the gap grew for nineteen releases without
    anything noticing, because reviews kept being written and kept landing in
    session artifacts instead of the tree.

    The grandfathered set is a frozen list rather than a date cutoff: a cutoff
    would quietly absorb the next release that skips a review, which is how the
    first nineteen accumulated. Adding to this set is a visible act, and
    `docs/reviews/README.md` explains why each entry is in it.
    """
    releases = re.findall(r"^## (\d[\d.]*) - ", (ROOT / "CHANGELOG.md")
                          .read_text(encoding="utf-8"), re.M)
    filed = {path.stem for path in (ROOT / "docs" / "reviews").glob("*.md")}
    problems: list[str] = []
    for version in releases:
        parts = version.split(".")
        is_major = len(parts) >= 3 and parts[2] == "0" and (len(parts) < 4 or parts[3] == "0")
        if not is_major or version in UNREVIEWED or version in filed:
            continue
        problems.append(
            f"{version} is a major release with no docs/reviews/{version}.md, and it "
            f"is not in the named unreviewed set"
        )
    stale = sorted(UNREVIEWED & filed)
    if stale:
        problems += [
            f"{version} is listed as unreviewed and has a review file; remove it "
            f"from UNREVIEWED" for version in stale
        ]
    return problems


def check_defect_count_is_pinned(status: dict[str, object]) -> list[str]:
    """The defect badge equals the count of F-entries in the methodology.

    Added in 0.6.0.0 when the review landed three entries at once: the badge is
    typed by hand, and a hand-typed count drifts on exactly the release that
    adds entries. The pin is checked against the document, and the badge against
    the pin, so all three agree or the gate says which one is lying.
    """
    entries = len(re.findall(r"^### F\d+", (ROOT / "docs" / "METHODOLOGY.md")
                             .read_text(encoding="utf-8"), re.M))
    pinned = status.get("defects_logged")
    problems: list[str] = []
    if pinned != entries:
        problems.append(f"METHODOLOGY has {entries} F-entries, STATUS.json pins {pinned}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if f"defects%20logged-{pinned}-" not in readme:
        problems.append(f"README defect badge does not match STATUS.json pin {pinned}")
    return problems


#: Decision numbers cited elsewhere in the tree that have no entry in the log.
#: Each one is a document resting its authority on a record that is not there.
#: The check below fails if a number here has gained an entry, so a resolved
#: item cannot sit in this list pretending to still be open.
#:
#: D-025 is cited by ``docs/WEBAPP.md`` as the reason publication went ahead
#: without T6, the legal position, and the sentence doing the citing says the
#: reason "is in the decision entry". Whether the entry was drafted and never
#: committed, renumbered, or never written, only the operator knows. Until it
#: is resolved the citation is the strongest claim in this repository resting
#: on the weakest evidence, which is why it is named here rather than deleted.
CITED_WITHOUT_AN_ENTRY = ("D-025",)


def check_decision_count_is_derived_from_the_log(status: dict[str, object]) -> list[str]:
    """The decision count comes from the log, and citations resolve to entries.

    Added at 0.31.0.0. ``defects_logged`` has been counted from METHODOLOGY and
    checked against the README badge since 0.6.0.0; ``decisions_recorded`` was
    compared only against a README row, so two hand-typed numbers agreed with
    each other and with nothing. They were both 27 against a log holding 25
    entries, and the drift hid a second thing: D-023 and D-025 are absent, and
    D-025 is cited by another document as settled.

    Same lesson as F31 one level up. A count that is not derived from the thing
    it counts is a claim, and a claim that agrees with a copy of itself is not
    corroborated.
    """
    text = (ROOT / "docs" / "DECISIONS.md").read_text(encoding="utf-8")
    entries = sorted(set(re.findall(r"^## (D-\d+)", text, re.M)))
    problems: list[str] = []

    pinned = status.get("decisions_recorded")
    if pinned != len(entries):
        problems.append(
            f"DECISIONS.md holds {len(entries)} entries, STATUS.json pins {pinned}")

    documents = sorted((ROOT / "docs").glob("*.md")) + [ROOT / "README.md", ROOT / "TODO.md"]
    cited: set[str] = set()
    for path in documents:
        if path.name == "DECISIONS.md":
            continue
        cited |= set(re.findall(r"\bD-\d{3}\b", path.read_text(encoding="utf-8")))

    dangling = sorted(cited - set(entries))
    for number in dangling:
        if number not in CITED_WITHOUT_AN_ENTRY:
            problems.append(
                f"{number} is cited in the tree and has no entry in docs/DECISIONS.md")
    for number in CITED_WITHOUT_AN_ENTRY:
        if number in entries:
            problems.append(
                f"{number} now has an entry; remove it from CITED_WITHOUT_AN_ENTRY")
        elif number not in cited:
            problems.append(
                f"{number} is no longer cited anywhere; remove it from "
                "CITED_WITHOUT_AN_ENTRY rather than leaving a tolerance for nothing")
    return problems


def check_badges_match_the_pins(status: dict[str, object]) -> list[str]:
    """Static badge values agree with STATUS.json.

    A live CI badge tells the truth by construction. A static one is a claim
    typed by hand, which is the shape of F31: a measurement block updated field
    by field until the flattering field is the stale one. Coverage is the one
    that would embarrass this repository most, so it is checked first.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    measured = status["measured"]
    assert isinstance(measured, dict)
    statistics = status.get("statistics", {})
    assert isinstance(statistics, dict)

    expected = {
        "tests": f"tests-{measured['tests_passing']}-",
        "coverage": f"coverage-{measured['coverage_percent']:.2f}%25-",
        "harness": f"harness-{status['harness_attacks']}%20attacks",
        "mutations": f"{measured['harness_mutations_killed']}%20mutation--verified",
        "runtime dependencies":
            f"runtime%20dependencies-{statistics.get('runtime_dependencies', 0)}-",
    }
    return [
        f"README badge for {label} does not match STATUS.json (expected {fragment!r})"
        for label, fragment in expected.items()
        if fragment not in readme
    ]


def check_cited_tests_exist() -> list[str]:
    """Every ``file.py::test_name`` cited in documentation resolves to a test.

    F42. `docs/THREAT-MODEL.md` cited a test measuring MT8 that has never existed
    in this repository under that name, and it survived three releases because
    nothing resolves a citation. A threat row naming a test that does not exist
    is a control that nobody is measuring while the table says otherwise, which
    is the same class as a README claim the tree does not implement.
    """
    problems: list[str] = []
    pattern = re.compile(r"([a-z_0-9]+\.py)::(test_[a-z_0-9]+)")
    for document in sorted(ROOT.glob("docs/*.md")) + [
        ROOT / "README.md",
        ROOT / "tests" / "harness" / "CATALOGUE.md",
    ]:
        if not document.exists():
            continue
        for filename, test_name in pattern.findall(document.read_text(encoding="utf-8")):
            candidates = list((ROOT / "tests").rglob(filename))
            if not candidates:
                problems.append(f"{document.name} cites {filename}, which does not exist")
                continue
            if not any(f"def {test_name}(" in path.read_text(encoding="utf-8")
                       for path in candidates):
                problems.append(f"{document.name} cites {filename}::{test_name}, which does not")
    return problems


def check_the_readme_status_agrees_with_the_sprint_files(
    status: dict[str, object],
) -> list[str]:
    """The README's status line must count the same sprints STATUS.json does.

    **What ``sprint_test_files`` means, because reading it wrong is F93.** The
    field's only other consumer checks that ``tests/test_sprintN.py`` exists,
    so a sprint is in this list when its code landed with regressions. It does
    **not** mean the sprint met the exit criterion in ``docs/MVP.md``. This
    check verifies only that the README's "Sprints 0 to N shipped" quotes the
    same N as the field. It cannot verify the completion claim beside it, and
    an earlier version of this docstring implied it could.

    The README said "Sprints 0 to 6" while the field listed nine, and nothing
    compared them for three releases - the F81 and F89 shape, in the first
    paragraph a reader sees. The repair for that drift then made the document
    agree with the field without checking what the field meant, which is F93
    and is the reason this docstring is longer than the check.

    The list must also be contiguous: "0 to N" is a truthful summary only over
    a list with no holes, and a hole is a sprint whose file was never written.
    """
    shipped = status.get("sprint_test_files")
    if not isinstance(shipped, list) or not shipped:
        return ["STATUS.json carries no sprint_test_files list"]
    numbers = sorted(int(value) for value in shipped)
    problems = []
    if numbers != list(range(numbers[0], numbers[-1] + 1)):
        problems.append(
            f"sprint_test_files has a hole: {numbers}. A gap is a sprint that was "
            "skipped or rounded up, and the README summary cannot describe it"
        )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    # The README counts sprint *files*, which is the same definition the field
    # uses, and states the count rather than a range. It moved from "Sprints 0
    # to N shipped" at 0.25.6.0 because the field is known to be behind the
    # tree and is left behind deliberately: raising it would assert that three
    # more sprints met their exit criteria. So the check compares the README
    # against the tree, and separately requires the README to say so when the
    # field disagrees, rather than forcing two numbers to match by editing
    # whichever is easier.
    files = sorted(
        int(match.group(1))
        for path in (ROOT / "tests").glob("test_sprint*.py")
        if (match := re.fullmatch(r"test_sprint(\d+)\.py", path.name))
    )
    claimed = re.search(r"\*\*(\w+) sprints have landed with their regression files\*\*",
                        readme)
    if claimed is None:
        problems.append(
            "the README status line no longer states how many sprints landed "
            "with their regression files; this check reads that sentence and "
            "cannot verify a rephrasing"
        )
    else:
        words = {"nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
                 "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16}
        said = words.get(claimed.group(1).lower())
        if said is None:
            problems.append(
                f"the README says {claimed.group(1)!r} sprints landed and this "
                "check does not know that number word"
            )
        elif said != len(files):
            problems.append(
                f"the README says {said} sprint files landed, the tree has "
                f"{len(files)}"
            )
    if len(files) != len(numbers) and "left wrong deliberately" not in readme:
        problems.append(
            f"sprint_test_files lists {len(numbers)} sprints and the tree has "
            f"{len(files)} sprint files, and the README does not say the field "
            "is behind on purpose"
        )
    return problems


def check_the_holdout_boundary_survives_in_the_corpus_block(
    status: dict[str, object],
) -> list[str]:
    """D-012a's freeze record must exist, and no write may silently drop it.

    The boundary between the design window and the holdout was frozen before
    any message content was read, and STATUS.json's ``corpus`` block is where
    that record lives. On 2026-08-09 ``corpus_inventory.py --write-status``
    replaced the block wholesale and erased it, and the gate passed, because no
    check read those fields - the exact F64 shape, one field further out. This
    check is the missing reader: the fields must be present, the boundary must
    be internally consistent, and the freeze flag must be an explicit boolean,
    so the next tool that eats the block turns the gate red instead of passing.
    """
    corpus = status.get("corpus")
    if not isinstance(corpus, dict):
        # The inventory check beside this one already reports the missing block.
        return []
    problems = []
    for field in (
        "design_window_high_id",
        "holdout_low_id",
        "holdout_share",
        "content_read_before_freeze",
    ):
        if field not in corpus:
            problems.append(
                f"corpus block has no {field}: the D-012a holdout record has been "
                "dropped by a write that did not own it"
            )
    if problems:
        return problems
    high, low = corpus["design_window_high_id"], corpus["holdout_low_id"]
    if not (isinstance(high, int) and isinstance(low, int) and low == high + 1):
        problems.append(
            f"holdout boundary is not contiguous: design_window_high_id {high} "
            f"and holdout_low_id {low} must be adjacent ids"
        )
    if not isinstance(corpus["content_read_before_freeze"], bool):
        problems.append(
            "content_read_before_freeze must be an explicit boolean, "
            "not a value that reads as one"
        )
    return problems


def main() -> int:
    """Run every audit. Returns a process exit code."""
    status = _status()
    problems = (
        check_version_pins(status)
        + check_every_sprint_file_is_named(status)
        + check_threat_model_numbering(status)
        + check_harness_catalogue(status)
        + check_cited_tests_exist()
        + check_readme_links_resolve()
        + check_every_document_is_pinned(status)
        + check_document_versions_match_their_pins(status)
        + check_readme_tables_match_the_pins(status)
        + check_major_releases_carry_a_review()
        + check_corpus_measurements_carry_an_inventory(status)
        + check_the_holdout_boundary_survives_in_the_corpus_block(status)
        + check_the_readme_status_agrees_with_the_sprint_files(status)
        + check_defect_count_is_pinned(status)
        + check_decision_count_is_derived_from_the_log(status)
        + check_statistics_match_the_tree(status)
        + check_measured_block_is_recomputed(status)
        + check_badges_match_the_pins(status)
        + check_contents_anchors_resolve()
    )
    for problem in problems:
        print(f"docs-audit: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"docs-audit: pins hold at {status['version']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
