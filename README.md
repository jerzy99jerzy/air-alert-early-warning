[![MAVO - cross-border early warning, base-rate gated](docs/assets/mavo-banner.gif)](docs/assets/mavo-banner.gif)

# air-alert-early-warning

[![CI](https://github.com/jerzy99jerzy/air-alert-early-warning/actions/workflows/ci.yml/badge.svg)](https://github.com/jerzy99jerzy/air-alert-early-warning/actions/workflows/ci.yml)
[![tests 328](https://img.shields.io/badge/tests-328-brightgreen)](tests/)
[![coverage 96.48%](https://img.shields.io/badge/coverage-96.48%25-brightgreen)](Makefile)
[![harness 13 attacks, 12 mutation-verified](https://img.shields.io/badge/harness-13%20attacks%2C%2012%20mutation--verified-brightgreen)](tests/harness/CATALOGUE.md)
[![defects logged 78](https://img.shields.io/badge/defects%20logged-78-informational)](docs/METHODOLOGY.md)
[![runtime dependencies 0](https://img.shields.io/badge/runtime%20dependencies-0-blue)](pyproject.toml)
[![python 3.11 | 3.14](https://img.shields.io/badge/python-3.11%20%7C%203.14-blue)](pyproject.toml)
[![licence Apache-2.0](https://img.shields.io/badge/licence-Apache--2.0-blue)](LICENSE)
[![status pre-alpha](https://img.shields.io/badge/status-pre--alpha-orange)](docs/MVP.md)

Only the first badge is live. **The rest are static, and static badges are
claims**, so every number in them is pinned in `STATUS.json` and
`tools/docs_audit.py` fails the gate when a badge and the pin disagree. A
coverage badge that flatters by a release is the defect class this repository
exists to attack, and it would be an embarrassing one to ship in the README.


**Codename MAVO.** Cross-border early warning built on Ukrainian air-alert feeds,
with a base-rate gate that a rule must pass before it is allowed to wake anyone up.

> Named after the codename of the secret project in Stanislaw Lem's *His Master's
> Voice* (1968): a team spends years deciding whether a signal from outside
> carries a message or is noise that happens to look like one. Lem's afterword
> notes that the codename already smuggles in the assumption it was meant to
> test, since calling something a *voice* presumes a speaker.

**Naming.** The distribution slug is descriptive because it is a search term. The
import namespace is `mavo` because it must be unique rather than descriptive. The
codename lives in documentation and conversation. Stated here rather than left
implicit, because that is where the inconsistency otherwise lives.

Status: pre-alpha, **four sprints from beta** on the plan in [`docs/MVP.md`](docs/MVP.md), which carries no dates on purpose: this is a weekend project and a schedule built on assumed availability is an unmeasured number of exactly the kind this repository removes from its own gate. **Sprints 0 to 9 shipped**, where shipped means the code landed with its regression file - which is what `STATUS.json` records and all it records. **Sprints completed, in the sense of meeting the exit criterion in `docs/MVP.md`, run to S7.** S8 is half met and declared half met; S9 is further from its criterion than S8, because that criterion needs 72 hours unattended and a first end-to-end latency distribution, and no command in this repository polls the channel in a loop yet. The two counts were read as one number until 0.22.0.0 (F93). The corpus is collected rather than awaited: **61,041 messages** over 118 nights, contiguous, digest recorded, held outside the tree.

Area resolution works against real channel content and the number that used to
sit here was wrong. **20 of 20 real messages resolve their area to a unique code
in the Ukrainian state register; 15 of those 20 are alerts and all 15 classify;
the other 5 are threat declarations, which belong to the kind stream rather than
the alert stream.** This README claimed **0 of 20** until 0.22.0.0. That figure
was measured on a code path the product does not run: `probe` built its source
without an area table, the `None` default selected the oblast-stem table
superseded in sprint 7, and the two tests written to announce F23's closure
called the same untabled path, so the tripwire stayed green and confirmed the
wrong thing for two sprints (F90). The table was right and the call was not.

What is still not measured is the part that matters most: **no hand-checked
correctness rate exists for western areas**, which are the only ones this
product is for. The sample is drawn and its draw is fingerprinted (T36); it is
not yet scored, and until it is, every correctness claim here is about
mechanism rather than about accuracy.

---

## The thesis

**MAVO reports a threat picture in real time. It does not predict what will
cross into Poland.**

Whether a munition crosses depends on Ukrainian air defence, on where the debris
of an intercepted one lands, on a drone losing its way, and on an adversary's
decisions minutes earlier. None of that is in any feed this project can reach,
and no amount of history makes it so. What is observable at the moment it
happens is the picture on the Ukrainian side: which areas are under alert, how
intense the activity is right now, what means the channel names, and how far the
nearest alerted area is from the Polish border.

That distinction is the whole design. It is why the tool resolves rajons and
hromadas down to kilometres from the border rather than scoring a binary
prediction, and why the statistical gate applies only to an alarm class that
does not yet exist. The reporting tier is judged on correctness, latency and
completeness.

**What it is being built as, since 0.16.1.0.** An element of warning
infrastructure rather than a reporting instrument alone (D-015, revision 1).
The boundary above does not move: no prediction, and the 0 of 22 result stands.
What moves is the standard the output is held to. Infrastructure that goes
quiet tells its reader the sky is calm, so a heartbeat, staleness on the face
of the output and an explicit blind state are core requirements rather than
backlog items, and end-to-end latency is a measured property rather than a
claimed one. A public repository is not a public warning service: recipients
are gated by T6 and T11, both open.

The observation that started the project stands and is now background rather
than thesis: every violation of Polish airspace in the observed period
coincided with a night of massed strikes on western Ukraine, and those campaign
nights cover roughly **57% of days** in the same period. A rule firing on every
one of them has perfect recall, precision equal to the base rate, a lift of
1.0, and has told its reader nothing the calendar did not. Restated at
0.9.0.0; the earlier predictive framing is recorded in D-015 rather than
overwritten.

**Two different wests are being counted here, and only one of them is this
project's.** The 57% is `[reported]`: another source's figure, over a period
this repository did not observe, resting on whatever that source meant by
"western Ukraine" - possibly including Kyiv oblast, Vinnytsia, or everything
west of the Dnipro. This project means the 36 raions of the eight western
oblasts as the state register lists them, which is narrower and checkable.
Nobody has compared the two, so the 57% is context rather than evidence.

## Where the information comes from

Stated in full, because a warning tool whose inputs are vague is a tool nobody
can check. Every row is what it is, including the rows that are weaker than they
look.

| Source | What it gives | Access | Standing |
| --- | --- | --- | --- |
| **t.me/s/air_alert_ua**, the public web preview of the official Ukrainian air-alert channel | Every alert and all-clear, tagged with the area and its unit type, within seconds of publication | Public page, no token, no account, no agreement. It can be withdrawn at any time and nothing obliges anyone to keep it | **The only signal source in use.** ~20 messages per page, ~514 messages a day measured over the corpus |
| **alerts.in.ua** and **api.ukrainealarm.com** | The same alerts, through APIs | Tokens, one applied for and unanswered | **Not independent.** Both draw from the channel above (D-010). Two feeds, one dependency, and treating them as two would be the kind of false redundancy that reads as robustness right up until the day it matters |
| **KATOTTG**, the Ukrainian state register of administrative units | The code, oblast and hierarchy behind every area the channel names | A file, published as open data under Creative Commons Attribution | Used offline, versioned in the tree, never called at runtime (D-016). No API key in the warning path, no rate limit where latency is the product, and no third party learning which raions a Polish user asks about at three in the morning |
| **OpenSky Network** (ADS-B) | A second, physically different kind of observation: aircraft that broadcast their own position | Registered 2026-08-10, 4,000 credits a day, one credit per call over the western box [measured] | **Not a drone-tier source, and the premise that it was is recorded as false.** Transponders are carried by aircraft that choose to be seen; Shahed-type munitions and missiles carry none. What it can measure is **the operating intensity of the Rzeszow-Jasionka hub**, which has potential diagnostic value during a war and is reported rather than scored (D-019, T42) |
| A Polish-side feed | Would close the loop | Unresolved (T8) | **None found that is machine-readable and timely.** RSO and NOTAM are readable; RCB and the announced government application are not, as far as anyone here has established |

**What follows from that table.** Everything this tool says about Ukraine is
`reported`: it is what the channel claims, not what the sky contains, and no
amount of processing upgrades that label. There is exactly one signal source,
its loss would be total, and the correct response to losing it is to say so
loudly rather than to go quiet.

**On the ADS-B row specifically.** Counting transmitting military aircraft over
the Jasionka hub is a lower bound and never a measurement of activity: an
operator that wants silence switches the transponder off, and plausibly does so
in exactly the situations a reader would most want to know about. A high count
means something. A low count means nothing at all, and the field will carry
that framing in itself rather than in a footnote. It takes no part in any
score.

## How the source is actually structured

The finding the project turned on, measured on 48,540 real messages in the
design window of the corpus.

**99.34% of messages carry a hashtag naming the area and its unit type**, in the
form `#Харківський_район`, `#м_Харків_та_Харківська_територіальна_громада`,
`#Донецька_область`. The name is in the nominative, spaces are underscores, and
the unit word is explicit, so nothing has to be inferred. There are **127
distinct tags across 99 nights**, and **126 of them resolve to a unique code in
the Ukrainian state register** (`data/reference/tag_map.csv`).

This explains F23 rather than merely recording it. The table shipped in sprint 6
searched for oblast names in message text and scored 0 of 20; the channel emits an oblast
tag in 515 of 69,676 occurrences and names raions the rest of the time. The
table could not have scored above zero, and the problem was never an incomplete
vocabulary.

### Where the tags come from, and what the 3.5% is a share of

The channel does not write prose about places. It appends a hashtag naming the
administrative unit the message is about: `#Самбірський_район`, the register
name in the nominative with spaces as underscores. **48,222 of 48,540 messages
carry one, 99.34%.** There are 127 distinct tags across 99 nights, and 126 of
them resolve to exactly one code in the state register.

That is the whole geocoder. No stemming, no truncation parameter, no
disambiguation, no classifier trained on anything: the channel labels every
message itself and this project reads the label. For contrast, the approach
this replaced - matching truncated register names against message text - reached
6.06% of messages as a lower bound, so structure beats the heuristic by roughly
a factor of six and needs no tuning (F23).

Counted over those tags: **2,456 of 69,676 occurrences, 3.5%, name a western
oblast.** The other 96.5% name front-line raions in the east and south, which
for a reader on the Polish side are facts about places 900 kilometres away.
The filter this project needs therefore arrives for free.

### What 3.5% does and does not mean, because the two are easy to swap

It is a share of **message traffic**. Of every hundred times this channel names
a place, three and a half are places near Poland.

It is **not** the share of nights the west is under alert, and it is **not**
how often anything comes close to the border. Those are three different
quantities and only the first one has been measured here:

| Question | Unit | Status |
| --- | --- | --- |
| How much of the channel's traffic is about the west? | tag occurrences | **3.5%, measured** |
| On how many nights is a western raion under alert? | nights | **not measured by this project.** The 57% above is a different source's figure for a possibly different area |
| How often does anything actually approach the Polish border? | crossings | Roughly a dozen events in four years `[reported]`, and this feed cannot see it at all |

Where the tags come from, what produces them, and the four things nobody has
checked about them: `docs/CHANNEL.md` section 10.

The third row is the one that matters most and the one nothing here can
answer. **The channel reports declared alert states for administrative units.
It does not observe objects, tracks or positions**, so no count derived from it
is a count of things being close. An alert in Sambirskyi raion means an
authority declared an alert for that raion; whether anything was over it, and
where, is not in the data.

So the two figures do not contradict each other and they are not two views of
one thing. 57% of days carrying a campaign night is compatible with the west
generating 3.5% of traffic, because the front-line oblasts have far more raions
and their alerts run continuously while western ones are short. **The west is
quiet in message volume**, which is why a western-only report has a naturally
small volume with no artificial rate limit standing in for judgement. Quiet in
volume is not the same as rarely under alert, and this project has not measured
the second.

Full measurement, the join to the register, the two rules it needed and what it
corrects: `docs/CHANNEL.md`.

## What this will not tell you

The section a competent reader reads first. Each bullet is registered in
`tests/lint_limitations.py` so it cannot quietly stop being true.

- It will not tell you that anything will cross the border. It tells you that a
  named rule fired at a named time, and what that rule has historically been
  worth. There is no probability of impact, because nothing here can compute one.
  (lint: no_probability_claim)
- It will not read a silent feed as an all-clear, and will not read a partial
  all-clear as a whole one. An area whose status is unknown stays `UNKNOWN`; a
  message that announces an all-clear while saying the alert continues is
  `PARTIAL_CLEAR`. Neither contributes to an alarm in either direction, and the
  lint enumerates the enum, so a fifth state would be covered on the day it is
  added. (lint: unknown_not_clear)
- It will not fit a model to the positive events. There are roughly a dozen of
  them across four years; a model trained on that would reproduce the
  overfitting that invalidated this project's first analysis. Rules are explicit
  predicates with thresholds in configuration. (lint: no_ml_dependency)
- It will not reach the network from anywhere except one file. `mavo/transport.py`
  is the only module that imports a network client, so what this tool can talk to
  has a single answer in a single place, and every adapter is testable without a
  network. `mavo collect --stub` and every other command still run fully offline
  with no credentials. (lint: network_reach_is_one_file)
- It is not a substitute for sirens or for the state alerting system. It operates
  one step earlier in the chain than those can, and is correspondingly less
  certain. That is the entire trade.

## Quickstart

```
pip install -e ".[dev]"

# generate a synthetic history and store it
mavo fixture --out data/raw/fixture.sqlite --weeks 52

# score every candidate rule against the base rate
mavo gate --weeks 208

# score the regime-split decision policy
mavo policy --weeks 208
mavo policy --weeks 208 --allocation demand
```

No token, no network, no data of your own. What the second command prints is a
property of the generator, not of the world.

**On real data.** The channel is public, so this needs no token either. Nothing
here is a simulation: these three commands hit the live source.

```
# one live poll, parsed and reported, nothing written
mavo collect

# the same poll, keeping the page exactly as served for later re-parsing
mavo collect --save-raw data/raw

# five pages of channel history, verbatim, one request per second
mavo backfill --out data/raw/corpus --pages 5 --delay 1.0
```

Expect `mavo collect` to report roughly twenty messages and **parse most of
them**, the misses being threat declarations rather than alerts. Until 0.22.0.0
this paragraph told you to expect almost nothing to parse and blamed F23: the
area table keying on oblast names. That was the right symptom and the wrong
cause. The table had keyed on register codes since sprint 7; `probe` called it
without one (F90). The unparsed count is still the number to read, and its being
visible rather than absent is the design. `skipped=unknown` on a single poll is the same discipline: one
invocation has no previous poll to compare against, and unknown is never
printed as zero.

`mavo backfill` prints the id range, the time span it reached, and a contiguity
line. **The span is the line to read first**: how far back a page count reaches
is a property of channel volume rather than arithmetic. It writes raw HTML and
parses nothing beyond the post ids it needs to page, because a corpus filtered
through the parser it exists to fix would not be evidence. `data/raw/` is
git-ignored, which is a policy rather than a convenience (see Layout).

Full option tables and failure modes: `docs/MANUAL.md` sections 4.4 and 4.5.

## The gate

A rule may raise a critical alarm only if it clears three conditions. Failing any
one is decisive.

| Condition | Floor | Why it is there |
| --- | --- | --- |
| Recall | at least 0.90 | A warning system that misses the event has no purpose |
| Lift, lower bound | at least 1.50 | A rule must beat the base rate at the lower bound of its precision interval, not at the point estimate. With about a dozen positive events the point moves by a factor on one night, and a rule that cannot beat the calendar with confidence is a calendar |
| Association | Fisher one-sided p at most 0.05 | Distinguishes the rule from the calendar |

Alarm rate is a hard control rather than a quality metric. That is the design
decision this repository exists to enforce.

## Current finding

Sprint 2 measured a recall of 0.47 for the missile conjunction and recorded it as
a failure. Sprint 3 probed what the average hid: **7 of 7 on missile nights, 0 of
8 on drone nights.** The rule was not mediocre. It was perfect at one job and
blind to another, and one global threshold cannot express that.

Splitting the decision into two regimes produces two shippable configurations:

| Configuration | Recall (served scope) | Alarms/week | Coverage gap |
| --- | --- | --- | --- |
| Missile + drone | 1.00 | 1.96 | none |
| Missile only | 1.00 | 0.63 | 8 drone crossings served by no regime |

Through 0.7.x the choice between them was decided by an attention budget, and
the two-regime configuration was the one that barely fit it. With the budget
removed (D-014) the alarms-per-week column is a measurement rather than a
verdict, and the trade that remains is the one that was always the real one: the
drone rule buys its recall from a signal that does not distinguish a drone night
ending in a crossing from one that does not.

The shippable shape is therefore missile in the alarm tier, drone demoted to the
observation tier, and the gap declared rather than hidden. Closing it needs a
signal that oblast-level alert state does not contain, which is what the ADS-B
channel is for. That moves the ADS-B work from optional enrichment to a
prerequisite for any drone-tier alarm.

## Layout

```
mavo/
  schema.py        normalized event, provenance labels, the ThreatSource boundary
  store.py         append-only log; any past moment is reconstructible
  baserate.py      the null model; top-level because it is the point
  rules.py         candidate rules as explicit predicates
  policy.py        regime split, one rule per timing regime
  evaluate.py      scoring against ground truth; shared with the future shadow mode
  errors.py        the refusal taxonomy; there is no warning type in this codebase
  transport.py     the only file that reaches the network
  backfill.py      retrieves channel history backwards, verbatim, resumable
  sources/
    fixture.py     synthetic scenarios, shipped as a CLI command
    telegram.py    the public channel adapter; its pattern table is under redesign
  cli.py           fixture / gate / policy / backfill / collect
tests/
  test_<domain>.py behaviour
  test_sprint<N>.py regression, one file per sprint, verified red before it is fixed
  lint_*.py        executable claims about the repository itself
  harness/         one scripted attack per threat-model row, plus its catalogue
tools/
  docs_audit.py    fails when a pin in STATUS.json disagrees with the tree
  manual_audit.py  fails when the manual describes a command the CLI does not have
  harness_mutation.py  disables each control and fails if its attack stays green
docs/
  BRIEF.md         the project for a reader who does not write code
  BRIEF-PL.md      the same, in Polish, and the original
  MANUAL.md        operator's manual; every section declares BUILT or NOT BUILT
  FOUNDATIONS.md   the observations and assumptions, each with its falsifier
  ARCHITECTURE.md  infrastructure: components, boundaries, dependency rules
  DATA-FLOW.md     data: one message from byte to verdict, and where it is lost
  MECHANISMS.md    how each mechanism works
  METHODOLOGY.md   what may be claimed, plus the defect log
  THREAT-MODEL.md  adversaries against this tool
  MVP.md           release criteria per audience
  DECISIONS.md     what was rejected, and what would reopen it
  COMPUTATION.md   the statistical machinery, with its stated weaknesses
  MOBILE.md        the notification channel: technology choice and its phases
  WEBAPP.md        the web tier: the contract, the three states, and the mockups
  reviews/         one review per major release, findings dispositioned
data/
  raw/             tier 1, never committed, git-ignored
  aggregates/      tier 2, counts only, committed
```

## The repository in numbers

Recounted from the tree by `tools/docs_audit.py` on every run and pinned in
`STATUS.json`. Until 0.6.2.0 that sentence described the intent and not the
mechanism: nothing checked these four rows, and all four were stale while
reading as authoritative. They are now a gate failure rather than a typo.

| | Files | Lines |
| --- | --- | --- |
| Package `mavo/` | 18 | 4,818 |
| Tests | 38 | 5,840 |
| Tools | 15 | 3,909 |
| Documentation | 43 | 15,447 |

**Documentation outweighs the package by nearly three to one**, and that ratio is
deliberate rather than accidental. The product of this project is a measurement,
and a measurement whose method is not written down is an opinion with a
confidence interval attached.

| | |
| --- | --- |
| Runtime dependencies | **0** |
| Development dependencies | 4 (pytest, pytest-cov, ruff, mypy) |
| Tests | 328, of which 13 are scripted attacks |
| Coverage | 96.48% against a floor of 95, a ratchet that is never lowered |
| Mutation-verified controls | 12 of 13 attacks; the one without a mutation is printed as unverified on every run |
| Threat-model rows | 14, each with a control or a named acceptance |
| Defects logged with their class | 78, the count pinned against the log itself |
| Decisions recorded with reopen conditions | 24 |
| Releases | 41 in the changelog; tags are fewer and some are cumulative (A11) |
| Corpus | 61,041 posts, contiguous, digest recorded, held outside the tree |

## Documentation

| Document | Contents |
| --- | --- |
| [**`docs/BRIEF.md`**](docs/BRIEF.md) | **Start here if you do not write code.** What the project is, why three violations a year make prediction indefensible, what it refuses to say, and the questions that would expose a weak answer |
| [`docs/BRIEF-PL.md`](docs/BRIEF-PL.md) | The same document in Polish, and the original: the readers it is written for are Polish |
| [**`docs/MANUAL.md`**](docs/MANUAL.md) | **Start here to use it.** Install, every command, how to read the output, operational limits, glossary. Each section declares BUILT, PARTIAL, NOT BUILT or NARRATIVE |
| [**`docs/FOUNDATIONS.md`**](docs/FOUNDATIONS.md) | **Start here to contribute.** The observations and assumptions everything rests on, each with its provenance label and what would falsify it |
| [`docs/DATA-FLOW.md`](docs/DATA-FLOW.md) | The data architecture: one message from byte to verdict, every transformation, and a table of exactly where information can be lost |
| [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) | What may be claimed, the defect log, and the probes that were run rather than read |
| [`docs/THREAT-MODEL.md`](docs/THREAT-MODEL.md) | MT1 to MT14, each with a control or a named acceptance and the test that measures it |
| [`docs/MECHANISMS.md`](docs/MECHANISMS.md) | Every mechanism with its rejected alternative |
| [`docs/COMPUTATION.md`](docs/COMPUTATION.md) | The statistical machinery the thesis stands on, with its stated weaknesses |
| [`docs/MOBILE.md`](docs/MOBILE.md) | The notification channel: technology choice, phases, and what gates distribution |
| [`docs/WEBAPP.md`](docs/WEBAPP.md) | The web tier: the `state.json` contract and who owns it, three feed states that must read differently, the palette and the theme-inversion failure behind it, and mockups of every state |
| [`docs/FEED-SPEC.md`](docs/FEED-SPEC.md) | What a machine-readable Polish alerting feed would have to be, written from consuming the Ukrainian one |
| [`docs/CHANNEL.md`](docs/CHANNEL.md) | What the source actually emits, measured, and the join to the state register |
| [`docs/OBSERVABILITY.md`](docs/OBSERVABILITY.md) | The durable run log and how a cycle is watched. Plan, not built |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Egress inventory, endpoint identity, containers, and where the daemon lives. Plan and open decisions |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | The infrastructure architecture: components, boundaries, dependency rules, process shape |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | What was rejected, and what would reopen it |
| [`docs/MVP.md`](docs/MVP.md) | Release criteria per audience, and five dated sprints to beta |
| [`docs/reviews/`](docs/reviews/) | One review per major release, every finding dispositioned. Twelve early majors have none and are named in `docs/reviews/README.md` rather than left to be counted |
| [`tests/harness/CATALOGUE.md`](tests/harness/CATALOGUE.md) | The attack catalogue, one row per threat |
| [`STATUS.json`](STATUS.json) | Machine-readable pins, enforced by `tools/docs_audit.py` |

## Verification

```
make verify
```

That is the only gate. CI calls it rather than restating its steps. It runs the
test suite with a coverage floor, ruff, mypy strict, four repository lints, two
audits that fail when documentation drifts from the code, and a mutation run that
disables each guarded control in a scratch tree and fails if the attack guarding
it stays green. The mutation run costs roughly seven seconds of the gate's
eleven, which is stated because a check nobody can afford is a check that gets
moved out of the gate and then stops running.

## Measured claims

A number appears in this documentation only when the code produced it.

- `make verify` green: 170 tests passing, of which 12 are harness attacks.
  Coverage 96.90% against a floor of 95. The floor stays a ratchet under T9:
  the rise is below the five-point threshold that moves it. The old caveat
  stands in kind:
  `transport.py` carries the one genuinely network-bound function, and it drags
  the total toward the floor. Whether to exclude it from the measurement is an
  open decision recorded in the 0.3.2.0 review, not something to resolve by
  quietly moving either number.
- On the adversarial synthetic history one candidate rule passes the gate,
  `R1-border-active`, with a lift lower bound of 1.69 against a floor of 1.50.
  The margin is thin, one night either way moves it, and synthetic history says
  nothing about the world.
- Area resolution on real channel content is **20 of 20**, and alert
  classification **15 of 20**, the five remainders being declarations. Pinned as
  assertions. The **0 of 20** this bullet carried until 0.22.0.0 measured a call
  shape the product does not use, and the assertion built to flip when F23 was
  fixed called that same shape, so it never flipped (F90 in
  `docs/METHODOLOGY.md`). Pinning a number is not the same as pinning the number
  the product produces.
- The harness is mutation-verified as of 0.4.0.0, after slipping twice. Ten
  controls disabled one at a time; the guarding attack must go red. **The first
  run killed 7 of 10**, and the three survivors were defects in the attacks
  themselves (F38 to F40), one of them written the same afternoon. One attack of
  eleven carries no mutation and is listed as unverified rather than assumed.
- Every number above except the classifier hit rate was produced against a
  synthetic history. None of them is a claim about the world.

### Where to start

| If you are | Read |
| --- | --- |
| Running it | [`docs/MANUAL.md`](docs/MANUAL.md) |
| Deciding whether to believe it | [`docs/FOUNDATIONS.md`](docs/FOUNDATIONS.md), then [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) |
| Changing how something works | [`docs/MECHANISMS.md`](docs/MECHANISMS.md) |
| Adding a component | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Following the data | [`docs/DATA-FLOW.md`](docs/DATA-FLOW.md) |
| Attacking it | [`docs/THREAT-MODEL.md`](docs/THREAT-MODEL.md) and [`tests/harness/CATALOGUE.md`](tests/harness/CATALOGUE.md) |

## Author

**Jerzy Siwecki**, Warsaw. Senior cybersecurity engineer; this is a weekend
project rather than anything's product, and no employer's.

The licence is open and the attribution requirement is real: Apache-2.0 keeps
the copyright notice and the NOTICE file with any redistribution, including
modified versions. Stated here rather than left to the licence text because
the two things people most often assume about a permissive licence are that it
waives attribution and that it waives the disclaimer, and it waives neither.

**What the disclaimer means in this particular case**, since this is warning
software: the licence's "AS IS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND"
is not boilerplate to skim past. This tool is pre-alpha, it has never delivered
a warning to anyone, **no hand-checked correctness rate exists for the western
areas it is built for**, and its threat-kind tables cover roughly one alert in
ten (F71). Anyone deploying
it for someone else's safety is taking a decision the author has not taken and
would want to be asked about first.

Corrections, defects and disagreements are welcome, and the useful form is in
[`CONTRIBUTING.md`](CONTRIBUTING.md). A finding against this project's own
interests is worth more here than a feature, and the defect log exists to prove
that is not just a sentence.

## License

Apache-2.0. See `LICENSE` and `NOTICE`.
