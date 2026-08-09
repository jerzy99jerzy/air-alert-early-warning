# METHODOLOGY

## What may be claimed

| Claim | Status |
| --- | --- |
| Every observed violation of Polish airspace coincided with a massed campaign against western Ukraine | measured, small sample |
| Campaigns cover roughly 57% of days in the period | measured |
| Lunar illumination is unrelated to attack timing | measured null, Rayleigh R = 0.013, p = 0.95 over 738 nights and 87,093 munitions |
| Transit times of six and thirty-three minutes | inference, arithmetic on stated speeds and distances |
| Any number printed by `mavo gate` or `mavo policy` | property of the generator, not of the world |
| Transit-time regimes are two, not a continuum | inference, from a factor of roughly five in transit speed |
| The drone regime is undecidable from alert state alone | speculation. True of this generator by construction, since its drone crossing nights are drawn from the same shape as its campaign nights. Whether it holds in reality is exactly what real data must answer, and assuming it now would be the mistake this project exists to avoid |
| The Telegram channel is the upstream of both Ukrainian APIs | inference, from public statements. What is load-bearing (MT9, D-010) is only that all three surfaces are correlated, which holds under any internal topology. The relative latency of channel versus APIs is a distinct claim, currently unknown, measured in sprint 5 rather than assumed |
| A rule's real-world precision | unknown. No real-data backtest has been run |

Nothing produced against the synthetic history is evidence about reality. It
validates the machinery, not the hypothesis. That sentence is printed by the CLI
so it travels with the output.

## Defect log

Each entry: what it was, why it survived, what class it belongs to.

### F1, sprint 2. The fixture flattered the rule it was meant to test

The generator classified campaign nights as drone-only, so the missile rule saw
missile-classified alerts exclusively on nights that ended in a crossing and
scored precision 1.000 by construction. Hardened so campaign nights carry missile
classification a third of the time; measured precision moved to 0.054.

Why it survived: the generator was read and looked adversarial, because it was
adversarial on four dimensions and not on the one the rule used. Found by running
the gate and disbelieving a perfect score.

Class: an adversarial fixture that is not adversarial on the axis under test is a
clean fixture wearing a costume. Every new rule now asks which fixture dimension
it consumes, and whether that dimension varies on negative nights.

### F2, sprint 2. A lint failed on the document explaining its own exclusion

`tests/lint_limitations.py` forbids the excluded variable's terms anywhere in the
package. On first run it failed against `baserate.py`, whose docstring named the
variable while explaining why it is absent.

Why it survived: it did not survive. The lint caught it on its first execution,
which is the intended behaviour of a claim written as a check.

Class: a term-level guard cannot distinguish use from mention. Resolved by moving
the explanation to `docs/DECISIONS.md` as its single home rather than by adding
an exemption, because an exemption mechanism is the thing that eventually gets
used to smuggle the variable back in.

### F3, sprint 2. A regression test passed against the bug it documented

`test_missile_classification_appears_on_nights_without_a_crossing` asked only for
a missile-classified night without a crossing. The poisoned-feed and
degraded-feed scenarios already satisfied it, so it stayed green against the
reverted generator and documented nothing.

Why it survived: it was written from the description of the defect rather than
from the mechanism, and it looked correct.

Class: a regression test that is not verified red against the previous state
implies coverage that does not exist, which is worse than no test. Rescoped to
campaign nights specifically and re-probed against a scratch copy.

### F4, sprint 2. The hygiene guard fired on the document that defines it

`tests/lint_hygiene.py` forbids absolute developer paths in tracked files. It
failed against `ENGINEERING.md`, which quotes the pattern as part of stating the
rule.

Why it survived: it did not. Like F2, the guard caught it on first execution.

Class: **use versus mention**, third instance in one sprint after F2 and F3. A
term-level or pattern-level guard cannot distinguish a variable being used from a
document explaining why it is excluded. Generalised rather than patched twice:
the exemption is a named constant `PATTERN_DEFINING_DOCS` listing the documents
that define a guarded pattern, so the next collision is a one-line addition with
a visible reason instead of a fourth ad-hoc skip.

The rule extracted: **a guard that greps must name the documents that define what
it greps for.** Any new lint in this repository states its exemption set
explicitly at the top of the file.

### F5, sprint 3. Two contradictory verdicts printed on one rule

The per-regime output printed `RuleRun.summary()`, which embeds a verdict gated
against the default budget, immediately above the verdict gated against the
rule's allocated share. The same rule read PASS and FAIL two lines apart.

Why it survived: the summary method predated the idea that a budget could be
allocated, and reusing it looked like reuse rather than a contradiction.

