[![MAVO - cross-border early warning, base-rate gated](docs/assets/mavo-banner.gif)](docs/assets/mavo-banner.gif)

# air-alert-early-warning

[![CI](https://github.com/jerzy99jerzy/air-alert-early-warning/actions/workflows/ci.yml/badge.svg)](https://github.com/jerzy99jerzy/air-alert-early-warning/actions/workflows/ci.yml)
[![tests 165](https://img.shields.io/badge/tests-165-brightgreen)](tests/)
[![coverage 96.97%](https://img.shields.io/badge/coverage-96.97%25-brightgreen)](Makefile)
[![harness 12 attacks, 11 mutation-verified](https://img.shields.io/badge/harness-12%20attacks%2C%2011%20mutation--verified-brightgreen)](tests/harness/CATALOGUE.md)
[![defects logged 38](https://img.shields.io/badge/defects%20logged-38-informational)](docs/METHODOLOGY.md)
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

Status: pre-alpha. Sprints 0 to 6 shipped. A live Telegram adapter is wired;
measured against real channel content its classifier scored **0 of 20**, and the
failure is pinned as assertions. The redesign waits for a corpus rather than a
schedule (D-011), because fitting to the twenty messages in hand would repeat
the defect it would claim to fix. The corpus is now retrievable rather than
awaited: `mavo backfill` pages backwards through the channel's history, which
was 321,498 posts on 2026-08-09.

---

## The thesis

Every violation of Polish airspace in the observed period coincided with a night
of massed Russian strikes on western Ukraine. That sounds like a warning signal
and is almost not one, because those campaigns cover roughly 57% of days. A rule
with perfect recall and a 57% firing rate is a calendar, not a detector.

The only available leverage is resolution: hour instead of night, border oblast
instead of country, classified means instead of a binary event. Whether that is
enough is an empirical question this repository is built to answer honestly,
including the answer *no*.

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

# score the regime-split policy against the shared attention budget
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
| Alarm rate | at most 2.00 per week, shared | Above this the audience learns to ignore it, and an adversary can induce that deliberately at no cost. The budget belongs to the recipient, so several rules divide one total rather than each getting their own |
| Association | Fisher one-sided p at most 0.05 | Distinguishes the rule from the calendar |

Alarm rate is a hard control rather than a quality metric. That is the design
decision this repository exists to enforce.

## Current finding

Sprint 2 measured a recall of 0.47 for the missile conjunction and recorded it as
a failure. Sprint 3 probed what the average hid: **7 of 7 on missile nights, 0 of
8 on drone nights.** The rule was not mediocre. It was perfect at one job and
blind to another, and one global threshold cannot express that.

Splitting the decision into two regimes, each with its own share of one shared
alarm budget, produces three configurations and no clean winner:

| Configuration | Recall (served scope) | Alarms/week | Headroom | Coverage gap |
| --- | --- | --- | --- | --- |
| Missile + drone, even split | 1.00 | 1.96 of 2.00 | 2% | none, but the drone regime overruns its 1.00 share at 1.34 |
| Missile + drone, demand + 25% headroom | not built | 2.46 requested | refused | allocator declines rather than trimming |
| Missile only | 1.00 | 0.63 of 2.00 | 69% | 8 drone crossings served by no regime |

The trade is real and is not resolved by tuning. Two regimes recover full recall
but consume the recipient's entire attention budget with a 2% margin, so a
busier month breaks the policy. One regime is comfortable and leaves drone
crossings unwarned.

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
  policy.py        regime split and the shared alarm budget
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
| Package `mavo/` | 14 | 2,293 |
| Tests | 25 | 2,366 |
| Tools | 3 | 573 |
| Documentation | 26 | 6,834 |

**Documentation outweighs the package by nearly three to one**, and that ratio is
deliberate rather than accidental. The product of this project is a measurement,
and a measurement whose method is not written down is an opinion with a
confidence interval attached.

| | |
| --- | --- |
| Runtime dependencies | **0** |
| Development dependencies | 4 (pytest, pytest-cov, ruff, mypy) |
| Tests | 165, of which 12 are scripted attacks |
| Coverage | 96.97% against a floor of 95, a ratchet that is never lowered |
| Mutation-verified controls | 11 of 12 attacks; the twelfth is printed as unverified on every run |
| Threat-model rows | 13, each with a control or a named acceptance |
| Defects logged with their class | 38, the count pinned against the log itself |
| Decisions recorded with reopen conditions | 14 |
| Releases | 17, of which 6 carry tags |
| Corpus | 60,680 posts, 118 days, contiguous, held outside the tree |

## Documentation

| Document | Contents |
| --- | --- |
| **`docs/BRIEF.md`** | **Start here if you do not write code.** What the project is, why the base rate is the hard part, and the questions that would expose a weak answer |
| **`docs/MANUAL.md`** | **Start here to use it.** Install, every command, how to read the output, operational limits, glossary. Each section declares BUILT, PARTIAL, NOT BUILT or NARRATIVE |
| **`docs/FOUNDATIONS.md`** | **Start here to contribute.** The observations and assumptions everything rests on, each with its provenance label and what would falsify it |
| `docs/DATA-FLOW.md` | The data architecture: one message from byte to verdict, every transformation, and a table of exactly where information can be lost |
| `docs/METHODOLOGY.md` | What may be claimed, the defect log, and the probes that were run rather than read |
| `docs/THREAT-MODEL.md` | MT1 to MT13, each with a control or a named acceptance and the test that measures it |
| `docs/MECHANISMS.md` | Every mechanism with its rejected alternative |
| `docs/COMPUTATION.md` | The statistical machinery the thesis stands on, with its stated weaknesses |
| `docs/MOBILE.md` | The notification channel: technology choice, phases, and what gates distribution |
| `docs/ARCHITECTURE.md` | The infrastructure architecture: components, boundaries, dependency rules, process shape |
| `docs/DECISIONS.md` | What was rejected, and what would reopen it |
| `docs/MVP.md` | Release criteria per audience, and the schedule to autumn |
| `docs/reviews/` | Pre-push review per version, every finding dispositioned |
| `tests/harness/CATALOGUE.md` | The attack catalogue, one row per threat |
| `STATUS.json` | Machine-readable pins, enforced by `tools/docs_audit.py` |

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

- `make verify` green: 165 tests passing, of which 12 are harness attacks.
  Coverage 96.97% against a floor of 95. The floor stays a ratchet under T9:
  the rise is below the five-point threshold that moves it. The old caveat
  stands in kind:
  `transport.py` carries the one genuinely network-bound function, and it drags
  the total toward the floor. Whether to exclude it from the measurement is an
  open decision recorded in the 0.3.2.0 review, not something to resolve by
  quietly moving either number.
- Every candidate rule fails the gate individually. The two-regime policy passes
  at 1.96 alarms per week against a budget of 2.00, which is a 2% margin and not
  a comfortable one.
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
