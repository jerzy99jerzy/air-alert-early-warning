# DECISIONS

```
Document:  docs/DECISIONS.md, version 2.17
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
(T14); or a Polish source with a stated availability commitment (T8a), any of
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
and useful, and it is what the observation of 30 July showed to be missing.

**The figure this decision originally cited was wrong, corrected 2026-08-10.**
It said the episode lasted thirteen minutes. Checked against reporting: the
object was detected in Polish airspace at 03:40 and disappeared from radar at
03:46, six minutes later, near Tarnawa-Kolonia in Lubelskie `[reported;
Dowodztwo Operacyjne RSZ via Polish press]`. No source found supports thirteen.
The number had been carried in this repository unsourced since the decision was
written.

**The correction strengthens the decision rather than weakening it.** Six
minutes is less room, not more, and the same reporting supplies something the
decision only asserted: Ukrainian fighters were pursuing the missiles up to the
Polish border and their radar signature was hard to separate from the missiles
themselves, which delayed identification. That is the mechanism D-015 names as
unobservable, described from the other side by the people who were watching it
happen.

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

### D-015, revision 1. From reporting instrument to warning infrastructure
Date: 2026-08-10. Status: adopted. The text above stands as the record of the
earlier position; this revision supersedes its framing and not its boundary.

**Decision.** MAVO is designed as an element of warning infrastructure rather
than solely as a situational reporting instrument. The design target is to be
the best available warning channel on the interval *before* a potential
crossing, judged on its own merits rather than against what the sirens, the RCB
text alerts or the RSO application do. Good situational awareness is the
product; latency is a property of it, not an enrichment of it.

**What does not change, and it is the part that matters.** The epistemic
boundary above holds in full. MAVO does not predict crossings; the 0 of 22
result stands, and no output may be phrased so that a reader can mistake a
report for a prediction. Being a warning channel means delivering the Ukrainian
picture faster and more legibly than the alternatives, not claiming to know
what crosses. `docs/FEED-SPEC.md` section 6 says sirens remain the fastest
channel to a sleeping person; that describes a different interval, after a
crossing and inside Poland, and is not in tension with this revision.

**What changes.**

1. **Silence becomes a liability rather than a gap.** A reporting instrument
   that goes quiet has missing data. Warning infrastructure that goes quiet is
   telling its reader the sky is calm. Heartbeat, staleness on the face of the
   output, and an explicit blind state move from backlog to core requirement.
   `docs/FEED-SPEC.md` section 4 was written about the Polish feed that does
   not exist; it now applies to this project's own output.
2. **Latency becomes a measured property end to end**, from channel post to
   state to rendered page. T39, T40, T41 and D-018 move from a backlog thread
   into the core. The MTProto latency claim in T41 stays
   `[inference, unmeasured]` until it is measured: infrastructure does not get
   to assume its own speed.
3. **T11 is a blocker rather than a formality.** Two conversations with
   recipients is the floor before shadow mode, not a box to tick.
4. **T6 escalates from a September date.** The distance between what the tool
   claims and what a reader does with it at half past three is a design
   surface, not a legal afterthought.
5. **Public framing follows.** Once this ships, no description of the project
   as pure reporting is accurate. The notifications sentence removed from the
   LinkedIn draft is a temporary hedge to revisit rather than a settled
   position.

**Reasoning.** Stated by the operator on 2026-08-10: sirens fail by reach and
audibility; machine data fails differently, by a silence that looks like calm.
That asymmetry is the one this repository documents about itself (F69, and
FEED-SPEC section 4), so accepting it as a design constraint is consistent
rather than novel. Designing to be best-possible on the pre-crossing interval
is the honest version of what the project was already doing, and the
reporting-instrument framing was in part a hedge against a responsibility now
explicitly accepted.

**What would change this.** T11 surfacing recipients who treat the output as a
take-cover signal despite the framing, which would reopen whether this posture
is tenable without institutional backing. A regulatory development making an
unofficial warning channel untenable for a private operator in Poland. Or
shadow-mode measurement showing end-to-end latency cannot in fact beat the
channels this means to precede, in which case the claim is withdrawn from the
framing rather than softened in it.

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
interface exists - and the second half is already false, because MTProto is a
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

## D-019. ADS-B visibility of military aircraft: measured, aggregated, published
Date: 2026-08-10. Status: adopted

**Decision.** MAVO consumes OpenSky Network state vectors for the western box
(latitude 48 to 52, longitude 22 to 27) and may publish an aggregate count of
transmitting military aircraft in the report and on the site. Raw vectors -
positions, callsigns, ICAO24 addresses - stay in the offline measurement layer
and are not published.

**Reasoning.** ADS-B is voluntary emission. An aircraft broadcasting on 1090 MHz
has chosen to be visible, and an operator that wants silence switches the
transponder off, which is routine practice. Aggregating public emissions is
standard and openly practised OSINT; this project adds no collection capability
and no datum unavailable to anyone with a receiver. During a war, logistics
activity at a hub is part of the situational picture a reader near the border
is entitled to see.

**The counterargument, recorded and rejected.** Raised in review on 2026-08-10:
a Polish-language threat-awareness site aggregating "ISR active over
Podkarpacie now" lowers the access threshold to information about defensive
assets, which inverts the argument this project makes in `docs/FEED-SPEC.md`
section 5, where the information defended was already broadcast by siren.
Rejected on the grounds above. The aggregate-only publication form is kept as a
hedge rather than as an admission that the objection holds.

**Semantics of the published figure, which is the load-bearing part.** The
count is a lower bound on *transmitting* aircraft and not a measurement of
activity. A high number means something; a low number means nothing, and
transponder silence plausibly correlates with exactly the situations a reader
would most want to know about [inference from operational practice,
unmeasured]. The field carries that framing in itself rather than in a
footnote. A zero rendering as calm would be this repository's founding failure
wearing a new coat.

**Preconditions before the field ships.** Sampler measurement across at least
three nights, one of them with a western-Ukraine alert, establishing the base
rate, its variance by hour, and the frequency of a null response. A schema
version bump on `state.json`, because FEED-SPEC section 3 property four is a
requirement this project wrote for others and therefore owes its own consumers.
And no participation in any score: the figure is reported, never weighed, the
same separation applied to the 96.5% of front-line traffic.

**What would change this.** A request from a Polish or allied institution to
withhold the field. Evidence that the aggregate is being cited as
targeting-relevant in a way raw trackers are not. A change in OpenSky's terms
restricting redistribution of derived aggregates. Or a measured base rate so
low that the field carries no signal, in which case it is dropped for being
uninformative rather than for being dangerous.

## D-020. The contract file is written by the producer, not inferred by the consumer
Date: 2026-08-10. Status: adopted

**Decision.** MAVO writes `state.json` itself, through `mavo report --json`.
The schema lives in `mavo/report.py` and is exercised by this repository's own
gate. The companion site reads that file and nothing else: no import of
`mavo`, no traversal of the event store, no knowledge of the domain types.

**Reasoning.** The site was built with an adapter that imported MAVO, walked
its store and read attributes off its domain objects, and the binding was
honestly labelled `[inference]` because it had never run against the package.
Its own pre-flight tool exists to discover which attribute names are wrong.
That arrangement puts the contract in the hands of the party that cannot check
it: a rename in `AreaRef` passes MAVO's gate, ships, and breaks the site
silently, at a moment nobody is watching a web page for regressions. Ownership
belongs where the checking is. The producer publishes a file with a schema
version in it; the consumer validates that version and refuses what it does
not understand.

**This is also what `docs/FEED-SPEC.md` asks of everyone else.** The
specification demands a public feed with codes rather than prose, both
transitions, a versioned schema and a heartbeat. Consuming our own output
through an inferred adapter, while asking a ministry for a versioned schema,
would be arguing a case this project does not follow. The `state.json` in
section 5 of `SITE-ARCHITECTURE.md` and the payload in `mavo/report.py` are
now the same artifact, written once.

**What this costs.** The site's adapter and its MAVO-introspection checks
become dead code and should be deleted rather than left as a second path. Two
readers of one contract is how the schema drifts.

**What would change this.** A consumer needing a projection MAVO has no reason
to compute, which would be an argument for a second exporter rather than for
an adapter reaching into the store. Or a measurement showing the file write is
a bottleneck under load, which the window arithmetic says is not close.

## D-021. One review per major release, and the ones that never got one are named
Date: 2026-08-10. Status: adopted

**Decision.** A review is written for every **major** release, meaning a change
to the second version component: 0.19.x to 0.20.0.0 needs one, 0.20.0.0 to
0.20.1.0 does not. `tools/docs_audit.py` fails the gate on a major release with
no file in `docs/reviews/`, and the releases that shipped without one are a
frozen list in that check rather than a date cutoff.

**Reasoning.** Four documents said this repository files one review per
release. It had filed nine for fifty. The rule was not being broken by
carelessness: reviews kept being written, and kept landing in session artifacts
outside the tree, so the practice continued while the record of it stopped
(F79). At five releases in an afternoon, one per release is a rule nobody can
follow, and a rule nobody can follow is not a stricter version of this one, it
is an absent one wearing a stricter one's language.

**Why a frozen list rather than a cutoff date.** A cutoff would silently absorb
the next release that skips a review, which is exactly how the first nineteen
accumulated. Adding a version to `UNREVIEWED` is an edit somebody makes on
purpose, in a file the gate reads, with a sentence in `docs/reviews/README.md`
saying why.

**What a review is, and what forbids writing them backwards.** A reading of a
tree by somebody who does not yet know what they will find. Three were filed
late at 0.20.1.0, unedited, each carrying a note saying when it was written;
that is legitimate because the reading happened. Producing a file now for
0.12.0.0 from the changelog would assert that something was examined when it
was not, which is the fabrication the rest of this apparatus exists against.

**What would change this.** A run of majors where the review finds nothing
three times running, which would suggest the trigger is wrong rather than the
practice. Or a move to release trains, where the unit worth reviewing stops
being the version number.


## D-022. A default argument may not select a superseded implementation

Sprint 7 replaced the oblast-stem area table with the register map and left the
old one behind `areas=None`. `probe()` - the whole live path - passed nothing,
so the product ran the superseded implementation for two sprints while the
repair sat one argument away (F90).

**The decision.** When an implementation is replaced, the old one is deleted in
the same release. A caller that has not been updated fails loudly or does the
new thing; it never silently gets the old behaviour. A `None` default that
means "use the version we stopped believing in" is the worst available option,
because it is invisible at every call site and reads as a convenience.

**Why not a deprecation warning instead.** A warning printed by a library into
a process nobody is watching is the same class of mechanism as the assertion
that failed here: it addresses a reader who is not there. Deleting the code
makes the compiler and the test suite the readers, and both are present.

**What this cost, stated so the cost is not forgotten.** Deleting `AREAS`
turned seven tests red, and repairing them meant rewriting three fixtures. That
work was not incidental to the deletion; it *was* the deletion doing its job,
surfacing the tests that had been written against the old implementation and
had been quietly passing ever since.

**What would reopen it.** A replacement that genuinely needs a migration window
- an external consumer on the old behaviour, which this project does not yet
have. In that case the old implementation stays reachable under a name that
says what it is (`classify_with_the_pre_sprint7_table`), never under a default,
and the name carries the release in which it goes.

## D-024. The event stream: two files, a twenty-minute window and a day

**Decision.** The contract gains an event stream at schema v3, published in two
places from one composition. `state.json` carries `events`, a twenty-minute
window of every transition, with `window_start` beside it. `feed.json` carries
the same shape over twenty-four hours. Both carry **all of Ukraine** and
**both roles**, `subject` and `continuation`. A cap of 5,000 events applies to
either window, with `truncated` in the payload when it binds.

**Why a stream at all.** `state.json` v2 carried the current picture and
seven-day counts and no history. A consumer cannot build a panel of what
happened tonight from a picture of now, however the page is written, and the
contract belongs to the producer (D-020), so the absence was ours to fix
rather than the site's to work around.

**Why two files rather than one longer window.** They have different costs.
`state.json` is re-read on every cycle and every open tab pays for it; a day of
history there is a recurring charge on a phone that may be on one bar during
exactly the night it matters. `feed.json` is fetched when a reader opens the
history and then obeys ordinary HTTP caching. Measured against the same budget
as the geometry: roughly 800 events a day is about 18 KiB gzipped, 1.2 seconds
on 120 kbit/s once, against 0.3 KiB per cycle for the short window.

**Why twenty minutes and not sixty.** Operator's decision, 2026-08-12. A dead
collector empties the panel three times faster, and the panel emptying is a
signal the page exists to deliver. The cost is that a device asleep for longer
than the window cannot distinguish a gap from a quiet stretch, which is why
`window_start` is published rather than left to be derived: the consumer
compares it against its own last successful read and refuses to render
continuity across a hole.

**Why all of Ukraine, and not the west.** The first draft filtered to the eight
western oblasts on a bandwidth argument. Measured, that argument was weak:
1.2 seconds once on the worst line this project designs for. The stronger
reason against filtering is that a quiet twenty minutes in the west during a
night when the east is burning is a different fact from a quiet night, and a
reader near the border is entitled to both. `counts_24h` splits west from rest
so the page can say which it is.

**Why both roles.** One message can clear an area and list five others as still
under alert: one `subject`, five `continuation`. A stream carrying only
subjects would drop the five areas that are still dangerous. This repository
has already made that loss once, in the 4,064 continuation areas discarded
before T37, and F82 is the same family.

**Why the cap is 5,000 rather than 200.** The first proposal said 200, on a
figure of "a dozen transitions a day". That figure described **western** areas
while the stream carries **all** of Ukraine: two denominators for one number,
the shape of T49. Measured: production ingested 27 events in 97 minutes on
2026-08-11, which is about 400 a day, and the per-message estimate over the
corpus gives about 800. A 200-event cap would have bound every single day,
which makes it a window with a misleading name and makes `truncated`
permanently true and therefore useless. At 5,000 the cap binds only above six
times anything measured, so `truncated` firing is itself a measurement.

**What would reopen it.** `truncated` going true, which turns the cap from a
safety net into a design parameter and means the window needs re-thinking
rather than raising. Or a measurement showing consumers fetch `feed.json` far
more often than the design assumes, which would collapse the cost argument for
the split.

## D-026. Beta stops depending on anyone asking for it

**Decision.** The beta definition in `docs/MVP.md` loses its middle clause.
Beta is the reporting instrument, live, with its correctness and latency
measured and published. Whether anyone has asked for it no longer bears on the
version number, and the blocker row for it is gone from the readiness table.

**Reasoning.** The clause was written when the only imagined delivery was a
push to two named phones, and in that world it was the same thing as consent.
It is not the same thing now. The site has been publicly reachable since
2026-08-12; who visits it is not a property of the instrument, is not
controlled by this repository, and does not shrink by writing code. Asking
permission to exist and being correct are different questions, and only the
second is what a version number should turn on.

**What did not change, and this is the part worth reading twice.** T11 still
gates **push delivery**. Waking somebody's phone at three in the morning
requires that they asked; a page they chose to open does not. The two were one
clause because the project once had one delivery path, and separating them is
the whole content of this decision. `docs/MVP.md` section 3 keeps the
requirement where it belongs, and the README keeps saying that recipients are
gated by T6 and T11.

**What stays in the way of beta.** Correctness measured on western areas
(T36), and end-to-end latency as a distribution rather than as fetch time per
poll (T40). Both are properties of the thing rather than of its audience, and
neither is close.

**What would reopen it.** A delivery path that pushes rather than waits,
at which point the consent question returns to the definition, because it is
then a property of what the instrument does rather than of who happens to read
it.


## D-027. The poll interval goes to thirty seconds

**Decision.** The channel is polled every 30 seconds rather than every 120,
and the report loop follows at the same cadence. `--interval` defaults to 30.

**What the change buys.** Two things, and the second matters more.

The obvious one is freshness: the floor on channel-to-render latency was half
the poll interval on average, so it falls from about 60 seconds to about 15.
On a page whose subject is announced in seconds, that is not a rounding error.

The one that decided it is **the cost of a missed poll**. The collector fails
on roughly one attempt in eight, measured, and consecutive failures happen: the
longest observed gap between successful reads was 7.0 minutes against a
600-second staleness threshold, leaving three minutes of margin rather than the
eight an independence assumption predicted. At 30 seconds the same run of two
failures costs 90 seconds instead of 390, and the margin stops being the thing
standing between this page and a degraded state nobody has ever watched it
enter.

**Why this is not rude to the source.** Measured on 2026-08-12: ten requests
in fifty seconds all returned 200 with a median of 0.24 s, a rate twenty-six
times more aggressive than the interval this decision replaces and five times
more aggressive than the one it introduces. That is evidence about a burst
rather than about a sustained rate, and the difference is stated rather than
glossed: a limiter that tolerates a burst can still act on a sustained
quadrupling.

**How we will know if it is.** T55 shipped at 0.26.0.0, so every refusal now
carries its elapsed time and exception class. A source that starts throttling
produces fast refusals with a recognisable shape, and the journal will say so
within a night. **The unreachable rate is the number to watch: if it rises
after this change, this decision caused it.** That is the measurement that
would reopen this entry, and it is available without any new work.

**What was deliberately not done.** No retry inside a poll, and no change to
the ten-second timeout. Both would mask the symptom T39 is still chasing, and
the interval change is defensible on its own terms while a retry would confuse
two questions.

**Correction, 0.28.1.0 (F98). The arithmetic above understates the cost of a
failure, and the decision survives the correction with a smaller margin than it
claimed.** Two errors, one in this repository and one on the host.

The ten-second timeout was ten seconds *per socket operation and per resolved
address*, not per attempt: a failed collection was measured twice at 20 seconds
on 2026-08-13. F98 makes the number a deadline for the whole fetch, so from
this release the figure the paragraph above uses is the figure the code
enforces. It was not, when the paragraph was written.

The second error is in the unit file rather than here, and it is
[reported, from the production host, not reproduced in this repository]:
`OnUnitActiveSec` measures from activation, so a failed run displaces the
following cycle by its own duration, and `AccuracySec` defaults to one minute,
which systemd may spend coalescing wakeups. Start-to-start intervals were
60, 37, 53, 33, 37, 37 and 33 seconds against a nominal 30 plus 5 of jitter.
At a 120-second interval this was invisible; at 30 it is the dominant term.

**Consequence for the decision.** A run of two failures costs more than the 90
seconds stated above, and the margin against the 600-second staleness threshold
is correspondingly smaller. The decision still holds - 90 or its corrected
value are both far below 390 - but the number in it was derived rather than
measured, and this entry should carry a measured cadence once the host has run
one uninterrupted hour with `AccuracySec=1s` in place. **That measurement is
the outstanding item on this decision**, and until it exists the margin here is
an estimate, not a bound.

**The outstanding measurement, taken 2026-08-14. This entry no longer rests on
an estimate.** [measured, on the production host, one uninterrupted hour]

`AccuracySec=1s` was applied to `mavo-collect.timer` and confirmed in place
(`systemctl show` reports `AccuracyUSec=1s`). One hour of the journal, read
after the change:

| | Start-to-start interval, nominal 30 s + 5 s jitter | n |
| --- | --- | --- |
| Before | 33, 37, 37, 37, 53, 60 s | 7 intervals, 2026-08-13 08:53-08:58 |
| After | 31 s ×20, 32 ×21, 33 ×24, 34 ×18, 35 ×23, 36 ×1 | 107 intervals, 2026-08-14 09:00-10:00 UTC |

Mean after: 33.06 s. Spread fell from 27 s to 5 s. The distribution is flat
across 31-35 with a single value at 36, which is the shape `RandomizedDelaySec=5`
predicts, and its theoretical mean is 32.5 s; the +0.56 s residual is
[inference] attributable to process spawn, against poll latencies of 0.29 to
0.60 s measured the previous day.

**Confirmed at twenty-four times the scale, 2026-08-17.** [measured, on the
production host, 24 hours] n=2619 start-to-start intervals: min 30.06, p50
33.00, p90 35.00, p99 35.01, **max 36.06** against the configuration's
theoretical ceiling of 36 s. The one-hour figure above was not a lucky window,
the mean is unchanged at 33.0, and **the caveat attached to this entry - that
the margin is an estimate until a measured cadence exists - is discharged.**
Method and units are in `docs/DEPLOYMENT.md`, which carries the date the host
was read.

**What this settles.** The hypothesis written into the drop-in was that
`AccuracySec`, rather than the duration of the run itself, dominated the
jitter. It did. Had the after-distribution still carried a tail near 50 s, the
mechanism in the paragraph above would have been wrong and this entry would
have needed rewriting rather than closing.

**Two facts that came free with the same reading.** 3600 / 33.06 = 108.9 and
108 polls were recorded, so the hour has no missing cycle [measured]. No
interval exceeded 36 s, so no poll in that hour hit a timeout, unlike the
window the day before which contained a 20.12-second failure and the 60-second
gap that followed it [inference from the interval distribution].

**The margin is now a bound rather than an estimate**, for this cadence on this
host. It stops being one if the interval changes, if `RandomizedDelaySec` is
removed, or if an hour appears with intervals above 40 s that no long-running
poll explains. The unreachable rate named earlier in this entry remains the
measurement that would reopen the decision itself.

**Provenance note.** The before-distribution was not instrumented for this
purpose. It was recovered from a journal excerpt pasted while checking
something else, which is why it has n=7 and the after-distribution has n=107.
An old behaviour already sitting in a log is cheaper than instrumenting for it
and cannot be contaminated by knowing what the change was meant to do; worth
looking for one before changing any timing in this project again.

## D-028. The ADS-B sampler: sixty seconds, raw vectors, and a record of every attempt
Date: 2026-08-14. Status: adopted

**Decision.** T42's sampler polls OpenSky `/states/all` over a box around
Rzeszow-Jasionka once every 60 seconds, stores **raw state vectors and never
derived landings**, keeps 8 days, and writes one row per poll attempt beside
the observations. It runs on `vm-mavo` as a separate unit, user and store, and
is not in this tree (`docs/DEPLOYMENT.md` section 2 says why).

This decision is about **collection**. D-019 governs publication and is
unchanged by it: the aggregate-only rule, the lower-bound semantics and the
preconditions all still hold, and nothing here brings a field closer to the
page than D-019 already allows.

**The box is not D-019's box.** D-019 samples the western box, latitude 48-52
and longitude 22-27, for transmitting aircraft over western Ukraine. This one
is latitude 49.75-50.47, longitude 21.35-22.69, roughly one square degree
around the airport, and it extends west of longitude 22 where D-019's does not.
Two boxes for two questions, stated here so a later reader does not merge them
into one dataset.

**Why raw vectors rather than landings.** Deriving a touchdown from ADS-B is a
guess that will be rewritten after the first week of real data, and an
interpretation can be recomputed over stored vectors any number of times while
an hour that was never polled does not come back. Writing the interpretation
first would have fixed a guess into the only record that exists.

**Why 60 seconds and not 300.** Credits are not the binding constraint: 1,440
of a 4,000-per-day allowance, and unused credits do not carry over, so a longer
interval saves nothing that can be spent later. The binding constraint is that
an approach through the box lasts roughly five minutes, so a 300-second
interval samples the phenomenon at its own period and yields one point per
approach or none. Aircraft that transmit intermittently would then be dropped
**selectively rather than randomly**, and that subset is the one with
diagnostic value. Over-sampling can be thinned at read time; under-sampling
cannot be undone. [inference, from approach speed and box size; the first week
either supports it or does not]

**Why 30 seconds was not chosen either.** 2,880 of 4,000 leaves 28% for retries
and restarts. Exhausting the allowance mid-afternoon would produce a hole whose
shape is indistinguishable from an outage, which is the failure this project is
built against.

**The attempt log, which is the load-bearing part.** A `polls` table records
every attempt, its HTTP status, its result count and whatever the server said
about remaining credits. Without it, an hour in which nothing was observed and
an hour in which the sampler was dead are the same empty set in storage, and no
care at rendering time recovers a distinction that was never written. The count
of results is **null for a failed poll and zero for an empty one**, and a
regression exists whose data can tell those apart, because a schema that cannot
represent the difference collapses it back at the first timeout. This is
`docs/FEED-SPEC.md` section 4 applied to this project's own consumption rather
than asked of somebody else, and it is written up there as property nine.

**Interval is a coverage parameter, not a setting.** Changing it mid-window
makes that window's sampling density non-uniform, and any chart drawn across
the seam has to say so rather than average over it. The `polls` table records
real timestamps, so achieved cadence is measurable rather than asserted; D-027
is the precedent for why that matters.

**What this does not become.** Not a drone-tier source. The premise that it
might be is recorded as false: Shahed-type munitions and cruise missiles carry
no transponder, and no sampling rate changes that. What is observable is the
operating intensity of a logistics hub, reported and never scored (D-019, T42).

**Cost per call is unmeasured at the time of writing.** The published allowance
is 4,000 per day and a small box is the cheapest bracket, but whether
`x-rate-limit-remaining` is returned on this endpoint has not been read from a
response yet. Until it is, the budget arithmetic above is [inference] and the
60-second choice is defended by resolution alone.

**What would reopen this.** The first week showing that adjacent samples add
nothing, in which case 120 or 300 seconds is right and the seam is documented.
A measured cost above one credit per call, which changes the arithmetic. The
deliverable narrowing to hourly density with no aircraft-level classification,
which removes the resolution argument entirely. Or the free-trial expiry, which
is a harder date for this collector than for anything else in the project: the
alert store is reconstructible from `data/raw` and from the channel, and a
rolling window of observation is reconstructible from nothing.

## D-029. The API's `type` is a category of alert, not a means of attack
Date: 2026-08-14. Status: adopted

**Decision.** `api.ukrainealarm.com`'s `type` field will not be used to resolve
`ThreatKind`, and no `ThreatKind` member will be added because that API has a
corresponding category. The field is recorded, mapped and reported by
`tools/api_kind_compare.py`; it reaches nothing else.

**What the field is.** Five categories: air alert, artillery, street fighting,
chemical, radiological. [reported, 2026-08-14, from three independent
descriptions: Ajax Systems' account of the Air Alert app it built and which
feeds this API, the Home Assistant integration's sensor list, and the
alerts.in.ua client library's typed accessors. Not [measured]: no response from
this project's key has been read, and `tools/api_kind_compare.py` prints the
returned vocabulary precisely so that this entry can be upgraded or reopened.]

**Why it cannot answer the question.** `AIR` covers a drone, a glide bomb, a
cruise missile, a ballistic missile, a MiG-31K takeoff and a threat from the
sea, under one value. **The single question a reader has - what is coming - is
exactly the one the category does not answer.** `ThreatKind` comes from a
different stream entirely: the channel's own declaration messages, which the
API does not model in any field.

**How the mistake was made twice, which is the part worth recording.** A
category and a kind have the same shape - a short enum hanging off an alert -
so the field reads as an answer. This project planned work on that assumption
and then wrote a recommendation on it, both before anybody read what the values
mean. Neither error was caught by reasoning; both were ended by reading a
description of the vocabulary. **The fixtures made it worse rather than better:**
all five in `tests/test_sprint13.py` use `"type": "AIR"`, a value invented by
whoever wrote them. That they happen to be right is coincidence, not
verification, and a suite full of one invented value looks exactly like a suite
full of measured ones.

**On the members that were asked for.** CHEMICAL, NUCLEAR and URBAN_FIGHTS get
no `ThreatKind` member here. The criterion is the one `ThreatKind.ARTILLERY`
states about itself: a member exists when **the channel names the thing and the
schema cannot hold it**, which is what F71 measured before 0.19.3.0 - messages
rejected whole for want of a member. Whether this channel names chemical,
radiological or street-fighting threats is **unmeasured**, and it cuts both
ways: if it does not, the members would be unreachable and the site would carry
legend entries for categories it can never draw; if it does, those messages are
being discarded today and this is a live defect rather than a feature request.
A corpus count decides it and has not been run.

**What must not follow from this entry.** That the API is useless. Its two
purposes stand and are why the adapter exists: end-to-end latency for T40, and
area coverage against the pattern table. Neither needs the `type` field.

**Reopen if:** the returned vocabulary contains a value outside the five;
the provider documents a sub-type or a free-text description beside the
category; or a corpus count shows the channel naming a threat this schema
cannot hold, which reopens the enum question on its own terms rather than on
this API's.

## D-030. A task identifier is issued by reading the file, never from memory
Date: 2026-08-14. Status: adopted

**Decision.** The next `T<n>` is `1 +` the highest number present in `TODO.md`,
read from the file in the same session that writes the entry. Precedence
resolves a collision: the entry that held a number first keeps it, and the
later entry is renumbered together with every reference to it.

**Class.** The same mechanism as a version typed at tag time: a value issued
from memory rather than derived from the artefact it must be unique within.
Three identifiers were each issued twice, one holder months old and one opened
in 0.32.x.

**Why it survived.** The index check counted entries and compared totals, and a
count is blind to identity. Completeness and uniqueness are different questions
and only the first had a check. The cost was realised before it was noticed:
`docs/DEPLOYMENT.md` tracked one `T57` while the changelog closed a different
one, so a sentence naming a task named two.

**Enforcement.** `check_identifiers_are_unique` in `tools/todo_index.py`, wired
into `--check` before the index comparison, because a colliding identifier
makes every later message ambiguous. Verified red against the collision as it
stood and green after the rename.

**What this enforcement does not cover.** The entry regex is `^## (T\d+)\.`,
so a suffixed identifier is invisible to it and a collision between two `T8a`
entries would pass. Named here rather than left implicit, and tracked as T62.

