# METHODOLOGY

What may be claimed, what was measured, and every defect this repository has
found in itself.

```
Document:  docs/METHODOLOGY.md, version 2.37
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
13. [Cost of composing a report, 2026-08-10](#cost-of-composing-a-report-2026-08-10)
14. [Threat-kind coverage after the F71 repair, 2026-08-10](#threat-kind-coverage-after-the-f71-repair-2026-08-10)
15. [Border column, independent verification, 2026-08-10](#border-column-independent-verification-2026-08-10)
16. [Hand-checked report sample, 2026-08-10, and its limits](#hand-checked-report-sample-2026-08-10-and-its-limits)
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
| [F74](#f74-01900-the-contracts-join-field-was-a-display-name-and-the-map-drew-nothing) | 0.19.0.0 | The contract's join field was a display name, and the map drew nothing |
| [F75](#f75-01900-the-terminal-announced-a-schema-version-the-file-did-not-carry) | 0.19.0.0 | The terminal announced a schema version the file did not carry |
| [F76](#f76-01920-the-trailing-counter-measured-how-finely-an-oblast-is-subdivided) | 0.19.2.0 | The trailing counter measured how finely an oblast is subdivided |
| [F77](#f77-01920-the-regression-file-claimed-a-verification-it-had-not-had) | 0.19.2.0 | The regression file claimed a verification it had not had |
| [F78](#f78-01930-the-missile-stem-was-one-letter-too-long-for-half-its-forms) | 0.19.3.0 | The missile stem was one letter too long for half its forms |
| [F79](#f79-02010-the-reviews-kept-happening-and-stopped-being-filed) | 0.20.1.0 | The reviews kept happening and stopped being filed |
| [F80](#f80-02120-a-fabricated-detail-and-an-overstated-adjective-in-the-document-written-to-be-believed) | 0.21.2.0 | A fabricated detail and an overstated adjective, in the document written to be believed |
| [F81](#f81-02140-the-corpus-total-counted-199-posts-twice) | 0.21.4.0 | The corpus total counted 199 posts twice |
| [F82](#f82-02140-the-labelling-instrument-showed-one-area-where-the-message-named-five) | 0.21.4.0 | The labelling instrument showed one area where the message named five |
| [F83](#f83-02150-the-cause-of-blindness-was-printed-only-on-the-path-nobody-runs) | 0.21.5.0 | The cause of blindness was printed only on the path nobody runs |
| [F84](#f84-02150-a-broken-observer-could-stop-the-heartbeat) | 0.21.5.0 | A broken observer could stop the heartbeat |
| [F85](#f85-02150-the-trailing-counter-lost-the-episode-that-outlived-the-window) | 0.21.5.0 | The trailing counter lost the episode that outlived the window |
| [F86](#f86-02150-the-alert-path-picked-a-threat-kind-by-dict-insertion-order) | 0.21.5.0 | The alert path picked a threat kind by dict insertion order |
| [F87](#f87-02150-the-fingerprint-promised-a-comparison-that-did-not-exist) | 0.21.5.0 | The fingerprint promised a comparison that did not exist |
| [F88](#f88-02150-a-post-repeated-inside-one-file-was-counted-twice-twice) | 0.21.5.0 | A post repeated inside one file was counted twice, twice |
| [F89](#f89-02160-the-discrepancy-had-an-explanation-and-the-explanation-was-wrong) | 0.21.6.0 | The discrepancy had an explanation, and the explanation was wrong |
| [F90](#f90-02200-the-live-path-never-reached-the-table-that-fixed-f23) | 0.22.0.0 | The live path never reached the table that fixed F23 |
| [F91](#f91-02200-the-f85-entry-claimed-a-direction-the-fold-does-not-have) | 0.22.0.0 | The F85 entry claimed a direction the fold does not have |
| [F92](#f92-02200-an-inference-labelled-measured-in-the-entry-about-inferences-labelled-measured) | 0.22.0.0 | An inference labelled measured, in the entry about inferences labelled measured |
| [F93](#f93-02200-shipped_sprints-means-a-test-file-exists-and-the-status-line-read-it-as-sprints-completed) | 0.22.0.0 | shipped_sprints means a test file exists, and the status line read it as sprints completed |
| [F94](#f94-02210-a-streaming-reader-held-its-connection-across-every-yield) | 0.22.1.0 | A streaming reader held its connection across every yield |
| [F95](#f95-02310-a-task-outlived-its-reason-and-kept-the-reason) | 0.23.1.0 | A task outlived its reason, and kept the reason |
| [F96](#f96-02400-the-live-command-polled-the-channel-and-dropped-what-it-understood) | 0.24.0.0 | The live command polled the channel and dropped what it understood |
| [F97](#f97-02420-replay-dropped-a-row-when-a-sort-key-tie-straddled-a-chunk-boundary) | 0.24.2.0 | Replay dropped a row when a sort-key tie straddled a chunk boundary |
| [F98](#f98-02810-the-ten-second-timeout-was-a-ten-second-timeout-per-socket-operation) | 0.28.1.0 | The ten-second timeout was a ten-second timeout per socket operation |
| [F99](#f99-03231-a-tag-was-created-over-a-gate-that-had-already-refused) | 0.32.3.1 | A tag was created over a gate that had already refused |

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

**One thing about that figure is open, and it was nearly recorded as a defect
in error.** 321,498 is the newest post id, and an id equals a count of posts
only if the sequence starts at 1 and skips nothing. The second half is
measured and holds: the collected range 260790 to 321830 spans 61,041 ids and
carries 61,041 distinct posts, so across 17% of the sequence there is not one
gap. The first half is untested. **One `before=20` request would settle it**
and none has been made, so the figure is `[measured as an id, assumed as a
count]` and the assumption is now visible. See the 0.22.0.0 review for why this
almost became a defect entry instead.

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
against the corpus inventoried the same day: 3,062 pages, **61,041 distinct
posts**, ids 260790 to 321830, digest `sha256:10266cbf7753...`. All 61,041
carried parseable text.

**This paragraph said something different until 0.21.6.0, and the difference is
F89.** It read "61,240 messages ... 61,041 messages carried parseable text",
which presented the gap as a parseability subset. It was not: 61,240 was the
inventory's file-sum with 199 posts counted twice (F81), `kind_coverage` keys
by post id and had always counted distinct posts, and the number of posts
without parseable text is zero. The measurement is the reference point for F71 and for any
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

### F74, 0.19.0.0. The contract's join field was a display name, and the map drew nothing

`state.json` v1 published the oblast in one field, and the value was the
register's Ukrainian name: `Львівська`. The consumer indexes its geometry by
ASCII slug (`lviv`), so every area failed to match. Measured against
`mavo-site` 1.2.0.0 by running that package's own `build_overlay` over a
state file this repository produced: **0 markers, 4 of 4 areas unplaceable.**

The distance list would have rendered completely, because it prints the name
rather than joining on it. So the failure mode was not an error page: it was a
page showing seven areas under alert beside a map showing none, with nothing
saying why. A reader would take the map for the truth, because a map looks
like a measurement and a list looks like an opinion.

**Why it survived.** The field was checked for being non-empty, printed in the
report a person reads, and asserted on in tests that all used the same value.
Nothing asked what a consumer would do with it, and the consumer was in
another repository with its own gate. D-020 moved contract *ownership* here
one release earlier; it did not move the consumer's geometry vocabulary, and
ownership without a test against a real consumer is a claim rather than a
control.

Class: **an identifier that means two things, and the join happened on the
wrong one** - the family of F63, one boundary further out.

**Repair.** `oblast` carries the ASCII slug, `oblast_name` carries the
register name, and the two are separate fields because they answer to
different readers. The slug comes from `mavo/areas.py::oblast_slug`, which
already existed and already agreed with the consumer's vocabulary on 22 of 23
oblasts. Held by `tests/test_sprint10.py`, verified red against a scratch copy
publishing the display name again.

**The twenty-third, and the sentence that was written about it was wrong.**
MAVO's register has one `kyiv`; the consumer's geometry splits `kyiv-city`
from `kyiv-oblast`, a real administrative distinction this project does not
make. The entry as first written said "the consumer maps it", in the present
tense, without anyone having looked. **Measured against `mavo-site` 1.2.0.0 on
2026-08-10**: the geometry carried `kyiv-oblast` and `kyiv-city`, there was no
`kyiv`, and no mapping existed anywhere in that package, so seven Kyiv-oblast
raions landed in `unplaceable` and drew no marker.

The correct side for the mapping was always the consumer, for the reason the
original sentence gave. What was wrong was the tense: a statement about
somebody else's code, written without reading it, in the entry recording a
defect caused by exactly that. Corrected at 0.19.2.0 and carried as T44.

**Measured against `mavo-site` 4.27.1.1 on 2026-08-17: it maps.**
`src/mavosite/contract.py` carries `SLUG_ALIASES = {"kyiv": "kyiv-oblast"}`,
resolved in `canonical_slug`, held by a test named
`test_the_kyiv_alias_is_the_only_divergence` in that repository's contract
suite, green. Named without the `file::test` form on purpose: the gate's
citation resolver looks for cited tests **in this tree**, and a citation it
would try and fail to resolve is worse than a prose name, because the failure
would be read as a missing test rather than as a test in another repository. T44's first half is met and the correction above had itself gone stale
by eleven of the consumer's releases before anybody read it again, which is
**F100**.

**What this release did not fix.** MAVO publishes no raion centroids, so every
marker is drawn at oblast scale with an uncertainty ellipse the size of the
oblast. Two raions under alert in one oblast render as one marker. That is
honest and it is also coarse; the fix is a centroid column beside the distance
column, and it is recorded as a task rather than done here.

### F75, 0.19.0.0. The terminal announced a schema version the file did not carry

`mavo report --json` printed `contract=<path> v=1` from a literal. The literal
was correct the day it was written and became false in the same release that
bumped the schema to v2, so the command wrote a v2 file and told its operator
it had written a v1 one.

Found by the operator running the release smoke test and reading the output,
which is the only reason it was caught before the tag: no test asserted on
that line, and the file itself was correct, so every other check passed.

Class: **a number copied out of its source of truth**, the family of F36 and
F64. The distinctive part here is the timing: the copy was accurate when made,
and the defect was created later by a change somewhere else entirely. A
constant duplicated into a message has a shelf life nobody writes down.

**Repair.** The message reads `SCHEMA_VERSION`, and a regression asserts that
the version in the printed line equals the version in the file on disk rather
than equalling any particular number. Verified red against a scratch copy with
the literal restored.

### F76, 0.19.2.0. The trailing counter measured how finely an oblast is subdivided

`trailing_counts` added one per transition into ACTIVE. The channel declares
alerts per raion, and a western episode lights every raion in an oblast at
once: 22 of the 81 western episodes in the design window touched all 36
western raions simultaneously. Measured on the shipped code: one episode over
Lviv oblast produced `alerts_count: 7`, one per raion in the map.

The consumer shades each oblast by that count. The map would therefore have
rendered administrative subdivision as intensity, and oblasts with more raions
would have been systematically darker, on a page whose whole purpose is to
show where the activity is.

**Why it survived.** The docstring stated the right intent - "how busy has
this oblast been" - and the regression beside it used **one raion**, so the
mutation that should have caught it had nothing to bite. This is the second
time in one sprint that a test passed because its data could not distinguish
the correct implementation from the wrong one; the first was the distance
sort, where the two orderings agreed on the pair chosen. A test whose data is
picked for convenience is a test whose data is picked by the implementation.

Class: **an instrument reporting its own framing as a property of the
material** (F59, F70, F71), with the unit of the count and the unit of the
event silently different.

**Repair.** An episode opens when an oblast goes from no active raion to one
and closes when the last is affirmatively cleared. `UNKNOWN` does not close an
episode, because silence is not an all-clear inside a counter any more than
anywhere else; an episode left open by an outage stays open, which is
conservative in the direction that does not understate. Held by four
regressions, three mutation-verified.

### F77, 0.19.2.0. The regression file claimed a verification it had not had

`tests/test_sprint10.py` opened with: "Each was verified red on a scratch copy
carrying the mutation named in its docstring." Counted at the moment it was
questioned: 40 tests, 22 naming a mutation, 13 actually run against one. The
sentence was written before any verification had happened, and was not revised
as tests were added over three releases.

This is the defect this repository exists to attack, in the file whose subject
is that a test which cannot fail is worthless. It cost nothing operationally
and everything in standing: every mutation-verification claim in the project
now needs to be read as a claim rather than a record, which is exactly the
suspicion an unearned assurance buys.

Class: **a claim about the tree that nothing compared against the tree** -
F73's family, aimed at the test suite instead of the README.

**Repair.** The header now says precisely which tests are mutation-verified
(those naming a mutation) and that the rest are ordinary regressions claiming
nothing more. No blanket assurance replaces it, because the honest version of
that sentence is a list, and the list is the docstrings.

## Cost of composing a report, 2026-08-10

`compose()` replays the whole event store on every call, and `mavo report
--watch` calls it once per interval. Measured [measured, Python 3.12.3, this
container, synthetic store, 120 areas]:

| Events in store | Time to compose |
| --- | --- |
| 5,000 | 57 ms |
| 20,000 | 211 ms |
| 60,000 | 723 ms |

Linear, 12.7x for 12x the events. At a 60 s interval this is not close to
binding today, and it is a curve rather than a constant: the store grows
monotonically and nothing prunes it. Recorded as a number rather than a
worry so the day it matters is visible before it arrives, and so that a claim
about end-to-end latency (D-018, T40) has this term in it rather than assuming
it away.

**What would change the shape.** A snapshot the loop reads instead of a full
replay, or a store that answers "current state per area" directly. Both are
work this project has no measurement to justify yet, which is why neither is
here.


### F78, 0.19.3.0. The missile stem was one letter too long for half its forms

Found while testing the F71 repair rather than by the measurement that
prompted it. `балістик` matches the noun the channel writes in
`Загроза балістики`, and misses the adjective in
`Загроза застосування балістичного озброєння`, because the stems diverge at
the eighth character. The declaration resolved to no kind and the message was
refused.

This sat underneath F71 and was invisible to it: the coverage run counted
MISSILE at 25 declarations and the obvious explanation, the missing short
declare form, was sufficient to account for a figure that low. A second cause
producing the same symptom does not show up in a number, only in the texts.

Class: **a pattern written from one example of a word**, the family of F23,
where the shipped area table searched a vocabulary the channel does not use.

**Repair.** `баліст`, which carries both forms. Held by
`tests/test_sprint11.py`, verified red against a scratch copy with the longer
stem restored.

**What it does not fix.** How many other kind markers have the same problem is
unknown: `ракет`, `бпла`, `шахед`, `каб`, `авіабомб` and the two artillery
stems were each written from one or two forms. T45 is the measurement, and the
near-miss review is the part of it that would find this class again.

## Threat-kind coverage after the F71 repair, 2026-08-10

Second run of `tools/kind_coverage.py --raw data/raw --sample 30` against the
same corpus that produced the baseline: 61,041 messages, the acceptance
recorded in T45. Both runs are on the operator's machine, Python 3.14.6.

| Quantity | Before (F71) | After the repair | Provenance |
| --- | --- | --- | --- |
| Declarations | 2,392 | 4,576 | measured |
| Lifts | 993 | 1,460 | measured |
| Still unparsed | 4,447 | 1,959 | measured |
| MISSILE | 25 | **242** | measured |
| DRONE | 1,492 | 2,756 | measured |
| GLIDE_BOMB | 1,868 | 2,104 | measured |
| ARTILLERY | no member existed | 934 | measured |
| Coverage, 1 h TTL | 0.128 | **0.196** | measured |
| `join_coverage`, 1 h TTL | 0.104 | **0.170** | measured |
| UNKNOWN after the join | 36,697 of 42,910 | 29,400 of 42,733 | measured |
| Near misses | 2,957 | 1,593 | measured |
| Declaration to lift, minutes | n=790, median 97 | n=1,223, median 96, p90 674 | measured |

**TTL is still not the binding constraint.** Coverage reads 0.196 at every
window from one hour to twenty-four. The parser's reach binds, exactly as at
the first measurement, and the figure that moved is the one the repair
touched.

**The missile regime is visible again.** 242 declarations against 25. The rule
that passes its own regime gate at 7 of 7 was previously invisible to the join
on 99% of the occasions it applied.

**What the near-miss pile said, which is worth more than the coverage
figure.** Three patterns, all measured rather than guessed:

1. **The channel lifts a threat in at least four phrasings** and the table
   listed one. `Відбій атаки дронів-камікадзе`, `Відбій атак дронів`, and
   `Відбій по КАБам` were all being dropped. Widened to `відбій` at 0.19.4.0.
2. **A declaration without a verb.** `КАБи 9677 на КРАМАТОРСЬК`,
   `каб напрямок Краматорськ`: the Donetsk-facing traffic announces a means
   with no declaration word at all. Catching it means treating the name of a
   munition as a declaration, which is a different kind of decision and is not
   taken here.
3. **The artillery near misses are not a kind-table problem.** `Загроза
   артобстрілу` over `Покровська територіальна громада` carries both a
   declare marker and a kind; it fails because that tag is not in the 127-row
   map.

   **Correction, 0.32.0.0.** This paragraph filed that under T34 and T34 is a
   different population: the 321 design-window messages carrying **no tag at
   all**. These carry a tag the map does not hold, which has a different cause
   - the map is built from the design window while the corpus runs 19 days
   longer - and a different repair. No task covered it, so the work read as
   scheduled for five sprints while nothing was pointed at it. T59 now does,
   and `tools/unmapped_tags.py` measures the size of it before anything is
   decided.

**The inversion that a coverage improvement would have bought.** The obvious
next step is adding `атак` so `Атака ударних БПЛА` resolves. Measured against
the near-miss pile: `Відбій атаки дронів-камікадзе` contains `атак` and, with
the old narrow lift marker, no lift phrase. Every lift of that shape would
have become a fresh DECLARED, an alarm raised by the message announcing its
end. It is refused today only because `атака дрон` does not match `атаки
дронів`, which is an accident of declension rather than a control.

Order therefore matters and is now stated as a rule: **the lift table is
widened before the declare table, never after.** The declare extension is not
in 0.19.4.0; it needs its own run, with this table as the new baseline.

**`небезпека` is dead, confirmed twice.** Zero hits at the first measurement
and zero again after a substantially different table. Removed rather than kept
as a hedge: a marker that has never matched anything is a claim about the
channel that the channel has refused 61,041 times.

## Border column, independent verification, 2026-08-10

S8 asks for the distance column to be spot-checked by hand before it is
trusted anywhere. It has been checked three ways, and the three answer
different questions.

| Check | Result | What it rules out |
| --- | --- | --- |
| Independent geometry and method: OSM-derived oblast outlines, WGS84 geodesic (geographiclib), 2026-08-10 | Lviv 57.2, Lutsk 85.4, Uzhhorod 51.6 km, each within 1.1 km of the column | A wrong method, and a wrong source |
| Independent simplification: the same Natural Earth 10m outline as simplified for the companion site, 1,039 vertices against this repository's 1,332 | Maximum divergence over the four spot-check points **0.04 km** | The column being sensitive to how the outline is simplified |
| Positional error of the source itself: 183 shared border vertices against OSM | median 0.0, p95 1.6, maximum 2.6 km | Nothing. This is the floor the column cannot do better than |

**What is therefore established.** The arithmetic is right, the sphere is not
the problem (worst case +0.31% at Kyiv, +1.4 km on 452 km), and the choice of
simplification costs two orders of magnitude less than the source's own
positional error. **The remaining uncertainty is the source's**, at roughly a
kilometre, and it is stated wherever the column is quoted.

**What is not established, and it is the part S8 actually cares about.** Every
check above tests distance from a *point*. The column publishes an interval
because the question is the distance to an area's nearest *edge*, and the
interval is derived from a disc of equal area rather than from the polygon.
For the border raions the interval reaches zero and is correct by
construction; for an oddly shaped raion it is an approximation nobody has
measured against real geometry. That measurement needs raion polygons with
register codes, which is T43's neighbourhood and is not in reach here.

## Hand-checked report sample, 2026-08-10, and its limits

The twenty real channel messages this repository has carried since sprint 4,
each rendered as the report would render it, and each judged by hand on the
three things S8 names.

| Dimension | Errors | Rate | Wilson 95% |
| --- | --- | --- | --- |
| Area | 0 of 20 | 0.0% | [0.0%, 16.1%] |
| Means | 0 of 20 | 0.0% | [0.0%, 16.1%] |
| Distance interval | 0 of 20 | 0.0% | [0.0%, 16.1%] |
| **Whole row** | **0 of 20** | **0.0%** | **[0.0%, 16.1%]** |

**This does not close S8, and saying it does would be the defect this
repository logs about other people.** Three reasons, each disqualifying on its
own:

1. **Not one western area in it.** All twenty resolve to Kharkiv,
   Dnipropetrovsk, Zaporizhzhia or Sumy: the 96.5% of traffic this product
   filters *out*. The distance intervals it judged are 700 to 1,000 km wide
   cases where an error of tens of kilometres is invisible. The intervals that
   matter are the ones reaching zero at the border, and none was tested.
2. **Twenty-six minutes of one afternoon.** The messages run 15:44 to 16:10 on
   one day, so they are not independent draws and several are the same
   announcement for neighbouring raions.
3. **The interval says almost nothing.** Zero errors in twenty bounds the true
   rate below 16%, which is compatible with a report wrong on one row in
   seven.

**What closes S8** is `tools/label_sample.py draw` against the design window,
fifty rows across both strata with western areas represented, scored with the
whole-row rate. The instrument now carries the three verdict columns S8 asks
for, and the whole-row figure exists because a reader sees one line rather
than three fields: a row is wrong if any of the three is.

### F79, 0.20.1.0. The reviews kept happening and stopped being filed

`docs/reviews/` is described in four documents as holding one review per
release. Counted on 2026-08-10: **nine files against fifty releases**, the most
recent for 0.11.1.0, with nineteen releases since.

The obvious reading is that the practice lapsed. It did not. Reviews were
carried out on 0.13.0.0 (items A1 to A13, with the border measurements that
moved three spot-check values from recited to measured), on 0.15.0.0, on
0.16.0.0, and on 0.20.0.0. Every one of them was written, and every one of them
became a session artifact outside the tree. **The work continued; the record of
it stopped**, and the four documents describing the record kept describing what
it was supposed to be.

**Why it survived.** `check_every_document_is_pinned` compares the set of files
in `docs/` against the pins in `STATUS.json`, so it notices a review that
exists and is unpinned. Nothing compared the number of reviews against the
number of releases, because that claim lived in prose in four documents and
prose is what every check in this gate is careful not to read.

Class: **class 1, a document describing a tree that has moved on**, and F73's
family specifically: a claim about the repository's own practice, in the
documents a reader trusts first.

**What makes this one worse than F73.** The claim was not merely stale. It
described a discipline the project uses to argue for its own reliability, in a
README that a reviewer reads before deciding whether to believe anything else
in it. Nine of fifty is not a lapse in bookkeeping; it is the difference
between "reviewed before every push" and "reviewed sometimes, filed rarely".

**Repair, three parts.** The rule is narrowed to one review per **major**
release and recorded as D-021, because one per release at five releases in an
afternoon is a rule that cannot be followed and therefore is not one.
`check_major_releases_carry_a_review` fails the gate on a major with no file,
with the twelve historical exceptions as a frozen list rather than a cutoff
date, since a cutoff is how the first nineteen accumulated. And the three
reviews that were written are filed, unedited, each carrying a note saying when
it was actually done.

**What is not repaired and cannot be.** Twelve major releases have no review
and never will. `docs/reviews/README.md` names them. Writing one now from the
changelog would assert that a tree was examined when it was not, and a
fabricated review is worse than an absent one: the absent one is visible.

### F80, 0.21.2.0. A fabricated detail and an overstated adjective, in the document written to be believed

Two defects in `docs/BRIEF.md` and `docs/BRIEF-PL.md`, found within an hour of
those documents being written, by the operator asking where a claim came from.

**A specific incident, unsourced, and with the wrong number in it.** The
section on where the project came from opened with a date, a voivodeship and a
duration, in the register of settled fact and with no provenance label, in a
document whose header promises every number carries one.

**The first repair was to delete it. That was half right and the second half
matters more.** Checked against reporting on 2026-08-10, the incident is real
and well documented: a Kh-101 cruise missile entered Polish airspace on the
night of 29 to 30 July 2026 during a mass attack on Ukraine, was detected at
03:40, was lost from radar at 03:46, and came down near Tarnawa-Kolonia in
Lubelskie about a hundred kilometres inside the country.

**The duration was wrong.** The brief said thirteen minutes. The reported
interval is **six**. No source supports thirteen, and the figure had been
carried in this repository since it was first written: it is in **D-015**, the
decision that defines what this project is, and in the T39/T40 latency thread
where it frames how much room a measurement has to fit into. Both are corrected
at 0.21.2.0.

**This is worse than the fabrication it was first classified as.** A detail
nobody can source is visible once somebody asks. A true event carrying a
number that is wrong by a factor of two travels, gets cited by the decision it
supports, and reads as verified because everything around it is. Deleting it
would have removed the visible copy and left the two load-bearing ones in
place.

**The correction strengthens what it corrects.** Six minutes is less room than
thirteen, so D-015's argument holds harder, and the same reporting supplies the
mechanism D-015 could only assert: Ukrainian fighters pursued the missiles to
the border and their radar signature was difficult to separate from the
missiles, which delayed identification. That is the unobservable this project
declines to predict, described by the people watching it.

**"Checked three independent ways."** `docs/METHODOLOGY.md` says "checked three
ways, and the three answer different questions": one independent source, one
re-check of the same outline simplified differently, and one measurement of the
source's own error whose row states it rules out nothing. The brief compressed
that into three independent confirmations, which is a stronger claim than the
section it summarised.

**A third, smaller, and it is the one a check can catch.** Both briefs said "34
open items" while the backlog held 35, because a task was added between writing
and reading. `docs/reviews/0.21.0.0.md` had recorded, in the release before,
that nothing compares the two language versions and that this is a concrete
risk. The risk materialised at the next change.

**Why all three arrived together.** Prose for people is the one surface in this
repository with no reader in the gate, and it is also the surface where the
goal changes from being correct to being understood. Those pull in opposite
directions: a specific date reads better than "in the period observed", and
"three independent ways" reads better than "three ways answering different
questions". Every other artifact here has something that punishes the more
persuasive phrasing. A brief has nothing.

Class: **class 1 in the one place where class 1 is least visible.** F73 and F79
were documents describing a tree that had moved on; this is a document
describing a tree that never was.

**Repair.** The incident is removed rather than sourced. The three-ways claim
is restated as the methodology states it, naming which of the three is
independent and which is a floor. The item count is removed entirely rather
than pinned, because a figure that changes weekly does not belong in a document
nobody re-reads weekly. `tools/brief_check.py` compares the figures the two
briefs share and their pinned values, and it is deliberately narrow: it reads
whole numbers of four digits or more, because Polish decimal commas and English
decimal points are the same figure in two unmatchable spellings and the first
run produced three false positives inside a minute.

**What no check will catch, stated so nobody assumes otherwise.** A fabricated
date and an overstated adjective are not reachable by any heuristic worth
having. They were caught by a person asking where a claim came from, and that
is the only mechanism that works here. This is an argument for reviewing prose
by reading it, not for building a weak check and feeling covered.

### F81, 0.21.4.0. The corpus total counted 199 posts twice

`corpus_inventory` summed the message count per snapshot file. Two backfill
runs produced snapshots on different offsets over the same posts:
`page-000321631-000321650.html` beside `page-000321650-000321669.html`, ten such
pairs running from post 321631 to 321829. Every post in that range sits in two
files and was counted in both.

**199 posts, and the arithmetic closes.** The inventory reports 61,240;
`tools/kind_coverage.py`, which reads posts rather than files, reported
**61,041** on the same corpus. 61,240 minus 199 is 61,041. Two tools counting
the same thing differed by exactly the size of the overlap, and the difference
sat unexamined in both outputs.

**Where the wrong number went.** `STATUS.json`, the README's at-a-glance table,
both briefs, `docs/CHANNEL.md`, and the denominator of anything expressed as a
share of the corpus.

**What limits the damage, stated because it is real and because it is not a
defence.** Every duplicated post is above 309380, so all of it is in the
holdout. The design window is untouched, no measurement taken so far used a
duplicated post, and the coverage figures are unaffected because the tool that
produced them was already counting posts. What is affected is the size of the
corpus as advertised, which is a claim this project makes about how much
evidence it has.

**Why it survived.** The inventory checks that a filename agrees with the
content it names, and every one of these files passes that check: each is
internally consistent, and the problem exists only between files. A snapshot
set was treated as a partition without anything testing that it is one.
Contiguity was checked; disjointness was not.

Class: **an aggregate over a set nobody checked was a set** - the family of
F70, where one counter served two different events.

**Repair.** The count is over distinct post ids. Duplicated ids are reported as
a problem rather than silently deduplicated, because a corpus holding the same
post in two files is a thing an operator should know about even after the
number is right. `new_messages` is a per-snapshot column so the CSV shows which
file first contributed each post.

**What still needs doing on the operator's machine:** re-run the inventory,
which will produce the corrected total and the duplicate report, and correct
`STATUS.json` and every document quoting the old figure. Until then the number
in this repository is 199 too high and is known to be.

### F82, 0.21.4.0. The labelling instrument showed one area where the message named five

The first real draw for T36 produced 50 rows, and **4 of the 40 resolved rows
were messages naming five raions each**: `Повітряна тривога в` followed by a
bulleted list, with five hashtags. The instrument printed only the first area,
so a labeller judging `area_ok` would have been judging a rendering the product
does not produce. `classify` emits one event per mention, so the report shows
all five.

Not a defect in the product, and a defect in the measurement of it, which is
the same seriousness: a hand-labelled error rate is only worth the fidelity of
what was put in front of the hand.

**Found because the sample was read before it was filled in.** The figures in
the draw's own output said nothing about this. It is visible only in the
messages.

**Repair.** Every named area is shown, with its own distance interval, and a
message naming any western area counts as western for stratification: it is one
this product would report on whatever else it also names.

### The first draw, and what it says about stratification

Recorded because it is the evidence for the change in 0.21.3.0 rather than an
argument for it.

Drawn proportionally from the design window: 42,854 resolved messages, 409 with
unresolved tags, 633 pages refused above the holdout boundary. Fifty rows, 40
resolved.

**Not one western area among the 40.** Kharkiv, Chernihiv, Dnipropetrovsk,
Sumy, Odesa, Zaporizhzhia, Mykolaiv, Poltava, Cherkasy. The estimate before
drawing was one or two; the draw returned zero, which is what a 3.5% share does
to a sample of forty.

**All ten unresolved-tag rows were the same tag**,
`Покровська_територіальна_громада`. If that holds across the 409, then T34 is
not a tail of unresolved tags: it is one tag that the register answers four
ways, and the cost of the refusal is concentrated rather than spread.

### F83, 0.21.5.0. The cause of blindness was printed only on the path nobody runs

`publish()` printed the exception that made a cycle blind under
`if on_cycle is None`, and `mavo report --watch` - the one production entry to
this loop - installs `announce` unconditionally. So in the mode an operator
actually runs, every blind cycle said `feed=blind` and the reason went nowhere;
the diagnostic existed only for a bare-library caller that does not exist.

**Why it survived.** The loop's tests exercise blindness through the library
call, most of them without a callback, which is exactly the configuration
where the message printed. A test that installed a callback and asserted the
message would have been red from the day the guard was written.

**Class.** A rule without a reader, in code rather than prose: the guard
encoded "do not interleave with the announcer's stdout" and delivered "tell
nobody". The repair prints unconditionally, on stderr, so a redirected stdout
still carries only announcements. Regression:
`test_the_blind_cause_is_printed_even_when_a_callback_is_installed`.

### F84, 0.21.5.0. A broken observer could stop the heartbeat

`on_cycle` was called bare. `announce` prints to stdout; a reader that closes
the pipe turns that print into `BrokenPipeError`, which propagated out of
`publish()` as a stack trace with no `PublishReport` - F46's shape,
reintroduced through the observability hook - and stopped the contract file a
consumer depends on because a console listener went away.

**Why it survived.** Every callback in the suite was a lambda that could not
fail. The observer was treated as infrastructure and tested as a constant.

**Repair, and the decision inside it.** The observer is not the product; the
file is. A callback that raises is disabled for the rest of the run, the
failure is printed to stderr and counted in `PublishReport.callback_failures`,
and publishing continues. The alternative - stopping with a named reason - was
rejected because it converts a cosmetic failure into the exact silence the
loop exists to prevent. `KeyboardInterrupt` is deliberately not caught there:
an operator interrupt during a callback is still an operator interrupt.
Reopen condition: if an operator is ever observed treating a quiet console as
a healthy loop the trade-off inverts, and the counter this repair added is how
that observation would be made. Regression:
`test_a_broken_callback_does_not_stop_the_heartbeat`.

### F85, 0.21.5.0. The trailing counter lost the episode that outlived the window

`trailing_counts` filtered events to the last seven days before folding. An
episode opened before the cutoff had its opening aged out of the fold, so an
oblast under one continuous alert longer than the window rendered as the
quietest on the map, and an all-clear falling inside the window closed an
episode the fold had never seen, so `last_alert_ended_at` went unrecorded.
This broke the module's own stated invariant, standing since F76: an episode
left open stays open, and the count does not understate.

**Why it survived.** The cutoff regression's fixture was a single un-cleared
ACTIVE thirty days old, asserted to count zero - which is precisely the
open-at-the-edge case the counter was wrong about. Test data chosen by the
implementation, measuring the code against itself: the same failure the F76
entry describes in its own regression, one release earlier.

**Repair.** The fold replays the whole log. Events before the cutoff move the
running state without counting; an episode still open as the window begins is
counted once as it crosses; only an episode both opened and affirmatively
closed before the window is outside it. **The claim that stood here until 0.22.0.0 -
that `recent_7d` counts "can move only upward under this change" - is
withdrawn as false, and the counterexample is F91.** The fold changes the
count in both directions, and which direction depends on the shape of the
episode at the window's edge.

The old fixture is replaced by
the correct guard, an episode opened *and closed* before the window.
Regressions: `test_an_episode_open_at_the_window_edge_still_counts`,
`test_an_episode_straddling_the_edge_records_its_close`,
`test_an_episode_closed_before_the_window_does_not_count`.

### F86, 0.21.5.0. The alert path picked a threat kind by dict insertion order

`classify_message` resolved the kind with a first-match `next()` over
`KIND_MARKERS`, so an alert naming missiles and drones together classified as
whichever marker happened to be defined earlier in the table. Three functions
up, `classify_kind_message` refuses the same ambiguity outright. One
repository, two answers to one question, and the deciding vote held by the
order rows were typed in: a reordering of the marker table - a pure
refactoring by every other measure - would have silently changed
classifications.

**Why it survived.** No test fed the alert path a two-kind message; the
refusal tests all target the kind path, where the refusal existed.

**Repair.** The alert path collects the set of named kinds and resolves only
when it has exactly one, `UNKNOWN` otherwise - the same refusal, now made in
both places. A message naming one means in two forms (`балістика` beside
`ракета`) still resolves, because both rows name the same kind. How often the
design window carries genuinely two-kind alerts is not measured here and is
folded into T45's second `kind_coverage` run. Regression:
`test_an_alert_naming_two_kinds_reports_unknown_rather_than_the_first_row`.

### F87, 0.21.5.0. The fingerprint promised a comparison that did not exist

The `label_sample` docstring promised from its first version that `score`
recomputes the draw's fingerprint "and a mismatch is reported rather than
tolerated". Nothing implemented the comparison: `draw` printed a hash to a
terminal, the hash was stored nowhere, and `score` printed a second hash with
nothing to compare it against. Beside it, the `post_id` column held a row
number 1..N while the docstring said the fingerprint covers "the sampled post
ids", and the channel's real ids - present in every block's `data-post`
anchor - were discarded, so a sampled row was traceable only to a text prefix.

**Why it survived.** T36 has never been scored, so the score path has never
run against a real file, and the promise was checked by nobody because its
reader was the future. The 0.21.4.0 handover names this class six times in
one session: a rule written down and enforced by nothing is a preference.

**Repair.** `draw` writes a draw record beside the CSV - seed, fingerprint
over the sampled post ids, stratum counts - and `score` recomputes the hash
from the file and refuses a mismatch against the record. A file without a
record scores with a loud warning that the draw cannot be verified. The
`post_id` column carries the channel's own ids. The sample a given seed draws
is unchanged, so the handover's seed 20260810 remains valid; the fingerprint
value differs from what an earlier draw printed, because it now hashes what
the docstring always said it hashed. Also made visible: messages that resolve
an area and are then refused by `classify` were silently dropped from the
population, and are now counted in the draw output. Regressions in
`tests/test_label_sample.py`.

### F88, 0.21.5.0. A post repeated inside one file was counted twice, twice

The F81 repair counted the corpus over distinct post ids across files, and
left the same defect one file inward: `messages` per snapshot was `len(ids)`
over every occurrence, and `new_messages` asked which file first carried each
post - a test every repetition *within* that file passes. A page that repeats
a `data-post` id would inflate both columns with nothing said.

**Why it survived.** No live page has been observed doing this; the defect is
latent, the same standing F62 had when the transport's `file://` acceptance
was closed. It was found by reading the repair for the case beside the one it
fixed. Contiguity was checked, cross-file disjointness was checked at
0.21.4.0, and within-file uniqueness completed the set nobody had named.

