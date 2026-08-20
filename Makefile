# `make verify` is the only gate. CI calls this target rather than restating it.
PY := python3
PKG := mavo

.PHONY: verify private-artifacts lint-precision manifest-completeness manifest manifest-write coverage lint lint-limitations lint-hygiene lint-mermaid lint-domain docs-audit manual-audit contract-check todo-index brief-check harness-mutation clean

verify: private-artifacts manifest-completeness coverage lint lint-limitations lint-hygiene lint-mermaid lint-domain lint-precision docs-audit manual-audit contract-check todo-index brief-check harness-mutation
	@echo "verify: OK"

# pytest exits 5 when nothing is collected. That exit code is NOT swallowed:
# an empty suite must fail the gate, not pass it.
#
# The two machine-readable reports are not extra output, they are the reason
# `docs-audit` can enforce `tests_passing` and `coverage_percent` instead of
# trusting them. They land in `.gate/`, which is ignored: they describe this
# run on this machine and committing them would create a third place where the
# same numbers can disagree. `coverage` runs before `docs-audit` in `verify`
# above, which is what makes the artefacts present when the audit reads them;
# `docs-audit` fails rather than skips when they are not.
coverage:
	@mkdir -p .gate
	$(PY) -m pytest tests -q --cov=$(PKG) --cov-branch --cov-report=term-missing --cov-report=json:.gate/coverage.json --junitxml=.gate/tests.xml

# `tools/` is inside the net. Half the measured numbers in STATUS.json are
# produced there, and `harness_mutation.py` is itself part of this gate; a
# gate whose own instruments are unlinted and untyped is auditing everything
# except the audit.
lint:
	ruff check $(PKG) tests tools
	mypy $(PKG) tools

lint-limitations:
	$(PY) tests/lint_limitations.py

lint-hygiene:
	$(PY) tests/lint_hygiene.py

lint-mermaid:
	$(PY) tests/lint_mermaid.py

lint-domain:
	$(PY) tests/lint_domain.py

# A figure printed past the precision that changes a decision is not rigour.
# Counted per document against a ceiling that may fall and may not rise,
# because which class a figure belongs to is not decidable from its shape:
# `0.076` and `7.84` look identical and only one of them is noise.
lint-precision:
	$(PY) tools/precision_lint.py

docs-audit:
	$(PY) tools/docs_audit.py

manual-audit:
	$(PY) tools/manual_audit.py

# D-020 put the state.json schema in this repository on the argument that the
# producer's gate can exercise it. Then nothing did, and F74 shipped: the
# consumer's map drew nothing while its distance list drew everything. This is
# the reader that argument implied.
contract-check:
	$(PY) tools/contract_check.py

# The backlog summarises itself, and a summary nobody checks is the shape of
# F31 and F73. `--check` compares the index block against the entries below it
# and fails on an open task with no tier, because a task nobody has ordered is
# a decision nobody has made.
todo-index:
	$(PY) tools/todo_index.py --check

# The two briefs are one document in two languages and drifted apart within an
# hour of the second one being written. This compares the figures they share,
# and only those: prose accuracy is not reachable by a check and pretending
# otherwise would be worse than the honest gap.
brief-check:
	$(PY) tools/brief_check.py

# F14, paid after two slips. A harness that has never been observed failing is
# not evidence. This copies the tree and runs pytest once per mutation, measured
# at roughly 7 seconds, which is why the cost is stated here rather than left to
# be discovered. It is in `verify` because a check outside the gate is a check
# that does not run.
harness-mutation:
	$(PY) tools/harness_mutation.py

clean:
	rm -rf dist build *.egg-info .pytest_cache .coverage htmlcov .gate

# The manifest answers two questions and they belong in different places, which
# is F101. Completeness - every tracked file listed, nothing listed untracked -
# survives an edit and is in `verify`. It is also the question `shasum -c` never
# had: that command cannot report a line the manifest does not contain, and
# thirteen tracked files were in exactly that state at 0.32.4.0.
manifest-completeness:
	$(PY) tools/check_manifest.py --completeness

# Digests answer whether the manifest describes *this commit*, so this is NOT in
# `verify`. It was, for one release, and it made the gate unrunnable after any
# edit: the only way past was to regenerate, which is the act the tool's own
# error message forbids. Run before a tag, on the detached worktree, and in CI
# after the push. Both halves run here.
manifest:
	$(PY) tools/check_manifest.py

# Regeneration is a release step, not a repair step. Running it to make a check
# green is the same act as moving a tag.
manifest-write:
	$(PY) tools/check_manifest.py --write

# OUTREACH.md and the pitch drafts live one directory from this tree and
# describe people rather than software: names, a ministry address, dates and
# contents of letters, and a log of a rule broken on purpose. One stray
# 'git add .' in the wrong directory publishes all of it, and a 404 on the
# public URL is a measurement of today, not a property of the repository.
# Path-based by design: a content pattern list would have to carry the very
# names it protects. Placed first in 'verify' because it is the cheapest
# check here and the only one whose failure a later commit cannot undo.
private-artifacts:
	$(PY) tools/check_no_private_artifacts.py
