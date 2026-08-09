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
- **A harness attack lands with a mutation, or is listed as unverified.** A new
  row in `tests/harness/CATALOGUE.md` adds an entry to `MUTATIONS` in
  `tools/harness_mutation.py` that disables the control it guards, and the attack
  must go red under it. Where no single substitution can disable the control, the
  attack goes in `UNVERIFIED` with the reason, and the count is printed on every
  run. A green attack is not evidence that a control holds; the first mutation
  run of this repository killed 7 of 10 and the three survivors were defects in
  the attacks, one of them written the same afternoon (F38 to F40).
- **A state is added by widening a check, not by naming a state.** The lint
  behind the unknown-not-clear claim enumerates `AlertState`, so a fifth member
  is covered the day it lands. Adding a member and a matching special case in the
  lint is the version of this that rots.

## Sprint shape

A sprint has a defect class or a capability, not a list of chores. Baseline green
first, probe rather than read, fix then generalise, regression test verified red,
self-review the diff, record the defect in `docs/METHODOLOGY.md`, one release.