**Repair.** Ids are deduplicated per file with order kept, and the repetition
is reported as a problem rather than absorbed, matching F81's rule that a
duplicate is a thing an operator hears about even after the number is right.
Regression:
`test_a_post_repeated_inside_one_file_is_counted_once_and_reported`.

### F89, 0.21.6.0. The discrepancy had an explanation, and the explanation was wrong

Two numbers for the size of one corpus sat in this repository for months:
the inventory's 61,240 and `kind_coverage`'s 61,041. F81 records that neither
was questioned. That entry is incomplete, and the missing half is the more
useful one: **the gap was not unnoticed, it was reconciled.** The kind-coverage
section of this document said "61,240 messages ... 61,041 messages carried
parseable text", which makes 61,041 a subset of 61,240 defined by
parseability, and 199 the count of messages with no readable text.

Both halves of that sentence are false. `kind_coverage` keys its message map by
post id, so it had always counted distinct posts and never occurrences; 61,041
*is* the total, not a subset of one. And the number of posts carrying no
parseable text is zero `[inference, 2026-08-11]`: `kind_coverage` counts posts
that carry a text div and reported 61,041, the inventory counts distinct posts
and reported 61,041, and both ran over the same corpus at the same digest, so
the difference between them is zero. **That is reasoning from two totals, not a
count of unparseable posts, and it was labelled "measured" here until
0.22.0.0** - inside the entry whose own subject is an inference recorded in the
position of a measurement. See F92. The measurement that would replace it is
one `kind_coverage` run reporting its own skipped count.