**Reopen if:** an identifier is issued by any means other than reading the
highest number from the file; or a collision is found that the check did not
stop, which means the check's parser and the file's headings have diverged.

## D-031. The collector runs as a systemd timer and a oneshot unit on a Linux VM

**Decision.** MAVO's collector runs on `vm-mavo`, an e2-micro in
`europe-central2-a`, as `mavo-collect.service` (`Type=oneshot`, `User=mavo`)
triggered by `mavo-collect.timer`. Supervision is systemd's: the timer owns the
cadence, the unit owns one poll, and neither owns a loop. The same shape runs
`mavo-push`; `mavo-report` and `mavo-adsb` are long-running units.

**This decision was made by deploying it on 2026-08-11 and is being recorded on
2026-08-17.** T25 asked which host the daemon lives on and carried status
`decision` for six days after the question had been answered by an operator
typing `systemctl enable`. Writing it down now is not bookkeeping: an
unrecorded decision cannot be reopened, because nobody can say what it was.

**Why a timer and a oneshot rather than a daemon**, argued after the fact and
therefore stated as such:

- **A crash is a missed poll, not an outage.** The next timer trigger starts a
  fresh process. A long-running loop that dies stays dead until something
  notices, and the thing that would notice does not exist yet.
- **Attribution is free.** Every poll is its own unit invocation in the
  journal, with its own exit status, which is how the 366-versus-14 timeout
  comparison in `docs/DEPLOYMENT.md` was possible at all. A loop would have put
  the same information inside one process's log, which is the log F103 records
  as never having been written.
