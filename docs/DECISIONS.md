# DECISIONS

```
Document:  docs/DECISIONS.md, version 2.0
Audience:  a contributor about to propose something that was already rejected,
           and anyone asking why an obvious approach was not taken
Companion: MECHANISMS (decisions at the level of one mechanism), FOUNDATIONS
           (the assumptions underneath), METHODOLOGY (what went wrong anyway)
Note:      every entry carries what would reopen it. A decision without a reopen
           condition is a preference wearing a decision's clothes
```


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

## D-002. A covariate that measures null is excluded, not merely unused
Date: 2026-08-05. Status: rejected (the covariate), adopted (the rule it set)

**Decision.** A candidate covariate that has been tested against the
attack-density series and returned a null does not enter any rule, score or
feature afterwards. The exclusion is enforced by `tests/lint_limitations.py` at
the term level, and the excluded terms are enumerated there rather than in the
documents: a guard has to name what it forbids, and that is the only place the
requirement applies.

**Reasoning.** The case that set this rule was tested on the full series, not a
subset: 738 attack nights, 87,093 munitions, September 2022 to April 2026.
Rayleigh R = 0.013, p = 0.95 on the directional test; Spearman correlation with
intensity r = +0.03, p = 0.44; mean covariate value on attack nights 49.1%
against a population mean of 50.1%. Three tests, one series, no effect at any
of them.

The general rule matters more than the instance. A variable that has been
measured to nothing is not neutral to leave lying around: it stays plausible,
it stays easy to reach for when a rule underperforms, and the next person to
reach for it will not repeat the measurement. Excluding it mechanically costs
one lint and removes a whole class of future argument.

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
Status: **superseded by D-014 (0.8.0.0).** Left in place with its reasoning intact: a decision log that deletes a superseded entry loses the ability to show what was believed and why.

Date: 2026-08-05. Status: adopted

**Decision.** A rule exceeding two alarms per week fails the gate outright,
regardless of precision, recall or lift.

**Reasoning.** Above that rate the audience learns to ignore the channel, which
destroys the product's only function. It is also an attack: an adversary who can
induce sub-threshold conditions can exhaust attention for free.

**What would change this.** Measured recipient behaviour showing tolerance for a
higher rate, which is an empirical question and not a preference.

## D-008. One shared alarm budget, allocated by measured demand
Status: **superseded by D-014 (0.8.0.0).** Left in place, same reason.

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
the page is a twenty-message window. *(Recorded as reasoned, and later found
false: the preview pages backwards, F44. The decision's conclusion - wait for a
corpus rather than fit to a sample - survived its wrong premise; the schedule
built on the premise did not, and 0.5.0.0 reordered it. Left in place because a
decision log that edits its own reasoning after the fact is a changelog of
opinions.)* A week spent redesigning against a sample
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

**Reasoning.** This project already abandoned one analysis for fitting to noise.
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

## D-012a. The boundary, computed and frozen
Date: 2026-08-09. Status: adopted, applies D-012

The corpus was retrieved on 2026-08-09: post ids 260841 to 321520, 60,680 posts
across 3,034 pages, spanning 2026-04-13 to 2026-08-09, contiguous with no
holes. The boundary below was computed from those ids **before any message
content was read**, which is the only property that makes it a holdout rather
than a test set chosen with hindsight.

| Window | Post ids | Posts | Share |
| --- | --- | --- | --- |
| Design | 260841 to 309380 | 48,540 | 80.0% |
| Holdout | 309381 to 321520 | 12,140 | 20.0% |

The boundary falls on a page edge because a page is the indivisible unit on
disk. That is why the split is 80.0% rather than exactly 80%.

**Frozen.** Moving this boundary after seeing a result is not a refinement, it
is the null result this project was built around, repeated with more data. If the
frozen table scores badly on the holdout, the response is a recorded defect and
a new sprint.


## D-013. The event store is a derived artifact, versioned by its parser

Date: 2026-08-09. Status: adopted

`content_hash` deliberately excludes `kind` and the message text: identity means
"this area entered this state at this moment according to this source". A
reclassification of the same transition - the exact thing the sprint-7 redesign
will produce for every message the 0/20 table misread - is a better *reading* of
an event, not a new event. Under `INSERT OR IGNORE` that has a sharp
consequence: appending re-parsed events to a store built by the old parser
silently keeps the old rows and drops every corrected one. The store would
preserve the defect the redesign fixes, invisibly, at the moment of fixing it.

The decision is not to widen the hash. Widening it to cover `kind` or the text
makes every parser improvement mint new identities, so a re-ingest *duplicates*
history instead of correcting it - the same defect with the opposite sign.