**Why this is the more serious half of F81.** An unnoticed discrepancy is
found by the first person who lines the numbers up. A discrepancy with a
plausible explanation beside it is not found at all: the explanation is what
stops anyone from lining them up again. The sentence was written in good
faith - a reader who sees 61,240 and 61,041 and knows some pages carry
non-text posts will reach for exactly this reconciliation - and it was never
checked against the tool it described.

**Class: an inference recorded in the position of a measurement.** The figure
carried no provenance label, so nothing in the document said the subset
relationship was reasoned rather than counted. The repository's own rule
covers this and the rule was not applied here.

**Repair.** The paragraph states the corrected figure, names all 61,041 posts
as carrying parseable text, and records what it used to say, because deleting
the wrong sentence would leave the correction unexplained - the third pattern
from the 0.21.4.0 handover. The corrected total is now measured on the
operator's machine: 3,062 pages, 61,041 distinct posts, 199 posts in more than
one snapshot across 20 files, digest `sha256:10266cbf...` unchanged from the
figure already in `STATUS.json`. **The digest not moving is the load-bearing
part**: this is the same corpus counted correctly, not a different corpus.

**Also measured, and null:** no snapshot repeats a post id inside itself. F88
is closed on the real corpus and stays latent rather than becoming a second
finding.

### F90, 0.22.0.0. The live path never reached the table that fixed F23

Sprint 7 replaced the oblast-stem area table with the 127-row register map and
closed F23 in the code. It did not close it in the product. `classify_message`
kept `areas: AreaTable | None = None` with the old dict behind the `None`
branch, and `probe()` - which is the whole live path, the thing `mavo collect`
runs - constructed its source without passing one. **Every live poll from
sprint 7 to 0.22.0.0 ran the sprint 6 implementation.** The register table was
opt-in and the superseded table was the default.

**The tripwire was wired to the same wrong path.** Two tests pinned the failure
as assertions, deliberately, so that F23 could not be fixed quietly:

    assert matched == 0, "area table now matches; update this pin and close F23"
    assert classified == 0, "classifier now matches; update this pin and close F23"

Both called `classify(message)` with no table. They were built to go red the
moment the gazetteer landed; the gazetteer landed and they stayed green,
because they measured the branch the repair did not touch. **An assertion that
pins the wrong call shape does not merely fail to catch a defect, it certifies
its absence** - and it was cited in the README, the limitations list and the
licence disclaimer as the reason to trust that the number could not drift
quietly.

**What the true numbers are**, measured against the same twenty real messages
that have been in this repository since sprint 4: **20 of 20 resolve their area
to a unique register code**, **15 of 20 classify as alerts**, and the remaining
**5 carry no alert-state marker because they are threat declarations**, which
belong to the kind stream. 15 and 5 are disjoint and sum to 20 - and both
numbers were already pinned separately in `STATUS.json`, beside the 0, for
three releases.

**Why it survived.** Every reader of the 0 had a reason not to question it. It
agreed with a documented defect (F23), it agreed with the observed behaviour of
`mavo collect`, and it was pinned by an assertion whose message promised to
announce its own obsolescence. The symptom the README described was real; only
the cause was wrong, and a correct symptom is the strongest possible cover for
a wrong diagnosis. This is F89's shape one layer down: not a discrepancy with a
false explanation, but a *defect* with a false explanation.

**Class: a superseded implementation left reachable as a default.** The repair
removes rather than guards. `AREAS` is deleted, `None` now means "load the
shipped table", and forgetting the argument costs a CSV read rather than two
sprints of capability. The same missing default silenced the kind stream in
`classify_kind_message` and is closed with it.

**A fourth finding fell out of the repair, and it is the one to carry forward.**
Fixing the wiring turned seven tests red, and every one of them was red for the
same reason: `PAGE`, the A12 attack page and the F50 pairing fixture were
written as oblast prose - `Львівська область<br/>Повітряна тривога`, no
hashtag. **The channel does not emit that shape.** 99.34% of its messages carry
a `#Name_unit` tag and an oblast name appears in 515 of 69,676 occurrences. The
fixtures had been written to match the implementation, so the suite measured
the parser against its own assumption and went on passing while the live path
parsed nothing. That is the third instance this session, after F85's cutoff
fixture and F82's sample, and the count is the point: **it is the dominant
failure mode in this repository**, ahead of any parsing or arithmetic error.
Regressions: `test_every_real_message_resolves_its_area_against_the_register`,
`test_the_live_path_classifies_the_alert_messages_it_is_given`,
`test_probe_uses_the_register_table_and_not_the_superseded_dict`.



### F91, 0.22.0.0. The F85 entry claimed a direction the fold does not have

F85 replaced the trailing counter's event filter with a two-phase fold, and the
entry, the 0.21.5.0 changelog and the commit message that carries it all state
that consumer-visible `recent_7d` counts "can move only upward under this
change". **They can move down.** Measured on the operator's machine, 2026-08-11,
against `v0.21.2.0` in a worktree and `main` side by side, printing
`mavo.report.__file__` from each so the comparison could not silently read one
tree twice:

| Tree | `alerts_count` for `lviv` |
| --- | --- |
| pre-F85 (`d988094`) | **2** |
| post-F85 (`1bca4ff`) | **1** |

The scenario: Sambir raion opens ten days before `as_of` and never clears;
inside the seven-day window Lviv raion, the same oblast, runs ACTIVE, CLEAR,
ACTIVE. The old fold dropped the pre-window event, so the oblast's running set
was empty at the window's start and each in-window ACTIVE opened a fresh
episode: two. The new fold carries Sambir across the boundary, so the running
set is never empty, the oblast never stops being under alert, and everything
folds into the one carried episode: one.

**Which count is right is a separate question and it is now open.** One is
defensible on the definition `alerts_count` claims - episodes at oblast level -
and the entry does not assert it is correct, only that the direction claim was
false.

**Why it survived.** All three regressions written for F85 used a single area
per oblast. With one area there is no case where a carried episode absorbs an
in-window one, so the fixtures could not express the failure. **Test data that
cannot express the failure it is checking for**, which is the fourth instance of
that class in one session after F82, F85's own fixture and F90's three.

**Class: a property asserted from a worked example.** One boundary case was
reasoned through, the conclusion was generalised to a direction, and it went
into a changelog and a commit message without a second case being tried. The
repair states the both-directions behaviour and adds the two-area regression:
`test_a_carried_episode_absorbs_an_in_window_one`.

### F92, 0.22.0.0. An inference labelled measured, in the entry about inferences labelled measured

F89 records that the corpus discrepancy survived because a plausible
explanation sat beside it, and names the class: an inference recorded in the
position of a measurement, carrying no provenance label. The entry then wrote
that the number of posts with no parseable text is zero, **"measured
2026-08-11 on the same corpus and the same digest"**.

It was not measured. It is a subtraction of two totals that happen to be equal,
made by someone with no access to `data/raw` - the corpus is excluded from every
package by design, so the run that sentence describes could not have happened.
The conclusion is probably true and the reasoning is sound. The label was
invented.

**Why it survived to a push.** It was written in the same pass as the entry
whose subject it violates, which is the condition under which a rule is least
likely to be applied: the rule was being *described* rather than used, and
describing a rule feels like complying with it.

**Class: the same one F89 names, one layer up.** The repair relabels the claim
`[inference, 2026-08-11]`, states the two totals it comes from, and names the
measurement that would replace it - one `kind_coverage` run reporting its own
skipped count, which nothing currently prints.

**A rule that follows from having this happen twice in two releases.** A
provenance label written in the same session as the claim it labels has not
been checked by anybody. It is not clear what mechanism would catch that, and
no mechanism is invented here; the failure is recorded so the next occurrence
is the third rather than the first.

### F93, 0.22.0.0. shipped_sprints means a test file exists, and the status line read it as sprints completed

The README's status paragraph said "Sprints 0 to 6 shipped" while
`STATUS.json` listed nine. The 0.22.0.0 review treated that as a stale
sentence, rewrote the README to say nine, and added a gate check binding the
two. **The semantics of the field were never read.**

`check_every_shipped_sprint_has_a_regression_file` is the only consumer, and
what it verifies is that `tests/test_sprintN.py` exists. `shipped_sprints`
therefore means *a sprint's code landed with regressions*, not *a sprint met
its exit criterion*. `docs/MVP.md` is explicit that S8 is partial and that S9's
criterion - 72 hours unattended plus a first end-to-end latency distribution -
is unmet; no command in the CLI polls the channel in a loop, so S9 could not
have met it.

Three things were wrong at once, and the third is the one worth keeping:

- **"Sprints 0 to 9 shipped" reads as nine sprints completed** and means nine
  sprints have test files. One word doing two jobs.
- **"Three sprints from beta" is arithmetic on the wrong set.** Five sprints
  were named, S7 closed, so **four** remain: S8's open half, S9, S10, S11.
- **A gate check was added that enforces the misleading sentence.** Faced with
  two disagreeing numbers, the repair changed the document to match the field
  and then built a reader to keep them matching - without establishing which
  was true. That is worse than the drift it was fixing: drift is visible, an
  enforced agreement between a true value and a false reading is not.

