# Security policy

## What counts as a defect here

This project makes three kinds of guarantee, and a failure of any of them is a
security defect rather than a bug:

1. **Suppression guarantees.** A source claiming implausibly broad activation
   must not produce alarms. If you can construct a feed state that raises an
   alarm through the suppression, that is a defect.
2. **State guarantees.** An unknown area state must never contribute to an
   all-clear or an alarm. A path where `UNKNOWN` behaves as `CLEAR` is a defect.
3. **Claim guarantees.** Every limitation in the README is registered in
   `tests/lint_limitations.py`. A claim in the documentation that the tree does
   not implement is a defect, and historically the most likely one.

Also in scope: any input that causes a parser to raise, and any path that writes
a raw per-subject record outside `data/raw/`.

## Reporting

Open a GitHub security advisory on this repository. If the finding concerns a
guarantee above, please include the input that demonstrates it; a probe is worth
more than a reading.

Expect an acknowledgement within seven days. This is a single-maintainer
repository, so a fix is not promised on a schedule, but the defect will be
recorded in `docs/METHODOLOGY.md` with its class either way.

## Out of scope

The correctness of upstream feeds. This tool reports what sources say, labelled
as `reported`, and cannot verify their claims.
