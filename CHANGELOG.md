# Changelog

All notable changes to this project. Entries state the defect, not the change.

**Releases 0.1.0 to 0.3.1.0 have no tags, and that is a debt rather than an
oversight.** They predate this repository being under version control, so the
first tagged release is 0.3.2.0. The alternative was reconstructing commits to
hang the earlier tags on, which would make the history lie about when the code
existed; a stated debt is cheaper and true. Their artefacts exist only as
hand-assembled archives with a `MANIFEST.sha256`.

**0.5.0.0 and 0.5.1.0 also carry no tags.** They were cut and verified but never
pushed: the corpus retrieval work moved fast enough that three releases happened
between one push and the next, and reconstructing commits for tree states that
were never published would be inventing history to satisfy a rule the rule does
not ask for. Their entries stay below because the defects they record are real.
The first tag after 0.4.0.0 is v0.5.2.0.

## 0.5.5.0 - 2026-08-09

Documentation raised to the level a contributor joining cold actually needs, and
two new checks so the additions cannot rot.

- `docs/MECHANISMS.md` rewritten from eight sections to twenty-five, one per
  mechanism, each with its code location, its constants, **the alternative that
  was rejected and why**, the failure it prevents, and the harness attack that
  guards it. The rejected alternative is the part that was missing: a document
  saying what the code does is a worse document than one saying what it does not
  do and why not.
- `docs/ARCHITECTURE.md` gains a module reference with the public surface and
  invariant of every module, a section naming **the four boundaries** and what
  each one buys, extension points with what landing each one requires, and the
  repository layout beyond the package.
- `docs/METHODOLOGY.md` gains a generated defect index and a section on **the
  four recurring defect classes**. Thirty-two entries reduce to four shapes, and
  a contributor who learns the shapes will recognise the next one faster than
  the last one was recognised.
- `docs/THREAT-MODEL.md`, `docs/MVP.md` and `docs/DECISIONS.md` gain header
  blocks in the same convention as the rest.
- README gains badges, a statistics table, and a reading map by intent. Only the
  CI badge is live; **the static ones are claims**, so `docs_audit` now fails the
  gate when a badge value disagrees with `STATUS.json`. Verified red by inflating
  the coverage badge to 99.90%.
- `docs_audit` also resolves every in-document anchor link. Six documents now
  carry a contents index, which is six new surfaces for the drift class that has
  produced four defects here already. Verified red by renaming a section.
- Statistics pinned in `STATUS.json`: 2,184 lines of package against 4,890 of
  documentation, a ratio that is deliberate.

## 0.5.4.0 - 2026-08-09

The corpus exists, and the boundary is frozen before anything reads it.

- Corpus retrieved: ids 260841 to 321520, 60,680 posts across 3,034 pages,
  2026-04-13 to 2026-08-09, contiguous, 313 MB.
- D-012a computes and freezes the design/holdout boundary at id 309381:
  48,540 posts for design, 12,140 for holdout, 20.0%. Computed
  from post ids with no message content read, which is the only thing that makes
  it a holdout rather than a test set chosen with hindsight.
- **Campaign nights are invisible in a daily count and visible hourly.** Daily
  volume is flat: median 590, max 764, a ratio of 1.29. Hourly volume runs a
  median of 25 against a maximum of 112. Routine alert and all-clear pairs from
  the whole country dominate the daily figure. The redesign must label candidate
  campaign windows by hour; the plan of finding them by day would have found
  nothing and concluded there was nothing to find.
- The hourly tail thins smoothly rather than stopping at a round number, so the
  channel has no throughput ceiling. This matters before anyone computes a
  vector from an activation sequence, because a capped channel would reorder
  and batch under load.
- Daily volume drifts about 20% upward from April to August with no step change,
  so the channel did not alter its format inside the corpus and the older window
  is usable for design.
- F49: the sixfold volume change reported while reading the backfill output was a
  division error, corrected to 25%. Recorded because the wrong number was the
  interesting one, and interesting is how a number reaches a document.

## 0.5.3.0 - 2026-08-09

Three defects in `backfill`, all found by running it against the real channel
for twenty-five minutes rather than by reading it. None of them threatened the
corpus; all three were in what the tool tells the operator.

- F46: interruption was not one of the five stop conditions, so Ctrl-C produced a
  stack trace and a run that had retrieved 1150 pages did not say so. It is now
  the sixth, named in the report like the others. Every stop condition in the
  original list was one the channel produces; the operator was not modelled as a
  source of endings at all.