**Class: agreement mistaken for correctness.** F81 and F89 are about
contradictions that nobody compared. This is the opposite failure and it was
produced *by* the fix for those: two numbers were compared, made to agree, and
neither was checked against what it meant.

**Repair.** The status line states both quantities separately and names the
sprint whose criterion is furthest from met. The check is narrowed to what it
can actually verify - that the sentence's sprint count matches the field, and
that the field's list has no holes - and its docstring now says what the field
means, so the next reader is not invited to make the same substitution.

**Repaired at 0.28.2.0, and the delay is the lesson.** The field is now
`sprint_test_files`, which is what it measures. For six releases the
reconciliation lived here, in the defect log, while the misleading name stayed
in the artefact a reader opens first, and review R-4 of 0.23.1.0 found three
documents disagreeing about which sprint was open partly because of it. A
defect entry records a repair; it is not one.

### F94, 0.22.1.0. A streaming reader held its connection across every yield

`EventStore.replay` and `replay_kinds` opened a connection, executed one
`SELECT`, and yielded rows from inside the `with closing(...)` block. The
connection therefore lived exactly as long as the generator, and a caller that
started a replay without finishing it - `next()` once, an early `break`,
storing the iterator to consume later - held a database handle open for as long
as it held the generator.

**Found from an operator's terminal, not from the suite.** `make verify` on
Python 3.14 printed `ResourceWarning: unclosed database`. The suite is green on
3.12 without it, and the warning is attributed to `areas.py`, which is only
where the collector happened to run.

**What was actually measured, 2026-08-11**, because the first account of this
was a guess and the guess was wrong:

| Caller shape | Descriptors held, before the repair | After |
| --- | --- | --- |
| replay consumed to exhaustion, 200 times | **0** | 0 |
| started, reference dropped immediately, 200 times | 3 | 0 |
| started and retained, 100 iterators | **201** | 0 |
| the same 100, after `del` and `gc.collect()` | **102** | 0 |

Two things follow, and the first retracts a claim made when this was first
raised. **The production path never leaked.** `publish` does `list(load())` and
`compose` does `list(events)`, so every caller in the tree consumes to
exhaustion, and the row above says that costs nothing. The suggestion that a
72-hour `--watch` run would accumulate descriptors was wrong, and was made from
the shape of the code rather than from a measurement.

**And garbage collection is not the backstop it looks like.** Half the handles
survived an explicit collection. Why exactly is not established here and the
mechanism is not asserted; what is established is that "the generator will be
collected eventually" is not a property this store can rely on.

**Class: a resource whose lifetime is the caller's attention span.** Latent, in
the family of F62 and F88 - nothing in the tree abandons a replay, and the
defect is closed rather than left for the first caller who does. The repair
reads in chunks of 500 with a connection per chunk, using keyset pagination on
`(ts_source, area_id)` rather than `LIMIT`/`OFFSET`, so a write landing between
chunks cannot make the reader skip or repeat a row. The iterator promise is
kept: an abandoned replay now costs one chunk of tuples and no open handle.

**What the repair gives up, stated rather than discovered later.** A replay is
now several statements instead of one, so a row appended mid-replay can appear
in a later chunk. The single-connection version took no transaction either, so
this is not a weaker guarantee than before - but it is a guarantee neither
version ever had, and writing it down here is cheaper than someone inferring it
from the old code's shape.

**The trap that nearly hid this, for the third time in one session.** The first
two attempts to measure the repair reported it as ineffective. Both ran a probe
script from a directory outside the tree, so `sys.path[0]` was the script's
directory and the installed package answered instead. Same failure as the F91
verification. A probe that does not print `module.__file__` is not a
measurement of the tree in front of you.

### F95, 0.23.1.0. A task outlived its reason, and kept the reason

T8 read, in full and unchanged since it was written:

> Sprint 6 assumes a Polish feed exists to switch to. RSO and NOTAM are machine
> readable; RCB and the announced government application probably are not.
> **Acceptance:** one working read from at least one Polish source, or a written
> finding that none exists and what that does to sprint 6.

Sprint 6 closed a long time ago; `shipped_sprints` reaches 9. The entry
justified itself by an assumption of a sprint that no longer exists and its
acceptance clause asked what a result "does to sprint 6", a question with no
addressee. **The task was still worth doing and every word explaining why was
stale.**

Three separate defects in six lines, which is what makes this worth an entry
rather than an edit:

**The reason expired and nothing noticed.** Sprints close and their tasks
outlive them; nothing in the backlog checks whether an entry's justification
still refers to something. `todo_index.py` verifies that the index matches the
entries and says nothing about whether an entry still makes sense.

**`blocked-external (access)` was false, and the label did the damage.** Nothing
in T8 needs anyone's permission. RCB posts publicly, and scraping a public web
preview is the exact technique that produced this project's entire Ukrainian
corpus. Labelling an unstarted measurement as externally blocked put it in the
category of things one waits for, and it was waited for across six sprints.
**A wrong status is worse than a wrong priority**, because priority invites
argument and status ends it.

**Two flat assertions with no provenance.** "RSO and NOTAM are machine
readable" carries no label in a repository where every load-bearing claim
carries one, and it sat beside "RCB (…) probably are not", which at least says
*probably*. Both were written before `docs/FEED-SPEC.md` existed and neither was
reconciled with it when it did.

**And the acceptance criterion was unfalsifiable in the positive direction.**
"One working read" does not say a read of what, resolved to what geography, at
what latency. FEED-SPEC section 3 defines five properties a consumable feed
must have, and a task about consumability that does not measure against them
would have been closed by whatever the first read happened to return.

**Class: an entry whose surrounding prose stopped being true while its subject
stayed true.** The same family as F93 - `shipped_sprints` read as sprint
completion - in that both are documents drifting from what they describe while
continuing to read plausibly. The difference is direction: F93 was a document
made to agree with a field nobody had read, and this is a document left
agreeing with a sprint nobody had reread.

**Repair.** T8 is replaced by T8a, a measurement with a verdict per source
against FEED-SPEC's five properties, promoted to tier 2 and marked as needing
nobody's permission; and T8b, the product-scope decision, separated out because
one entry was carrying a measurement and a decision, and the measurement was
hostage to the decision nobody was making. Every reference in
`ARCHITECTURE.md`, `DECISIONS.md`, `FEED-SPEC.md` and `MVP.md` is repointed,
and `MVP.md`'s "unresolved access" row - which had inherited T8's false label -
is corrected in place with the correction stated.

**No mechanism is proposed for the general case.** A lint that checks whether a
task's justification still refers to a live sprint is writable, and it would
have caught this one and probably nothing else. The count is the useful part:
one occurrence, found by reading the entry aloud when somebody finally wanted
to do the task.

### F96, 0.24.0.0. The live command polled the channel and dropped what it understood

`mavo collect` fetched the page, parsed it, printed how many messages it
understood, and discarded the events. `probe()` returned a `ParseReport` and a
duration; the `ThreatEvent`s and the declaration stream went out of scope with
the source that produced them.

**There was no path in this product from the live channel into the store.**
`fixture` writes a synthetic history, `backfill` writes raw pages, `report`
reads a store. Nothing wrote one from the channel. The full flag list of the
only command that touches the network was `--stub` and `--save-raw`.

**How it survived, and it is not the usual answer.** This is not a rule with no
reader or a test pinning the wrong call shape. Every store this project has
ever rendered from was filled by hand, on a laptop, by `fixture` or by a
backfill followed by an import that lived in a session rather than in the
package. The gap was invisible for as long as nobody tried to run the thing
unattended - which is the definition of shadow mode, which is S9, which has
never run.

**It was found within an hour of the first real deployment**, by
`mavo-report.service` restarting in a loop against a store that did not exist,
on a machine whose whole purpose was to answer whether the loop can run for 72
hours. `docs/MVP.md` lists S9's exit criterion as 72 hours unattended with
every cycle accounted for. **The exit criterion could not have been met by any
amount of work on a laptop**, and the entry for T25 said as much in a sentence
about sleeping machines, without anyone noticing it applied to more than power
management.

**Class: a missing edge between two components that were each complete.** The
collector parses and the store records, both tested, both correct, and nothing
joined them. Neither component's tests could have caught it, because the defect
is the absence of a caller rather than a fault in either. The gate is green at
310 tests and was green throughout.

**Repair.** `poll_once` returns the source, its events and the elapsed time;
`probe` keeps its counting-only reading and delegates rather than
reimplementing. `mavo collect --store` appends **both streams** - alerts and
declarations - because they are separate events with separate lifetimes (T16)
and a caller that stored one would produce a store whose kind coverage silently
read zero. A store that cannot be written exits 7 rather than printing a
successful poll, for the same reason `--save-raw` has its own code: a wrapper
reading stdout must not mistake a lost write for an empty sky.

**Idempotence was already there and is now load-bearing.** The store deduplicates
on content hash, so a poll every two minutes over a twenty-message window
re-sees almost everything it saw last time and appends only what is new. The
regression asserts the count does not grow on a repeated poll, because a log
that grew every cycle would be a record of the polling rather than of the
channel.

**What this does not fix.** The command is still one-shot; running it on a
timer is a deployment decision rather than a feature, and `skipped` stays
`unknown` on every poll because a fresh source has no baseline to compare post
ids against. Making the skipped count a measurement needs a resident source,
which is the sprint-6 note in that branch and is still true.

### F97, 0.24.2.0. Replay dropped a row when a sort-key tie straddled a chunk boundary

`EventStore._chunks` paged on `(ts_source, area_id)` with a strict `>`
comparison, and its docstring asserted that the schema makes that pair unique
per row. The schema asserts no such thing: the only uniqueness is
`content_hash PRIMARY KEY`. When two rows share a timestamp and an area and
the chunk boundary falls between them, the resume key equals the key of the
row not yet served, the strict comparison excludes it, and the row leaves the
replay with no counter moving anywhere.

**The tie is not a corner case, it is a documented behaviour of the channel.**
T37 records the shape: one message clears an area and lists the same area as
still under alert. Two rows, one `ts_source`, one `area_id`, two content
hashes. Measured on 2026-08-12 with the tied pair placed at rows 500 and 501
against `CHUNK = 500`: 501 appended, 500 replayed. The row lost was the one
saying the area is still under alert. Negative control, the same pair away
from the boundary: 402 appended, 402 replayed.

`replay_kinds` shares the machinery and is affected identically. A tie there
is a missile and a drone declaration for one area in the same second, which is
what a mass alert looks like.

**Class: test data chosen by the implementation, fifth instance.** The
exactness test for the paging existed, named this exact failure in its
docstring, and stayed green, because its factory `_many` builds keys that
never tie. The data could not distinguish a tie-safe keyset from a strict one.
The second contributor is a false uniqueness claim written into a docstring
and never checked against the DDL, which everything downstream then read as
settled.

**Why the harness did not catch it.** MT15 guards "a still dangerous area is
not silently dropped" and stayed green throughout. It exercises the
composition layer; the drop happens in pagination, one layer below, before
composition sees the row. An attack is only as deep as the layer it
exercises, and this is the second time that has been the answer.

**Repair.** The key is `(ts_source, area_id, content_hash)`. The hash is
appended by `_chunks` itself as the final SELECT column, so the readers'
column indices are untouched. A consequence worth stating: order within a tie
is now a property of content rather than of insertion, so two stores rebuilt
from the same corpus replay identically, which `consistency_check` had been
relying on without saying so.

**Mutation observed red:** the tiebreak stripped, restoring the pair keyset.

**What this does not fix.** The chunked reader still takes no transaction, so
a row appended mid-replay can appear in the replay. That was true of the
single-connection version as well and is not a regression; it remains
unmeasured whether any caller depends on it not happening.

### F98, 0.28.1.0. The ten-second timeout was a ten-second timeout per socket operation

`UrllibTransport.fetch` passed `timeout_s` to `urlopen`, and every caller,
every document and one shipped decision read that number as the cost of a
failed attempt. It is not. `urlopen` hands the value to the socket, where it
bounds **each blocking operation separately**, and `socket.create_connection`
re-applies it to **each resolved address**:

```
for res in getaddrinfo(host, port, 0, SOCK_STREAM):
    ...
    sock.settimeout(timeout)
    sock.connect(sa)
```

[measured, from the standard library source on 3.12.3]. A host with an A and
an AAAA record therefore costs two timeouts before the read has started, and a
connect that stalls followed by a read that stalls costs two more. The
production host is IPv6-only, so the address that cannot work is attempted
anyway.

**What was observed.** A failed collection took 20 seconds against a
`DEFAULT_TIMEOUT_S` of 10.0, measured twice on the production host on
2026-08-13. Which of the two amplifications produced it is not established:
both are present, and one experiment on that host distinguishes them. The
repair bounds both, so the distinction is now diagnostic rather than load
bearing.

**Class: a constant that names a guarantee the code does not make.** Third
instance, after the docstring uniqueness claim in F97 and the `shipped_sprints`
field that means "a test file exists" in F93. The pattern is a name read as a
promise by everything downstream, with nothing checking the name against the
behaviour. A number with no test that would fail if it were wrong is a label.

**Why it survived.** The refusal message added by T55 carries the elapsed time,
and that elapsed time is the evidence. It was logged correctly for two
releases and read by nobody, because the diagnostic was built to answer "is the
source throttling" and the number it reports also answers "does the bound hold",
which nobody was asking.

**What it falsified.** D-027's deciding argument is arithmetic: a run of two
failures costs 90 seconds against a 600-second staleness threshold. That figure
assumes a failure costs one interval. It costs its own wall clock as well, and
the wall clock was twice the number the decision used. The entry now carries
the correction.

**Repair.** `timeout_s` becomes a deadline for the whole fetch. `connect_within`
spends one budget across every resolved address rather than repeating it, and
the connection hands the read whatever the connect and the TLS handshake left.
The fetch goes through a deadline-carrying opener instead of `urlopen`, which
has no argument for this.

**Mutations observed red:** the budget computed once before the address loop
rather than inside it; the floor dropped from `remaining_budget`; the remaining
budget computed and never applied to the socket.

**What this does not fix.** `getaddrinfo` itself is not bounded by any of this,
so a stalled resolver still costs what it costs. Nothing in this repository can
bound it without a thread, and a thread in the network seam is a larger change
than the defect justifies. Stated rather than left to be discovered.

### F99, 0.32.3.1. A tag was created over a gate that had already refused

`make verify` stopped at `lint-hygiene: CHANGELOG top entry 0.32.2.0 !=
pyproject 0.32.3.1` and returned a non-zero status. The commit, the assertion,
the tag and the push were run afterwards as four separate commands, and
`v0.32.3.0` now names a tree that fails its own gate. CI said so within twenty
seconds, on a badge the README carries on the front page.

**What the assertion asserted.** `git status --porcelain` empty, and
`git show HEAD:STATUS.json` reporting the expected version. Both were true.
Neither can observe a gate result: one measures the worktree against the index
and the other reads a string out of a file the operator had edited by hand.
The step named itself an assertion before the tag and checked two properties
that a red gate leaves untouched.

**Class: a check whose success is indistinguishable from its failure**, which
is the same class as offering a five-occurrence string as proof that a
one-occurrence change was deployed. Fourth instance of the wider family, after
F90, F96 and F97: a state read from an artefact rather than from the thing that
produces it, and stated with confidence.

**Why it survived.** The gate and the commit were separate commands in the
release procedure, deliberately, because a different defect had taught that
chaining `commit && tag && push` silently skips the tag when the commit is a
no-op. That lesson was applied one step too far. `verify && commit` is a
chain that must hold, because the gate's entire purpose is to have the power
to stop the commit; `commit && tag` is a chain that must not, because a no-op
commit is not a reason to skip a tag. The two cases were treated as one rule.

**Repair.** Two, and both are needed. The gate is chained to the commit, so a
refusal prevents the commit rather than being read and passed over. And before
a tag is created, the gate is run against a worktree of `HEAD` in a fresh
virtual environment, because the run that matters is the one against the commit
the tag will name, not against the tree the operator has been editing. Until
that lives in the Makefile it is a preference rather than a rule, which is this
repository's own standing test for whether something is enforced.

