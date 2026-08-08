# Contributing

Invariants a change must not break. `make verify` enforces most of them; the rest
are here because they are judgement rather than syntax.

## The one principle

A claim the repository makes about itself is executable. If a change adds a
sentence about what the tool does or does not do, that sentence gets a check in
`tests/lint_limitations.py` in the same commit, or it does not go in.

## Invariants

- **One namespace.** `mavo` is the only top-level package. `tests/lint_domain.py`
  fails otherwise.
- **`baserate.py` stays top-level.** It is the point of the project and stays
  visible in a directory listing.
- **Unknown is never the safe state.** New state handling adds a test asserting
  both directions.
- **Runtime dependencies stay empty** unless the changelog entry that adds one
  justifies it.
- **No astronomical variable.** See `docs/DECISIONS.md` D-002. This is enforced
  at the term level in package source.
- **A regression test is verified to fail against the previous state**, not
  assumed to. Unpack the last tag into a scratch directory, drop the test in,
  confirm red. This has already caught a mis-scoped test in this repository.
- **Gate thresholds are published in the README.** Moving one is a scope change
  and the README table moves in the same commit, with the reason.

## Sprint shape

A sprint has a defect class or a capability, not a list of chores. Baseline green
first, probe rather than read, fix then generalise, regression test verified red,
self-review the diff, record the defect in `docs/METHODOLOGY.md`, one release.