Class: a formatted string that embeds a decision cannot be reused in a context
where the decision is made differently. Split into `metrics_line`, which reports
measurements only, and `summary`, which adds the verdict.

### F6, sprint 3. An average across two populations read as one weak rule

Sprint 2 measured recall 0.47 for the missile conjunction and recorded a
mediocre rule. Broken down by scenario it is 7 of 7 on missile nights and 0 of 8
on drone nights.

Why it survived: 0.47 is a plausible number for a mediocre rule, so it invited no
question. Nothing in the output suggested the positive class was not homogeneous.

Class: **a metric computed over a heterogeneous population describes none of its
parts.** Any recall, precision or lead time in this repository is now reported
per regime, and a combined figure is only computed for a policy that declares
which regimes it serves.

### F7, sprint 3. The budget was treated as a property of the rule

Two rules, each gated against two alarms per week, produce four. The threshold
was a module constant, so nothing prevented allocating it repeatedly.

Why it survived: with one rule the distinction between a rule's budget and the
recipient's budget is invisible.

Class: a limit that protects a shared resource must be held by the resource, not
by each consumer. `gate` takes an allocated share, `DecisionPolicy` validates
that shares sum within the total, and the allocator raises rather than trimming.

### F8, sprint 3. A coverage gap folded into the denominator

Scoring a partial policy over all crossings punished it for a job it never
claimed. Scoping the denominator to served regimes fixed that and immediately
created the opposite defect: a one-regime policy reporting recall 1.00 and
reading as complete.

Why it survived: for about ten minutes, between writing the scoping fix and
running the test that expected the missile-only policy to pass.

Class: **the same defect as unknown resolving to clear**, one layer up. Absence
of coverage is not evidence of coverage. Unserved crossings are now counted by
kind, exposed as `has_coverage_gap`, and printed in the summary, with a test
asserting the line is present.

### F23, sprint 4 measurement. The area table matched nothing at all

Twenty real messages from the channel, classified by the shipped table: 0 hits.
The state layer matched 15 of 20 and the means layer 4 of 20; the area layer
matched **0 of 20**.

Cause: the channel names **raions and hromadas**, never oblasts. "Повітряна
тривога в Павлоградський район". The table keyed on oblast stems, so it could
not match by construction.

Why it survived: the table was written from reasoning about how the channel
plausibly words its messages, and the reasoning was coherent and wrong. Nothing
in the code could have caught it; only real content could.

Class: **a plausible model of an external system is not a measurement of it.**
The design already assumed the table was wrong in detail and made the failure
visible through the unparsed counter. It did not assume the failure would be
total.

### F24, sprint 4 measurement. The geographic model has a missing artifact

A message says "Павлоградський район" and nothing else. Nothing in the text
identifies the oblast. Mapping raions and hromadas to oblasts needs a gazetteer
that does not exist in this repository, and without it the whole geo layer,
including the border-oblast rules that the entire thesis rests on, has no input.

Class: a missing reference dataset masquerading as a parsing problem.

### F25, sprint 4 measurement. Means of attack is a separate message class

`ThreatEvent` carries `kind` as an attribute of an alert. The channel emits it as
its own message, tied to a hromada and not to an alert: "Загроза застосування
керованих авіаційних бомб (КАБів)", "Атака дронів-камікадзе типу Молнія",
"Відбій загрози ударних БпЛА".

This is architectural, not cosmetic. The regime split depends on knowing the
means, and the means arrives on a different message with a different lifetime
than the alert it qualifies.

### F26, sprint 4 measurement. There is a fourth state

"🟡 Відбій тривоги в Куп'янський район. Зверніть увагу, тривога ще триває у:
- Куп'янський район." An all-clear that says the alert continues. Classifying it
as CLEAR would be actively wrong, and the tri-state has no member for it.

Class: the same family as UNKNOWN resolving to CLEAR, and found the same way:
by looking at what the source actually says rather than at what the model
expects it to say.

**Closed in 0.4.0.0.** `AlertState.PARTIAL_CLEAR`, kept distinct from UNKNOWN
because silence and contradiction are different evidence.

### F27, sprint 4 measurement. The page is a window, not a stream

The channel page serves roughly the last twenty messages. During a mass alert the
channel emits far more than twenty in a short period, so a poll interval that is
comfortable at rest can silently skip messages exactly when the messages matter.
Not detected, and not currently detectable, because a skipped message leaves no
trace.

**Closed in 0.4.0.0.** Post ids compared across polls, with the unmeasurable case
reported as unknown rather than zero. MT12, harness A11.

### F31, 0.3.2.0 audit. A measured pin went stale field by field

