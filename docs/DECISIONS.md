# DECISIONS

One entry per decision, including the ones that felt obvious. The last field is
the one usually omitted and the one that keeps a decision from becoming dogma.

## D-001. Codename in documentation, descriptive slug, unique namespace
Date: 2026-08-05. Status: adopted

**Decision.** The repository slug is `air-alert-early-warning`, the import
namespace is `mavo`, and the codename MAVO lives in documentation.

**Reasoning.** A slug is a search term and should be boring. An import path is a
namespace and must be unique rather than descriptive; five generic top-level
packages in an earlier repository planted five collision candidates in
`site-packages` on every install. The codename carries the thesis and belongs
where a reader is already reading prose.

**What would change this.** Publication to PyPI under a name collision, or a
decision to ship several related tools that should share a namespace prefix.

## D-002. Lunar illumination is excluded, not merely unused
Date: 2026-08-05. Status: rejected

**Decision.** No astronomical variable enters any rule, score or feature. The
exclusion is enforced by `tests/lint_limitations.py` at the term level and the
variable is not named in package source.

**Reasoning.** The hypothesis was tested on the full series: 738 attack nights,
87,093 munitions, September 2022 to April 2026. Rayleigh R = 0.013, p = 0.95.
Spearman correlation of illumination with intensity r = +0.03, p = 0.44. Mean
illumination on attack nights 49.1% against a population mean of 50.1%. No
plausible mechanism survives contact with the guidance systems actually in use.
An earlier analysis built on this variable was formally retracted.

**What would change this.** A published mechanism tied to a specific guidance or
acquisition mode, plus a pre-registered test on data not used to generate the
hypothesis. A fresh correlation found by searching the same series does not
qualify and is the exact failure being guarded against.

## D-003. Explicit rules, not a learned model
Date: 2026-08-05. Status: adopted

**Decision.** Rules are hand-written predicates with thresholds in
configuration. Runtime dependencies stay empty.

**Reasoning.** The positive class is roughly a dozen events across four years.
Any model fitted to that reproduces the overfitting that invalidated the first
analysis, and is unauditable besides. Explicit thresholds are falsifiable.

**What would change this.** A positive class in the hundreds, from a real
multi-year dataset with independent validation, and a use case where a human
cannot inspect the decision.

## D-004. Not a competitor to the state alerting system
Date: 2026-08-05. Status: adopted

**Decision.** No pursuit of mass adoption. The tool is positioned one step
earlier in the chain and says so.

**Reasoning.** The announced government application inherits a fourteen-million
user base and official authority. More importantly it is fed by the same
detection chain as the sirens, so its latency floor is the moment of detection.
This tool reads a feed from before the border, which is a different point in the
chain rather than a competing product. A state actor also cannot tolerate false
positives at that scale, which permanently leaves the early and uncertain niche
vacant for structural rather than technical reasons.

**What would change this.** The state channel publishing an ingestible upstream
feed, which would make the early tier redundant rather than complementary.

## D-005. No web UI, no mobile client
Date: 2026-08-05. Status: adopted

**Decision.** The first output channel is a Signal bot reusing existing
infrastructure. No browser interface.

**Reasoning.** A mobile client is a sprint of work that tests nothing about
whether the signal is worth delivering. Recorded because it is obvious now and
will not be in three months.

**What would change this.** A recipient group that cannot use Signal, or a
requirement to display geography that a text message cannot carry.

## D-006. Apache-2.0
Date: 2026-08-05. Status: adopted

**Decision.** Apache-2.0, matching `phantomatics`.

**Reasoning.** The portfolio currently carries three licences with no stated
reasoning, which is the first thing a partner asks about. This repository is
defensive tooling with no commercial dual-licence intent, and the patent grant is
worth more here than copyleft would be.

**What would change this.** A commercial offering built on the same tree, which
would make the `phantomatics` AGPL-plus-commercial split the better model.

## D-007. Alarm rate is a hard control, not a quality metric
Date: 2026-08-05. Status: adopted

**Decision.** A rule exceeding two alarms per week fails the gate outright,
regardless of precision, recall or lift.

**Reasoning.** Above that rate the audience learns to ignore the channel, which
destroys the product's only function. It is also an attack: an adversary who can
induce sub-threshold conditions can exhaust attention for free.

**What would change this.** Measured recipient behaviour showing tolerance for a
higher rate, which is an empirical question and not a preference.

## D-008. One shared alarm budget, allocated by measured demand
Date: 2026-08-06. Status: adopted

**Decision.** The two alarms per week limit is a property of the recipient. Rules
divide one total rather than each holding their own, allocation follows measured
firing rate with headroom, and an allocator that cannot fit the demand raises
instead of trimming.

**Reasoning.** Two rules each cleared at the full budget produce twice the budget,
which is the number that destroys the channel. Trimming a share silently to make
the sum fit yields a policy that passes its own gate and overruns the person it
is meant to serve, which is worse than a policy that refuses to exist.