- **T25's own argument holds.** A laptop that sleeps writes a record whose holes
  look like quiet nights. A named systemd unit on a VM gives that attribution
  without a signed wrapper, a `KeepAlive` plist or a TCC-safe data directory.

**What this costs, and it is not nothing.** A oneshot per poll pays process
spawn 2,619 times a day; measured at roughly 0.56 s of the 33.06 s mean
interval, which is the residual D-027 attributes to spawn. It also means there
is no process holding state between polls, so anything needing cross-poll
state - a skipped-window count, a session's own cycle numbering - belongs to a
loop rather than to this unit.

**Corrected before this entry shipped, and the correction is F104.** The first
draft continued: *M0 is therefore a new unit, not a change to this one.* That
was inferred from `Type=oneshot` in the unit file without reading the CLI, and
it is wrong. **The loop already exists**: `mavo report --watch --json` runs on
this host as `mavo-report.service`, `publish()` has accepted a `log` since
0.23.0.0, and attaching the run log turned out to be one argument at one call
site. What this entry governs is the *collector*; the loop is a second
long-running unit that was already there and already the right place. The
distinction that survives is narrower than the sentence claimed: the collector
cannot carry cross-poll state, and nothing about the run log ever needed it
to.

**Reopen if:** a poll's work grows to where spawn cost is no longer a rounding
error against the interval; or M0 needs cross-poll state, in which case this
entry governs the collector and a second entry governs the loop; or the host
moves off GCP, which changes the supervision question rather than reusing this
answer.