**And this entry was first written as F80**, over an entry that had held the
number since 0.21.2.0, in the release whose subject is an identifier issued
from memory rather than read from the file. The count agreed with the pin
throughout, because eighty entries under seventy-nine names still total
eighty. `check_defect_identifiers_are_unique` now runs before that count,
verified red against the collision and green after the rename.

**Reopen if:** a tag is created without a green gate measured on the commit it
names; or an `F<n>` is issued by any means other than reading the highest
number from the log.

### F100, 0.32.5.0. A correction about another repository, in the present tense, stale for eleven of its releases

The F74 entry above records a sentence that asserted, in the present tense and
without anybody having read the code, that the consumer mapped `kyiv`. The
repair was to check, find it false, state it, and carry the gap as T44. That
repair was correct on 2026-08-10.

**It stopped being correct on the consumer's next release and stayed in the
tree for eleven more.** `mavo-site` shipped `SLUG_ALIASES = {"kyiv":
"kyiv-oblast"}` with a named test; this repository went on stating **It does
not** in bold, in the register of settled fact, in the paragraph that exists to
explain why a claim about another repository must be measured. Read on
2026-08-17 against `mavo-site` 4.27.1.1: the alias is present, resolved in
`canonical_slug`, and held by a test in a green suite.

Class: **a claim about a system this repository does not control, written
without an anchor to the version it was true of.** The same family as F66 and
F74, and the second time this exact sentence has been the instance.

**Why it survived.** Three reasons, and the third is the one worth keeping.

1. Nothing in the gate reads the other repository, and nothing should: D-020
   removed that coupling deliberately and re-adding it to make a documentation
   check possible would be paying for a sentence with an architecture.
2. The correction read as finished. A paragraph that says "checked afterwards"
   looks measured, and it was, once. **A measurement without the version it was
   taken against is a claim with a timestamp missing**, and this file has a
   convention for exactly that which the paragraph did not use.
3. T44 existed and was correctly filed, so the gap was tracked. What was not
   tracked was the *documentation of the gap*, which is a different artefact
   with a different failure mode: the task can close and the prose can stay.

**Repair.** The passage is restated with both measurements and both dates, the
first in the past tense with its version anchor. T44's remaining half, the slug
pair named in `docs/WEBAPP.md`, ships in this release, and the task closes
against evidence on both sides rather than against an assertion. The convention
this makes explicit: **a statement about another repository carries the version
it was read against, or it is not written.**

**Not repaired, and named rather than implied.** No check enforces the
convention. A `claim_lint` rule reporting a present-tense sentence naming
`mavo-site` without an adjacent version string is buildable and is not in this
release, because a lint written in the same hour as the defect it targets tends
to encode the one instance rather than the class. Until it exists this is a
preference, by this repository's own standing test.

**Reopen if:** any document here states a property of `mavo-site` without the
version it was measured against; or T44's closure is found to rest on the
consumer's code having been read once rather than tested.

### F101, 0.32.6.0. A control that produced the behaviour it forbade

`tools/check_manifest.py` shipped at 0.32.5.0 with both of its questions in one
check, and that check second in `verify`. Within a day the first edit to
`TODO.md` made the gate unrunnable: the digest of an edited file disagrees with
its entry, which is what an edited file is. The only way past a red gate was
`make manifest-write`, and **that tool's own error message says to run it as
part of the release chain and never as a way of making this check green.** The
placement made the forbidden act the only available one.

Class: **a control whose scope was right and whose placement was wrong**, and
the placement turned it into a generator of the behaviour it existed to
prevent. Not the same as a check that is too strict; a strict check refuses
work, this one prescribed a shortcut.

**What was actually conflated.** Two questions with different subjects.
*Completeness* - every tracked file listed, nothing listed untracked - is a
property of the tree at any moment and survives an edit. *Digests* are a
property of a **commit**, and a working tree under edit is supposed to differ
from one. One is a gate question and the other is a release question, and they
were run by one command because they read the same file.

**Why it survived.** The control was verified red on five cases before it
shipped, and every one of them was a release-shaped case: a file added, a file
removed, content changed on a clean tree, the manifest absent, no repository.
**None was the pattern the operator is in most of the time**, which is an
edited tree with the gate being run to find out whether the edit is sound. The
test suite reproduced the author's workflow, which was one regeneration
followed by one gate run, and the author's workflow was the unrepresentative
one. Coverage of a control's *inputs* is not coverage of its *placement*.

**Repair.** `manifest-completeness` is in `verify` and is edit-insensitive.
`make manifest` runs both halves and is not in `verify`: it is for the release
chain, for the gate on the detached worktree where the tree is clean by
construction, and for CI after the push, which is where a release that skipped
regeneration becomes visible to somebody other than whoever forgot. **The
placement is held by a test that reads the `verify` line of the Makefile**,
because a test of the functions alone would stay green if the digest target
came back to the gate, which is precisely the regression this entry is about.

**Reopen if:** the digest target reappears in `verify`; or any check in the
gate is answered by an operator running a command the check's own message tells
them not to run.

### F102, 0.32.7.0. Three claims about the production host, all stale, all pessimistic

Read on 2026-08-17 against `vm-mavo`:

| Claim, and where it lived | True until | Actually |
| --- | --- | --- |
| "runs pre-0.28.1.0, so F98 is not deployed" - T60 and `docs/DEPLOYMENT.md` | 2026-08-14 18:13 UTC | 0.32.2.0, `connect_within` present, 10 s bound holding on the wire |
| "`AccuracySec=1s` unconfirmed, D-027's margin is an estimate" - a handover outside version control | 2026-08-14 | applied, and D-027 **already carried** the one-hour measurement |
| "T27, jitter, `ready`" - `TODO.md` | before 2026-08-11 | `RandomizedDelaySec=5` deployed and in the drop-in |

Class: **a statement about a system outside the gate's reach, written in the
present tense, correct when written.** F100's class, three more instances, and
one of them was in a document the repository does not contain.

**The direction is the finding.** Every one of these understated the state of
the project. F98 was deployed and we said it was not; the cadence was measured
and we said it was an estimate; jitter shipped and the backlog called it ready.
Nothing in the whole set overstated progress. **This repository's discipline
refuses to round completion up, and that discipline is asymmetric**: an
overclaim is caught by the next person who checks, because checking is what the
gate does, while an underclaim is stable, comfortable and invisible. It reads
as rigour. Correcting one requires someone to go and look for good news, and
nothing in this project ever prompts that.

The single claim that went the other way - that tags here are GPG-signed, when
five of five are annotated and unsigned and no key exists - came from a
handover, which is the one artefact in this system with no gate at all.

**Why it survived.** `docs/DEPLOYMENT.md` 1.4 opened by saying it describes a
shape rather than a state and added a state section to fix exactly this. That
section was then written once and never re-read, because **a document that says
"this part is the state" still has no mechanism that notices when the state
moves.** Saying a paragraph is perishable does not date it.

**Repair.** `docs/DEPLOYMENT.md` carries `Host state measured: YYYY-MM-DD` and
`check_the_host_claim_is_no_older_than_the_release` fails the gate when that
date falls more than fourteen days behind the newest CHANGELOG date. The check
cannot verify the content and does not pretend to; **it converts an
unverifiable claim into a verifiable freshness**, which is the whole of what a
repository can do about a machine it cannot see. Compared against the release
date rather than the clock, so an old commit stays green forever and the
question is asked at the only moment anyone can answer it.

**Reopen if:** a host figure appears anywhere outside `docs/DEPLOYMENT.md`
without a date; or the fourteen days pass without the check firing.

### F103, 0.32.7.0. Observability configured on the host, documented, tested to 98%, and never once called

`mavo-collect.service` carries `Environment=MAVO_LOG_FILE=/var/lib/mavo/run.jsonl`.
No such file has ever existed. Not permissions: the directory is writable and
holds `events`, `state.json` and `feed.json`, written by the same unit as the
same user.

**`mavo.obs.from_environment` has no caller in the package.** [measured, grep
across `mavo/` and `tools/` at 0.32.6.0] `mavo/report.py` imports `RunLog` and
uses it only as the type of an optional parameter that nothing passes.
`docs/OBSERVABILITY.md` shows the variable alongside `mavo watch`, which is not
a subcommand: the CLI offers `backfill`, `collect`, `fixture`, `gate`, `policy`
and `report`. The loop the sink was designed for is M0 and waits on T25, which
was itself unrecorded until D-031.

Class: **a control that is switched on everywhere a person would look and
connected nowhere.** Stronger than dead code, which announces itself by being
unreachable. Every observation point here reports healthy: the unit sets the
variable, the document describes the behaviour, `mavo/obs.py` sits at 98%
branch coverage with a mutation-verified redaction test, and the file's absence
is indistinguishable from a quiet log.

**Why it survived.** Three reinforcing reasons.

1. **The module was built and tested against its acceptance rather than against
   a caller.** `docs/OBSERVABILITY.md` section 9 wrote seven criteria before the
   code, five are met, and every one of them tests the sink *given a sink*.
   None asks whether anything constructs one. Acceptance written before the code
   protects against building the wrong thing and not against building the right
   thing and leaving it unplugged.
2. **The environment variable made the host look wired.** Somebody read the
   documented invocation, took the variable from it, and put it in the unit that
   exists - `collect` - rather than the one the document names, which does not.
   The configuration is a faithful copy of an instruction for a command that was
   never built.
3. **Absence is the default reading of a missing log.** This is the project's
   own central error, committed against its own instrumentation: an empty set
   because nobody wrote and an empty set because nothing happened look the same,
   and the artefact that would tell them apart is the one that does not exist.
   The same shape appeared twice more in the session that found this, in a
   `journalctl` call returning zero for want of a group membership, and in a
   backlog entry reading `ready` for want of anyone asking the host.

**Repair, and it is deliberately partial.** The variable is not removed and the
sink is not wired in this release. Removing it would erase the evidence; wiring
it into a `oneshot` that runs 2,619 times a day produces a different artefact
from the continuous record the design is for, and D-031 records that M0 is a new
unit rather than a flag on this one. What ships is the finding, written into
`docs/DEPLOYMENT.md` beside the variable so its silence cannot be read as a
quiet log, and T23 restated: **the sink and reader exist and are not attached**,
which is a different task from the one the entry described.

**Reopen if:** T23 attaches the sink without a test that fails when nothing
writes; or any other configuration is added to a unit for a code path that has
no caller.

## The drift, and where its boundary is

*Written 2026-08-17, after a session in which six claims in and around this
repository were found stale in one afternoon. This section is not a defect
entry. It is the answer to why there were six.*

### What was actually wrong

| Claim | Where it lived | Gated? |
| --- | --- | --- |
| the consumer does not map `kyiv` | `docs/METHODOLOGY.md` | yes, and about another repository |
| the host runs pre-F98 | `TODO.md`, `docs/DEPLOYMENT.md` | yes, and about a machine |
| T27 jitter is `ready` | `TODO.md` | yes, and about a machine |
| `AccuracySec` is unconfirmed | a handover, outside version control | no |
| tags here are GPG-signed | a handover, outside version control | no |
| the run log is being written | a systemd unit on the host | no |

**The gate is excellent inside its perimeter and the perimeter is
`git ls-files`.** Every failure in that table is a claim that crossed a
boundary: to another repository, to a machine, or to a document nobody's tooling
reads. Not one of them is a claim about this package's own code, because claims
about this package's own code are checked eleven ways before they can be
committed.

That is not an argument for widening the perimeter. Reaching into the consumer
would rebuild the coupling D-020 removed; reaching into the host from CI needs
credentials CI should not hold. **The boundary is correct and the claims cross
it anyway**, which means the repair is never "check the far side" and always
"hold the part of a crossing claim that stays on this side": its version anchor
(F100), its date (F102), the symbol that proves it rather than the number that
asserts it (T60).

### Why nobody noticed, stated as a mechanism rather than as inattention

**The unit of progress in the plan is a sprint; the unit of work is a release.**
Fourteen releases have landed since S8 and `docs/MVP.md` has five sprint rows.
Jitter, the drop-in, the timers and the host all arrived inside releases that
were doing something else, and no step in the release procedure asks which
backlog entries a release touched. `tools/todo_index.py` checks that the index
agrees with the entries beneath it; nothing checks that the entries agree with
the tree, and nothing could check that they agree with the host.

**Deployment produces no commit.** The host acquired four units, two timers, a
drop-in and an environment variable through operator actions that left no trace
in version control. Everything that happens outside the repository is invisible
to every check the repository has, and `docs/DEPLOYMENT.md` was the designated
place for it precisely because that is true - which made that one file carry the
whole burden with no mechanism behind it.

**Absence is the default reading of everything unchecked.** A missing
`run.jsonl` reads as a quiet log. A `journalctl` without `adm` returns zero and
reads as no timeouts. A backlog entry saying `ready` reads as untouched. In all
three the artefact that would say otherwise is the artefact that does not exist.
**This project's central rule - silence is never confirmed absence - is enforced
in the product's output and nowhere in the product's bookkeeping.**

### The asymmetry, which is the part worth keeping

Five of the six stale claims understated the project. F98 was deployed and we
said it was not. The cadence was measured and D-027 already said so while a
handover said it was an estimate. Jitter shipped and the backlog called it
ready. The consumer mapped `kyiv` and this file said in bold that it did not.

**The discipline that refuses to round completion up has no counterpart that
refuses to round it down.** An overclaim is unstable: the gate, the reviewer or
the next release finds it, because finding overclaims is what all of this
machinery is for. An underclaim is stable, cheap and flattering to the
project's self-image as rigorous. Correcting one requires somebody to go looking
for good news, and no procedure here has ever asked anyone to do that.

The single claim that ran the other way, that tags are signed, came from a
handover. **The one artefact with no discipline at all was the one that
overstated**, which is consistent rather than ironic: outside the gate, error
has no preferred direction.

### What this costs and what was done about it

The cost is not embarrassment. It is that the sprint plan routed a session into
deploying something already deployed, and that S9 was described as five open
tasks when three of them were done. **A backlog that understates completion
spends real work re-deciding settled questions**, and it does so invisibly,
because re-deciding looks like diligence.

Three repairs ship in 0.32.7.0 and none of them is a resolution to be more
careful:

- **F102's check.** A dated host claim, and the gate refuses one more than
  fourteen days older than the release. Freshness is checkable where content is
  not.
- **F100's convention.** A statement about another repository carries the
  version it was read against. Still unenforced, still recorded as unenforced.
- **D-031.** The decision that had been made by deployment is written down, so
  that it can be reopened rather than rediscovered.

What is *not* repaired, and is named so the next session does not mistake it for
solved: **nothing asks, at release time, which backlog entries this release
closed.** That question would have caught T27 and T60 months of releases
earlier. It is a candidate for `tools/release.sh` and it is not in this release,
because a check that asks a human a question is a preference until it can fail.

### F104, 0.32.7.0. An architectural conclusion about this package, drawn from a unit file instead of from the code

D-031's first draft said: *M0 is therefore a new unit, not a change to this
one*, and T23's rewritten acceptance repeated it as *per D-031 that is M0's new
unit*. Both were inferred from `Type=oneshot` in `mavo-collect.service`, one
step of reasoning from a fact about systemd to a claim about this package's
architecture, with the package unread.

**It is wrong and cheaply so.** `mavo report --watch --json` is the loop; it
runs on the same host as `mavo-report.service`; `publish()` in `mavo/report.py`
has accepted a `log: RunLog | None` parameter since the sink shipped at
0.23.0.0. Attaching the run log was one argument at one call site. The
conclusion that M0 needed building first would have deferred T23 behind work
that does not exist.

Class: **an inference about a system from the shape of its deployment**, which
is F102's class with the arrow reversed. F102 is a stale claim about a machine
held in a repository; this is a fresh claim about a repository drawn from a
machine. Same boundary, same failure to cross it by reading.

**Why it survived for the length of one afternoon rather than one release.** It
was caught by writing the test before the release rather than after, and by
nothing else. There is no check that could have caught it: the sentence was in a
decision entry, decision entries are prose, and prose about architecture is
exactly what `claim_lint` cannot reach.

**Why it happened at all**, which is the part worth keeping. It was written in
the same session as F102, whose subject is claims made without measurement, and
by the same reasoning F102 describes: the unit file was in front of me and the
CLI was not, so the available evidence became the answer. **Proximity of
evidence decided the conclusion, and the conclusion was stated in the register
of a settled decision.** The repair is not vigilance. It is that a decision
entry asserting a property of the code names the file and function it read, the
way a measurement names its date.

