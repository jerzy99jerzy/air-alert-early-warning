# METHODOLOGY

What may be claimed, what was measured, and every defect this repository has
found in itself.

```
Document:  docs/METHODOLOGY.md, version 2.10
Audience:  a contributor deciding what a number is allowed to mean, and anyone
           auditing whether this repository is as careful as it says
Companion: FOUNDATIONS (the assumptions), MECHANISMS (how each control works),
           DECISIONS (what was rejected), reviews/ (per-release dispositions)
Note:      the defect log is the most useful document here for a new
           contributor. Read the classes rather than the incidents: most of the
           entries are variations on four or five recurring shapes
```

## Contents

1. [What may be claimed](#what-may-be-claimed)
2. [The recurring defect classes](#the-recurring-defect-classes)
3. [Defect index](#defect-index)
4. [Defect log](#defect-log)
5. [Corpus measurements, 2026-08-09](#corpus-measurements-2026-08-09)
6. [Channel measurements, 2026-08-09](#channel-measurements-2026-08-09)
7. [Verification probes run in sprint 5](#verification-probes-run-in-sprint-5)
8. [Measurement of the pattern table, 2026-08-08](#measurement-of-the-pattern-table-2026-08-08)
9. [Sprint 3 finding](#sprint-3-finding)
10. [Verification probes run in sprint 2](#verification-probes-run-in-sprint-2)
11. [Sprint 2 finding](#sprint-2-finding)
12. [Threat-kind coverage measurement, 2026-08-10](#threat-kind-coverage-measurement-2026-08-10)

## What may be claimed

| Claim | Status |
| --- | --- |
| Every observed violation of Polish airspace coincided with a massed campaign against western Ukraine | measured, small sample |
| Campaigns cover roughly 57% of days in the period | measured |
| 22 western-wide alert episodes in the design window coincided with zero reported Polish airspace violations | reported, absence of evidence rather than evidence of absence: Polish media searched 2026-08-09 for 29 Apr, 28 and 29 May, 20 Jun 2026. Minor incursions may go unreported (T35) |
| The only confirmed crossing in the corpus period, 30 July 2026, falls in the holdout | measured, from the frozen boundary and the reported date |
| Tag and prose name the same area in 38,520 of 38,521 comparable design-window messages (99.997%) | measured, `tools/consistency_check.py`. Internal consistency, not truth |
| 86.7% of comparable messages name one area; the tail runs to eight and stops | measured, same run |
| 5.2% of comparable messages carry a continuation list naming 4,064 areas where the alert is still running | measured, same run. The pipeline discards all of it (T37) |
| 99.34% of design-window messages carry a `#Name_unit` hashtag; 127 distinct tags; 126 resolve to a unique register code | measured, 48,540 messages, `docs/CHANNEL.md` |
| Western oblasts hold 3.5% of tag occurrences (2,456 of 69,676) | measured, same run |
| Matching register names in text reaches 6.06% as a lower bound against 99.34% for tags | measured, `tools/register_probe.py` |
| Per-night message volume does not separate nights: every design night carries more than 120 messages, at ~490/night | measured, 2427 pages, 48,540 messages, 99 nights |
| Per-hour peak volume does separate: peak >= 60 on 24.2% of nights, >= 80 on 7.1%, >= 120 on none | measured, same run |
| The channel names an oblast in 1.05% of messages (510 of 48,540) | measured, same run. F23's 0-of-20 was too small a sample to see it |
| The tested candidate covariate is unrelated to attack timing | measured null, Rayleigh R = 0.013, p = 0.95 over 738 nights and 87,093 munitions. Directional test on the full series, not a subset |
| Transit times of six and thirty-three minutes | inference, arithmetic on stated speeds and distances |
| Any number printed by `mavo gate` or `mavo policy` | property of the generator, not of the world |
| Transit-time regimes are two, not a continuum | inference, from a factor of roughly five in transit speed |
| The drone regime is undecidable from alert state alone | speculation. True of this generator by construction, since its drone crossing nights are drawn from the same shape as its campaign nights. Whether it holds in reality is exactly what real data must answer, and assuming it now would be the mistake this project exists to avoid |
| The Telegram channel is the upstream of both Ukrainian APIs | inference, from public statements. What is load-bearing (MT9, D-010) is only that all three surfaces are correlated, which holds under any internal topology. The relative latency of channel versus APIs is a distinct claim, currently unknown, measured in sprint 5 rather than assumed |
| A rule's real-world precision | unknown. No real-data backtest has been run |

Nothing produced against the synthetic history is evidence about reality. It
validates the machinery, not the hypothesis. That sentence is printed by the CLI
so it travels with the output.

## The recurring defect classes

Forty-odd entries, four shapes. A contributor who internalises these will predict
most of what this repository is fussy about, and will recognise the next one
faster than the last one was recognised.

**Class 1: a document describing a tree that has moved on.** The portfolio's
founding defect (ANANKE's README claiming a protection the code lacked) and four
of this repository's own: F32, F33, F42, F43. Every check in the gate that
touches documentation checks *shape* rather than *reference* (counts, numbering,
parseability, version pins), and prose stays uncovered. The citation resolver in
`docs_audit` is the first check that resolves a claim to the thing it names.

**Class 2: a check that cannot fail.** F38 (an assertion satisfied by the failure
it was meant to detect), F39 (a test that never reached its code), F40 (the same,
found the same day), F44 (a probe whose negative result was indistinguishable
from its positive one), F45 (a red-verification that imported what it was
verifying). The remediation is a question rather than a tool: **what would this
have printed if the thing I am testing were false?**

**Class 3: absence read as success.** F8 (a coverage gap folded into a
denominator), F26 (a contradiction resolving to all-clear), F27 (a skipped window
leaving no trace), F46 (an interrupted run reporting nothing about what it had
retrieved). This is the class the whole product is about, which is why it keeps
appearing inside the tooling as well as in the domain.

**Class 4: a number that drifted from what produced it.** F31 (a measurement
block updated field by field), F36 (a version string duplicated outside its
source of truth), F37 (a manifest proving completeness and read as proving
currency), F49 (arithmetic in prose with nothing to check it).

**One entry belongs to none of them and is worth reading on its own:** F1, the
fixture that flattered the rule it was meant to test. It is the closest this
repository has come to the mistake it was built after.

## Defect index

| Entry | Found in | What it was |
| --- | --- | --- |
| [F1](#f1-sprint-2-the-fixture-flattered-the-rule-it-was-meant-to-test) | sprint 2 | The fixture flattered the rule it was meant to test |
| [F2](#f2-sprint-2-a-lint-failed-on-the-document-explaining-its-own-exclusion) | sprint 2 | A lint failed on the document explaining its own exclusion |
| [F3](#f3-sprint-2-a-regression-test-passed-against-the-bug-it-documented) | sprint 2 | A regression test passed against the bug it documented |
| [F4](#f4-sprint-2-the-hygiene-guard-fired-on-the-document-that-defines-it) | sprint 2 | The hygiene guard fired on the document that defines it |
| [F5](#f5-sprint-3-two-contradictory-verdicts-printed-on-one-rule) | sprint 3 | Two contradictory verdicts printed on one rule |
| [F6](#f6-sprint-3-an-average-across-two-populations-read-as-one-weak-rule) | sprint 3 | An average across two populations read as one weak rule |
| [F7](#f7-sprint-3-the-budget-was-treated-as-a-property-of-the-rule) | sprint 3 | The budget was treated as a property of the rule |
| [F8](#f8-sprint-3-a-coverage-gap-folded-into-the-denominator) | sprint 3 | A coverage gap folded into the denominator |
| [F23](#f23-sprint-4-measurement-the-area-table-matched-nothing-at-all) | sprint 4 measurement | The area table matched nothing at all |
| [F24](#f24-sprint-4-measurement-the-geographic-model-has-a-missing-artifact) | sprint 4 measurement | The geographic model has a missing artifact |
| [F25](#f25-sprint-4-measurement-means-of-attack-is-a-separate-message-class) | sprint 4 measurement | Means of attack is a separate message class |
| [F26](#f26-sprint-4-measurement-there-is-a-fourth-state) | sprint 4 measurement | There is a fourth state |
| [F27](#f27-sprint-4-measurement-the-page-is-a-window-not-a-stream) | sprint 4 measurement | The page is a window, not a stream |
| [F31](#f31-0320-audit-a-measured-pin-went-stale-field-by-field) | 0.3.2.0 audit | A measured pin went stale field by field |
| [F32](#f32-0320-audit-the-readme-described-the-release-before-last) | 0.3.2.0 audit | The README described the release before last |
| [F33](#f33-0320-audit-a-threat-model-row-cited-a-decision-that-was-never-written) | 0.3.2.0 audit | A threat-model row cited a decision that was never written |
| [F34](#f34-0320-audit-one-document-contradicted-itself-across-two-sections) | 0.3.2.0 audit | One document contradicted itself across two sections |
| [F35](#f35-0320-audit-a-stated-rule-applied-to-two-of-three-cases) | 0.3.2.0 audit | A stated rule applied to two of three cases |
| [F36](#f36-0320-audit-a-version-string-lived-outside-its-single-source-of-truth) | 0.3.2.0 audit | A version string lived outside its single source of truth |
| [F37](#f37-0321-a-manifest-proves-completeness-not-currency) | 0.3.2.1 | A manifest proves completeness, not currency |
| [F38](#f38-sprint-5-an-attack-that-could-not-fail) | sprint 5 | An attack that could not fail |
| [F39](#f39-sprint-5-an-attack-that-never-reached-the-code-it-tested) | sprint 5 | An attack that never reached the code it tested |
| [F40](#f40-sprint-5-a-new-attack-with-the-same-defect-caught-the-same-day) | sprint 5 | A new attack with the same defect, caught the same day |
| [F41](#f41-sprint-5-ci-restated-the-gate-it-claimed-not-to-restate) | sprint 5 | CI restated the gate it claimed not to restate |
| [F42](#f42-0400-audit-a-threat-row-cited-a-test-that-has-never-existed) | 0.4.0.0 audit | A threat row cited a test that has never existed |
| [F43](#f43-0400-audit-the-architecture-diagram-omitted-the-only-live-source) | 0.4.0.0 audit | The architecture diagram omitted the only live source |
| [F44](#f44-sprint-6-a-schedule-built-on-a-probe-whose-failure-was-invisible) | sprint 6 | A schedule built on a probe whose failure was invisible |
| [F45](#f45-sprint-6-the-red-verification-probe-imported-the-code-it-was-checking) | sprint 6 | The red-verification probe imported the code it was checking |
| [F46](#f46-0530-interruption-was-not-one-of-the-stop-conditions) | 0.5.3.0 | Interruption was not one of the stop conditions |
| [F47](#f47-0530-two-runs-could-share-one-output-directory) | 0.5.3.0 | Two runs could share one output directory |
| [F48](#f48-0530-a-twenty-five-minute-run-printed-nothing-until-it-ended) | 0.5.3.0 | A twenty-five minute run printed nothing until it ended |
| [F49](#f49-0540-a-dramatic-finding-produced-by-a-division-error) | 0.5.4.0 | A dramatic finding produced by a division error |
| [F50](#f50-0600-review-the-page-fixture-encoded-the-parsers-assumption) | 0.6.0.0 review | The page fixture encoded the parser's assumption |
| [F51](#f51-0600-review-an-interrupted-write-could-plant-a-hole-the-census-cannot-see) | 0.6.0.0 review | An interrupted write could plant a hole the census cannot see |
| [F52](#f52-0600-review-the-stores-ordering-contract-was-an-accident-of-uniform-input) | 0.6.0.0 review | The store's ordering contract was an accident of uniform input |
| [F53](#f53-0700-a-plan-declared-the-projects-purpose-out-of-scope) | 0.7.0.0 | A plan declared the project's purpose out of scope |
| [F54](#f54-0700-an-access-blocker-outlived-the-access-problem) | 0.7.0.0 | An access blocker outlived the access problem |
| [F55](#f55-0700-two-figures-in-the-documents-were-written-from-memory) | 0.7.0.0 | Two figures in the documents were written from memory |
| [F56](#f56-0800-a-defect-entry-was-itself-wrong) | 0.8.0.0 | A defect entry was itself wrong |
| [F57](#f57-0800-a-control-was-removed-and-the-log-says-so) | 0.8.0.0 | A control was removed, and the log says so |
| [F58](#f58-0900-one-corpus-was-sized-for-two-different-requirements) | 0.9.0.0 | One corpus was sized for two different requirements |
| [F59](#f59-01000-a-probe-presented-an-arbitrary-match-as-an-attribution) | 0.10.0.0 | A probe presented an arbitrary match as an attribution |
| [F60](#f60-01020-an-unknown-tag-was-overwritten-by-a-prose-guess) | 0.10.2.0 | An unknown tag was overwritten by a prose guess |
| [F61](#f61-01110-a-timestamp-that-parses-cleanly-became-an-outage-one-layer-up) | 0.11.1.0 | A timestamp that parses cleanly became an outage one layer up |
| [F62](#f62-01110-the-transport-would-read-the-filesystem-when-handed-the-wrong-string) | 0.11.1.0 | The transport would read the filesystem when handed the wrong string |
| [F63](#f63-01110-a-duplicated-tag-in-the-map-resolved-by-file-order) | 0.11.1.0 | A duplicated tag in the map resolved by file order |
| [F64](#f64-01120-a-pin-that-nothing-compared-against-the-tree) | 0.11.2.0 | A pin that nothing compared against the tree |
| [F67](#f67-01400-the-regime-split-could-not-fire-on-live-input) | 0.14.0.0 | The regime split could not fire on live input |
| [F68](#f68-01500-the-evidence-base-had-no-inventory) | 0.15.0.0 | The evidence base had no inventory |
| [F69](#f69-01600-the-inventory-writer-ate-the-freeze-record-beside-it) | 0.16.0.0 | The inventory writer ate the freeze record beside it |
| [F70](#f70-01600-one-counter-for-two-different-events-and-it-flattered-the-join) | 0.16.0.0 | One counter for two different events, and it flattered the join |
| [F71](#f71-01610-the-kind-tables-cover-one-alert-in-ten-and-nobody-had-counted) | 0.16.1.0 | The kind tables cover one alert in ten, and nobody had counted |
| [F72](#f72-01610-nine-documents-disagreed-with-their-pins-while-the-gate-said-pins-held) | 0.16.1.0 | Nine documents disagreed with their pins while the gate said pins held |
| [F73](#f73-01610-the-readme-claimed-its-own-tables-were-checked-and-they-were-not) | 0.16.1.0 | The README claimed its own tables were checked, and they were not |

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

### F44, sprint 6. A schedule built on a probe whose failure was invisible

For two sprints this repository held that the corpus could only be collected
forward in time. It shaped T19, D-011, the sprint 5 scope decision, and the
advice to start a cron immediately. It was wrong: the channel's web preview
accepts a `before` parameter and pages backwards through the full history, which
on 2026-08-09 was 321,498 posts at exactly 20 per page.

The belief came from one observation, that `mavo collect` sees a twenty-message
window, generalised from the command to the channel without a probe against the
channel. When the probe was finally designed it asked for posts before id
1000000 against a channel whose newest post was 321498, which returns the newest
page. **A working parameter and an ignored parameter produce identical output at
that value.** The probe was re-run with a cursor inside the real range and
settled it in one request.

Class: **a probe whose negative result is indistinguishable from a null result.**
Distinct from an untested assumption, and worse, because running it produces the
feeling of having checked. Every probe now has to answer: what would this have
printed if the thing I am testing were false? If the answer is "the same", it is
not a probe.

Cost: two sprints of scheduling around a constraint that did not exist. Nothing
built on it was wasted, since window-gap detection (F27) is needed either way,
but the ordering was wrong and the corpus is two days later than it needed to be.

### F45, sprint 6. The red-verification probe imported the code it was checking

The sprint 6 regression suite was run against a scratch copy of 0.4.0.0 and
passed, which would have meant the tests assert nothing. The scratch copy did not
contain `mavo/backfill.py`; the editable install did, pointing at the working
tree, so the scratch tests imported the new module while appearing to run against
the old tree.

Why it survived: for about ninety seconds. It is recorded because the mechanism
is general. The repository's standing rule is to unpack the previous tag into a
scratch directory and confirm red, and an editable install silently defeats that
rule for every sprint that adds a module, which is most of them.

Class: same family as F44. A verification step that produces the same output
whether or not the thing it verifies is true. Remediation: the red-verification
probe uninstalls the package first, and CONTRIBUTING.md says so.

### F46, 0.5.3.0. Interruption was not one of the stop conditions

`backfill` named five reasons a run can end and reported whichever applied. The
sixth, and the most frequent in practice, is the operator pressing Ctrl-C, and it
was not among them. `KeyboardInterrupt` travelled through the loop, so a run that
had retrieved 1150 pages printed sixty lines of stack trace and said nothing
about the 1150.

Why it survived: every stop condition in the list is a condition the *channel*
produces. The operator was not modelled as a source of stop conditions at all,
which is the same blind spot as a threat model that covers adversaries and not
users.

Class: **a report that exists for every ending except the likely one.** The
adjacent instance is a summary that prints on success and not on failure, which
this repository would have caught; this one hid behind an exception type nobody
thought of as an ending.

### F47, 0.5.3.0. Two runs could share one output directory

Starting a second `backfill` against a directory an existing run was writing was
possible and silent. The corpus survives it, because snapshot names derive from
id ranges and the second writer produces identical bytes, but the request rate
doubles against a service whose tolerance is measured only over a burst of twenty
(T21).

Why it survived: the tool was written to be idempotent, and idempotence was read
as covering concurrency. It covers repetition. Found by doing it.

Class: a property proven for one axis and assumed on another. An advisory lock
with the holder's pid now refuses, and takes over from a dead holder rather than
requiring a cleanup step nobody remembers.

### F48, 0.5.3.0. A twenty-five minute run printed nothing until it ended

The report is written at the end. For a five-page probe that is invisible; for
2800 pages it means `tail -f` shows an empty file for twenty-five minutes and
working is indistinguishable from hung.

Class: an output shape validated at one scale and shipped for another. Progress
now goes to stderr every 25 pages, leaving stdout carrying only the report so a
redirect still yields a clean artefact.

### F49, 0.5.4.0. A dramatic finding produced by a division error

Reading the backfill report, I calculated that the channel had emitted 4.3 posts
per hour in April against 27 now, called it a sixfold change, and offered it as a
measured finding with consequences for whether the older corpus was usable at
all. The arithmetic was wrong: 34,000 posts over 71 days is 479 per day and 20
per hour, against roughly 25 now. A 25% drift, not a 600% one.

Caught by computing the daily distribution, which showed a flat series with a
median of 590 and a maximum of 764, incompatible with the claim already made.

Why it survived even briefly: the wrong number was interesting. A sixfold change
implies a story about format changes and unusable history; the true number
implies nothing and needs no story. Nothing in the pipeline was harmed, because
the claim was made in conversation rather than committed, but a claim made
confidently in conversation is how a claim reaches a document.

Class: **arithmetic in prose, uncounted by anything.** Every number in this
repository that a check touches has been right; this one had no check because it
was spoken rather than written. The remediation is not a tool, it is the rule
already in this document applied to conversation as well as to files: a
derived number is inference and is labelled, and an inference that implies a
consequence gets recomputed before the consequence is stated.


### F50, 0.6.0.0 review. The page fixture encoded the parser's assumption

The message regex required `<time>` to precede the text div. On the live page
the time element sits in the message footer, after the text, so the page-wide
scan paired message N's timestamp with message N+1's text, dropped the first
text on the page, and orphaned the last timestamp: every live-parsed event one
message late, silently. In the missile regime the whole warning budget is about
six minutes, so the shift is not cosmetic; it is the lead-time measurement
quietly poisoned, and it compounds with window overflow (F27) during exactly the
mass alerts that matter.

Why it survived: `tests/fixtures/channel.html` was synthetic and written in the
regex's order rather than the channel's. A fixture that encodes the code's
assumption measures the code against itself and can only ever agree with it.
The 0/20 classifier measurement (F23) used raw message texts, never the page
shape, so the two known defects did not overlap and neither exposed the other.

**Verified on the retrieved corpus, 2026-08-09** [measured]: on a full
20-message page the markers alternate strictly text-then-time, and all 20
blocks carry a `data-post` anchor. The footer order is not an assumption about
t.me/s; it is the shape of every page in the evidence, so the shift was
systematic, not occasional.

Class: **the same family as F1** - the fixture flattered the thing it was meant
to test - one layer down, at the page structure rather than the rule. Repaired
by parsing per `data-post` block with the timestamp searched inside the block
only, in either internal order; the fixture is now a page in the live footer
order; harness A12 (MT13) asserts exact pairing on two messages and its
mutation, which widens the timestamp search back to the whole body, goes red.

### F51, 0.6.0.0 review. An interrupted write could plant a hole the census cannot see

`backfill` wrote each snapshot with a plain `write_text`. An interrupt or crash
mid-write leaves a truncated `page-*.html` whose *name* still claims the full id
range. `--resume` then skips it as already retrieved, and `contiguity_gaps`
reads ranges from filenames, so the hole is structurally invisible: a census
with a hole it cannot see, which is a sample that believes otherwise - the
sentence this module's own docstring uses about someone else.

Why it survived: the failure needs an interrupt to land inside a single write of
roughly a hundred kilobytes, a window of milliseconds per page. The 3,034-page
retrieval simply never hit it. A defect that needs bad luck to fire is still a
defect; the corpus is the only evidence this project has.

Class: a durability guarantee assumed rather than constructed. Repaired with
write-to-scratch-then-`os.replace`, atomic on POSIX; the scratch suffix keeps a
crashed leftover out of the `page-*.html` glob every reader uses. The corpus on
disk predates the fix and passed its contiguity check, which bounds the exposure
but does not retroactively make the writes atomic.

### F52, 0.6.0.0 review. The store's ordering contract was an accident of uniform input

`replay` orders by `ts_source` stored as ISO text. Lexicographic order over ISO
strings is chronological only when every string carries one uniform offset, and
nothing enforced that: the Telegram adapter emits aware-UTC, the fixture
generator emitted naive datetimes, and the two had simply never met in one
store. Had they, replay order would have been wrong exactly where two sources
correlate - the system's whole job - and any aware/naive comparison in
`latency_s` would have raised, converting a correctness defect into an outage.

A second face of the same defect: `content_hash` hashed the timestamp as
spelled, so one instant reported as `+02:00` by one poll and `+00:00` by
another hashed as two transitions, and idempotence silently depended on the
reporter's clock presentation.

Class: **a contract held up by a coincidence of inputs.** Repaired at the single
point of entry: the store normalizes to UTC and refuses a naive timestamp with
`NaiveTimestamp` rather than repairing it, because repairing means inventing an
offset; the hash normalizes an aware timestamp to UTC before spelling it; the
fixture generator now emits aware-UTC. Three regressions in `test_store.py`
hold the refusal, the true-chronology replay across mixed offsets, and the
one-instant-one-hash identity.


### F53, 0.7.0.0. A plan declared the project's purpose out of scope

`docs/MOBILE.md` v1.0 closed with a section headed "Explicitly out of scope"
whose first item was public distribution. The project's target scope is a
publicly available warning system. The sentence was not a decision that was
later reversed; it was wrong when written, and it was written with the
confidence of a decision.

Why it survived a full release: it was consistent with everything around it.
`docs/MVP.md` topped out at "public repository as a portfolio artefact", T6
asked about "a private circle", and the threat model deferred output-channel
threats on the strength of a small trusting audience. Each of those is
defensible alone, and together they formed a coherent smaller project that
nothing in the repository contradicted. The gate cannot catch this class at
all: every check here verifies that documents agree with the tree and with each
other, and these documents agreed.

Class: **the destination restated as the nearest reachable point.** Distinct
from claim drift (F31), where a true statement goes stale. Here the statement
was never true, and it survived because it described something achievable. The
tell, available in hindsight, is that no document stated a goal the project
could not currently reach, which for a project this incomplete is itself
suspicious.

Repaired by naming the actual scope in three places rather than one: Audience D
in `docs/MVP.md` with its blockers typed, a `Sequencing, not exclusion` section
in `docs/MOBILE.md` replacing the incorrect one, and T6 restated to ask counsel
the broader question. No lint is proposed: a check that a document states an
ambitious enough goal is not a check, it is an opinion with a build step.

### F54, 0.7.0.0. An access blocker outlived the access problem

Two rows in `docs/MVP.md` read `blocked on the token` after sprint 6 retrieved
60,680 real messages without a token. One of them, `Defect log entries from
real data`, had in fact been satisfied earlier still: F23 was measured against
20 live messages in sprint 4.

The type system in that document is the point of it. **Access** blockers do not
shrink no matter how many sprints pass; **engineering** blockers do. A row
mistyped as access is a row nobody attacks, so the error is self-preserving:
it removes itself from the list of things anyone tries to fix.

Class: F44's family (a belief outliving its evidence), specialised to
scheduling. The retrieval that falsified it is recorded three documents away,
in `docs/DECISIONS.md`, and nothing connects the two. Repaired by correcting
both rows with the reason stated in the table, and by recording the correction
as a scope change under that document's own amendment rule.

### F55, 0.7.0.0. Two figures in the documents were written from memory

`docs/COMPUTATION.md` cited a constant `MAX_ALARMS_PER_WEEK = 2.0`. **This half
of the entry was wrong and is corrected in F56.** The constant did exist, in
`mavo/baserate.py`; the check that "found" its absence imported it from
`mavo.policy` and treated one failed import as proof. The second half stands.
`docs/MOBILE.md` described the channel as "measured at ~650 posts/day", which
is an inference from a single 14.7-hour window, labelled as inference in both
`docs/FOUNDATIONS.md` and this file. The corpus gives ~514/day as an actual
measurement across 118 days.

Both errors are the same move: a figure restated confidently in a new document
without being re-read from its source, one of them in the document whose whole
subject is that numbers come from measurement rather than memory.

Class: **provenance laundering.** A claim's label improves as it is copied,
because the copy loses the qualifier and keeps the number. The existing audits
verify cited *test names* and pinned *counts*; neither reads prose for symbol
names or for a label that has quietly been upgraded. Repaired by correction and
by stating the provenance inline at both sites. A cheap partial guard is
available and not yet built: extracting backtick-quoted identifiers from the
documents and failing when one does not appear in the package. It is recorded
as T22 rather than claimed here.


### F56, 0.8.0.0. A defect entry was itself wrong

F55 recorded two figures written from memory. One of them was not: it claimed
`MAX_ALARMS_PER_WEEK` did not exist in the package. It did, in
`mavo/baserate.py`, and the original sentence in `docs/COMPUTATION.md` was
correct. The check that produced the finding imported the name from
`mavo.policy`, got an `ImportError`, and concluded absence from a single failed
lookup in one module. The "correction" then replaced a true citation with a
different one.

Why it matters more than the error it claimed: a defect log is only worth
reading if its entries are true. A false entry costs more than the defect it
describes, because it spends the credibility that makes the rest of the log
useful, and it does so silently.

Class: **absence inferred from one place looked.** The same shape as F44, where
a probe's negative result was indistinguishable from its positive one; here a
failed import in one module was read as a fact about the package. Repaired by
correcting F55 in place with a pointer rather than deleting it, restoring the
citation, and by T22, which would have caught the original claim and this one:
a check that verifies backticked identifiers against the whole package cannot be
fooled by looking in the wrong module.

### F57, 0.8.0.0. A control was removed, and the log says so

Not a defect. Recorded here because the log is the place where this repository
writes down things that weaken it, and a control leaving the tree qualifies
whether or not the reasoning for removing it is sound.

The alarm-rate condition, the shared budget, the construction-time
over-allocation refusal, harness attack A5 and threat-model row MT5 were all
removed at 0.8.0.0 on the operator's decision (D-014). The reasoning is in the
decision and is not repeated here. What belongs in this file is the shape of the
change: **a hard control was replaced by a different hard control, not by
nothing.** The gate still has three conditions, and the new one, a floor on the
lower bound of lift, is mutation-verified by the same attack slot the old one
occupied.

What genuinely left the tree without a replacement is the refusal of alarm
fatigue as an attack surface. An adversary able to induce firings is now bounded
by the poison check and the lift floor, not by a rate. The author judged the
trade acceptable because the removed control rested on a number nobody had
measured. This paragraph exists so that judgement can be re-examined rather than
rediscovered.

Measured consequence, recorded rather than tuned: on the adversarial synthetic
history `R1-border-active` now passes the gate, at 2.52 alarms per week with a
lift lower bound of 1.69 against a floor of 1.50. Through 0.7.x nothing passed.
The margin is thin and the history is synthetic.


### F58, 0.9.0.0. One corpus was sized for two different requirements

The corpus was sized to give the classifier redesign enough real message variety
and it does: 60,680 messages over 118 days, of which 48,540 in the design
window. It was then assumed to be the evidence base for scoring a rule against
crossings, and for that it is far too short. Ninety-nine design nights against
roughly twelve crossings in four years gives an expected count of **0.81**. The
one crossing in the corpus period, 30 July 2026, falls in the holdout rather
than the design window.

Nobody wrote the second requirement down, so nobody noticed it was unmet. Both
requirements are legitimate and they size a corpus by different arithmetic: one
by message variety, the other by positive-event count, and the second needs
roughly fifteen times the span.

Why it surfaced only now: it took a measurement to see it. The threshold sweep
produced a usable cost axis immediately and then had nothing to say about
recall, and that silence was the finding. Reasoning about the corpus without
running anything had not exposed it in three releases.

Class: **one artifact serving two unstated requirements.** Repaired by stating
both: the corpus is sized for classification, and rule scoring against crossings
is deferred by D-015 rather than served by a longer retrieval. Had the thesis
stayed predictive, the repair would have been about 37,500 pages and ten hours
of paging, which is the number recorded here so that a future reader restoring
the predictive framing knows its price.


### F59, 0.10.0.0. A probe presented an arbitrary match as an attribution

`tools/register_probe.py` matched truncated register names against message text
and reported 16.56% of messages carrying a western area name, with
`Миколаївська, Львівська` as the busiest match at 1,075 hits. A single grep
showed the underlying text was `Миколаївський район`, a raion of *Mykolaiv*
oblast, listed beside `Вознесенський` and `Первомайський`, its neighbours.

Two independent defects, both in code written the same afternoon.

**The attribution was arbitrary.** When a stem matched several register entries
the probe took the first, `table[stem][0]`, and printed its oblast as though it
were a finding. An ordering artefact of the register was rendered as geography.

**The scope restriction created the collision it hid.** Restricting the register
to the eight western oblasts made `Миколаївський` unique *within that scope*, so
a stem that collides nationally looked clean. A restriction on the register is
not a restriction on the text, and the text is what is being searched.

Class: **a key with multiple values, reported as though it had one.** Repaired by
judging ambiguity against the whole country rather than the restricted scope, by
excluding colliding stems from attribution instead of assigning them, and by
splitting the headline figure into an upper and a lower bound that are printed
together. The corrected lower bound is 6.06%, and 77 of 445 stems in scope
collide somewhere in the country, meaning 17% of the vocabulary had been treated
as unambiguous when it was not.

The larger lesson is not about the bug. The measurement it produced was an
answer to the wrong question: the channel labels its areas with hashtags in
99.34% of messages, and no amount of repairing a text-matching heuristic would
have reached that. The grep that exposed the defect also showed the structure,
which is recorded in `docs/CHANNEL.md`.


### F60, 0.10.2.0. An unknown tag was overwritten by a prose guess

Sprint 7 made area resolution prefer the channel's own hashtag and kept the
oblast-name table as a fallback for the 0.66% of messages carrying no tag. The
fallback was wired to fire whenever the tag path returned nothing, which is not
the same condition. A message that carried a tag the map did not know, and
happened to mention an oblast in prose, resolved to that oblast: a guess drawn
from the table that scores 0 of 20 on real content, attached to an event, while
the unknown tag was reported separately as though nothing had been decided.

Found by running the sprint's own mutation check rather than by reading. The
assertion that failed printed `assert 'lviv' != 'lviv'`, which showed that the
old table still matched the test message through its prose, and that observation
is what exposed the wider condition.

Class: **a fallback whose trigger is wider than its justification.** The
justification was "the channel said nothing about the area"; the trigger was
"the tag path produced nothing", and those differ exactly when the channel said
something the map cannot read, which is the case the alias work exists for
(T33). Repaired: a message with tags that resolve to nothing returns no
classification at all, so the unknown tag is the only outcome. The fallback is
now reachable only from messages with no tags, which is what it was for. A
report naming the wrong place is worse than no report, because it is actionable.

### F61, 0.11.1.0. A timestamp that parses cleanly became an outage one layer up

`_parse_timestamp` accepted any string `fromisoformat` accepts, and
`fromisoformat` accepts `2026-09-01T21:00:00`: valid ISO, no UTC offset, a naive
datetime. `poll()` built a `ThreatEvent` around it and honoured its never-raise
contract, and the store then refused the event at `append` with
`NaiveTimestamp` (F52) - so a malformed *message* became an *outage*, one layer
above the contract that exists to prevent exactly that. Found in an external
review by composing the two guarantees rather than reading either one.

**Why it survived.** Harness attack A9 covered the hostile timestamp that does
not parse (`datetime="nonsense"`) and asserted that `poll` returns. The
timestamp that parses into the wrong shape took a different branch, and no test
asserted the composition: that whatever `poll` returns, the store accepts. Each
layer was correct against its own contract, and the defect lived in the seam.

Class: **two refusals composed into a raise.** Repaired at the parser: a naive
datetime is malformed by the same standard as an unparseable one and takes the
same path - unparsed, counted, reported.
`tests/test_telegram.py::test_f61_a_naive_content_timestamp_never_becomes_an_event`
asserts the composition itself, not either layer alone.


### F62, 0.11.1.0. The transport would read the filesystem when handed the wrong string

`UrllibTransport.fetch` passed its URL straight to `urlopen`, which also speaks
`file://`. Handed `file:///etc/hostname` it returned the file's contents as
though they were a fetched page. Every URL in the package is a constant today,
so nothing hostile could reach it; the defect is latent, and latent is the only
time a local-file-read is cheap to remove.

**Why it survived.** The transport's stated scope was "the one seam between this
package and the internet", and every test exercised it through that framing:
size cap, exception mapping, lossy decode. Nobody asked what it does with a
string that is not the internet.

Class: **a capability wider than the stated scope, unexercised and therefore
invisible.** Repaired with a scheme check that refuses anything but http(s) as
`SourceUnavailable`, keeping the raises-one-thing contract.
`tests/test_transport.py::test_f62_a_non_http_scheme_is_refused` holds it.


### F63, 0.11.1.0. A duplicated tag in the map resolved by file order

`AreaTable.from_csv` wrote rows into a dict keyed by tag, so a tag appearing
twice resolved to whichever row came later in the file. The map has no
duplicates today, which is why nothing fired; the defect is that if it ever
gained one - a hand edit, a bad merge of a register update - the contradiction
would be absorbed and an area would resolve to a code chosen by row order,
silently.

**Why it survived.** The map is generated and checked for other properties
(codes present, ambiguity flagged), and dict assignment is the idiomatic load
loop. Absorbing a duplicate key is what dicts do; that is exactly why the one
artifact area resolution trusts must not be loaded by one without a check.

Class: **a key with multiple values, resolved by accident rather than reported**
 - the same class as F59, one layer earlier in the pipeline. Repaired with a
refusal: `DuplicateTag` at load, before any resolution can happen.
`tests/test_areas.py::test_f63_a_duplicate_tag_in_the_map_is_refused` holds it.


### F64, 0.11.2.0. A pin that nothing compared against the tree

`STATUS.json` carries a `documents` block naming every design document and its
version, and eleven checks in `tools/docs_audit.py` read `STATUS.json`. None of
them read this block against the tree. A document could be added and be entirely
invisible to the gate: unpinned, or pinned at a version its own header no longer
carried, and every check would still pass and print `pins hold`.

**Why it survived.** The block looks like a check because it sits beside real
ones. It was maintained by hand on every release that touched a document, and
hand maintenance that happens to be correct is indistinguishable from a check,
right up to the release where somebody forgets. This release is that release:
`docs/reviews/0.11.1.0.md` was written, added, and not pinned, and the gate said
`pins hold at 0.11.1.0`.

Class: **a claim the repository makes about itself that is not executable**,
which is the failure ENGINEERING.md section 0 exists to name. The block was a
sentence in JSON.

Repaired by comparing the block against `docs/**/*.md` in both directions: a
document in the tree and not in the block fails, and a pin naming a document that
no longer exists fails too, because a stale pin is a claim about a file nobody
can read. Top-level documents stay out of scope deliberately: they are versioned
by the release rather than by a marker of their own, and pretending otherwise
would add four pins that mean nothing.


### Distance to the Polish border, 2026-08-09

The column T32 asked for, delivered as an interval rather than the scalar the
criterion named. Every one of the 127 mapped areas carries one.

| Quantity | Value | Label |
| --- | --- | --- |
| Areas with a distance | 127 of 127 | measured |
| Nearest area centre (Самбірський район) | 14.2 km | measured |
| Farthest (Кальміуський район) | 1074.0 km | measured |
| Areas whose interval reaches zero | 5 | measured |
| Register centre points and areas | ua-geo, KATOTTG joined to OSM relations | reported, not verified here |
| Border outline | Natural Earth 10m, ~1 km positional error | reported |
| True nearest-edge distance | - | **not measured**, and stated as not measured |

**What is measured** is the geodesic distance from each area's registered centre
point to the nearest point on the Polish outline, and the radius of a disc with
the same area. **What is not measured** is the distance from the area's edge,
which is what a reader actually wants. The gap is not small and is not random:
it is largest exactly for the border raions this project exists to watch.
Самбірський район shares an edge with Poland, so its true distance is zero while
its centre sits 14.2 km away.

So the column is an interval, `lower` to `upper`, and `AreaRef.border_interval`
renders `0-46 km` rather than `14 km`. A reader who sees `0-46` knows the alert
may be at the border and knows the report cannot say more. A reader who sees
`14 km` has been told something false to one decimal place.

**This deviates from T32's own acceptance criterion**, which asked for one
scalar per area. Recorded rather than taken quietly: this project allows a
criterion to move after the fact only when the replacement is harder to satisfy
than the original, and an interval is harder to produce and harder to quote than
a number. Closing the gap needs polygons keyed by KATOTTG, which no source
reachable offline provides; the recipe is in `tools/border_distance.py`.

**The spot check caught the author, not the code.** Four settlement distances
were written down by hand before the run, as T32 requires. Lutsk was bounded at
90 to 130 km from an estimate; the tool measured 85.1 km and refused to write
the file. An independent flat-earth cross-check gave 86.4 km against the nearest
border vertex, so the bound was what was wrong, and it was widened with that
reason recorded in the source. A bound widened because the measurement
disagreed is a defect unless the bound is shown to be the error.


### F67, 0.14.0.0. The regime split could not fire on live input

Every regime rule tests `event.kind is MISSILE` or `is DRONE`. `kind` was read
off the alert message, and the channel does not put it there. Measured on the
twenty real messages held as fixtures: 15 carry an alert state, 4 carry a kind
marker, **0 carry both**. So on live input every alert arrived UNKNOWN and no
regime rule could fire, permanently and silently.

**Why it survived five sprints.** F25 recorded the shape in sprint 4, in one
paragraph, correctly, and called it architectural rather than cosmetic. It was
then filed as T16 and the sprint that would have done it kept being the next
one. Every test that exercises a rule builds its events from the fixture
generator, which attaches a kind to the alert because that is how the dataclass
is shaped, so the suite measured the rules against the one input where the
defect cannot appear. That is the same sentence as F65's, which is why both are
in the same class.

**What makes this one worse than F65.** The regime split is not a detail of the
rules; it is the project's central finding. A global recall of 0.47 was masking
a missile rule at 7 of 7 and a drone rule at 0 of 8, and separating them is what
made an honest claim possible at all. On real input that separation had nothing
to separate by.

Class: **one identifier, two meanings, joined by an equality test** - the same
as F65, one field over. Repaired by giving the kind its own stream, its own
table and its own lifetime, and joining it to alerts by oblast and time in
`mavo/kinds.py` before the rules see them.
`tests/test_sprint9.py` holds it, including the case where two kinds are live at
once and the join answers UNKNOWN rather than picking.

**Not repaired: whether the join has coverage.** The mechanism exists; whether
the source declares a means often enough for it to matter is a measurement on
the corpus, and the corpus is not in the tree. Until `tools/kind_coverage.py`
has been run, the honest statement is that the regime split can now fire, not
that it will.


### F68, 0.15.0.0. The evidence base had no inventory

On 2026-08-09 the corpus was lost. Sixty thousand posts, 118 days, one copy on
one laptop, no second copy, no checksum, no inventory, and no entry anywhere
saying where it lived. Every measurement this project publishes was derived from
it: 99.34% tag coverage, 48,540 messages, 127 tags, 99.997% tag-prose agreement,
22 western-wide nights, 0 of 22 crossings.

The tree carried a `MANIFEST.sha256` over 101 source files and nothing at all
over the data those files exist to analyse.

**What survives and what does not.** The published figures remain true as a
record of what was measured; the method is written down and the arithmetic is
reproducible. What is gone is the ability to *re-derive* them, and to answer the
one question a reader is entitled to ask: is the data you measured the data you
say you measured. `docs/FEED-SPEC.md` argues in section 1 that the Ukrainian
channel could be verified rather than taken on trust. Between the loss and this
release, MAVO could not offer the same.

**Why it survived.** Because it was never modelled as a defect class. The
project's discipline is aimed at claims in code and prose, and it is thorough
there: pins, audits, manifests, mutation-verified controls. The data those
claims are about sat outside every one of those mechanisms, in a directory that
is correctly gitignored as tier 1 and was therefore invisible to all of them.
Tier 1 means *not committed*; it was read as *not tracked at all*.

**Recovery, and the trap in it.** Telegram addresses posts by id and a page
re-fetched is a page unchanged, so re-collecting the same id range yields the
same corpus. The trap is that without an inventory, "the second copy is the
first one" is an assumption, in exactly the place this project refuses them.

Class: **a critical artifact with no inventory** - the same shape as F64, a pin
nothing compared against the tree, one layer further out: a claim about
something the gate could not see. Repaired with
`tools/corpus_inventory.py`, which writes per-page checksums, id range,
contiguity and an aggregate digest into `data/aggregates/corpus_manifest.csv`
(tier 2, committed), and a `docs_audit` check that fails when `STATUS.json`
carries a design-window figure and the inventory does not exist or disagrees
with it. A corpus measurement is now uncommittable without the identity of the
corpus it came from.

*The first draft of that check matched only keys ending in `_design_window` and
would have let `design_window_messages` and its siblings through: a check
written to catch exactly those figures, missing half of them. Caught by its own
regression before release, and recorded here rather than quietly widened.*


## Corpus measurements, 2026-08-09

Metadata only. No message content was read before the holdout boundary was
frozen (D-012a).

| Quantity | Value | Provenance |
| --- | --- | --- |
| Range | ids 260841 to 321520, 60,680 posts, 3,034 pages | measured |
| Span | 2026-04-13 to 2026-08-09, 118 days | measured, from `datetime` attributes |
| Contiguity | no gaps | measured, `mavo backfill` exit 0 |
| Size on disk | 313 MB | measured |
| Daily volume | median 590, min 382, max 764 | measured over 45 days |
| Daily volume trend | about +20% from April to August, gradual | inference. No step change, so the channel did not alter its format or cadence inside the corpus, and the older window is usable for design |
| Hourly volume | median about 25, maximum 112 | measured |
| Ceiling | none | inference. The hourly tail thins smoothly to 112 with one hour per value rather than stopping at a round number, which is what a throughput cap would look like |
| Campaign visibility | visible hourly at roughly 4.5x the median hour, invisible daily | **inference, and it changes the unit.** Routine alert and all-clear pairs from the whole country dominate a daily count and dissolve a campaign into it. Candidate campaign windows must be labelled by hour, not by day |

## Channel measurements, 2026-08-09

Taken against the live channel from a residential connection in Warsaw. Every
row is a measurement of that channel on that day, not a property of Telegram.

| Quantity | Value | Provenance |
| --- | --- | --- |
| Page size | exactly 20 posts | measured, four runs, no page returned a different count |
| Newest post id | 321498 at 08:0x, 321519 at 08:33 | measured |
| Backwards paging | works with a cursor inside the live id range | measured. The first probe used a cursor above the range and could not distinguish a working parameter from an ignored one (F44) |
| Channel volume | ~27 posts/hour, ~650/day, ~32 pages/day | inference from one 14.7-hour window (17:53 to 08:33) spanning an evening and a night. A campaign night is expected to be a multiple of this and has not been observed |
| Tolerated request rate | 0.2 s between requests, clean over 20 requests | measured, burst only. `posts=400` in both the 0.5 s and 0.2 s runs, so the service was not silently truncating pages |
| Tolerated rate over a long run | unknown | **not measured.** Twenty requests is a burst; rate limits commonly apply to sustained volume. The 2900-page run this number would authorise is 145 times longer, and generalising from the burst is the F44 pattern |

The default delay stays at 1.0 s. It was not lowered to the measured burst
figure, because a measurement of 20 requests does not license a claim about
2900, and a default is a claim. 0.5 s is documented as the operating rate for
long runs with that limitation stated, which is a recommendation the operator
applies knowingly rather than a number the tool asserts.

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


---

## Sprint 7: what the negative result means, and what it does not

The design window holds 81 western episodes, of which 22 touch all 36 western
raions at once. Polish sources report **no airspace violation on any of the four
busiest western nights**, and the one confirmed crossing of the corpus period,
30 July 2026, falls in the holdout rather than the design window.

Recorded here because a project that only writes down its confirmations is a
brochure.

**What it would have meant under the old thesis.** A predictive rule firing on
western-wide alerts would have scored 0 of 22 in this window. Ninety-nine nights
of data, twenty-two candidate firings, no hits, and nothing to show. That is not
a surprise: crossings run at two to four a year and western-wide alerts at
roughly one in four nights, so coincidence has to be rare. It is the base-rate
argument arriving as an observation rather than as arithmetic.

**What it means under the current one.** Nothing against the project. D-015
states that the tool reports a picture and predicts nothing, and the picture it
reports was true on all 22 nights: the whole of western Ukraine was under alert.
The negative result is the strongest available confirmation that dropping the
predictive framing was correct, and it arrived one release after the decision
rather than one release before, which is luck rather than foresight.

**The expectation this measurement does not touch.** The working assumption is
that incursions are *deliberately organised against the Polish border* rather
than being spillover from strikes deeper in Ukraine. If that is right, a
predictor keyed to strike intensity was doomed for a second, independent reason:
the intent it would need to observe is not a function of the volume it can see.
This is [speculation] and is recorded as such; it is not evidence for anything
and it is not used anywhere in the code. Its only role is to keep anyone from
reviving the predictive framing on the grounds that a longer corpus would fix
it.

**Its limit, stated.** Absence of press coverage is not absence of event. A
single drone that crosses and is downed without debris may never reach national
media. T35 records the check that would turn this from an absence of evidence
into a measurement: the operational command's own posts for those four dates.


---

## Sprint 7 closed: how, and on a criterion that changed

T36 required a hand-labelled sample of at least fifty messages, because when the
criterion was written no automated check appeared to exist. One did. **The
channel writes the area name twice**, once in prose and once as a tag, and two
independent copies of the same fact in one message can be compared by a machine.

**The measurement.** 38,521 comparable messages in the design window, tag and
prose naming the same area in **38,520 of them, 99.997%**. The single
disagreement is an after-action damage report tagged at oblast level whose prose
names the raion: both correct, different granularity. Errors of area
resolution in the design window: **zero observed**.

**The criterion changed and this is the record of it**, under the amendment rule
in `docs/MVP.md`. The replacement is not easier, which is the only defensible
reason to change a criterion after the fact. It is stronger in coverage by three
orders of magnitude, 38,521 messages against fifty, so the interval is ±0.02%
where a hand sample would have been ±5%. It is weaker in kind: internal
consistency is not truth, and a channel that named the wrong raion in both
places would be agreed with rather than caught.

**What the measurement does not cover, stated because it is the residual and
somebody will otherwise treat 99.997% as covering everything.** 9,701 messages
carry a tag and no prose area the map recognises, and this check says nothing
about them. They are 20% of the corpus. The hand sample is therefore not
retired, it is **retargeted**: T36 now samples from that population alone, where
it is the only instrument available, rather than from the population where an
exhaustive check exists.

**Two findings the check produced by disagreeing with itself first.**

The first run reported 96.972% and printed twenty-five disagreements, all of one
shape: an all-clear carrying a continuation list, `Відбій ... Зверніть увагу,
тривога ще триває у: - Запорізька область - Пологівський район`. The tag names
the area the all-clear is about; the list names areas where the alert continues.
Two roles in one message, compared as one set. Separating them moved agreement
from 96.972% to 99.997%, and the message class is now known: 5.2% of comparable
messages, naming 4,064 areas as still running, **every one of which the pipeline
discards** (T37).

The run before that reported disagreements that were almost entirely the
probe's own regex: `(?:в|у|на)` carried no word boundary, so the `на` ending
`Повітряна` matched and the capture became `тривога в Миргородський`. Third
instance in one session of an instrument reporting its own defect as a property
of the material (F59, the west_activity denominator, this). The repair was not a
better pattern: candidate names are now kept only when the map already knows
them, because `район` is also an ordinary noun and no pattern over that word can
tell an administrative unit from the area of an old town.


### F69, 0.16.0.0. The inventory writer ate the freeze record beside it

`tools/corpus_inventory.py --write-status` assigned `status["corpus"] = {...}`,
replacing the block rather than merging into it. The block already held the
D-012a holdout record - `design_window_high_id`, `holdout_low_id`,
`holdout_share`, `content_read_before_freeze` - the boundary frozen before any
message content was read, which is what makes the holdout a holdout rather than
a second look at data already seen. One run erased all four, and `make verify`
passed.

**Why it survived.** Two reasons, and the second is the one that matters. The
first: the write looked like an update, and a tool writing figures it just
measured is exactly the discipline this project asks for elsewhere. The second:
**nothing read those fields.** Eleven checks read `STATUS.json` and not one of
them asked whether the freeze record was still there, so the gate could not
distinguish a block that had been updated from a block that had been eaten.

Class: **F64, a pin nothing compared against the tree**, committed inside the
tool built to close that class one layer out (F68). Recorded rather than
quietly corrected because the pattern is now three deep and the repair had to
address the reader, not only the writer.

**Repair, both halves.** `patch_corpus_block()` merges, and ownership is by an
explicit list rather than by acquaintance: inventory fields overwrite, the
superseded hand-written schema (`posts`, `post_id_low`, `post_id_high`,
`retrieved`, `contiguous`, `span_days`) is retired with each removal printed,
and every other key survives - including keys invented after this function was
written. A naive merge was rejected: it would leave two contradictory
descriptions of the corpus in one block, `posts: 60680` beside
`messages: 61240`, and the stale one is the one somebody quotes.

The second half is `docs_audit.check_the_holdout_boundary_survives_in_the_corpus_block`,
the reader those fields never had: the four fields must be present, the boundary
must be two adjacent ids, and the freeze flag must be an explicit boolean.
Held by `tests/test_corpus_inventory.py::test_a_status_write_does_not_erase_fields_it_does_not_own`
and `tests/test_corpus_inventory.py::test_the_gate_refuses_a_corpus_block_missing_the_holdout_record`,
both verified red against a scratch copy carrying the original assignment and a
disabled guard respectively.

### F70, 0.16.0.0. One counter for two different events, and it flattered the join

`JoinReport.resolved` counted two things as one: alerts whose own message named
the means of attack, and alerts the join supplied a regime for. `coverage`
divided that total by every alert, so it took credit for regimes the join never
touched. Nothing was arithmetically wrong, which is why it survived: the number
was correct for a question nobody had asked, and it was about to be quoted as
the answer to the question T16 exists to settle.

**Why it survived.** The counter was named after its effect rather than its
cause, and no test asked where a resolution came from. Three tests asserted on
`resolved` and each was satisfiable either way.

Class: **an instrument reporting its own framing as a property of the material**
 - the family of F59 and the `?before=` probe of F44, where the measurement and
the thing measured were not separable in the output.

**Repair.** `carried` and `joined` are separate fields; `resolved` survives as
their sum, so existing assertions keep their meaning. `join_coverage` is the
join's own performance - of the alerts that arrived without a kind, the share it
resolved to exactly one - and it is the figure to quote when the question is
whether the join works. `JoinReport.line()` prints both, so the TTL sweep in
`tools/kind_coverage.py` shows the split without a caller having to know about
it. Held by `tests/test_sprint9.py::test_t16_a_message_that_states_its_own_kind_is_not_overwritten`,
verified red against a scratch copy that merges the counters again.

### F71, 0.16.1.0. The kind tables cover one alert in ten, and nobody had counted

`tools/kind_coverage.py` was built in 0.16.0.0 to measure what the threat-kind
marker tables actually catch. Run on 2026-08-10 against 61,041 messages, it
answered: coverage 0.128 at a one-hour TTL, `join_coverage` 0.104, and 36,697
of 42,910 alerts leaving the join as UNKNOWN.

The figure that matters most is smaller. Of 2,392 declarations, **25 were
MISSILE, or 1.0%**. The missile rule is the only rule that has ever passed the
gate on its own regime (7 of 7), and the channel announces ballistics as
`Загроза балістики`, a form carrying no declaration marker at all. The one
working rule is invisible to the join on almost every occasion it applies.

Four failure modes, each confirmed against corpus text [measured]:

| Text from the channel | Declaration marker | Kind | Outcome |
| --- | --- | --- | --- |
| `Атака дронів-камікадзе` | hits | none, `дрон` is not in KIND_MARKERS | rejected |
| `Загроза балістики` | none | `балістик` yields missile | rejected |
| `Загроза керованих авіабомб` / `Загроза КАБ` | none | `каб` yields glide_bomb | rejected |
| `Відбій загрози артобстрілу` | lift hits | none, artillery does not exist in ThreatKind | rejected |

**Why it survived.** T16 was recorded as unblocking the classifier, and it does
unblock it - on the traffic the tables happen to parse. Nothing measured the
denominator until the instrument existed, and the instrument was built one
release after the claim.

**Two named risks did not materialise, which is also a result.** The comment
added in 0.16.0.0 flagged `небезпека` as possibly over-broad; it has **zero**
hits, so the marker is dead rather than wide, and the guessed direction of
error was beside the actual one. No lift inversion appears in the sample.

**TTL is not the binding constraint.** Coverage moves from 0.128 to 0.127
between a one-hour and a twenty-four-hour TTL. Tuning it would be work on the
wrong term; the parser's reach is the term that binds.

Class: **an instrument reporting its own framing as a property of the
material** - the family of F59 and F70. Logged rather than repaired: the tables
are `[assumption, unmeasured]` and the repair needs this measurement as its
reference point, so the fix ships against a baseline instead of against a
memory of one.

### F72, 0.16.1.0. Nine documents disagreed with their pins while the gate said pins held

`STATUS.json` pins a version for every document. On 0.16.1.0, nine of them
disagreed with the marker inside the document: `docs/FEED-SPEC.md` declared 1.0
against a pin of 1.3, `docs/MVP.md` 3.0 against 3.2, and seven more by one or
two minor versions. Every release since 0.12.0.0 printed `docs-audit: pins hold`.

**Why it survived.** `check_every_document_is_pinned` compares the *set* of
documents against the tree, and its own docstring says so outright: a marker
"could drift, or it could carry no marker at all, and every check here would
still pass". The failure was written down at the moment the check was added and
was not guarded then. That makes this worse than an ordinary unguarded pin: the
prediction existed in the file that needed it.

Class: **F64, a pin with no reader**, with a note attached explaining where the
next one would come from.

**Repair.** `check_document_versions_match_their_pins` reads both marker styles
in the tree (the fenced `Document: ..., version N.N` block and the newer
`Version: N.N / date` line), reports a document carrying neither rather than
skipping it, and treats `docs/reviews/` as out of scope because a review is
versioned by the release it reviews. Held by
`tests/test_docs_audit_versions.py`, six regressions, verified red on a scratch
copy carrying the pre-repair headers.

**The repair had the defect it was repairing, caught in verification.** Removing
the check's line from `main` left every regression green, because the tests
import the function directly and the gate is what calls it. A sixth test now
reads `main` and fails if either new check is defined and not registered.

### F73, 0.16.1.0. The README claimed its own tables were checked, and they were not

Directly above the size table, the README says these rows are recounted from
the tree on every run and that a stale row is "a gate failure rather than a
typo". That sentence describes `check_statistics_match_the_tree`, added in
0.6.2.0, which compares `STATUS.json` against the tree. Nothing compared the
README against either.

By 0.16.1.0 every row of both README tables was stale, including **206 tests,
96.14% coverage and 49 defects** printed twelve lines below badges reading 208,
96.16% and 51 - badges the gate does enforce. The same document stated two
different test counts, and the enforced one was not the one a reader reaches
first. The corpus row still described the 9 August retrieval after the tree had
moved to the 10 August inventory.

**Why it survived.** The repair in 0.6.2.0 closed one edge of a triangle. Pins
were compared against the tree, badges against the pins, and the prose tables
against nothing - while the paragraph introducing them asserted the opposite.
A claim that a check exists, sitting in a document the check does not read, is
the F66 shape aimed at this repository's front page.

Class: **class 1, a document describing a tree that has moved on**, compounded
by class 4: the drifted numbers were introduced by a repair that stopped one
step short and said it had not.

**Repair.** `check_readme_tables_match_the_pins` locates rows by label rather
than by position, so reordering the table cannot silently drop a row from the
audit, and reports a missing label instead of skipping it. Held by
`tests/test_docs_audit_readme.py`, verified red against the pre-repair README.

## Threat-kind coverage measurement, 2026-08-10

Produced by `PYTHONPATH=. python3 tools/kind_coverage.py --raw data/raw --sample 30`
against the corpus inventoried the same day: 3,062 pages, 61,240 messages, ids
260790 to 321830, digest `sha256:10266cbf7753...`. 61,041 messages carried
parseable text. The measurement is the reference point for F71 and for any
later repair of the marker tables.

| Quantity | Value | Provenance |
| --- | --- | --- |
| Declarations | 2,392 | measured |
| Lifts | 993 | measured |
| Still unparsed | 4,447 | measured |
| Kinds assigned | GLIDE_BOMB 1,868, DRONE 1,492, MISSILE 25 | measured |
| Marker hits | `загроза застосування` 1,374, `загроза удар` 1,018, `відбій загрози` 993, `небезпека` 0 | measured |
| Near misses | 2,957 | measured |
| Declaration to lift | n=790, median 97 min, p90 586 min, max 7,094 min | measured |
| Active alerts | 42,910 | measured |
| Coverage by TTL | 0.128 at 1 h, 0.127 at 24 h | measured |
| `join_coverage` by TTL | 0.104 at 1 h, 0.103 at 24 h | measured |
| UNKNOWN after the join | 36,697 of 42,910 | measured |

**What it does not say.** Nothing here measures whether an assigned kind is
*correct*; it measures how often one is assigned at all. The hand-labelled
correctness sample (T36) remains open, and a coverage figure without it can
only bound the problem from one side.