## D-032. S9's window admits planned restarts of the report loop, and says how many

**Decision.** S9's exit criterion is amended while the window is running. It
now requires 72 hours of **uninterrupted collection** with every cycle
accounted for and every pause named with its cause, and permits **at most two
planned restarts of `mavo-report.service`**, each reported as its own segment
rather than absorbed into a single figure. `mavo-collect.timer` is untouched
for the duration: it produces the evidence and it feeds T40.

**Amending a criterion inside its own window is the shape this project treats
as a defect elsewhere**, so the reasons are stated rather than assumed.

- **The original number was declared, not measured.** "72 hours unattended"
  entered `docs/MVP.md` before the collector had run at all. It survives here
  because it has a defensible reading found afterwards - three nights is the
  minimum at which time-of-day separates from night-to-night variance, and
  ~8,640 report cycles put an upper bound of 3.5e-4 on the unexplained-gap rate
  by the rule of three - and neither of those was the reason it was written.
- **The decision is taken while it is free.** Nothing needs a restart today.
  A rule settled at the moment it becomes expensive is a rule shaped by what
  the author wanted at that moment, which is the rounding-up F102 describes.
- **The permitted restart does not threaten what the window measures.** The
  three things it must show are the latency distribution, the gap rate in the
  collector's cadence, and the `degraded` duty cycle. All three are properties
  of `mavo-collect` and of the store; a five-second restart of the consuming
  loop is visible in `run.jsonl` as a `sink.opened` line and is therefore a
  **named** pause rather than a hole.

