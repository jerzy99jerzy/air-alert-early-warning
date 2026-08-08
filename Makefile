# `make verify` is the only gate. CI calls this target rather than restating it.
PY := python3
PKG := mavo

.PHONY: verify coverage lint lint-limitations lint-hygiene lint-mermaid lint-domain docs-audit manual-audit clean

verify: coverage lint lint-limitations lint-hygiene lint-mermaid lint-domain docs-audit manual-audit
	@echo "verify: OK"

# pytest exits 5 when nothing is collected. That exit code is NOT swallowed:
# an empty suite must fail the gate, not pass it.
coverage:
	$(PY) -m pytest tests -q --cov=$(PKG) --cov-branch --cov-report=term-missing

lint:
	ruff check $(PKG) tests
	mypy $(PKG)

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

clean:
	rm -rf dist build *.egg-info .pytest_cache .coverage htmlcov