- F47: two runs could share one output directory silently. The corpus survives it
  because snapshots are named by id range, but the request rate doubles against a
  service whose tolerance is measured only over a burst of twenty. An advisory
  lock carrying the holder's pid now refuses with exit code 6, and takes over
  from a dead holder rather than requiring a cleanup step nobody remembers.
- F48: a 2800-page run printed nothing for twenty-five minutes, so working and
  hung looked the same. Progress goes to stderr every 25 pages; stdout still
  carries only the report, so a redirect yields a clean artefact. `--quiet`
  suppresses it.

## 0.5.2.0 - 2026-08-09

Documentation for contributors. No behaviour changed.

- `docs/FOUNDATIONS.md`: the observations and assumptions the project rests on,
  six assumptions each with its falsifier, the provenance table, and the section
  that says what would make this project stop. Includes the assumption most
  likely to be argued with, that attention is a finite resource owned by the
  recipient, recorded together with the challenge to it rather than as settled.
- `docs/DATA-FLOW.md`: the data architecture. One message from byte to verdict
  across seven stages, the corpus as a parallel pipeline that deliberately stops
  early, the three data tiers, and a closing table of every stage that can lose
  information and how that loss is made visible. Invisible loss is the defect
  class this repository exists to attack, so it gets its own table.
- `docs/ARCHITECTURE.md` restructured as the infrastructure document: components,
  the four dependency rules with what enforces each, process and deployment
  shape, and a section naming what is deliberately absent. Architecture and data
  flow were one document and answered two questions badly.
- `docs/MANUAL.md` gains the header block, contents index and glossary in the
  `pirx` convention, plus a section 9 glossary of twenty-two terms.
- `CONTRIBUTING.md` gains a reading order.

## 0.5.1.0 - 2026-08-09

- `mavo backfill --resume` continues below the lowest id already on disk and
  prints where it started. Without it an interrupted run re-walks everything it
  already holds, which on the 2900-page corpus is the entire run again. It
  refuses rather than choosing when combined with `--before`: two cursors, one
  loop, and a start point that depends on an unprinted argument is a start point
  the output cannot be read without.
- T21 closed with a stated limit. 0.5 s and 0.2 s both measured clean over 20
  requests, with `posts=400` in each, so the service was not silently truncating
  pages. **The default was not lowered.** A burst of 20 does not license a claim
  about a run 145 times longer, and a default is a claim; that is the F44 pattern
  and it is refused here on purpose.
- Channel measurements table added to `docs/METHODOLOGY.md`, including the row
  that says what remains unmeasured.

## 0.5.0.0 - 2026-08-09

Sprint 6, part one. The corpus is retrieved rather than awaited.

- F44: for two sprints this repository held that the corpus could only be
  collected forward in time, because the channel page is a twenty-message
  window. That was true of `mavo collect` and false of the channel: the web
  preview accepts a `before` parameter and pages backwards through the full
  history, 321,498 posts at exactly 20 per page as measured on 2026-08-09. The
  belief shaped T19, D-011, the sprint 5 scope decision and the advice to start
  a cron immediately. The probe that should have caught it asked for posts
  before id 1000000 against a channel whose newest was 321498, where a working
  parameter and an ignored one produce identical output.
- `mavo backfill` walks history backwards and writes each page verbatim, named
  by id range so a re-run resumes rather than duplicates. It parses nothing
  beyond post ids: the corpus exists because the pattern table is wrong, and a
  corpus filtered through that table would not be evidence.
- Contiguity is computed from what is on disk and every hole is printed with its
  id range and size, exit code 5. A corpus with holes it does not name is a
  sample that believes it is a census.
- Five stop conditions, each named in the report: page count exhausted,
  `--stop-at-id` reached, a page with no posts, a page that failed to move
  backwards, an unreachable source. A short run is never silently a short
  history.
- F45: the red-verification probe for this sprint passed against a scratch copy
  of 0.4.0.0 and should not have. The editable install resolved `mavo` to the
  working tree, so the scratch imported the new module. Ninety seconds of
  survival, recorded because the mechanism defeats the repository's standing
  regression rule for every sprint that adds a module. CONTRIBUTING.md now says
  to uninstall first.
- D-012: the design/holdout boundary is declared before any message content is
  read. The holdout is the newest 20% of posts by id. A holdout chosen after
  looking is not a holdout.
- T21 added: the 1.0 second delay is a deliberately conservative guess and is
  labelled as one. Measure the tolerated rate before the large run.

New dependency count: zero.

## 0.4.0.0 - 2026-08-09

Sprint 5. The evidence container before the evidence.