**What is refused.** Restarting or reinstalling anything under
`mavo-collect`. That resets the window, with no argument available, because the
collector's continuity *is* the measurement.

**Honest note on the author's interest.** This amendment is convenient for the
rate of work, and convenience is a reason to distrust it. It is recorded with
that stated rather than left for a reader to infer.

**Reopen if:** a third restart of the report loop is wanted inside one window,
in which case the window restarts rather than the limit rising; or any restart
turns out not to be visible in `run.jsonl`, which would make "named pause" an
assertion rather than a record.
## D-033. Delivery is paced to composition, not to a fraction of it

**Decision.** `mavo-push.timer` runs at `OnUnitActiveSec=30` with
`AccuracySec=1s`, matching `mavo-collect.timer` and the report loop rather than
sitting at a multiple of them.

**The alternative was 60 s and it was not obviously worse.** Worst-case payload
age at the consumer would have been roughly 95 s, still under the 120 s the
consumer uses to decide whether its own reading is current, and it would have
doubled the connection count rather than quadrupling it.

**Thirty wins on the shape of the claim, not on the margin.** At 30 s the
property is an invariant a reader can check in one sentence: *every picture the
producer composes reaches the site.* At 60 s the property is a ratio, and a
ratio is a claim about two numbers that must both stay put. Either cadence
moving breaks it silently, which is exactly how F116 happened: the ratio was
one in four and nothing watched either side of it. An invariant survives a
change to one side by failing loudly; a ratio survives it by drifting.

**The cost, named rather than absorbed.** Accepted `mavo-push` connections go
from about 1,290 a day to about 5,760, so journald on `vm-site` grows roughly
fourfold. **Journald retention is unmeasured on both hosts**, which means this
decision spends a budget nobody has counted. That is accepted here as a task
rather than as an assumption; the sibling repository carries the same gap as
TA-09.

**What does not change.** The consumer's stream keys on the content of the
picture rather than on the file's timestamp, so delivering an identical
document does not wake a reader's tab, and the reload cost the consumer tracks
does not rise with this.

**What this decision does not touch.** `RandomizedDelaySec` on this timer. It
was not read in the session that made the change, so it is neither restated as
a fact nor adjusted on the strength of a document.

**Reopen if:** the 24-hour distribution after this change shows a p99 above
45 s, which would mean something other than the interval is pacing it; or
journald retention on either host turns out shorter than the window a
post-mortem needs; or the report loop's cadence moves, in which case this timer
moves with it rather than staying at 30 and re-earning the ratio this decision
refuses.
## D-034. The producer publishes whether it polled, instead of leaving the consumer to infer it

**The measurement this was waiting for.** `feed_state` is computed from the age
of the newest *event*, not of the newest successful poll, so a channel that is
quiet ages into `degraded` while every component is healthy. T65 blocked on the
duty cycle. It is **20.5% of cycles**: 4,051 `degraded` against 15,710 `ok`
over 19,761 `publish.cycle` records, 2026-08-17 to 2026-08-24 `[measured]`. The
daily spread is 13.2% to 32.8% over six full days, so no single figure
describes it and any sentence quoting one is quoting a mean over a range that
doubles.

**Decision: option 2, narrowed to one field.** The contract gains the age of
the last successful poll. Not a fourth feed state (option 1) and not poll
outcomes as rows in the store (option 2 as originally posed, which grows the
store by 2,861 rows a day and changes what the store is for).

**Why not option 3, which is cheapest and which this project would normally
take.** Option 3 was to leave the behaviour and change the sentence. It is
already implemented, by the wrong party: the consumer's `headline()` splits
`degraded` into "the source is quiet and our reading is fresh" and "something
on our side is not working", and it decides which by measuring **its own render
age** against a threshold. That is a heuristic reconstructing a fact the
producer holds and does not publish. It also failed for a fortnight without
anybody noticing, because the delivery cadence pushed the render age past the
threshold on a healthy pipeline (F116), and the consumer logged its half as
F-S45. **A downstream heuristic standing in for an upstream fact is the thing
to remove, not the thing to bless**, and blessing it in a decision entry would
make the accident permanent.

**What it costs and what it blocks on.** The field is cheap; the value behind
it is not, because `mavo collect` writes to `print` and has no sink, so nothing
in this repository currently knows when the last successful poll was without
grepping a journal (T71). **T71 is therefore a prerequisite and this decision
schedules it rather than assuming it**, which is the sequencing D-032 used for
the same shape. Adding an optional field to schema 3 does not break a consumer
that ignores it, so the contract version does not move under D-020.

**Reopen if:** the duty cycle falls below about 5%, which would make the whole
question small enough that option 3's concession is honest; or T71 turns out to
cost more than a fourth feed state would, in which case the two options are
re-compared on measured effort rather than on the shape of the claim.

**F107 closes with this**, having been the anecdote that opened it: eight
minutes on 2026-08-17 gave 13 against 5, which is 27.8% and sits inside the
measured daily range rather than outside it. The anecdote was directionally
right and was labelled as an anecdote, which is the only reason it survives
being quoted here.

## D-035. Tags stay unsigned, and the record says so rather than the reader guessing

**Decision.** Tag signing is out of scope. Every tag this repository has is
annotated and unsigned, and every tag it makes next will be, until something in
the reopen condition below changes.

**The state, measured 2026-08-17** across `v0.3.2.0`, `v0.20.0.0`, `v0.30.0.0`,
`v0.32.0.0` and `v0.32.4.0`: all annotated, none signed, no secret key on the
operator's machine, `user.signingkey` unset. `v0.39.0.1` was cut on 2026-08-24
under the same conditions.

