# Changelog

All notable changes to this project. Entries state the defect, not the change.

## 0.3.2.0 - 2026-08-08

Consistency audit. The documentation had drifted from the tree in six places,
each found by re-running the gate and re-reading every claim against it.

- F31: `STATUS.json` pinned coverage at 98.59 while the gate measured 95.33; the
  block's test count had been updated twice while coverage rode along from
  sprint 2, under a note claiming the whole block comes from `make verify`. A
  partially updated measurement block is worse than an unmeasured one.
- F32: the README described the release before last: sprints "0 to 3", "no live
  feed", 89 tests, 8 attacks, MT1 to MT10, a twice-stale harness owner, and a
  layout missing three modules. Every stale sentence sat outside the five claims
  `lint_limitations` registers, which is the gap, not the excuse.
- F33: MT9 cited `docs/DECISIONS.md` D-010, which had never been written.
  D-010 now records the correlated Ukrainian dependency and its revocability,
  with reopen conditions; T13 closes with it. The upstream *direction* (channel
  feeds APIs, or siblings of one chain) is downgraded to a labelled inference in
  METHODOLOGY: correlation is load-bearing and holds either way, relative
  latency does not and gets measured in sprint 5.
- F34: `docs/MVP.md` gated latency measurement on the API token three sections
  above a schedule saying sprint 4 ships ingestion without waiting on anyone.
  Amended and recorded as a scope change.
- F35: F29 claimed the real-content measurement was pinned as assertions; two of
  three layers were, the means layer (4 of 20) stayed prose. Pinned.
- F36: `transport.py` hardcoded `mavo/0.3.0.0` in the User-Agent at 0.3.1.0. The
  constant now derives from `__version__`.
- `mavo collect --save-raw DIR` writes the fetched page verbatim before parsing,
  with its own failure exit code (4). Added now rather than in sprint 5 because
  the corpus (T19) can only be collected forward in time: the page is a
  twenty-message window, and content not saved this week does not exist next
  week. New dependency count: zero.
- T19 (corpus, with a window) and T20 (OpenSky, recategorised to self-service)
  added; T4 narrowed to future adapters after sprint 4 delivered its Telegram
  half.

## 0.3.1.0 - 2026-08-08

The pattern table measured against real channel content. It scored zero.

- F23: the area table matched 0 of 20 real messages. The channel names raions and
  hromadas, never oblasts, and the table was keyed on oblast stems, so it could
  not match by construction. The state layer matched 15 of 20 and was correct;
  the means layer matched 4 of 20.
- F24: a message names an area and nothing else, so mapping raions to oblasts
  needs a gazetteer this repository does not have. The border-oblast rules the
  whole thesis rests on currently have no input.
- F25: means of attack is a separate message class with its own lifetime, not an
  attribute of an alert. `ThreatEvent` models it wrongly.
- F26: a fourth state exists. A yellow all-clear that says the alert continues
  must not resolve to CLEAR.
- F27: the page is a window of roughly twenty messages, so a poll interval that
  is comfortable at rest can skip messages during a mass alert, leaving no trace.
- The measurement is pinned as assertions rather than described in prose. Three
  tests assert the zero hit rate, so F23 cannot be closed quietly: fixing it
  requires flipping a pin.
- Real message content saved verbatim as `tests/fixtures/real_messages.py`.

Nothing was tuned in response. The classifier still scores zero; the redesign is
sprint 5, and shipping a table hastily patched against twenty messages would
repeat the mistake at a smaller scale.

## 0.3.0.0 - 2026-08-08

Sprint 4. Live ingestion, with the access blocker off the critical path.

- `mavo/transport.py` is the only file in the package that reaches the network.
  A test asserts nothing else imports `urllib`, so "what can this thing talk to"
  has one answer in one file.
- `TelegramChannelSource` reads the public channel that is the shared upstream of
  both Ukrainian APIs. It buys no independence, and MT9 says so: a wrong or
  silent upstream is wrong or silent here too. What it buys is data today
  instead of data when someone answers an email.
- F17: a parser that raises converts a hostile string into an outage during the
  only window that matters. Content failures are absorbed and reported;
  `SourceUnavailable` is raised for reachability alone.
- F18: a stale pattern table would make a live channel look quiet. Unmatched
  messages are counted and printed, never dropped, so drift between the table
  and the channel appears in the output rather than as an absence of events.
- MT11 added: an unreachable source is not a quiet one, and `mavo collect` exits
  3 rather than 0 so a wrapper cannot confuse them.
- Harness gains A9 and A10. MT7 is no longer fixture-only.
- Stated limit, not implied away: parsing is tested against an injected
  transport. That a live channel emits the shapes the pattern table expects is
  not tested and cannot be from a test suite.

## 0.2.1.0 - 2026-08-06

Documentation, banner, and alignment with the portfolio standard set by `pirx`.

- Versioning moves to four segments, matching `pirx`. The bump is its own commit.
  Earlier entries keep their three-segment tags; renaming a shipped tag would
  break the only thing a tag is for.
- `docs/MANUAL.md`: operator's manual, written from the first sprint rather than
  at the end. Every section declares BUILT, PARTIAL, NOT BUILT or NARRATIVE, and
  `tools/manual_audit.py` fails the gate when a CLI subcommand has no section.