`STATUS.json` carried `coverage_percent: 98.59` at 0.3.1.0 while `make verify`
measured 95.33 on Python 3.12. `tests_passing` in the same block had been
updated twice (110, then 114) while coverage rode along from sprint 2, under a
note claiming every number in the block is produced by the gate.

Why it survived: the block is updated by hand, one field at a time, and nothing
audits it. `tools/docs_audit.py` checks version pins, sprint files, threat rows
and the harness count, and stops there. The stale number was also the flattering
one: 98.59 with a 3.6-point margin reads better than 95.33 with 0.33.

Class: **a partially updated measurement block is worse than an unmeasured one**,
because the fresh fields lend the stale ones their credibility. Candidate fix, a
decision rather than this release: either `docs_audit` regenerates the measured
block from a gate run, or the block is dropped and the review file becomes its
single home.

### F32, 0.3.2.0 audit. The README described the release before last

Four claims in one document: "Sprints 0 to 3 complete. No live feed is wired"
(sprint 4 shipped a live adapter), "89 tests passing, of which 8 are harness
attacks. Coverage 98.59%" (117, 10, 96.34), "MT1 to MT10" (eleven rows), and the
harness-mutation owner still "0.3.0.0" after being re-owned twice. The layout
section omitted `transport.py`, `errors.py` and `sources/telegram.py` entirely.

Why it survived: every one of these sentences sits outside the five claims
registered in `tests/lint_limitations.py`. The lint verifies exactly what it was
told to verify, and the "Measured claims" section, which exists precisely to
carry numbers, is not on its list.

Class: the ANANKE README failure, in the repository that quotes it as the
founding defect. Prose about the tree that is not registered as a check drifts,
reliably, within two releases.

### F33, 0.3.2.0 audit. A threat-model row cited a decision that was never written

MT9 said "recorded in `docs/DECISIONS.md` D-010". DECISIONS.md ended at D-009.
T13, whose acceptance is that entry, sat at `ready` while the threat model
claimed its output already existed.

Why it survived: the reference was written when the decision was intended, and
intending to write a document feels like having written it. No audit resolves
cross-document references.

Class: documentation claiming a record that does not exist, the doc-to-doc
variant of describing a protection the tree does not implement. D-010 now
exists; T13 is closed by it.

### F34, 0.3.2.0 audit. One document contradicted itself across two sections

`docs/MVP.md` Audience A gated "Live feed latency measurement" on the API token
while the schedule table three sections down said sprint 4 ships "live ingestion
without waiting on anyone". Both were left standing in the same file for two
releases.

Class: an amendment applied where the change happened and not where the claim
lived. Same family as F32, narrower blast radius.

### F35, 0.3.2.0 audit. A stated rule applied to two of three cases

F29 pinned the 2026-08-08 measurement as assertions "rather than prose": the
state layer (15) and the area layer (0) got tests, the means layer (4) stayed a
table row. Two layers could not drift quietly and one could.

Class: partial application of a rule the release notes claimed in full. Pinned
now, same wording as the others.

### F36, 0.3.2.0 audit. A version string lived outside its single source of truth

`transport.py` hardcoded `USER_AGENT = "mavo/0.3.0.0"` and shipped that way at
0.3.1.0. The constant now derives from `__version__`.

Class: duplicated state drifts on the first update it is not part of. The same
reason `pyproject.toml` is the single dependency source of truth.

### F37, 0.3.2.1. A manifest proves completeness, not currency

The archive unpacked onto the workstation was the build before last: no
`data/aggregates/.gitkeep`, no CHANGELOG paragraph about the untagged releases.
`shasum -c` passed, because an archive is internally consistent with its own
manifest whichever build produced it. The initial commit was then made with a
message asserting a paragraph the tree did not contain.

Why it survived: the transfer rule in ENGINEERING.md answers "did every file
arrive intact" and was read as answering "is this the current build". Two
different questions with one check between them.

Class: an integrity check mistaken for a freshness check. The same shape as
absence read as success, one layer out from the code.

### F38, sprint 5. An attack that could not fail

