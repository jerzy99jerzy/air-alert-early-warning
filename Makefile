# `make verify` is the only gate. CI calls this target rather than restating it.
PY := python3
PKG := mavo

.PHONY: verify coverage lint lint-limitations lint-hygiene lint-mermaid lint-domain docs-audit manual-audit contract-check todo-index brief-check harness-mutation clean

verify: coverage lint lint-limitations lint-hygiene lint-mermaid lint-domain docs-audit manual-audit contract-check todo-index brief-check harness-mutation
	@echo "verify: OK"

# pytest exits 5 when nothing is collected. That exit code is NOT swallowed:
# an empty suite must fail the gate, not pass it.
coverage:
	$(PY) -m pytest tests -q --cov=$(PKG) --cov-branch --cov-report=term-missing

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
	rm -rf dist build *.egg-info .pytest_cache .coverage htmlcov