**Repair.** D-031 carries the correction and the narrower claim that survives:
the collector cannot hold cross-poll state, and the run log never needed it to.
T23 closed. This entry, so that the next architectural sentence in a decision
entry is read as needing a citation.

**Reopen if:** any entry in `docs/DECISIONS.md` asserts a property of this
package's code without naming where it was read.

### F106, 0.32.8.0. The same inference, the third time, inside the release that documents it

`docs/DEPLOYMENT.md`, F103 and the 0.32.7.0 changelog entry all state that
`MAVO_LOG_FILE` sits on `mavo-collect.service` and belongs on
`mavo-report.service`, with a deploy step to move it. **It was already on both.**
Read on 2026-08-17 at deploy time: `mavo-report.service` has carried
`Environment=MAVO_LOG_FILE=/var/lib/mavo/run.jsonl` since it was written.

The claim came from reading the collector's unit, not finding the loop there,
and concluding the variable was misplaced - without opening the unit that runs
the loop. F104 records the same mechanism about the CLI four hours earlier, and
F102 records it about the host that morning. **Three instances in one session,
each in a document whose subject is the previous one.**

Class: F104's exactly. What is new is only the count, and the count is the
finding: the mechanism does not yield to having been named. Writing "proximity
of evidence decided the conclusion" into a defect entry did not stop the next
conclusion being decided by proximity of evidence.

**Why it survived to a tag.** Every check that could have caught it is on the
far side of the boundary the drift section describes. The gate reads this tree;
the claim is about a file on a machine. The release procedure verifies the
content under the tag, which is exactly the wrong artefact: the content was
faithfully tagged and the content was wrong. **The only control that applies is
reading the unit, and reading the unit is what produced the correct answer
thirty minutes later, during the deploy the false claim had scheduled.**

**Repair.** `docs/DEPLOYMENT.md` corrected: the deploy is an install and a
restart, no unit edit. F103's second fault withdrawn - the variable was on the
right unit and unread, which is one fault rather than two. The tag stands;
deleting it would remove the record rather than the error.

**What is not repaired.** No check exists and none is proposed here. A rule
that a claim about a systemd unit must quote `systemctl cat` output is
writable and would have caught all three; it is not written in the same release
that found the third instance, for the reason F100 gives about lints written in
the hour of the defect. It is **T64**.

**Reopen if:** a fourth instance occurs, at which point the pattern is not a
defect but a property of how this work is done, and the repair is procedural
rather than documentary.

### F107, 0.32.8.0. A measured quiet is rendered as a degraded instrument

`Report.feed_state` is decided by `staleness_s`, which is
`as_of - newest_observation`, and `newest_observation` is
`max(e.ts_source for e in latest.values())`: the source timestamp of the newest
**event**. `DEFAULT_VALID_FOR_S` is 600. So ten minutes without a change of
alert state anywhere the collector tracks produces `feed=degraded`, and the
page tells its reader to treat the picture as stale.

**The pipeline is demonstrably healthy while this happens.** Observed on the
production host on 2026-08-17: `mavo-collect` polling every ~33 s, exit status
0, `messages=20 parsed=19 stored=0 new events (seen=13)`. The channel was
asked, it answered, thirteen events were recognised and all were already known.
**A successful poll that yields no state change is a measured quiet, not an
absent observation**, and the report cannot see the difference because the
store holds alert events and not poll outcomes.

Class: **the project's central rule inverted.** Not silence rendered as calm,
which the design refuses everywhere: measured calm rendered as a broken
instrument. The direction is the safer of the two and it is still a conflation,
and a reader told to distrust a picture that is accurate learns to distrust the
next one too.

**Frequency is not yet known and the figure here is an anecdote, labelled as
one.** Eight minutes of `run.jsonl` on 2026-08-17 carried 13 `degraded` cycles
against 5 `ok`, and the state oscillated across the threshold rather than
sticking. **The measurement that settles it is the S9 window**: 72 hours of
`publish.cycle` records carry `feed_state` per cycle, which gives the duty
cycle with between-day variance. Recorded now, quantified then, and this entry
is not closed until it carries the number.

**Why it survived.** It has always behaved this way and nothing was watching.
The state is visible only in a journal line and on the page itself, and neither
is read continuously; the run log that makes it countable was attached four
hours before this entry was written, by T23. **The first thing the new
instrument was used for was a defect nobody had noticed in the thing it
instruments**, which is the argument for T23 that T23's own entry did not make.

**Not repaired here, and the shape of the repair is a decision rather than a
fix.** Options are visible and none is obviously right: a fourth feed state for
"polled successfully, nothing changed"; recording poll outcomes in the store so
freshness can be computed from observation rather than from events; or leaving
the behaviour and changing what the page says about it. Each changes the
contract or the schema. **T65**, with the S9 figure as its input.

**Reopen condition, stated because this entry ships open:** it closes when the
duty cycle is measured and a decision entry names the chosen repair.

### F108, 0.33.0.1. The manifest gate could not see the files it was missing

`tools/check_manifest.py` reads the tree through `git ls-files`, so an
**untracked** file is not a file to any check in that module. `--write` omits
it, `--completeness` then holds against a list that does not contain it,
`make verify` goes green, `git add` follows, and the manifest is wrong one
commit before anybody looks. The gate's perimeter and the release's perimeter
were the same command and were assumed to be the same set.

**Second occurrence in two days.** `5626e790` failed CI on 2026-08-17 and
`bb85ec5` fixed it with a commit whose entire content was rewritten digests.
That fix restored the state and left the mechanism, which is the difference
between a repair and a correction.

**Repaired at 0.33.0.1.** `completeness` now also fails on a file that is
present, not ignored and not yet tracked. `--exclude-standard` keeps `.venv`,
`.gate` and outreach artefacts invisible; `MANIFEST.sha256` is excluded by name
for the same self-reference reason it is excluded elsewhere. Verified in both
directions: red on a planted untracked file, green on a clean tree.

**What the repair did not reach, found at 0.35.0.0.** The documented release
order after this defect read apply → add → verify → manifest, and that order
**cannot be executed when a release adds a file**: `manifest-completeness` is
inside `verify`, so `verify` fails on the new file before the manifest is ever
written. Measured twice in one session while shipping 0.34.0.0. The order is
now apply → add → **manifest-write** → verify → manifest → commit → tag, and it
is in `docs/DEPLOYMENT.md` rather than only in a handover.

**This entry itself is the third finding.** F108 was written into
`CHANGELOG.md` at 0.33.0.1 and not into this file, and the gate could not see
that either: `check_defect_count_is_pinned` compares the entry count against
`STATUS.json` and the README badge, so three artefacts agreed about a number
while the newest defect sat outside all of them. Four older identifiers are in
the same state. `check_every_cited_defect_has_an_entry` closes the mechanism at
0.35.0.0 and names those four rather than inventing entries for them.

**Reopen condition:** it reopens if a release ships with the manifest
regenerated to make a check green, which is the act the tool's own error
message forbids.

### F109, 0.36.0.0. A pinned failure rate that was two orders of magnitude wrong

`docs/DEPLOYMENT.md` has carried **0.076%** as the collector's poll failure
rate since 2026-08-14, and `README.md` was corrected at 0.33.0.2 to agree with
it, replacing an older sentence that said roughly one poll in eight. **The
older sentence was closer.** The measured rate is between 9.7% and 10.6%.

**How the pin was built.** Its numerator, 14, counts fetches over 15 seconds
in the seven days after F98 landed. Its denominator, "roughly 18,350 polls",
is within two per cent of the number of *successful* collections in the whole
journal, which spans nine days. A numerator from one window over a denominator
from another, and the quotient described as a failure rate.

**What is actually there** `[measured 2026-08-20, on the host]`:

| Window | Attempts | Refusals | Rate |
| --- | --- | --- | --- |
| 08-14 18:13 → 08-17 11:02, the window the pin names | 7,074 | 689 | 9.7% |
| 08-17 11:02 → 08-20 11:02, the S9 window | 7,850 | 774 | 9.9% |
| Whole journal | 19,956 | 1,966 | 9.9% |
| Four live probe series, same afternoon | 180 | 19 | 10.6% |

**F98 bounded the cost of a failure and not its frequency, and the pin read
the bound as the frequency.** Every refusal in the journal sits at 10.0
seconds, which is the timeout doing exactly what F98 made it do.

**What the failure is.** `time_connect` is zero on every refusal and the
response body is empty: a SYN goes out and nothing comes back. Not DNS - 40
probes with the address pinned and resolution skipped refused at the same rate
as 40 with it. Not the missing IPv4 route - 20 consecutive fetches all chose
the AAAA record and none touched the A record. Not path MTU - a black hole
there would complete the handshake and stall on transfer, and these never
reach the handshake. **Which side drops the packets is `[unknown]`** and T70
holds the question.

**Repair, and its evidence.** Every successful connect measured took 23 to 55
ms, so `CONNECT_BUDGET_S = 2.0` cannot cut off a connection that was going to
work and stops paying ten seconds for silence. In 7 of 7 observed cases an
immediate retry connected, so one retry removes most of the rate; the
one-sided 95% lower bound on retry success is 65%, which puts the repaired
rate between 1.1% and 3.7% `[inference from n=7]`. **The retry is made only
when the connection was never established**, because a request that arrived
may have been acted on and repeating it would be a decision about the far
side rather than about our own timeout.

**Reopen condition:** it reopens if the refusal rate measured after this
release lands on the host is not below 4%, which would mean the failures are
correlated at the timescale a retry works on, and the estimate above rested on
seven observations.

**Reopened 2026-08-21, before the window could even be read.** F110: 0.36.0.0
crashed on the failures instead of refusing them, so the 14-hour window
measured a broken exit path. The rate over that window, counted as starts
minus finishes, was 10.9% - unchanged. The repair carrying the retry reached
the host at 08:52:36 UTC as 0.36.0.1 and the acceptance clock restarted there.

**A same-day probe moved the cause** `[measured 2026-08-21, 09:15-09:28 UTC]`:
600 ICMP packets to the channel's address returned with **0% loss** (rtt 22.8
±0.3 ms), while 600 TCP requests in the same window failed at **10.7%**, and
the collector polling at its own 33 s cadence through that same window refused
**zero of 34**. Loss on the path is excluded at 99.8% power; what remains
selects on protocol and on request rate, which is the shape of a limiter -
**the hypothesis T39 closed on an n=10 probe on 2026-08-11, wrongly.** Which
side imposes it is still `[unknown]`.

### F110, 0.36.0.1. A resolver that returned datagram addresses, and a cap that reached them

`connect_within` called `socket.getaddrinfo(host, port)` with no `type`.
**That returns three entries per family, not one**: `SOCK_STREAM`,
`SOCK_DGRAM` and `SOCK_RAW`, so six for a host with an A and an AAAA record
`[measured]`. The loop walked all of them.

`connect()` on a datagram socket returns immediately, because there is nothing
to negotiate; it records a default peer and reports success. `connect_within`
handed back a socket that looked open, `ssl.wrap_socket` refused it from
inside the standard library with `NotImplementedError`, and that is a
`RuntimeError` rather than an `OSError`, so it was caught by nothing: not the
retry, not `fetch`, not `_cmd_collect`.

**Latent from 0.28.1.0, reachable from 0.36.0.0.** F98 gave the first attempt
the entire ten-second deadline, so the loop always broke on an exhausted
budget before it could reach a second entry. F109's two-second cap left eight
seconds behind, and the defect was one release old the moment it became
reachable.

**Measured on the host over 2026-08-20 18:19 to 2026-08-21 08:23**: 1,539
starts, 1,371 finishes, **168 processes killed by a traceback**, exit
`1/FAILURE` where the contract says `3` for unreachable. Not one
`[UNREACHABLE]` line was written, so a count of refusals over that window read
**zero**, and this session read that zero as a quiet network for one full
turn. The refusal rate had not moved: 168 of 1,539 is 10.9%, against 9.9% the
day before.

**Three repairs, because one would have been the same bet again:**

* `resolve_stream` asks for `SOCK_STREAM` only. The defect at its source.
* `_attempt_one` refuses a non-stream candidate. The resolver is an injectable
  seam, and a fix that lives only in the default protects the production path
  and nothing else.
* `fetch` maps **any** exception to `SourceUnavailable`, naming the type in
  the message. The old tuple was a guess about what `http.client` plus `ssl`
  can raise; the guess was wrong once and would be wrong again. The tuple
  survives as `RETRYABLE`, deciding only what is worth a second attempt, where
  narrow is right: an exception nobody predicted is not evidence that trying
  again would go better.

**Why the regressions missed it, and this is the part worth carrying.** The
test written for F109 handed `connect_within` two addresses and made both
`SOCK_STREAM`, because that is what its author believed `getaddrinfo`
returns. The fixture was arranged from the implementation's belief rather than
from the interface, which is the recurring defect class this project logs, and
it produced a suite that could not have failed on the bug it was written
beside. The regression now passes a datagram address deliberately, and a
second test asserts against the **real** resolver that the six-entry premise
still holds, so this cannot decay into testing a stub.

**Reopen condition:** it reopens if any exception leaves `UrllibTransport.fetch`
as anything other than `SourceUnavailable`, or if `mavo-collect` exits
`1/FAILURE` on the host for a network cause.

### F111, 0.38.0.0. Five counters in one evening, none of which measured what it was read as

Not five defects. One, with five instances, all in instruments this assistant
built to answer a question and then read as though the answer were the
question's.

| Instrument | Read as | Actually measured |
| --- | --- | --- |
| `wszystkie/wszystkie` | the whole feed | 156 of 461 communiques |
| `totalItems` | the total | items on the requested page |
| `dig +short AAAA \| wc -l` | address records | records **and** CNAME lines |
| `grep -c 'Stopień:'` | messages carrying a degree | 2 of 106, against a body that visibly contains it |
| `curl` timeouts to five hosts | a publisher blocking datacentres | this host having no IPv4 egress |

The fifth is the expensive one. A conclusion had been drafted, in words, for a
public document naming a broadcaster and a ministry, on the strength of five
timeouts. The control that overturned it was requested by the operator, not
supplied by the assistant, and it took one command.

**Why they survived.** Each instrument returned a number of the right type and
a plausible magnitude. Nothing about `156`, `20`, `1`, `2` or a timeout looks
wrong. The check that catches this class is not review; it is building the
falsifying case into the measurement, and it worked exactly once tonight: the
date-range probe printed the span of the records it received alongside their
count, so a filter that had been ignored could not read as a filter that had
worked.

**F103's lesson, one layer out.** That entry recorded a conclusion drawn from
whichever file was open rather than from the file the conclusion was about.
This is the same act performed on a command: the output of the command that was
run, read as the output of the command that was meant.

**Remediation, and it is a rule rather than a fix.** A counter without a
falsifying case beside it is not a measurement. Where a probe can return a
plausible number for the wrong reason - a scope that silently narrows, a
parameter silently ignored, a pattern that matches a superset - the probe must
print the fact that would distinguish the two, in the same output, or it does
not get quoted.

**Reopen condition:** it reopens the next time a number reaches a document or a
decision without a stated way it could have been wrong.

### F112, 0.38.0.1. A date quoted correctly in conversation and transposed by two years in the tree

The MSWiA page dates its decision entrusting the Government Centre for
Security with publishing communiques to 30 April 2024. The session that read
that page quoted it correctly, with a citation, in conversation. What was then
written into this repository, in five places at once - the module docstring,
the backlog, the changelog, the release review and FEED-SPEC - said 2026.

**Why it matters more than a typo.** FEED-SPEC is the document written for
exactly the institutions whose decision the date describes. A reader there who
knows their own calendar finds the error in seconds, and every measured number
around it inherits the doubt. The five copies also show how the error
propagates: one wrong transcription, pasted with confidence into every artefact
that needed the fact.

**Why it survived.** 2026 is this project's present, so the digits looked at
home among every other date in the tree. Nothing checks a date in prose
against a source, and F111's rule - a counter without a falsifying case is not
a measurement - was applied to counters and not to transcription. It is the
sixth instance of F111's class in one session: a value of the right shape,
read as the value that was meant.