The decision is to name what the store is. **The raw page corpus is the
evidence; a store is a reading of it, and a reading is versioned by the parser
that produced it.** A new parser writes a new store from the raw corpus; it
never appends over an old parser's rows. This is already how the repository
works - `backfill` writes pages and nothing else precisely so parsing can happen
"later, from disk, as many times as the redesign needs" - so the decision
records the practice and closes the one path that contradicts it.

Trigger to reopen: a live, append-forever deployment where rebuilding from raw
pages stops being cheap. At that point a `parser_version` column and a stated
migration rule replace this convention, in the same release.


## D-014. The attention budget is removed; a lift floor takes its place
Date: 2026-08-09. Status: adopted, superseding D-007 and D-008

**Decision.** The two alarms per week limit is removed. It is no longer a gate
condition, no longer a constant in `mavo/baserate.py`, and no longer an
allocation refused at policy construction. The gate keeps three conditions:
recall at or above 0.90, **the lower bound of lift at or above 1.5**, and a
one-sided Fisher p at or below 0.05. The alarm rate is still computed and still
printed, labelled as measured and not gated.

**Reasoning, in the operator's words and not softened.** The budget encoded an
assumption about how a recipient behaves at a given notification frequency, and
nobody had measured it. Users who care will leave the tool on and moderate the
push settings themselves; users who do not will mute it and open it when they
are worried. Modelling that behaviour from an armchair and then hard-coding the
model as a refusal is the same error this project refuses everywhere else: a
plausible mechanism, encoded before measurement.

**What the budget was accidentally doing, and what replaces it.** With the
alarm-rate condition removed, a rule firing on every campaign night has perfect
recall and a p-value of 1e-03, so it passes on the two remaining conditions
while telling the recipient nothing they did not have from the calendar. The
budget had been serving as an accidental proxy for "the firing must carry
information". The lift floor states that directly, and states it at the *lower*
bound of the precision interval rather than the point estimate, because with a
dozen positive events a point lift moves by a factor on one night either way.
On the measured scenarios: a rule firing on 57% of nights reaches a lower bound
of 1.01 and fails; on 30% it reaches 1.92 and passes; on 14% it reaches 3.70.

**What was lost, stated plainly rather than argued away.** Alarm fatigue as an
attack surface is no longer refused by construction. An adversary able to
induce firings can no longer be stopped by a rate condition; what remains is the
poison check, the lift floor, and the recipient's own notification controls. The
author considers this an acceptable trade because the removed control rested on
an unmeasured number. This paragraph exists so that a future reader can weigh
that trade rather than discover it.

**Measured consequence, recorded rather than tuned.** On the adversarial
synthetic history, `R1-border-active` now passes the gate at 2.52 alarms per
week with a lift lower bound of 1.69. Through 0.7.x nothing passed. The margin
over the floor is thin, and the history is synthetic, so this is a statement
about the machinery and not about the world.

**What would change this.** A measurement. If mute and unsubscribe rates are
recorded once the channel exists and show that recipients disengage above some
frequency, that frequency returns as a condition with a number behind it. The
successor to T11 is that measurement rather than two conversations.


## D-015. The tool reports a picture; it does not predict a crossing
Date: 2026-08-09. Status: adopted

**Decision.** The product is a real-time situational report about the threat
picture on the Ukrainian side, with area resolution and distance to the Polish
border. Predicting a crossing is out of scope, permanently, and no output may be
phrased so that a reader can mistake one for the other.

**Reasoning.** A crossing is the outcome of processes none of the available
feeds observe: interception, where debris of an intercepted munition falls,
navigation failure, and an adversary's choices minutes earlier. A predictor
trained or tuned against roughly a dozen positive events would be fitting to
noise generated by mechanisms it cannot see, which is the failure this project
was founded on refusing. Reporting what is happening now, faster and more
completely than anything else available to a private person, is both achievable
and useful, and it is what the observation of 30 July showed to be missing: the
whole episode lasted thirteen minutes.

**What this changes, and it is more than wording.** The dozen crossings stop
being the target variable, so T28 stops blocking and the corpus no longer needs
to be long enough to contain them. The 57% base rate stops being the number to
beat. The gate, with recall, lift and Fisher, applies to an alarm class alone,
if one is ever built; the reporting tier is judged on correctness, latency and
completeness, all measurable on the corpus in hand. Area resolution stops being
a supporting gazetteer and becomes the core of the product (D-016).

**What would change this.** Evidence that a specific, mechanically explicable
precursor is observable in the feeds and precedes crossings, pre-registered and
tested on data it did not generate. Not a correlation found by searching the
same series.

## D-016. Geocoding is a versioned file, not a service call
Date: 2026-08-09. Status: adopted

**Decision.** Area resolution uses the Ukrainian state administrative register
(KATOTTG, КАТОТТГ, successor to KOATUU) as a file in the repository, joined to centroids
and boundaries from OpenStreetMap. Distance from each area to the Polish border
is computed once, offline, and stored as a column. No geocoding API is called at
runtime, by this or any other provider.