**What would change this.** Measured recipient behaviour showing a different
tolerance, or a delivery channel where alarm cost is not attention (a dashboard
rather than a push).

## D-009. Drone regime demoted to the observation tier
Date: 2026-08-06. Status: adopted, provisional

**Decision.** Only the missile regime may raise a critical alarm. The drone
regime runs silent, and the coverage gap is declared in the output rather than
hidden by scoping the denominator.

**Reasoning.** The two-regime policy recovers full recall but leaves 2% of the
attention budget spare, which is not a margin. The drone rule buys its recall by
firing often, because nothing in oblast-level alert state separates a drone night
that ends in a crossing from one that does not.

**What would change this.** A second signal type that discriminates within drone
nights. ADS-B activity over eastern Poland is the leading candidate, which is why
that work is now a prerequisite rather than an enrichment. Real data showing the
discriminator exists in the alert stream after all would also reopen it.

## D-010. Both Ukrainian feeds are one dependency, accepted with open eyes
Date: 2026-08-08. Status: adopted

**Decision.** alerts.in.ua, api.ukrainealarm.com and the public Telegram channel
are treated as a single correlated dependency, not as independent sources.
Two-source agreement between them is never counted as confirmation (MT9). Access
to both APIs is revocable without cause or notice, and the ukrainealarm offer
contract changes unilaterally by being reposted (MT10, T12); the dependency is
accepted on those terms because no alternative feed of Ukrainian alert state
exists at this latency.

**Reasoning.** All three surfaces draw on the same upstream alerting chain, so a
wrong or silent upstream is wrong or silent everywhere at once. Multiple sources
protect against transport failure only. Pretending otherwise would let a
correlated failure masquerade as consensus, which is the exact class of
flattering default this repository is built against. The revocability is a legal
fact of the accepted contract, reviewed in full before acceptance, not a risk
discovered later.

**Which surface is upstream of which is not established.** The working model,
that the channel feeds the APIs, is an inference from public statements, not a
measurement. The correlation conclusion holds under any internal topology; the
relative latency of channel versus APIs does not, and is measured in sprint 6
rather than assumed.

**What would change this.** Either service moving to its own independent
acquisition; the ADS-B channel landing as a genuinely independent observation
(T14); or a Polish source with a stated availability commitment (T8), any of
which would demote this from an accepted single point of failure to one input
among several.

## D-011. The classifier redesign waits for the corpus, not for the schedule
Date: 2026-08-09. Status: adopted

**Decision.** Sprint 5 was scheduled as the pattern-table redesign and did not
run it. The redesign waits until at least a week of real channel content exists
(T19). Sprint 5 instead built the parts of the source layer that determine
whether that content, once collected, can be trusted: the fourth state and
window-gap detection.

**Reasoning.** The table can only be rewritten against observed content, and the
only content in hand is twenty messages from twenty minutes of one evening,
covering four eastern oblasts and no western one. Fitting to it would reproduce
F23 at a smaller scale, which F28 already refused once. Meanwhile the corpus has
a property the code does not: it can only be collected forward in time, because
the page is a twenty-message window. A week spent redesigning against a sample
is a week the corpus is not being collected, and an undetected skip during a
mass alert would put holes in it that nothing downstream could see.

**What would change this.** Seven consecutive days of snapshots with gap
statistics, split into a design window and a holdout window. A gazetteer arriving
sooner would change what the redesign can attempt but not when it should start.

**What this costs.** The alarm tier cannot ship in September either way, because
border crossings run at two to four a year and no four-week window validates
recall. The schedule in `docs/MVP.md` is amended rather than quietly slipped.

## D-012. The corpus is split before it is read, and the rule is written down first
Date: 2026-08-09. Status: adopted

**Decision.** The design window is everything the classifier redesign may look
at. The holdout is everything it may not, until the redesign is frozen. The
boundary is a post id, chosen before any message content is read, and recorded
here: **the holdout is the newest 20% of posts by id in the corpus at the moment
the redesign begins.** Newest rather than oldest, because the redesign must be
tested against the channel as it writes today, not as it wrote in 2023.

**Reasoning.** This project already retracted one analysis for fitting to noise.
The corpus removes the excuse that there was nothing to fit to, and replaces it
with the harder problem: with hundreds of thousands of messages it is possible to
iterate a pattern table until it scores well on everything it has seen and
nothing else. A holdout chosen after looking is not a holdout, and a holdout
chosen by a rule written after the first disappointing result is worse, because
it comes with a story.

**What this costs.** A fifth of the corpus is unavailable during the work that
needs it most, and the first honest score arrives only once. If the frozen table
scores badly on the holdout, that is the finding, and the response is a recorded
defect and a new sprint, not a second look.

**What would change this.** Nothing about convenience. A change in what the
channel emits, a restructuring that makes the newest fifth unrepresentative of
the near future, would justify moving the boundary, and would be recorded as a
scope change with its reason before the new boundary is used.