**Remediation.** A second-hand fact that enters the tree carries its
provenance label at the point of entry, not only in the conversation that
found it, and the label includes the date of reading. The corrected passages
now do. The structural fix - checking labelled claims against their sources -
is T22's scope and T22 is still open; this entry is the argument for its
priority.

**Reopen condition:** the next externally-sourced date or figure that reaches
the tree without a provenance label, or the next one found wrong.

### F113, 0.39.0.0. The index that cannot drift read an entry's prose as its status

`tools/todo_index.py::state_of` searched the whole status blob for a state
word, and `ENTRY` extends that blob to the first blank line, so it includes the
entry's own explanation of its history. Four entries declaring `` `ready` ``
carried the note *Moved from S8 at 0.32.9.0* and were counted `moved`, which
the generated table renders as closed.

The table under-reported open work by four: 24 of 70 closed rather than 28 of
42 open, tier 1 at eleven rather than ten, S9 holding five tasks rather than
three and S11 three rather than two. T47 is tier 1 and was invisible.

**Why it survived.** `--check` compares the rendered block against what the
same classifier produces, so both sides shared the fault and agreed. A
self-consistency check is not a truth check; regenerating from a wrong
function always reproduces the wrong answer. This is the class F111 named -
a counter with no falsifying case - applied to a classifier.

**Why the first repair was refused.** Reading only the first physical line
also moved T40, whose sprint token is on the second, and T50, whose `done` is
not on the first. Measured before shipping: six entries changed instead of
four. A fix that changes more than the defect is a second defect wearing the
first one's justification. The shipped repair requires the declared backticked
token for `moved` alone and moves exactly the four.

**A fifth instance surfaced from the regression rather than the report.** T61
declared `` `ready` `` and said in the same sentence that it is a decision
rather than work, so the classifier called it `decision` - the right answer
reached from the wrong half of the line. The token was corrected; the guard
added here reports the two halves disagreeing instead of silently picking one.

**Remediation.** `tests/test_todo_index_state.py`, with cases that pair a
declared state against prose naming a different one, so a classifier reading
either half alone can be told from one reading the declaration. Named mutation:
restore `"moved" in lowered`.

**Reopen condition:** the next state word that appears in this file as ordinary
prose, or the next gate whose check consumes the function it is checking.

### F114, 0.39.0.0. The alert count collapses under overlap, hardest where attack is heaviest

`trailing_counts` opens an episode when an oblast goes from no raion under
alert to at least one, and closes it only on an affirmative all-clear of the
last one. Under sustained attack the raions overlap and the oblast never falls
wholly quiet, so a week of alerts counts as one.

**Measured**, eight Kharkiv raions over a seven-day window: twenty
oblast-wide alerts each cleanly cleared count as 20; the same twenty with one
raion's all-clear missing count as **1**; forty single-raion alerts count as
40 when spaced and **1** when staggered to overlap. The same forty alerts, two
answers, differing only in whether they overlap.

**Neither branch is an error condition.** Overlap is the normal state of an
oblast under sustained attack, and a declaration closed by silence rather than
by an affirmative all-clear is the normal behaviour of the source.

**What a reader concluded.** Kharkiv rendered `1` for a week in which it was
under alert almost continuously, beside a caption saying the column counts
alert declarations. The consumer's map shades from the same field, so the most
continuously attacked oblast drew paler than one with six discrete episodes -
measured, bucket 1 against bucket 2. That is F76's failure in a new direction:
the shading stopped measuring how finely an oblast is subdivided and started
measuring how often it fell completely silent.

**Why it survived.** `trailing_counts`' own docstring records of F76 that *the
regression that should have caught it used one raion, so the mutation had
nothing to bite*. That weakness was never repaired. No fixture put two raions
of one oblast into overlapping alert, and a single-raion fixture cannot express
overlap at all, so no mutation of this fold could go red on it. The lesson was
written down and the fixtures were not changed.

**Remediation.** `alert_seconds` and `still_under_alert` on `RecentOblast` and
`RecentArea`, in `state.json` and `feed.json`, bounded by `tools/contract_check.py`
against their own window. The oblast figure is a **union** over simultaneous
raions, not a sum, or it would measure subdivision again in a new field.
Clipped at both edges and clamped at `as_of`, because a source clock ahead of
ours must not publish minutes that had not happened. `alerts_count` stays,
renamed in prose to what it measures: how many separate flare-ups, not how bad
the week was.

`tests/test_trailing_duration.py`, six regressions, every fixture carrying two
raions of one oblast, five named mutations verified red.

**Reopen condition:** the first quantity added to the trailing block whose
regression uses one raion, or the first shading scale that reads `alerts_count`
again.

### F115, 0.39.0.0. A rationale that defended a different quantity than the one rendered

`trailing_counts` and `trailing_areas` both carried: *only an affirmative
all-clear closes one, which means an episode left open by a feed outage stays
open, and the count errs in the direction that does not understate.*

The sentence is true of the alert **state** - an open episode keeps the area
shown as still dangerous - and false of the **count**, which is the number a
reader sees. The identical rule suppresses every subsequent episode, measured
above at forty to one, and the suppression is largest for the most attacked
oblast.

**The same wrong word travelled.** `docs/WEBAPP.md` described `recent_7d[]` as
counting *declarations*, which is precisely the number F76 was logged for
removing, and the consumer's own caption and its `contract_fields` justification
were copied from that row. One sentence in a contract document became three
wrong sentences downstream, in two repositories, in front of readers.

**Why it survived.** No check compares a rationale against the behaviour it
describes, and no check compares a consumer's caption against the producer
contract row it paraphrases. Prose was reviewed as prose; the arithmetic it
claimed was never run against it.

**Remediation.** Both docstrings say which quantity the rule protects and which
it suppresses. The `recent_7d[]` row and the shading paragraph in
`docs/WEBAPP.md` say what the field measures, that it inverts, and which field
a consumer should shade by instead. The consumer's caption and justification
are corrected as F-S41 in its own log.

**Reopen condition:** the next docstring that argues for a rule's direction
without a test asserting that direction, or the next consumer string that
paraphrases a producer contract row with no check joining them.
### F116, 0.39.0.1. Delivery ran four times slower than composition, and neither end recorded it

Three components pace this system. `mavo-collect.timer` and
`mavo-report.service` both carry drop-ins taking them from the base 120 s to
30 s. `mavo-push.timer` carried the base `OnUnitActiveSec=120` and no drop-in
[measured on the host, 2026-08-24]. **Two thirds of the pipeline was tightened
and the third was not, and the third is the only one a reader depends on.**

**What it cost, from the two ends independently.** The report loop composed
2,861 pictures a day: 19,760 `publish.cycle` records over 2026-08-17 to
2026-08-24, median interval 30.2 s, p95 34.3 s, maximum 34.8 s, zero intervals
above 120 s [measured, `/var/lib/mavo/run.jsonl`]. The site accepted 1,290
`mavo-push` connections in 24 hours, and one delivery is two connections
because `accept-state` takes one target per invocation, so **645 rounds against
2,861 compositions** [measured, `sshd` in journald on `vm-site`, 2026-08-23
09:01 to 2026-08-24 08:59]. Four of every five composed pictures never reached
a reader. Zero failed pushes: the channel was reliable and rare, which is why
nothing ever complained.

**The gaps were wider than the nominal.** Median 139 s, p95 139 s, maximum
162 s against `OnUnitActiveSec=120` [measured, 1,289 gaps]. This timer sets no
`AccuracySec`, so systemd's default one-minute slack applies: the same
mechanism D-027 named for `mavo-collect.timer` and repaired there and only
there.

**What it did downstream.** The consumer treats its own reading as current when
the payload is under 120 s old. Payload age at render is report age at push
plus time since the last delivery, so it reached roughly 190 s, and the page
told a reader that something on our side was not working while every component
was healthy. Logged there as F-S45; the cause is here.

**Why it survived.** `run.jsonl` carries three event kinds and nothing else:
`publish.interval`, `publish.cycle`, `sink.opened` [measured, 39,524 lines].
**None of them names a delivery.** This repository instruments the work and not
its effect, so the last stage before a reader is the one stage with no record,
and a cadence nobody writes down is a cadence nobody can find wrong. T71 is
this shape one stage earlier, where the cost is only diagnostic.

`docs/DEPLOYMENT.md` stated the 120 s cadence accurately for every release
since it was written. The document was not wrong; nothing compared it to the
cadence of the loop it feeds. That is T64's shape: a claim about a unit,
correct in isolation, load-bearing only in a comparison nobody makes.

**Remediation.** A drop-in on the host takes `mavo-push.timer` to
`OnUnitActiveSec=30` with `AccuracySec=1s`, confirmed through `systemctl show`
as `OnUnitActiveUSec=30s` and `AccuracyUSec=1s`, with three service completions
observed inside 80 s [measured, 2026-08-24]. **The resulting 24-hour
distribution is not measured and is carried as outstanding** in
`docs/DEPLOYMENT.md` rather than predicted here, the way D-027's own drop-in
was carried until its evidence arrived. The instrumentation gap is not closed
by this release and is not closed by the drop-in either.

**Reopen condition:** the next timer whose interval is set without comparing it
to the cadence of the stage it feeds; or any delivery cadence that changes
again with no record of a delivery in `run.jsonl`.

### F117, 0.39.0.1. A freshness gate on a date, over rows that nothing checks

`docs/DEPLOYMENT.md` opens its host section with `Host state measured:` and a
date, and `tools/docs_audit.py` fails the gate when that date falls more than
fourteen days behind the release being cut. The check passed on 0.38.0.0 and on
0.39.0.0.

**Four rows under it were false.** `Installed` read 0.36.0.1 against a measured
0.39.0.0; `Installed at` read 2026-08-21 08:52:36 against a measured 2026-08-23
13:40:15; `main` read 0.37.0.0 against 0.39.0.0; `Behind by` read one release
against zero [measured on the host, 2026-08-24, by importing the installed
package through its own interpreter and reading the `.dist-info` mtime].

**A deploy happened and was never recorded.** The history table below the
first one ends at 0.36.0.1 marked `current`, and 0.39.0.0 went onto the host
two days later. **Seven releases sit in that gap** [measured, from the
changelog headings], and whether any of them was ever installed **cannot be
recovered**: the filesystem keeps only the current install and nobody wrote the
row at the time. It is marked `[unknown]` rather than reconstructed from the
version numbers, on the same rule that keeps `CITED_DEFECTS_WITHOUT_AN_ENTRY`
from growing invented entries.

**Why it survived.** The gate checks the date and not the rows. A date is cheap
to bump and rows are not, so enforcing freshness selects for updating the one
thing the check reads, and the section's preamble names exactly the divergence
it is meant to prevent (F102) while the protection against it is a timestamp.
This is the consumer's `producer_version_read` shape - a pin only an odd read
can move, going stale in bursts - inside the document that exists to describe
the host.

**Remediation, and what is deliberately not done.** The rows are re-measured
with the commands that produced them, the history table gains its row, and the
gap is named. **The gate is not extended in this release.** A check that reads
the host is one this gate cannot run, by construction, and the section says so.
What *is* inside the perimeter and is not built: comparing the `main` row in
this table against `STATUS.json`'s `version`, which is a comparison between two
files in the tree. Deferring it is only defensible with a due date, so it has
one: **the next release that touches `tools/docs_audit.py`.** Without that,
this paragraph is a preference wearing a decision's clothes.

**Reopen condition:** the next time this section's date moves and a row under
it does not; or the first release in which the `main` row and `STATUS.json`
disagree.
### F118, 0.39.1.0. Two backlog entries outlived the facts they asserted, and the index that cannot drift could not see it

**T62 was closed by the tree and stayed open in the backlog.** Its acceptance
was that both identifier parsers admit a letter suffix and the counts are
re-derived. `ENTRY` in `tools/todo_index.py` is `^## (T\d+[a-z]?)\.`,
`decision_entries` is `^## (D-\d+[a-z]?)` and `cited_decisions` is
`\bD-\d{3}[a-z]?\b` `[measured, from the tree]`. `T8a` and `T8b` appear in the
generated index and `D-012a` counts separately in a pin of 32. Every clause of
the acceptance held, and the entry sat `ready` through six releases.

**T72 asserted the wrong files.** It named `tests/test_obs.py` and
`tests/test_store.py`, "about fifteen sites". The run that closed it found four
sites and neither file was among them: `tests/test_rso.py`,
`tests/test_latency.py`, `tests/test_sprint8.py` and `tools/latency.py`
`[measured]`. The last is not a test at all, so the entry's own title -
"the suite leaks handles" - was narrower than the defect.

**Why the index could not catch either.** `tools/todo_index.py` reads the state
each entry *declares* and says so in its own docstring: an entry that lies about
itself is counted as it declares. That is a correct design and it bounds what
the instrument is for. The consequence, which was not written down, is that the
one thing the backlog is not gated against is **its own factual content**, and
both halves of this defect are that: a completed task declaring itself open,
and an open task describing a tree that had moved.

**The generated block is not implicated and neither is the checker.** Both did
exactly what they promise. This is the shape the consumer's `TODO.md` header
anticipated in prose when it made provenance labels mandatory on load-bearing
figures inside entries, and it is the same asymmetry as F115: the number is
gated and the sentence beside it is not.

**Remediation.** Both entries closed with the reading that closed them named.
**No check is added**, and the reason is not cost: a checker that could verify
an entry's factual claims would have to re-run the acceptance test of every
open task on every build, which is the build. What is available instead is the
discipline the closing of these two suggests - an entry's claims are re-read
when the entry is next touched - and a discipline is not a gate, so this
paragraph is a preference and is labelled one.

**Reopen condition:** the next backlog entry found to be closable on evidence
already in the tree, which would make three instances and an argument for
sampling open entries against the tree on some cadence rather than none.

### F119, 0.39.1.0. A context manager that commits and does not close, read as if it closed

`with sqlite3.connect(path) as conn:` commits or rolls back the transaction on
exit. **It does not close the connection.** Four sites in this tree used it as
though it did: `tests/test_rso.py`, `tests/test_latency.py`,
`tests/test_sprint8.py` and `tools/latency.py` `[measured, grep]`.

**The correct pattern was already in the tree, seven times.** `mavo/store.py`
wraps every connection in `contextlib.closing`, and `tests/test_store.py` even
names that pattern in a docstring. So this was not a thing nobody knew; it was a
thing that looked done at four call sites, in the shape of the guard rather
than the guarantee.

**How it surfaced, which is the part worth keeping.** It did not surface from
reading. It surfaced because a release ran the suite on CPython 3.14, where the
unclosed connections were reported as sixteen `ResourceWarning`s, against a
build container on 3.12 where the same suite printed none `[measured, both
runs, 2026-08-24]`. **The defect was interpreter-visible and environment-hidden,
and the matrix is the only reason it was seen at all**, which is the argument
for a version matrix stated as evidence rather than as policy.

**Why it survived.** `filterwarnings` was absent from `pyproject.toml`, so
warnings printed into a summary block below a green result. A warning nobody
reads is a finding the suite discarded, and the suite discarded this one on
every run for as long as the sites existed.

**Remediation.** The four sites use `closing()`. `filterwarnings = ["error"]`
is in `pyproject.toml`, which closes T72 and makes the next such warning a
failure rather than a paragraph. The flag is the receipt; the handles were the
work, which is what that entry said.

**Two things the closing run taught that the finding did not.**

**The failure names a file with no database in it.** With the flag on, 3.14
fails `tests/test_obs.py::test_enabling_bodies_leaves_a_mark_in_the_record_it_weakened`
with seven unraisable warnings. That module contains no `sqlite3` at all
`[measured, grep]`. `pytest` attributes an unraisable to whichever test was
running when the collector fired, not to the one that leaked, and the seven
belong to `tools/latency.py` reached through `tests/test_latency.py`, which
sorts immediately before `test_obs`. **A report that names a file is not a
measurement of where the fault is**, and reading it as one would have sent the
repair into the wrong module. Recorded because T72's own entry had already
guessed at file names once and been wrong, and this is the mechanism that makes
that guess easy to keep making.