**Why not start now.** A signed tag in the middle of an unsigned series is a
question a reader has to research rather than an assurance they can act on:
they must establish whether the earlier tags are unsigned because the practice
began later or because something failed. Starting badly is worse than not
starting, and this is a single-maintainer repository where a signature attests
to a key nobody has published or cross-signed.

**One claim from T65's entry is not repeated here, deliberately.** That entry
argued signing was unnecessary because "the authorship record this project
already has, Software Heritage and OpenTimestamps", is independent of it.
**Nothing in this tree establishes that either exists** - no archival
identifier, no timestamp receipt, no check. It may well be true and it is not
evidence, and a decision resting on it would be the shape of F100 again:
believing a claim about this repository because a document about this
repository made it. This decision therefore rests only on the measured state of
the tags.

**Reopen if:** a second maintainer can cut a release, which turns a signature
from self-attestation into a distinction; or this project accepts recipients
under T6 and T11, which changes what a reader is entitled to verify; or the
Software Heritage and OpenTimestamps claim is checked and turns out to be
false, which would leave the authorship record resting on nothing and make the
cheap half worth taking.

## D-036. The collector's record is a row per attempt in the store, and the sink keeps the run
Date: 2026-08-29. Status: adopted

**The question, and it had two answers in one tree.** T80: `mavo collect`
leaves nothing either invocation can read, so `skipped` is `unknown` on every
poll the host has ever made and D-034's field has no value to compose from.
Where the record lives was answered twice, differently, and the answer taken
depended on which sprint wrote the collector. `mavo/store.py` holds
`feed_attempts` for the RSO feed - outcome, url, item count, NULL for a
refusal - and its schema comment calls it FEED-SPEC property nine, owed by
this project to itself. T66 records that attempt completeness for the channel
"lives in journald and in `run.jsonl`, **not in the store**". One question,
one tree, two answers.

**Decision.** Every poll of an external feed writes one row to
`feed_attempts`, whichever feed it is. The channel joins RSO in the table it
already has rather than getting a second mechanism next to it. `run.jsonl`
keeps what it holds today, which is the *run*: cycles, intervals, the sink's
own provenance. The discriminator is not the feed and not the sprint. It is
**whether anything in the product reads the record back**. The report path
reads the store and only the store, so a fact the contract must publish lives
in the store; a fact only a person greps lives in the sink.

**What this costs T66, stated rather than absorbed.** T66's sentence is that
attempt completeness cannot live in the store, and its reason is exact: "a
poll that never returned writes nothing, and a quiet channel writes nothing,
and the two are the same row count". That reasoning is about the `events`
table and it is correct about it. It is false of a table with a row per
attempt, which is what `feed_attempts` is and what the `events` table is not.
The premise changes; the conclusion drawn from the old premise does not
survive it. T66's instrument therefore reads the store, and the entry is
corrected with this reason rather than quietly re-pointed.

**What this costs D-034.** That decision names T71 - a `collect.attempt`
record in `run.jsonl` - as its prerequisite, and T80 showed T71 as scoped
cannot deliver it: the field is composed by `mavo report --watch`, which reads
the store. So the prerequisite moves rather than the decision. D-034's chosen
option is unchanged, its field is unchanged, and what it waits on is now a
`feed_attempts` row from the channel. **D-034 also rejected "poll outcomes as
rows in the store" and this entry adopts it**, which is a reversal and is
recorded as one. The rejection rested on two grounds. The first was row
growth, asserted at 2,861 a day and never costed: measured here at **146
bytes a row, 372 KiB a day, 133 MiB a year** at the 33 s cadence with one
refusal in eight `[measured, 2026-08-29, on a synthetic store in a container,
not on the host - the host figure is a deployment reading and is owed]`.
Against a store the host has been filling since 2026-08-11, that is a cost
worth naming and not one worth a second mechanism. The second ground was that
it "changes what the store is for", and that had already happened: T67 put
`feed_attempts` and `communiques` in this file at 0.38.0.0 and nothing
reopened the question.

**What this costs T71.** Re-scoped, not closed. `sink_from_environment()` in
`_cmd_collect` is no longer the route to D-034, and whether the collect path
wants run-level lines in `run.jsonl` for its own sake is a separate and
smaller question with no decision blocked behind it.

**One consequence was found by taking this decision and is worse than the
decision.** Adding one column to `feed_attempts` makes every store written by
an earlier version unopenable, and the remedy `_refuse_an_older_schema` prints
is D-013's: rebuild from the raw corpus. That remedy restores `events` and
`kind_events` and **deletes `communiques` and `feed_attempts`**, neither of
which is derived from anything - a poll attempt is a record of what this
program did at a moment that will not come again. The guard's prescribed
repair destroys the evidence the guard was protecting, and it would have run
on the production host in this release. F124. The tables are now split:
derived tables are refused with D-013's remedy and its scope stated, recorded
tables gain the missing column, nullable and without a default, so a row
written before the column reads NULL. A column this version cannot type is
still a refusal, with a remedy that does not begin by deleting the file.

**Reopen if:** the attempts table outgrows what a person can read on the host
- the measurement above says when, and the answer is retention rather than a
second mechanism, which is what `mavo-adsb` already does; or a second consumer
appears for the run-level record, which would make `run.jsonl` a product
surface rather than a diagnostic one and move the discriminator; or the report
path acquires a reason to read a log, which would be a change to "one writer,
one record, one direction" and belongs in its own entry rather than here.

## D-037. The workflow names its triggers, and the tag run is kept on purpose
Date: 2026-08-29. Status: adopted

**Decision.** `.github/workflows/ci.yml` triggers on pushes to `main`, on tags
matching `v*`, and on pull requests. The tag run stays.

**What was there.** `on: [push, pull_request]`, no filter, which runs the
matrix on every branch and every tag. Measured on `v0.39.0.0`: two runs, 38 s
and 40 s, over one commit `[measured, from the run list]`. `mavo-site` refuses
the same duplication deliberately under its D-S57 and this repository did not,
which made the difference between the two an accident rather than a position -
T76's actual complaint, and it is answered by naming the triggers whichever way
they are named.

**Why the tag run is kept rather than removed, which is the half T76 left
open.** `actions/checkout` resolves the ref it is given, so the tag run asks a
question the commit run cannot: *does the tree this tag points at pass*. The
release procedure here says to tag on the full commit hash and never on `HEAD`
or `HEAD~n`, and a tag placed on the wrong commit is precisely the failure that
rule exists to prevent. Nothing else in this project can catch it: the local
gate runs before the tag exists, and `make manifest` on the commit push reads
the commit. **The duplicated bytes are the ordinary case and the run is not for
the ordinary case.**

**What it costs.** A second matrix run per release, free here because the
repository is public, and not free in the consumer - which is why D-S57 goes
the other way there and why the two repositories now disagree on the record
rather than by accident. And branch pushes other than `main` stop being built:
this is a single-maintainer repository that works on `main`, pull requests
still run, and a branch that wants a run gets a pull request.

**What this does not do.** It does not make the tag run *verify* anything the
commit run did not, in the case where the tag is correct, and no reader should
take a green tag run as independent evidence about the code. It is a check on
the pointer, not on the tree.

**Reopen if:** this repository stops being public, which makes the second run
cost money and re-weighs it against a check that fires on a mistake nobody has
yet made here; or a release procedure lands that verifies the tag's target
locally before pushing, which would move the check inside the gate where it is
cheaper and earlier.


## D-038. An instrument that reads the store ships in the package
Date: 2026-08-29. Status: adopted

**Decision.** Diagnostic instruments whose input is the event store are `mavo`
subcommands, installed by the wheel and documented in the manual, which the
manual audit polices. Instruments whose input is the tree stay in `tools/`,
where the gate runs them. The discriminator is where the input lives, and it
mirrors D-036's: that decision asked *who reads the record back*, this one
asks *where must the reader stand to read it*.