**Reasoning.** A commercial geocoding API would produce the same numbers and
would add three things this project refuses: a runtime dependency and an API key
in the warning path, a rate limit on the one path where latency is the product,
and a third party who learns which rajons a Polish user is asking about at three
in the morning. A file has none of those, is auditable, is diffable, and works
with the network down, which is the state the tool most needs to survive.

**Practical shape.** The register gives the hierarchy hromada, raion, oblast
with stable codes, which is exactly the mapping the channel's wording needs
(F23: the shipped table keyed on oblasts while the channel emits the smaller
units). Distance to the border is a precomputed scalar per area, so a message
becomes "Yavorivskyi rajon, Lviv oblast, 34 km" without a single network call.

**What would change this.** Nothing about convenience. Only a demonstration
that the register is unusable for the wording the channel actually emits, which
is an empirical question the design window can answer.

## D-017. The channel is consumed at its own pace, under one identity

Date: 2026-08-09. Status: adopted

**Decision.** MAVO consumes the Telegram channel from one address, under one
identity, at a rate it can state publicly. Rotating IP addresses, distributing
requests across proxies, or otherwise obscuring the consumer from the source in
order to raise throughput is refused. Rejected while re-collecting the corpus
after losing it (F68), when the question "could we stress-test the limit
anonymously" was the obvious next thought.

**Reasoning.** Three, in ascending order of weight.

It would measure the wrong thing. The question worth answering is not where the
limit is but whether the requirement sits below it, and the requirement is one
poll every two minutes (T39). Probing for a ceiling we do not intend to
approach is looking for a block.

It would make availability depend on concealment. A warning system whose feed
survives only while its consumer is unrecognisable to its source has a
dependency it cannot supervise, cannot document, and cannot hand to anyone else
to operate.

It would cost the argument. `docs/FEED-SPEC.md` asks Polish institutions for a
feed that is public, unauthenticated and honestly consumable, and it rests on
the observation that the Ukrainian channel could be verified rather than taken
on trust. A project that simultaneously rotated addresses to extract more from
someone else's preview page forfeits the standing to ask.

**What would change this.** Not throughput. Only a demonstration that ordinary,
identified consumption at the required rate is refused *and* that no faster
interface exists — and the second half is already false, because MTProto is a
push interface and is the answer to the latency question anyway (T41).

## D-018. Collection does not scale; delivery does

Date: 2026-08-09. Status: adopted

**Decision.** The collector runs as exactly one process on one always-on host
that the operator controls (T25). Moving it to cloud infrastructure is a
decision about *availability*, not about throughput, and it is taken on those
grounds or not at all. The scalability question belongs to the delivery side and
arrives with M2, when the number of recipients stops being one.

**Reasoning.** One channel, one stream. A second collector instance adds no
throughput: it doubles the request rate against a source this project is
deliberately careful with, and it produces two copies of the truth about one
window that then have to be reconciled. Under the push interface (T41) it is
starker still, since that is a single long-lived connection under a single
identity and replicating it is meaningless.

What genuinely fails today is uptime, and it failed visibly during the corpus
re-collection: a laptop taken out of a clamshell stand is an outage, and in a
log an unplanned one is indistinguishable from a gap in the channel. That is
the argument for a host, and it is sufficient on its own.

The side that does scale is delivery. `docs/MOBILE.md` already records that an
ntfy instance serving one operator is a container while the same instance
serving an open subscriber list is a service with an availability target, which
would be the first component here to have one.

**Consequence for T39, and it is not optional.** The two successful backfill
runs went out over a residential connection. Data-centre address ranges are
treated differently by most anti-bot layers, so moving the collector to cloud
infrastructure changes the consumer's profile and **invalidates both
observations**. The tolerated-rate ladder restarts from five minutes on the new
address; it does not continue. Recorded here because the alternative is somebody
migrating the host and assuming the measurement travelled with it.

**What comes with the host, into `docs/DEPLOYMENT.md` before the move rather
than after.** An MTProto secret on someone else's machine, tier-1 corpus data on
someone else's disk, and a Telegram identity linked to the operator administered
remotely. None is a blocker; all three are things to write down first.

**What this does not license.** Being in a cloud is not an argument for moving
the alarm path onto managed push. The constraint in `docs/MOBILE.md` is
infrastructure the operator controls, which a VPS satisfies as well as a box
under a desk; FCM and APNs are a third party on the path that wakes a person,
and that is a separate decision with separate reasoning.

**What would change this.** A measurement showing that one collector cannot keep
up with the channel, which the window arithmetic currently says is not close, or
a second independent signal (ADS-B, T20) whose collection genuinely parallelises
because it is a different source rather than a second reader of the same one.