**Three of the four sites were repaired and the fourth was asserted to be.** The
edit that fixed them ran as one script, the script raised on an unrelated
assertion partway down, and `tools/latency.py` sat below the raise. On the
build container - CPython 3.12 - the whole gate then ran green over an
unrepaired site, and the drafts of this entry, of T72's closure and of the
changelog all said four. **This is the release's own class committed inside the
release that logs it**: a claim written from an intention rather than from a
reading. It was caught by the 3.14 job, which is the second time in one release
that the matrix rather than the author found the thing.

**Reopen condition:** the next warning class the suite is found to be printing
and passing over, or a `filterwarnings` entry added to silence one rather than
to fix it; or the next edit script whose partial completion is reported as
completion.

### F120, 0.39.1.0. One timestamp ahead of our clock disables the staleness machine

`Report.staleness_s` subtracted the newest source timestamp from `as_of`, and
`feed_state` compared the result against `valid_for_s`. **A negative age passes
that comparison**, so one event stamped in the future pinned the feed to `ok`
for as long as it stayed the newest row.

**Measured on a scratch store before the repair** `[measured, 2026-08-26]`:

| store | published state | `observation_age_s` |
| --- | --- | --- |
| real traffic, newest row 6 h old | `degraded` | 21,600 |
| the same store plus one row stamped +1 min | `ok` | -60 |
| dead 7 days plus one row stamped +1 year | `ok` | -31,536,000 |

The third line also published `source_last_message_at` in 2027 and an empty
`events` block, because `event_window` has always excluded stamps after
`as_of`. **Two readings of one row, one line apart in the same file**: the
window treated it as not yet real and the freshness basis treated it as
evidence.

**The realistic cause is our own host, not the channel.** The stamp comes from
the page's `<time datetime=...>` attribute, so any backward drift of the
collector's clock puts *every* event in the future and makes `degraded`
unreachable. `trailing_counts` already clamps `ts_source` against `as_of` for
durations, with a comment recording that T40 measured the two clocks
disagreeing **in both directions**. One module treated the skew as a hazard,
the module that decides whether the picture may be trusted treated it as
evidence, and neither knew about the other.

**Why it survived.** Every fixture in `test_sprint10.py` and
`test_trailing_duration.py` stamps its events at or before `as_of`, which is
what a well-behaved source does. A guard that only fires outside the
well-behaved case cannot be seen by fixtures drawn from inside it - the same
shape as F76 and F114, one field over. T54, *observe the staleness machine
crossing once on a real host*, is tier 1 and still open: the one instrument
that would have met this has not been run.

**The repair.** The freshness basis is the newest stamp no further ahead than
`SKEW_TOLERANCE_S`, the age is floored at zero, a store whose every row is past
the tolerance is `blind` rather than fresh, and the disagreement is published
as `clock_skew_s` instead of being absorbed into the sign of a number. The
tolerance is 120 s and is **[assumption, unmeasured]**; the measurement that
replaces it is the negative tail of `ThreatEvent.latency_s` over a week on the
host, which the store already carries and nothing has read for this purpose.

**Not repaired here, and named so it is not mistaken for repaired.** The
content fold is untouched: an area whose newest row is a future event still
publishes that row's state. Whether the picture may call itself fresh and what
the picture says are different questions, and fixing them in one commit would
have left neither pinned.

### F121, 0.39.1.0. The corpus is read with a different text normalisation than the channel

`read_snapshot_messages` stripped tags and stopped. `_strip`, which every live
poll goes through, additionally turns `<br>` into a newline and decodes HTML
entities. **So every published corpus measurement was taken against a text the
classifier never sees**, and the divergence runs in both directions on a single
message `[measured, 2026-08-26]`:

```
corpus reader : '&#33; Відбій тривоги в #Кам&#39;янець-Подільський_район'
live reader   : "! Відбій\nтривоги в #Кам'янець-Подільський_район"
state         : CLEAR   /  None
tags          : ()      /  ("Кам'янець-Подільський_район",)
```

The corpus **over-reads states**, because a marker broken by `<br>` is rejoined
with a space, and **under-reads areas**, because an undecoded entity breaks the
tag pattern at the apostrophe. They do not cancel: they bias different
measurements in different directions.

**What rests on it.** `kind_coverage_1h`, `kind_join_coverage_1h`, the
`unmapped_tags` pile, and the near-miss review that produced the current
`KIND_MARKERS` table under F71. Three of the 127 rows in `tag_map.csv` carry an
apostrophe `[measured]`; whether the channel serves those as `&#39;` is
**[nieustalone]** and is the frequency question T78 exists to answer.

**Why it survived.** The reader was moved into the package at 0.31.0.0 under
the argument that a copied reader is two readers that can disagree, and its
docstring has said "one reader, one answer" ever since. The move fixed the
duplication and left the divergence, and the tree still holds six page-walking
loops split across two normalisations: `consistency_check`, `label_sample`,
`register_probe`, `threshold_sweep` and `west_activity` use `_strip`;
`kind_coverage`, `unmapped_tags` and `vocab_gaps` did not.
`tests/test_backfill_reader.py` pinned the reader against a fixture carrying no
entities and no `<br>` - **a fixture written by the implementation rather than
against it**, which is the recurrent class in this register.

**Consequence to state plainly:** this repair does not correct the affected
figures, it invalidates them. The re-run with the difference recorded either
way, including a zero difference, is T78.

### F122, 0.39.1.0. The manual's onboarding transcript, from a parser deleted twenty-eight releases earlier

`docs/MANUAL.md` section 4.5 printed `messages=3 parsed=2 unparsed=1` for
`mavo collect --stub tests/fixtures/channel.html`. The tree produced
`messages=3 parsed=0 unparsed=3` `[measured, 2026-08-26]`. The transcript was a
run of the pre-sprint-7 parser, which read oblast names out of prose; the
fixture beside it was a page in that same dead format, and F23 measured that
model at 0 of 20 against real content.

**The fixture was referenced by no test.** Eight test modules build their own
page inline through a local `_page()` helper. The only thing pointing at
`tests/fixtures/channel.html` was the manual, which pointed a first-time reader
at it as the offline smoke test - so the documented first run demonstrated a
pipeline that understood none of its input.

Two more errors in the same section: it said the command "does not yet write to
the store; that lands with continuous collection in sprint 6", fifteen releases
after `--store` shipped under F96, and its option table did not list `--store`
either. Four options across the CLI had no row in the manual at all
`[measured]`: `rso --category`, `rso --page`, `report --feed`,
`report --interval`.

**Why it survived: the gate audits the manual's shape and not its contents.**
`manual-audit` has been a `verify` step for nineteen releases and checks that
every subcommand has a section, that every section declares a kind, and that
the three gate thresholds are quoted. All three were green throughout. A manual
that falls behind is worse than none because it is believed, and the first
thing a reader believes is the output block - the one artefact nothing compared
against anything.

**The repair.** `manual-audit` executes the fenced transcripts and compares the
first line, with `latency=` and timestamps masked as varying; and it fails when
a CLI option has no row. Execution is restricted to `mavo collect --stub`,
because every other command either reaches the network or constructs an
`EventStore`, which creates the directory it was pointed at: **a check with a
side effect is a check that changes its own answer.** The fixture is a page in
the current channel format, and the transcript the manual has always printed is
now the transcript the command produces.

### F123, 0.39.1.0. The skipped-window measurement cannot fire on the deployed path

T18 is recorded as done, sprint 5, with the acceptance "consecutive polls
compare post ids and report the skipped count". `_last_id` lives on the
`TelegramChannelSource` instance; `_cmd_collect` builds a fresh source on every
invocation; and `mavo-collect.service` is a `oneshot` under a 30 s timer. **No
two polls have ever met in one process on the host.** Three consecutive
invocations against one stub `[measured, 2026-08-26]`:

```
poll 1: messages=3 parsed=2 unparsed=1 skipped=unknown
poll 2: messages=3 parsed=2 unparsed=1 skipped=unknown
poll 3: messages=3 parsed=2 unparsed=1 skipped=unknown
```

F27 records that the post id is *the only thing that makes a skip observable*,
and this is the defence against a mass alert overrunning the twenty-message
window - which is the one condition under which the whole product matters. It
has been unmeasurable since deployment.

**Why it survived.** The acceptance was met, by a class that production never
instantiates. `_cmd_collect` even prints a note explaining that a single poll
has no baseline "under continuous collection, which holds the source open", and
continuous collection is not what runs: the note describes an architecture the
deployment does not have and reads as a caveat rather than as an outage.

**Not repaired in this release**, and the reason is sequencing rather than
effort. The cursor has to live where two invocations can both reach it, which
is the same question D-034 raised for the age of the last successful poll and
T66 answered differently for the same feed: the store holds `feed_attempts` for
RSO with a comment calling it a debt this project owes itself, and T66 records
that attempt completeness for the channel "lives in journald and in
`run.jsonl`, not in the store". **Two answers to one question in one tree.**
A decision settles it and the work is one entry behind it; the number is
issued when that entry is written, by reading the log. The acceptance test is
written and held outside the suite until then, because a permanently red gate
is a gate nobody reads.

**This entry reserved D-035 in its first draft**, a number taken at the same
release by the decision that tags stay unsigned. It was inferred from
`decisions_recorded` in `STATUS.json` instead of read out of the decision log,
which is the act D-030 forbids. **`make verify` was green over it**, and that
is the part worth logging: `docs_audit` fails on a cited `D-` number with no
entry, and it did fail the moment the citation was corrected to the next
unissued number. It cannot fail on a number whose entry exists and is about
something else. **A referential check does not catch a semantic collision**, and the
repair is not a better check but not reserving numbers in advance.

### F124, 0.41.0.0. The schema guard prescribes a repair that deletes the evidence

`EventStore._refuse_an_older_schema` refused a store that was missing a column
from any of its four tables, and the refusal named one remedy for all four:
rebuild from the raw corpus rather than migrate, per D-013. That is correct for
`events` and `kind_events`, which are derived - every row is reproducible from
the pages on disk, and an in-place migration would invent values no row ever
carried.

**It is destructive for the other two.** `feed_attempts` is a record of what
this program did at moments that will not come again, and `communiques` holds
a third party's messages from an endpoint that pages away. Neither is
derivable from the corpus or from anything else, so executing the prescribed
remedy on a store refused for their sake **deletes the only copy**. The guard's
instruction is the loss it exists to prevent, one table over.

**It was about to fire.** D-036 adds `elapsed_s` to `feed_attempts`. Under the
old guard the production store on `vm-mavo` becomes unopenable on the first
poll after the deploy, `mavo collect` exits 7 every 33 seconds, and the
documented fix throws away every attempt record the host holds. The defect was
found by writing the release that would have triggered it, which is the only
reason it was found at all: nothing in the gate can see a store it has never
opened, and no test in the tree had ever built a `feed_attempts` table one
column short.

**Class two, and the fifth instance in the register.** A mechanism shaped like
a guard whose guarantee runs the wrong way. The three earlier ones failed to
protect; this one protects and then instructs the caller to do the damage
itself, which is worse, because a reader following the message believes they
are recovering.

**Repair.** `DERIVED_TABLES` and `RECORDED_TABLES` are separate lists with the
reasoning beside them. A derived table missing a column is still refused, and
the message now states which tables its remedy covers. A recorded table gains
the column: `ALTER TABLE ... ADD COLUMN`, nullable, no default, so every row
written before the column reads NULL - the value that means "not measured"
everywhere else in this project and the only one that is not an invention. A
column this version has no type for is still a refusal, with a remedy that does
not begin by deleting the file.

**The migration is not silent.** `EventStore.migrations_applied` names what was
added and the commands print it once, at the moment it happens. A repair that
leaves no trace is the same class as the guard that does not guard: the next
reader cannot tell a store that was migrated from one that was always this
shape. `test_an_ordinary_open_reports_no_migration` holds the other half, so
the line is information rather than noise.

**What is still unenforceable.** No check here can open the store on the host.
The three regressions build the three shapes by hand - a derived table one
column short, a recorded table missing a column this version knows, a recorded
table missing one it does not - because there is no older version of this class
to run and constructing the shape is the closest a repository gets to the
machine it cannot reach.

### F125, 0.41.0.0. A backlog entry attributed to a lint a claim the lint does not make

T80 argued that `mavo report --watch` cannot compose D-034's field from
`run.jsonl`, and gave as its authority: "`tests/lint_domain.py` asserts that
the pipeline never reads its own reader, 'one writer, one record, one
direction'". Read on 2026-08-29, the function is
`check_the_pipeline_does_not_import_its_reader` and what it asserts is that no
module under `mavo/` imports `tools.progress`. That is a ban on one import of
one module. It says nothing about the report path reading a sink, and it would
pass a `mavo/report.py` that opened `run.jsonl` directly.

**The conclusion survives; the citation does not.** The report path genuinely
cannot read the log, because `mavo collect` is a `oneshot` and `mavo report
--watch` is a separate long-running process, so the only state they share is
the store and the filesystem - and because "one writer, one record, one
direction" is a real principle in `docs/OBSERVABILITY.md` section 6 that the
lint enforces one instance of. The entry reached a true conclusion by citing a
check that does not support it.

**Class three, and this is the register's cheapest instance of it.** The
conclusion was drawn from the file that was open - the entry's author knew the
principle and knew a lint enforced something in that family - rather than from
the file the conclusion was about. Nothing failed, nothing broke, and the cost
is entirely to a later reader who follows the citation to check the argument
and finds it does not say that.

**Why it is logged rather than corrected in place.** T80's sentence is being
rewritten this release anyway, as the task closes. An entry that quietly
repairs its own false premise stops being evidence about how the work is done,
which is the rule T20 established when its own gating assumption turned out to
be false. The correction is in the task; the record that the argument rested on
a misread check is here.

**No repair is proposed, and that is a position.** Widening the lint to forbid
`mavo/` reading `run.jsonl` would encode the instance rather than the class,
which is F100's note, and nothing is currently trying to do it. What would
change that is a second reason to want the report path reading a log, at which
point the principle is worth a check rather than a sentence.

### F126, 0.42.0.0. One note asserted one cause for three different states

`mavo collect` printed, on every poll whose skipped count was unmeasurable:

```
NOTE: skipped is unknown, not zero. A single poll has no baseline to measure a
skipped window against.
```

There are three ways to reach that branch and the note asserts one of them.
**No store**, so nothing could have kept a baseline. **A store with no earlier
page bound**, which is a first poll and resolves itself on the next one.
**A page carrying no post ids at all**, with a baseline sitting right there -
which is what a restructured page, a changed markup, or a hostile response
looks like, and is the only one of the three worth waking up for.

**F44's class, in the diagnostics rather than in the schedule**: a line whose
outcomes do not separate its hypotheses. A reader seeing this note could not
tell a healthy first poll from the channel having stopped serving post ids, and
the second is the failure F27 named as the one with no error code. The note was
also written as a permanent property of the command - "a single poll has no
baseline" reads as an architectural fact rather than as a state - which is how
it survived F123 being logged against the same branch without anybody reading
it as a defect.

**Found while repairing F123 and not by it.** The cursor work made the second
case resolvable and the third case newly distinguishable, and the note went on
saying the same sentence for all three. Logged separately because the repairs
are separate: F123 is a cursor that could not survive a process, this is a
diagnostic that could not distinguish its own causes, and fixing one does not
fix the other.

**Repair.** Three branches, three sentences, and the third quotes the baseline
it has: `the baseline is post 301 and this page carried no post ids at all`.
`test_a_page_with_no_post_ids_says_which_unknown_it_is` builds exactly that
state - a good page, then an id-less one - and asserts the note names the
right cause.

**One thing rewritten in the same release is not a defect and says so.**
`_window` set its cursor with `max(last, self._last_id or last)`. The `or`
reads as a guard against a falsy cursor and guards nothing: it substitutes
`last` when the cursor is `None` or `0`, and `max(last, last)` equals
`max(last, 0)` for every positive post id, so every input produced the same
value. It is written out because the field is now seeded from outside the
process, where a reader has more reason to ask what a zero would do. Checked
before rewriting rather than claimed afterwards, and recorded here because a
release that quietly rewrites an expression under a defect number it does not
deserve is padding the register.