The sprint that was scheduled here was the classifier redesign. It was not run,
because the corpus it needs does not exist yet and twenty messages from twenty
minutes of one evening are a probe, not a design basis (F28, D-011). What can be
built without the corpus is the part of the source layer that decides whether
the corpus, once collected, will be trustworthy.

- F26 closed: `AlertState.PARTIAL_CLEAR`. A message announcing an all-clear
  while saying the alert continues had nowhere to go in a three-state model and
  would have resolved to CLEAR. It is deliberately not folded into UNKNOWN:
  UNKNOWN is silence, PARTIAL_CLEAR is contradiction, and a contradiction is
  evidence while silence is not.
- F27 closed: post ids are compared across polls and the skipped count is
  reported. **Unknown is printed as unknown, never as zero.** A first poll has no
  baseline and a page without ids has no observable, and in both cases claiming
  continuity would be the flattering default. MT12 and harness A11 added.
- `classify_state` split out of `classify`. The state layer was the one of three
  that was correct on real content (15 of 20) and could only be exercised through
  an area conjunct that matches nothing, so it was untestable in practice.
- F14 closed after two slips: the harness is mutation-verified. Ten controls
  disabled one at a time in a scratch tree; the guarding attack must go red.
  `tools/harness_mutation.py`, in `make verify`, measured at roughly 7 seconds.
- F38: A4 did not measure the alarm-rate gate. Its contingency table failed on
  association as well, and its assertion looked for the substring "alarm rate",
  which the *passing* reason also contains. Both halves survived the budget being
  disabled. Found by the mutation run on its first execution.
- F39: A9 did not reach the parser it claimed to test. Its six hostile bodies
  used single-quoted class attributes and the page serves double quotes, so the
  message regex matched nothing and every body was absorbed unparsed. The attack
  passed by not arriving. Present since 0.3.0.0, where it was recorded as
  closing MT7 for the Telegram adapter.
- F40: A11, written in this sprint, tested the unknown-versus-zero decision on
  the one path that returns before reaching it. The tool caught a defect in an
  attack written the same afternoon.
- F41: `ci.yml` carried `hygiene`, `docs-audit` and `manual-audit` as separate
  jobs restating steps `verify` already runs, in a repository whose README says
  CI does not restate the gate. Removed. This is the ENGINEERING section 2 drift
  in the repository that quotes it.
- The lint behind the unknown-not-clear claim now enumerates `AlertState` rather
  than naming UNKNOWN, so the fourth state was covered on the day it landed and
  a fifth would be too.

Documentation audited against the tree in the same release, since three of the
last four releases found a document describing an earlier version of it:

- F42: MT8 cited a test that has never existed under that name. The control was
  tested; the row's account of how was false for three releases. `docs_audit`
  now resolves every `file.py::test_name` cited in `docs/`, the README and the
  catalogue, and was verified red against the defect before it was fixed.
- F43: `ARCHITECTURE.md` omitted the Telegram adapter, the transport layer,
  `policy.py` and `evaluate.py`, and labelled two blocks with sprint numbers the
  schedule had moved past. `lint_mermaid` checks that a diagram parses, not that
  it is true.
- MT2 widened to the fourth state. `SECURITY.md` and `CONTRIBUTING.md` now state
  the state guarantee over the enumeration rather than over a list of names.
  `MECHANISMS.md` gained the two mechanisms this sprint shipped. The manual's
  sprint labels, operational limits and troubleshooting table were corrected.

Not done, and not a slip: the pattern table still scores 0 of 20 and its pins
still hold. The gazetteer (T15) needs a reference dataset this repository does
not have, and the means-as-message-class rework (T16) needs the corpus to answer
how a means message joins an alert by area and time window.

## 0.3.2.1 - 2026-08-08

A transfer defect, not a code change. The tree is identical to 0.3.2.0 except
for the two files 0.3.2.0 was supposed to contain.

- F37: the archive unpacked onto the workstation was the build before last. It
  lacked `data/aggregates/.gitkeep` and the CHANGELOG paragraph recording that
  releases 0.1.0 to 0.3.1.0 carry no tags. The initial commit's message then
  asserted that paragraph was in CHANGELOG.md, which it was not: a commit
  message claiming a document the tree does not contain, which is the same
  class as a changelog entry claiming a protection the code does not implement.
  Survived because the manifest check passed: an archive is internally
  consistent with its own manifest whichever build it came from, so
  `shasum -c` proves completeness and says nothing about currency.
- The manifest is regenerated here. Class fix deferred to 0.4.0.0 as a decision:
  either the manifest carries the version it was built from, or the archive
  filename is not the only place the build is identified.

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