A4 asserted that a rule with perfect recall still fails the gate on alarm rate.
Its contingency table also failed the association condition, so `verdict.passes`
stayed False with the alarm budget disabled, and its second assertion looked for
the substring "alarm rate", which the *passing* reason ("alarm rate 6.08/week
within budget") also contains. Two independent reasons the attack could not
distinguish a working control from a removed one.

Why it survived: it was green, and a green attack looks like a passing control.
Nothing in a passing test distinguishes "the control held" from "the assertion
cannot fail". Found by disabling the control and watching the test stay green.

Class: **an assertion satisfied by the failure it is meant to detect.** Every
harness assertion now names the specific failure rather than a substring shared
by both outcomes, and the table is constructed so exactly one condition fails.

### F39, sprint 5. An attack that never reached the code it tested

A9 fed six hostile bodies to the Telegram adapter and asserted nothing raised.
The bodies used `<div class='...'>` with single quotes; the message regex is
written against the double quotes the page actually serves. Nothing matched, so
`messages=0`, the parser was never entered, and `parsed <= messages` held as
`0 <= 0`. The attack passed by not arriving.

Why it survived: present since 0.3.0.0, where the review recorded A9 as closing
MT7 for the live adapter. The hostile fixtures were written by hand next to a
regex neither was checked against.

Class: **a test that exercises no code passes for the wrong reason.** A9 now
counts the messages that reached the parser and fails if the count is zero, so
the attack asserts its own arrival before asserting anything about behaviour.

### F40, sprint 5. A new attack with the same defect, caught the same day

A11 was written in this sprint to guard MT12. Its unknown-versus-zero assertion
used a page with no post ids, which `_window` answers by returning early, before
the code that decides whether an unmeasured gap is unknown or zero. The
governing case is a first poll with ids, which the attack did not cover.

Why it survived: about two hours, between writing the attack and running the
mutation tool for the first time.

Class: same as F38. Worth its own entry because it is evidence about the tool
rather than about the attack: the mutation run caught a defect in an attack
written by the same person on the same afternoon, which is the case a review by
reading is least likely to catch.

### F41, sprint 5. CI restated the gate it claimed not to restate

`ci.yml` ran `hygiene`, `docs-audit` and `manual-audit` as separate jobs
duplicating steps `make verify` already runs, while README.md and ENGINEERING.md
both state that CI calls the gate rather than restating its steps.

Why it survived: each job was added in the same commit as the check it mirrors,
which felt like belt and braces rather than duplication. The failure mode is the
one ENGINEERING section 2 names: two lists of checks drift, and the weaker one is
what actually runs.

Class: a claim about the repository contradicted by a file in it. The same class
as F32, one directory over.

### F42, 0.4.0.0 audit. A threat row cited a test that has never existed

MT8 named a test in `test_store.py` called `repeated_polling_does_not_grow_the_log`
as the measurement of idempotence. No test of that name has ever been in this
repository; the real one is `repoll_with_new_ingest_time_does_not_duplicate`.
The control exists and is tested, so nothing was unguarded, but the table's claim
about how it was guarded was false for three releases.

Why it survived: nothing resolved documentation citations. `docs_audit` checked
row counts, numbering gaps and catalogue-to-test correspondence by number, and a
row citing a plausible-sounding test name passed all three.

Class: same as F33, one level of indirection down. F33 was a document citing a
document that did not exist; this is a document citing a test that does not
exist, and the consequence is worse, because a named test reads as a measurement.
`docs_audit.check_cited_tests_exist` now resolves every module-and-test citation
in `docs/`, the README and the catalogue, and was verified red against this
defect before the citation was corrected. It also refuses a dead citation written
inside a defect log, which is why this entry names the old test without citing it
in the usual form: the check has no exemption list, and adding one for prose
about defects is how exemption lists start.

### F43, 0.4.0.0 audit. The architecture diagram omitted the only live source

`docs/ARCHITECTURE.md` drew four sources, none of them the Telegram adapter that
sprint 4 shipped and that is the only wired live feed. It also carried no
transport node, no `policy.py` and no `evaluate.py`, labelled the alarm tier
"sprint 4" after sprint 4 shipped without it, and labelled the Polish adapter
"sprint 6" after the schedule moved. The block index, whose stated purpose is
that a rename leaves a visibly stale row, had gained no row since sprint 2.

Why it survived: `lint_mermaid` validates that diagrams parse, not that they
describe the tree. A diagram that is syntactically clean and semantically two
releases old passes every check in the gate.

Class: the ANANKE class again, in the document whose entire job is to say what
talks to what. Recorded rather than quietly redrawn: this is the third document
in three releases found describing an earlier version of the tree, which is
evidence about the process and not about any one file.

## Verification probes run in sprint 5

| Claim | Probe | Result |
| --- | --- | --- |
| The sprint 5 regression tests are red against 0.3.2.1 | Scratch copy of the previous tag with a shim reproducing the old state semantics, so the red is behavioural rather than an import error | 7 of 9 red. Two are guards rather than regressions: they assert an ordinary all-clear is still CLEAR and an unrecognised message is still None, and they pass both before and after by design |
| The harness measures its controls | Ten controls disabled one at a time in a scratch tree, guarding attack run against each | 7 of 10 killed on the first run. F38, F39 and F40 found. 10 of 10 after they were fixed |
| A7 has no mutation | Attempted: the fixture source generates rather than parses, so any mutation that makes it raise is an injected fault rather than a removed control | Recorded as unverified rather than given a flattering mutation. 1 of 11 attacks carries no mutation |

## Measurement of the pattern table, 2026-08-08

| Layer | Matched | Note |
| --- | --- | --- |
| State | 15 / 20 | "Повітряна тривога в" and "Відбій тривоги в" confirmed correct. The 5 misses are threat-type messages, a different class entirely |
| Means | 4 / 20 | "каб" and "бпла" fire. "дрон" is absent from the table; "шахед" and "ракет" did not appear in this window at all |
| Area | 0 / 20 | Total failure. See F23 |
| **Whole classifier** | **0 / 20** | Area is a required conjunct, so a total area failure is a total classifier failure |

Not measured: the HTML message-splitting regex. The page was retrieved through a
text-extracting fetcher, so `<time datetime=...>` was not visible and the regex
over raw HTML remains unverified. That is a separate claim and it is still open.

Also not measured, and worth stating: no western oblast appeared in this window.
Every message concerned Dnipropetrovsk, Kharkiv, Sumy or Zaporizhzhia. That is a
property of the twenty minutes sampled, not of the feed.

## Sprint 3 finding

The regime split works, and the cost is the recipient's attention.

| Configuration | Recall, served scope | Alarms/week | Headroom | Coverage gap |
| --- | --- | --- | --- | --- |
| Missile + drone, even split | 1.00 | 1.96 of 2.00 | 2% | none; drone regime overruns its 1.00 share at 1.34 |
| Missile + drone, demand + 25% headroom | not built | 2.46 requested | refused | allocator declines |
| Missile only | 1.00 | 0.63 of 2.00 | 69% | 8 drone crossings unserved |

Three consequences.

The even split is arbitrary and wrong. The drone regime needs roughly twice the
missile regime, so an even allocation fails a regime the total could afford.
Allocation by measured demand is the correct shape, and it is implemented.

The two-regime policy is not robust. It passes with a 2% margin, which any
busier month erases. Passing at zero headroom is not the same as passing.

The drone regime is not solvable from this data. Nothing in oblast-level alert
state separates a drone night that ends in a crossing from one that does not, so
the drone rule buys recall by firing often. This moves the ADS-B channel from
optional enrichment to a prerequisite for any drone-tier alarm, and it is the
strongest argument in the project for a second signal type rather than a second
source of the same signal.

## Verification probes run in sprint 2

Claims about this repository, each verified by running something rather than by
reading it.

| Claim | Probe | Result |
| --- | --- | --- |
| An empty repository fails the gate | Copied Makefile, pyproject and lints into a bare directory with no tests, ran `make verify` | Red. Coverage step exits non-zero at 0.00% against a floor of 95 |
| The sprint 1 regression test is red against the previous state | Scratch copy with `is_clear` rewritten as `state != ACTIVE` | Red, plus `lint-limitations` independently caught it |
| The sprint 2 regression tests are red against the previous state | Scratch copy with the fixture hardening reverted | One red, one green. The green one was mis-scoped and was rewritten. See F3 |
| The README quickstart works from zero | Fresh copy, `pip install -e ".[dev]"`, both quickstart commands run verbatim | Both succeed. No step missing from the README |
| The Fisher implementation is correct | Independent exact-fraction computation of a 2x2 with margins 3/4 by 4/3 | 4/35, matching. The test's original expected value of 1/21 was wrong and was corrected |

## Sprint 2 finding

All four candidate rules fail the gate on the adversarial history.

| Rule | Recall | Alarms/week | Precision | Verdict |
| --- | --- | --- | --- | --- |
| R1 border active | 1.00 | 2.52 | 0.029 | fails alarm rate |
| R2 westward escalation | 1.00 | 4.27 | 0.017 | fails alarm rate |
| R3 border missile | 0.47 | 0.62 | 0.054 | fails recall |
| Conjunction | 0.47 | 0.62 | 0.054 | fails recall |

Two consequences, both recorded rather than tuned away.

The regime split is a requirement. One rule cannot hold the alarm rate and keep
drone nights, so sprint 3 splits the decision into a missile path and a drone
path with separate thresholds and separate budgets.

The conjunction currently adds nothing. Its numbers are identical to R3, meaning
R2 fires on every night R3 fires and the third conjunct is inert as defined.
Either R2 is redefined to carry information R3 lacks, or it is dropped and the
README stops describing a three-part conjunction.