**Found on deploy day, one command after it mattered.** 0.41.0.0 shipped
`tools/attempts.py` to read `feed_attempts`; 0.42.0.0 gave that table its
first production rows; and the first attempt to read them on `vm-mavo` found
that `pip` installs the package and not `tools/`, so the instrument built for
the production table could not run on the only machine that has one. It was
also in no operator document, because `manual_audit` covers `mavo` commands
and nothing covers `tools/` - two absences with one cause, which is that the
instrument was filed by what it is instead of by where it runs.

**What it costs.** The package gains an import of no runtime weight and the
CLI gains a subcommand; the wheel stays dependency-free. `tools/attempts.py`
remains as a one-screen forwarding shim so a written-down command line keeps
working, and prints where the instrument went.

**Reopen if:** an instrument turns up that reads both the store and the tree,
which this discriminator cannot file; or the host gains a repository checkout
for some other reason, which would make `tools/` reachable and the move
merely aesthetic.

## D-039. `collect` takes no lock, on arithmetic rather than on hope
Date: 2026-08-29. Status: adopted

**Decision.** `mavo collect` does not serialise against a concurrent
invocation of itself. `backfill` keeps its `DirectoryLock`; `collect` runs
bare, and this entry is the reason a reader will not find one.

**The arithmetic.** The timer fires every 30 s with 1 s accuracy; the fetch
deadline is 10 s (F98) and the store writes are milliseconds on the measured
path (0.26 s total poll latency on the host, 2026-08-29). For two invocations
to overlap, one poll would have to outlive the interval, and the deadline
forbids it by a factor of three. `systemd` additionally serialises starts of
the same `oneshot` unit, so overlap requires a *manual* invocation beside the
timer - which deploy day produces, and which is why this entry exists.

**Why the overlap is benign when it happens anyway.** Both invocations read
`newest_page_id`, which is `MAX(last_id)` and cannot be moved backwards by
either writer; both append attempt rows, which do not collide; and event
writes are idempotent by content hash. The worst measured outcome is the same
window's `skipped` computed twice and printed twice, two journal lines for
one fact - noise, not loss. A `DirectoryLock` here would convert that noise
into a refused poll, and T26 records that the lock's liveness check reads pids
through a namespace it does not verify, so the cure carries its own defect
into the one path that matters.

**Reopen if:** the fetch deadline is ever configured at or above the timer
interval, which deletes the arithmetic; or a second writer to the same store
appears that is not this command.

## D-040. `api.ukrainealarm.com` becomes the primary source, immediately
Date: 2026-08-30. Status: adopted

**Decision.** `mavo collect-api` is the production collector from the 0.44.0.0
deploy onward. There is no waiting period and no fallback threshold: the
switch happens the moment the deploy does. The channel collector's timer
stays running beside it - as the watchman for the publisher's return, not as
a source of anything while the channel is silent.

**What forced a decision at all.** The Telegram channel, the only signal
source in use since the project began, stopped publishing on 2026-08-29 at
04:55 UTC on post 334744 and stayed silent through an attack ISW measured at
over 28 hours. Three independent readers (the `/s/` web preview, TGStat,
telemetr.io) see the same last post; the host, the link, the parser and the
cache are each excluded by measurement; the sky was not quiet. The publisher
stopped publishing mid-wave, gave no announcement, and the cause is
unestablished. Meanwhile the official API was measured live on 2026-08-30:
authenticated, answering in about a quarter of a second, carrying 62 alerts begun after the channel
fell silent. A working upstream behind a dead output.

**Why immediately, with the 72-hour window considered and rejected.** A
fallback threshold of 72 hours from the last post (2026-09-01 ~05:00 UTC) was
proposed and had one honest property: it was a calendar convenience aligned
with the CI budget reset, not an epistemic requirement. Every criterion that
would make the switch safe is already met and measured - the API observed
live and authenticated, the adapter through the full gate, all-clear
synthesis closed by tests, the persistence that a `oneshot` deployment needs
shipped in the same release. The threshold's passage would have added no
information about either pipe. This project's own rule says a rule without a
gate check is a preference; a wait without a criterion is the same defect
with a clock on it. And the cost of waiting is not neutral: each cycle spent
polling a dead output while a live path stands measured is manufactured
blindness, the exact condition - silence rendered as something other than
what it is - the project exists to refuse.

**What this is not.** Not a second source. MT9 stands in full: the API and
the channel draw on one upstream, agreement between them is agreement between
two views of one origin, and no sentence anywhere may read "two sources
confirm". The switch buys delivery-path resilience, not observational
independence. `source_id` on every event keeps the pipes distinguishable in
the store, which is also what makes the switch reversible by data rather than
by memory if the channel returns.

**The cost, named.** Three, all bounded and pointing the safe way. *One:* the
all-clear degrades from an announced transition to an inference dated at
observation - the API stops listing an alert rather than ending it, so every
`CLEAR` this source emits carries `Provenance.INFERENCE` and the moment we
saw the absence, not the moment it happened. *Two:* channel episodes still
open at 04:55 that the first API snapshot does not list stay open - the API
cannot close what it never saw. The pre-switch `mavo report` reading in
`docs/DEPLOYMENT.md` establishes whether that set is empty; if it is not,
reconciling it is a named follow-up, never a silent one. *Three:* if the
channel returns while the API collects, both pipes write the same
transitions with skewed timestamps; event writes are idempotent by content
hash, the episode builder treats a duplicate as a no-op, and the store's
labels keep the union's provenance statable - a union of two delivery paths
of one upstream, deduplicated by content, is a sentence someone can say.

**Reopen if:** the API's terms change to forbid this use; its measured
latency or availability degrades below what the channel provided; or a
genuinely independent observation path appears, at which point the question
is no longer which pipe but whether "two sources" can finally be said.

## D-041. Episodes the dead channel left open are closed by observation or not at all
Date: 2026-08-30. Status: adopted, mechanism deferred

**The problem, measured.** On the day of the D-040 switchover the store held
29 areas whose newest event was an ACTIVE from the channel, the oldest stamped
2026-08-28T04:00Z. The API cannot close them: it never saw them, and an
episode with no all-clear grows against the wall clock forever (T81). **None
is western**, measured twice before and after the switch, so the contract a
Polish reader sees was never affected; the whole question is about the rest of
the map.

**Decision.** A frozen episode may be closed by a synthesised CLEAR **only
when a successful observation says the area is not alerting**, and never as
housekeeping. Three conditions, all required:

1. The area is in the area table, so the API is able to name it at all.
2. The API resolved that area on a poll that succeeded, and did not list it.
3. **No area containing it was listed either.** This is the condition the
   first draft of this decision lacked, and it is the one that matters most.

**Why the third condition exists.** The channel tagged raions; the API reports
whichever level the operator declared, which on 2026-08-30 was 56 districts, 5
states and 5 communities. Donetsk oblast alerts as a *state*, and the eight
frozen Donetsk raions are eight different area ids that the API will never
mention while it is naming their parent. Closing them on absence would write
into the store, permanently, that the front line is quiet - the exact
inversion of this project's rule, produced by a repair.

**No hand-edited store, ever.** Any closure is a `ThreatEvent` appended
through the normal path, carrying `source_id="reconcile"` so the store can
always say which rows came down a pipe and which were derived,
`provenance=INFERENCE`, and `ts_source` set to the observation that licensed
it. `docs/DECISIONS.md` D-013 says a re-reading happens by rebuilding from the
corpus, and this is the one thing a rebuild cannot produce, which is why it
gets a label of its own rather than a quiet insert.

**Mechanism deferred to a later release, deliberately.** F128 in this same
release makes the API resolve four names it could not resolve before, so the
set of areas the API is *able* to name changed inside the release that
discovered the problem. Writing the tool against the old measurement would
build on a number this release invalidates. The next step is to re-measure
after this deploy, not to ship `mavo reconcile` on figures from before it.

**Reopen if:** the frozen set reaches a western area, at which point this stops
being a question about the rest of the map and becomes one about the contract.

## D-042. The API says "air" and this project does not say "missile"
Date: 2026-08-30. Status: adopted

