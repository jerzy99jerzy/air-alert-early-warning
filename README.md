[![MAVO - cross-border early warning, base-rate gated](docs/assets/mavo-banner.gif)](docs/assets/mavo-banner.gif)

# air-alert-early-warning

[![CI](https://github.com/jerzy99jerzy/air-alert-early-warning/actions/workflows/ci.yml/badge.svg)](https://github.com/jerzy99jerzy/air-alert-early-warning/actions/workflows/ci.yml)
[![tests 208](https://img.shields.io/badge/tests-208-brightgreen)](tests/)
[![coverage 96.16%](https://img.shields.io/badge/coverage-96.16%25-brightgreen)](Makefile)
[![harness 13 attacks, 12 mutation-verified](https://img.shields.io/badge/harness-13%20attacks%2C%2012%20mutation--verified-brightgreen)](tests/harness/CATALOGUE.md)
[![defects logged 51](https://img.shields.io/badge/defects%20logged-51-informational)](docs/METHODOLOGY.md)
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

Status: pre-alpha, five sprints from beta on the plan in [`docs/MVP.md`](docs/MVP.md), which carries no dates on purpose: this is a weekend project and a schedule built on assumed availability is an unmeasured number of exactly the kind this repository removes from its own gate. Sprints 0 to 6 shipped. A live Telegram adapter is wired;
measured against real channel content its classifier scored **0 of 20**, and the
failure is pinned as assertions. The redesign waits for a corpus rather than a
schedule (D-011), because fitting to the twenty messages in hand would repeat
the defect it would claim to fix. The corpus is now retrievable rather than
awaited: `mavo backfill` pages backwards through the channel's history, which
was 321,498 posts on 2026-08-09.

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

The observation that started the project stands and is now background rather
than thesis: every violation of Polish airspace in the observed period
coincided with a night of massed strikes on western Ukraine, and those campaigns
cover roughly 57% of days, which is why a prediction built on them would be a
calendar. Restated at 0.9.0.0; the earlier predictive framing is recorded in
D-015 rather than overwritten.

## Where the information comes from

Stated in full, because a warning tool whose inputs are vague is a tool nobody
can check. Every row is what it is, including the rows that are weaker than they
look.

| Source | What it gives | Access | Standing |
| --- | --- | --- | --- |
| **t.me/s/air_alert_ua**, the public web preview of the official Ukrainian air-alert channel | Every alert and all-clear, tagged with the area and its unit type, within seconds of publication | Public page, no token, no account, no agreement. It can be withdrawn at any time and nothing obliges anyone to keep it | **The only signal source in use.** ~20 messages per page, ~514 messages a day measured over the corpus |
| **alerts.in.ua** and **api.ukrainealarm.com** | The same alerts, through APIs | Tokens, one applied for and unanswered | **Not independent.** Both draw from the channel above (D-010). Two feeds, one dependency, and treating them as two would be the kind of false redundancy that reads as robustness right up until the day it matters |
| **KATOTTG**, the Ukrainian state register of administrative units | The code, oblast and hierarchy behind every area the channel names | A file, published as open data under Creative Commons Attribution | Used offline, versioned in the tree, never called at runtime (D-016). No API key in the warning path, no rate limit where latency is the product, and no third party learning which raions a Polish user asks about at three in the morning |
| **OpenSky Network** (ADS-B) | A second, physically different kind of observation | Self-service registration | **Not in use and not in the beta plan.** It was a prerequisite for a drone alarm tier that D-015 took off the critical path. Valuable later, blocking nothing now |
| A Polish-side feed | Would close the loop | Unresolved (T8) | **None found that is machine-readable and timely.** RSO and NOTAM are readable; RCB and the announced government application are not, as far as anyone here has established |

**What follows from that table.** Everything this tool says about Ukraine is
`reported`: it is what the channel claims, not what the sky contains, and no
amount of processing upgrades that label. There is exactly one signal source,
its loss would be total, and the correct response to losing it is to say so
loudly rather than to go quiet.

## How the source is actually structured

The finding the project turned on, measured on 48,540 real messages in the
design window of the corpus.

**99.34% of messages carry a hashtag naming the area and its unit type**, in the
form `#Харківський_район`, `#м_Харків_та_Харківська_територіальна_громада`,
`#Донецька_область`. The name is in the nominative, spaces are underscores, and
the unit word is explicit, so nothing has to be inferred. There are **127
distinct tags across 99 nights**, and **126 of them resolve to a unique code in
the Ukrainian state register** (`data/reference/tag_map.csv`).

This explains F23 rather than merely recording it. The shipped table searched
for oblast names in message text and scored 0 of 20; the channel emits an oblast
tag in 515 of 69,676 occurrences and names raions the rest of the time. The
table could not have scored above zero, and the problem was never an incomplete
vocabulary.

**3.5% of tag occurrences belong to western oblasts.** The other 96.5% are
front-line raions in the east and south, which for a reader on the Polish side
are facts about places 900 kilometres away. The channel labels the difference
itself, so the filter this project needs arrives for free rather than as a
classifier that has to be trained and trusted. A western-only report has a
naturally small volume because the west is naturally quiet, with no artificial
rate limit standing in for judgement.

Full measurement, the join to the register, the two rules it needed and what it
corrects: `docs/CHANNEL.md`.

## What this will not tell you

The section a competent reader reads first. Each bullet is registered in
`tests/lint_limitations.py` so it cannot quietly stop being true.

- It will not tell you that anything will cross the border. It tells you that a
  named rule fired at a named time, and what that rule has historically been
  worth. There is no probability of impact, because nothing here can compute one.
  (lint: no_probability_claim)
- It will not reintroduce a covariate that a measured null result has excluded.
  Exclusions here are earned by measurement, not by taste: the candidate that
  established this rule was tested against the full attack-density series, 738
  attack nights and 87,093 munitions, and returned a null (Rayleigh R = 0.013,
  p = 0.95). The excluded terms are enumerated in the lint rather than in prose,
  so re-introduction takes a deliberate test change. See D-002 in
  `docs/DECISIONS.md`. (lint: no_excluded_covariate)
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

Expect `mavo collect` to report roughly twenty messages and **parse almost none
of them**. That is not a broken install, it is F23 printing itself: the shipped
area table keys on oblast names and the channel emits raions and hromadas, so
classification fails by construction and the redesign is the next sprint. The
unparsed count is the number to read, and its being visible rather than absent
is the design. `skipped=unknown` on a single poll is the same discipline: one
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
  reviews/         one pre-push review per release, findings dispositioned
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
| Package `mavo/` | 16 | 3,225 |
| Tests | 31 | 3,254 |
| Tools | 11 | 2,582 |
| Documentation | 32 | 10,076 |

**Documentation outweighs the package by nearly three to one**, and that ratio is
deliberate rather than accidental. The product of this project is a measurement,
and a measurement whose method is not written down is an opinion with a
confidence interval attached.

| | |
| --- | --- |
| Runtime dependencies | **0** |
| Development dependencies | 4 (pytest, pytest-cov, ruff, mypy) |
| Tests | 206, of which 13 are scripted attacks |
| Coverage | 96.14% against a floor of 95, a ratchet that is never lowered |
| Mutation-verified controls | 12 of 13 attacks; the twelfth is printed as unverified on every run |
| Threat-model rows | 14, each with a control or a named acceptance |
| Defects logged with their class | 49, the count pinned against the log itself |
| Decisions recorded with reopen conditions | 19 |
| Releases | 30, of which 19 carry tags |
| Corpus | 60,680 posts, 118 days, contiguous, held outside the tree |

## Documentation

| Document | Contents |
| --- | --- |
| [**`docs/BRIEF.md`**](docs/BRIEF.md) | **Start here if you do not write code.** What the project is, why the base rate is the hard part, and the questions that would expose a weak answer |
| [**`docs/MANUAL.md`**](docs/MANUAL.md) | **Start here to use it.** Install, every command, how to read the output, operational limits, glossary. Each section declares BUILT, PARTIAL, NOT BUILT or NARRATIVE |
| [**`docs/FOUNDATIONS.md`**](docs/FOUNDATIONS.md) | **Start here to contribute.** The observations and assumptions everything rests on, each with its provenance label and what would falsify it |
| [`docs/DATA-FLOW.md`](docs/DATA-FLOW.md) | The data architecture: one message from byte to verdict, every transformation, and a table of exactly where information can be lost |
| [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) | What may be claimed, the defect log, and the probes that were run rather than read |
| [`docs/THREAT-MODEL.md`](docs/THREAT-MODEL.md) | MT1 to MT14, each with a control or a named acceptance and the test that measures it |
| [`docs/MECHANISMS.md`](docs/MECHANISMS.md) | Every mechanism with its rejected alternative |
| [`docs/COMPUTATION.md`](docs/COMPUTATION.md) | The statistical machinery the thesis stands on, with its stated weaknesses |
| [`docs/MOBILE.md`](docs/MOBILE.md) | The notification channel: technology choice, phases, and what gates distribution |
| [`docs/FEED-SPEC.md`](docs/FEED-SPEC.md) | What a machine-readable Polish alerting feed would have to be, written from consuming the Ukrainian one |
| [`docs/CHANNEL.md`](docs/CHANNEL.md) | What the source actually emits, measured, and the join to the state register |
| [`docs/OBSERVABILITY.md`](docs/OBSERVABILITY.md) | The durable run log and how a cycle is watched. Plan, not built |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Egress inventory, endpoint identity, containers, and where the daemon lives. Plan and open decisions |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | The infrastructure architecture: components, boundaries, dependency rules, process shape |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | What was rejected, and what would reopen it |
| [`docs/MVP.md`](docs/MVP.md) | Release criteria per audience, and five dated sprints to beta |
| [`docs/reviews/`](docs/reviews/) | Pre-push review per version, every finding dispositioned |
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
- The classifier hit rate on real channel content is **0 of 20**, pinned as
  assertions so it cannot be fixed quietly. See F23 in `docs/METHODOLOGY.md`.
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

## License

Apache-2.0. See `LICENSE` and `NOTICE`.