- `STATUS.json` pins the version and the shipped-sprint set; `tools/docs_audit.py`
  fails when a document's declared version drifts past it.
- Refusals are a type. `mavo/errors.py` carries the taxonomy and there is no
  warning type in this codebase: a condition either refuses or it does not exist.
- `tests/harness/`: scripted attacks, one per threat-model row, asserting the
  correct typed refusal rather than merely an exception.
- Animated banner in `docs/assets/`.

## 0.2.0.0 - 2026-08-06

Sprint 3. Regime split and the shared attention budget.

- F6: a recall figure averaged a rule that was perfect at one job with the same
  rule being blind to another. Sprint 2 reported 0.47 for the missile conjunction
  and called it mediocre; scored per regime it is 7 of 7 on missile nights and 0
  of 8 on drone nights. Present since the rule was written. Found by a probe that
  broke the figure down by scenario before any code was changed.
- F7: two rules each cleared at the full alarm budget produce twice the budget.
  The budget belongs to the recipient, not to the rule, so `gate` now takes an
  allocated share and `DecisionPolicy` refuses to allocate more than it holds.
- F8: an unserved crossing kind excluded from the recall denominator without
  being reported makes a partial policy read as complete. Same defect class as
  unknown resolving to clear, in a different place. `PolicyRun` now counts and
  prints the coverage gap, and a test asserts it appears in the summary.
- F5: the per-regime output printed the rule's own verdict, computed against the
  default budget, beside the regime verdict computed against its allocated share.
  Two contradictory verdicts on one rule. Split into `metrics_line` and
  `summary`.
- Allocation by measured demand refuses rather than trimming. Silently shrinking
  a share to make the sum fit produces a policy that passes its own gate while
  overrunning the recipient, which is worse than refusing to build it.
- Finding, recorded rather than tuned away: the two-regime policy recovers recall
  1.00 but consumes 1.96 of a 2.00 weekly budget. At a 25% headroom requirement
  it needs 2.46 and does not fit. The missile-only policy is comfortable and
  leaves 8 drone crossings served by no regime.
- Not fixed in this sprint: R2 remains inert. The missile conjunction's numbers
  are still indistinguishable from R3's, so the westward-escalation conjunct
  still carries no information. T3 stays open.

## 0.1.0 - 2026-08-05

Sprints 0, 1 and 2. First tag.

### Sprint 0, repository and gate

- `make verify` is the only gate and CI calls it rather than restating its steps.
  A workflow that lists checks individually drifts the moment a check is added to
  the Makefile.
- An empty test suite fails the gate rather than passing it. pytest treats
  "nothing collected" as success and an unset coverage floor as satisfied, so a
  fresh repository goes green with no tests. Same failure class as
  unknown-resolves-safe: absence read as success.
- Data tiers and `.gitignore` written in the first commit, because retrofitting
  them means rewriting history.

### Sprint 1, adapter boundary and store

- `AlertState` is a tri-state and `UNKNOWN` never resolves to `CLEAR`. Written as
  `is_clear()` rather than `state != ACTIVE` at each call site, because the
  negation is the defect: a feed that goes silent has not reported an all-clear.
- Store writes are idempotent by content hash, which excludes `ts_ingest`.
  Without it, re-polling an unchanged transition every 30 seconds multiplies rows
  until the replay no longer reconstructs the past.
- `Provenance.weakest([])` returns SPECULATION, not MEASURED. An empty input
  resolving to the strongest label is the flattering-default failure.

### Sprint 2, base-rate gate

- `baserate.py` is a top-level module rather than a helper inside the decision
  layer, and `tests/lint_domain.py` fails if it moves.
- F1: the synthetic history classified campaign nights as drone-only, so the
  missile rule scored precision 1.000 by construction. Hardened so campaign
  nights carry missile classification a third of the time; measured precision
  moved to 0.054, a twenty-fold overstatement. Present since the generator was
  written, found by running the gate rather than reading the code.
- F2: `tests/lint_limitations.py` failed on its first run against `baserate.py`,
  whose docstring named the excluded variable while explaining the exclusion. The
  term now lives only in `docs/DECISIONS.md` (D-002), which is its single home.
- F3: a regression test written from the defect description rather than the
  mechanism passed against the reverted generator, because two other scenarios
  already satisfied it. A regression test that is not verified red documents
  nothing and implies coverage that does not exist. Rescoped and re-probed.
- F4: the hygiene guard fired on `ENGINEERING.md`, which quotes the developer-path
  pattern in the course of forbidding it. Third use-versus-mention collision in
  one sprint, so the exemption is a named `PATTERN_DEFINING_DOCS` constant rather
  than a second ad-hoc skip.
- Coverage floor set at 95, three points below the measured 98.3. A floor, not a
  target: a target invites tests written for the number.
- Finding, recorded rather than tuned away: all four candidate rules fail the
  gate on the adversarial history. R1 and R2 fail on alarm rate, R3 and the
  conjunction fail on recall. A single rule cannot serve both the missile and the
  drone regime, so the regime split is a requirement rather than a refinement.