**Decision.** `AIR` maps to `ThreatKind.UNKNOWN`. `ARTILLERY` keeps its name,
because the source states it.

**What was wrong.** The adapter shipped at 0.44.0.0 mapped `AIR` to
`ThreatKind.MISSILE`, and from 15:11 on the day it deployed every alert on the
map drew a missile icon. The channel named the means of attack because it
wrote it in prose - ballistic, drone, glide bomb - and the API has one type for
everything that flies. The mapping put a classification on the reader's page
that no operator made.

**Three consequences, and the icon is the least of them.** `kind` crosses the
contract, so the consumer renders it: a reader saw a claim about means of
attack that came from this repository rather than from Ukraine. `r3_border_missile`
fires on a border oblast reporting an alert **classified as a missile threat**,
so a blanket MISSILE hands it a match for every air alert, and its hit count
stops measuring anything. And `ThreatKind.DRONE` can no longer occur at all, so
the drone rule's silence would read as a measurement rather than as a missing
input.

**The cost, which is the third cost of D-040 and was not named there.**
Switching sources cost this project the classification of the means of attack.
The kind-dependent rules are not wrong; they have no input. Their zero is
`[unestablished]`, not `[measured]`, and any evaluation run over API-sourced
events must say so rather than reporting a rate. Recovering it needs a source
that classifies - the channel returning, or a second endpoint that states a
type - and until then the honest page says the kind was not stated, which is a
sentence the consumer already knows how to render and explain.

**Reopen if:** the API gains a type that distinguishes what is in the air, or
the channel returns and can be joined on the same transition.

## D-043. D-041's parent condition is retired on a measurement

Date: 2026-08-30. Status: adopted. Settled in `docs/reviews/0.47.0.0.md` §3 and
written here one release late; the gap between settling and recording is the
numbering drift D-035 already paid for once.

**Decision.** `mavo reconcile` no longer refuses closure when a parent area is
mentioned. The other two D-041 conditions stand unchanged: the snapshot must be
`fresh`, and membership in it protects every live alarm from closure.

**Why.** The condition guarded against closing raions the API would only ever
name through their oblast. The payload of 2026-08-30 named eight Donetsk raions
individually, each resolving; the premise is measured false, and a guard whose
premise is false does not guard, it filters. The falsification is recorded in
the review rather than deleted, because a guard removed without its reason
recorded is a guard someone will reinstall.

**Reopen when** the API is observed naming an oblast in place of its raions
during an alarm those raions are under - the original premise, measured true.

## D-044. An area present in a fresh snapshot never renders as calm

Date: 2026-08-31. Status: adopted

**Decision.** The unit of alarm is `(area_id, kind)` at every layer, and three
changes ship together because no one of them is sufficient:

1. **The fold works per `(area_id, kind)`.** `compose` and
   `EventStore.newest_by_area_kind` fold on the key; an area is not clear when
   any of its kinds is not clear, tested with `is_clear` and never with
   `!= ACTIVE`, so the ACTIVE-to-UNKNOWN asymmetry survives. Which surviving
   kind *names* the area is `state_precedence` - `ACTIVE > PARTIAL_CLEAR >
   UNKNOWN > CLEAR`, ties to the newer stamp - a headline, never a verdict.
   `AreaPicture` gains `kinds`, one standing per live kind; `kind` and `since`
   remain as the headline's derived fields, so the v3 contract is extended and
   not changed, and the consumer at 4.60.0.0 - measured to validate required
   fields only - keeps rendering without a coordinated release.
2. **A re-assertion on the snapshot source is dated by observation.**
   `redate_reassertions` (pure, in `mavo/schema.py`) runs at the write boundary
   in `collect-api`: an ACTIVE whose `(area_id, kind)` carries a stored CLEAR
   no older than its stamp takes `ts_source = observed_at`, with the source's
   own word kept in `raw_fields`. Snapshot sources only. An assertion from a
   snapshot means "standing now"; from a log it means "a message existed at T",
   and re-dating the log path resurrected ended alerts on every re-read and
   broke idempotence - measured by `test_sprint11` against the first draft. The
   check lives in the collector rather than the adapter because the store
   belongs to the collector and the `ThreatSource` protocol is `source_id` and
   `poll()`.
3. **`reconcile` tests ghosts per kind and gains `--unmask`.** A ghost is a
   `(area_id, kind)` whose newest row is a channel ACTIVE and whose key the
   fresh snapshot does not hold; the old area-level test left thirteen stale
   channel rows out of reach on areas the API was reporting under a different
   kind. `--unmask` raises `ACTIVE` for every key the snapshot reports whose
   newest stored row is a clear or absent: `ts_source = saved_at`,
   `provenance=INFERENCE`, `source_id="reconcile"`, the superseded clear in
   `raw_fields`. A gate refuses `--apply` when a ghost sits on an area the
   snapshot reports and `--unmask` was not given, because closing it alone
   would take a live area dark while reporting success.

**What was wrong.** F133: source, identity and fold held three different
answers to what a unit of alarm is, and the clear of one threat kind erased
the area. Fifteen areas rendered calm during measured alarms on 2026-08-30 -
thirteen whose API key was cleared by the D-042 re-key with no activation
stored since, two whose concurrent air alert ended over a chronic artillery
alarm running since 19 April. The population was a ratchet, not a tide: a
chronic alarm never re-emits, and a re-assertion was unstorable by content
hash, so "wait for it to end" was not a mitigation on any human timescale.

**Why no part ships alone.** Part 1 alone publishes the thirteen on a dead
channel's authority. Part 2 alone changes nothing for anyone currently masked.
Part 3 alone raises rows the area-level fold can still lose to a later clear
on another kind. Together the fifteen clear at the next `--unmask`, the class
stops recurring, and no area is published on a dead channel's word.

**Reopen when** a source appears whose unit is neither an area nor an
`(area, kind)` pair - a corridor, a trajectory - and the fold's key stops
being the source's key again.

## D-045. `kind` is part of row identity

Date: 2026-08-31. Status: adopted. Its own number rather than a clause of
D-044, because it changes the identity of every row this project will ever
write and it touches D-013.

**Decision.** `ThreatEvent.content_hash` includes `kind.value`. `ts_ingest`,
`oblast` and the raw text stay out for the reasons D-013 gave.

**Why this is D-013 outgrown rather than reversed.** D-013 excluded `kind` on
the premise that a transition is something an *area* undergoes, so a
reclassification was a better reading of one event. D-044 measured that
premise false: an area carries several threat kinds at once and they begin and
end independently. Under the old identity, two kinds asserted for one area at
one instant by one source were one row, and the second was silently discarded
at the write boundary - a granularity mismatch of exactly F133's class, one
layer down. The API stamps batches identically (eight areas measured sharing
one `ts_source` on 2026-08-26), so the collision is live on the primary
source, and `reconcile --unmask` produces it by construction, since every row
it writes carries one `saved_at`.

**The finding that settled it** `[inference, mechanical]`: the old identity is
the measured mechanism behind the thirteen's missing activations. At the
D-042 re-key, `(area, UNKNOWN)` entered `current` as a new key and the source
emitted its activation - which hashed identically to the pre-D-042
`(area, MISSILE)` row already stored, `kind` being excluded, and was discarded
as a duplicate. The thirteen were not areas the API forgot; they were areas
whose activations this store refused.

**Migration, bounded and stated.** Old rows keep the hashes they were written
with; nothing rewrites them. A transition re-offered across the deploy lands a
second time under the new formula. The API source re-offers nothing - a key in
`previous` never re-emits - and the channel collector reads forward of its
page cursor against a publisher that stopped on 2026-08-29, so the expected
duplicate count on the production store is zero and any duplicate that does
land carries the same area, kind, state and stamp as its original and folds to
the same standing. D-013's own mechanism is untouched: a re-reading of the raw
corpus still happens by rebuilding a store, and a rebuild computes every hash
with one formula.

**Reopen when** a source is observed reclassifying a live transition in place -
same area, same instant, better kind - at a rate where two rows per
reclassification distort the trailing counts. That was D-013's case; it has
not been observed on either source.

