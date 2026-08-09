# The computation MAVO stands on

Version: 1.0 / 2026-08-09
Audience: a reader who wants to check the arithmetic rather than trust it.
Code: `mavo/baserate.py` (every statistic), `mavo/evaluate.py` (how histories
become tables), `mavo/policy.py` (how the budget binds). Nothing statistical
lives anywhere else, deliberately: the null model is a top-level module and a
domain lint fails the build if it stops being one.

Provenance convention as everywhere in this repository: **measured** /
**reported** / **inference** / **speculation**, and an assessment inherits the
weakest label of its inputs (`Provenance.weakest`; an empty input is
SPECULATION, because absence is never the flattering state).

## Contents

- [The problem, stated numerically](#the-problem-stated-numerically)
- [The contingency table](#the-contingency-table)
- [Base rate, precision, recall, lift](#base-rate-precision-recall-lift)
- [Why unknown is never zero](#why-unknown-is-never-zero)
- [The Wilson interval](#the-wilson-interval)
- [The Fisher exact test](#the-fisher-exact-test)
- [The gate: three conditions](#the-gate-three-conditions)
- [The alarm budget as a statistical control](#the-alarm-budget-as-a-statistical-control)
- [The regime split, or what an average hid](#the-regime-split-or-what-an-average-hid)
- [Why there is no model](#why-there-is-no-model)
- [Design and holdout](#design-and-holdout)
- [What this machinery does not compute](#what-this-machinery-does-not-compute)
- [Stated weaknesses](#stated-weaknesses)

## The problem, stated numerically

The thesis rests on one observed coincidence and one number that nearly
destroys it. Every violation of Polish airspace in the observed period fell on
a night of massed strikes against western Ukraine [reported; source coverage
discussed in `docs/FOUNDATIONS.md`]. Those campaign nights cover roughly **57%
of days** in the same period [reported]. The positive class — actual crossings —
holds roughly **a dozen events across four years** [reported].

Both numbers are load-bearing:

- 57% means a rule that fires on every campaign night has perfect recall and
  is a calendar. Its precision equals the base rate by construction, its lift
  is 1.0, and it has told the recipient nothing the date did not.
- Twelve positives means every estimate downstream is small-sample. Point
  estimates of precision and recall carry intervals wide enough to change the
  verdict, which is why the machinery reports intervals and exact p-values
  rather than proportions alone, and why nothing here is fitted.

Everything below is the consequence of taking those two numbers seriously.

## The contingency table

The unit of observation is a **night** (an observation window), not an event.
Each night is scored once against each rule:

|  | crossing occurred | no crossing |
| --- | --- | --- |
| rule fired | a | b |
| rule silent | c | d |

`Contingency(a, b, c, d)` with `n = a+b+c+d`, `fired = a+b`, `events = a+c`.
The scoring loop is `evaluate.run_rule`: a rule returns the *moment* it would
have fired or `None`, and the moment matters because lead time — the minutes a
warning buys — is measured only on true positives, as the median over `a`.

Windows are nights rather than hours because the positive events are nightly
phenomena and an hourly table would multiply `d` without adding information,
flattering every p-value for free [inference].

## Base rate, precision, recall, lift

All four in `mavo/baserate.py`, each returning `None` when undefined:

- **base rate** `= events / n` — the probability of a crossing with no rule at
  all. This is the null model: the calendar.
- **precision** `= a / fired` — P(crossing | fired). Undefined when the rule
  never fired.
- **recall** `= a / events` — P(fired | crossing). Undefined when no crossing
  was observed.
- **lift** `= precision / base rate` — the only number here that measures
  *information*. A lift of 1.0 means the rule's firing changed nothing about
  the probability of a crossing; at a 57% base rate, high precision is cheap
  and lift is what separates a detector from a calendar.

## Why unknown is never zero

`precision` of a rule that never fired is `None`, not `0.0`
(`test_baserate.py::test_precision_of_a_rule_that_never_fired_is_unknown_not_zero`).
Reporting zero would make an *untested* rule indistinguishable from a *bad*
one, and the difference decides what happens next: a bad rule is dropped, an
untested one is tested. The same convention holds for recall without events,
base rate of an empty history, and lift without firings. This is the
statistical face of the project's central invariant — UNKNOWN never resolves
to CLEAR — applied to its own metrics. Every `summary()` prints the word
`unknown` rather than a numeral.

## The Wilson interval

Precision is reported with a Wilson score interval (`wilson_interval`,
default z = 1.96), not a normal approximation, because the counts are small.
For successes s over t trials with p&#770; = s/t:

    center = (p̂ + z²/2t) / (1 + z²/t)
    margin = z · sqrt( p̂(1−p̂)/t + z²/4t² ) / (1 + z²/t)

The normal ("Wald") interval collapses to zero width at p&#770; ∈ {0, 1} and
undercovers badly below t ≈ 40 — precisely the regime a dozen positives puts
every cell in. Wilson stays honest at the boundaries: 7 of 7 does not report
certainty, it reports roughly [0.65, 1.0] [measured, by running the function].
The interval is clamped to [0, 1] and is `None` for zero trials
(`test_baserate.py::test_wilson_interval_without_trials_is_unknown`).

## The Fisher exact test

The gate's association statistic is a **one-sided Fisher exact test**
(`fisher_exact_greater`): the probability, under the null hypothesis that
firing and crossings are independent with the margins fixed, of a table at
least as favorable as the observed one. It is the hypergeometric upper tail:

    P = Σ_{k=a}^{min(row1, col1)}  C(row1, k) · C(row2, col1−k) / C(n, col1)

computed on `math.comb` over integers, exactly — no floating-point series, no
continuity correction, no approximation to be wrong about.

Three choices worth defending:

- **Why exact and not chi-squared.** The chi-squared approximation is unsafe
  when expected cell counts fall below ~5; with a ≤ 12 positives, cell `a`'s
  expectation is below 5 for any rule that is not a calendar. Fisher is valid
  at any count.
- **Why one-sided.** The alternative hypothesis is directional by
  construction: a rule is only interesting if firing makes a crossing *more*
  likely. A rule anticorrelated with crossings is not a discovery, it is a
  bug, and it should fail the gate rather than pass it with a two-sided
  p-value.
- **Why `math.comb` and not SciPy.** A tool whose product is a measurement is
  weakened by a dependency tree nobody audits; this is the only statistic the
  gate needs, and thirty lines of stdlib are checkable by hand
  (`test_baserate.py::test_fisher_matches_a_hand_checked_table` pins one table
  against a hand computation). The zero-runtime-dependency claim in the README
  is lint-enforced, and this function is the reason it can be.

Degenerate tables (no rows, a silent rule, no events) return 1.0: no evidence
of association is reported as no evidence, not as an error
(`test_baserate.py::test_fisher_of_a_degenerate_table_is_one`).

## The gate: three conditions

`gate()` decides whether a rule may drive a critical alarm. Failing any one
condition is decisive; all three verdicts are printed with their reasons.

| Condition | Threshold | What failing means |
| --- | --- | --- |
| recall | ≥ 0.90 | The rule sleeps through crossings. A warning system that misses the event it exists for has no reason to exist, whatever its precision |
| alarm rate | ≤ allocated budget/week | The rule spends more attention than the recipient has. See the next section: this is a hard control, not a quality score |
| Fisher p | ≤ 0.05 | The association is not distinguishable from the calendar. The rule may be a superstition with good manners |

The asymmetry is deliberate: recall has a floor and precision has none,
because precision is priced *indirectly* through the alarm rate. A
low-precision rule at a 57% base rate fires constantly and dies on the budget
condition; a low-recall rule dies on its own condition. Every failure mode has
exactly one owner.

## The alarm budget as a statistical control

`MAX_ALARMS_PER_WEEK = 2.0` is the recipient's attention, treated as the
binding constraint of the whole system. The number is currently an
**assumption about a hypothetical audience** [speculation, and flagged: T11
exists to replace it with two recorded answers to "at what firing rate would
you stop reading this"].

The arithmetic that makes it a *statistical* control rather than a UX
preference: alarm fatigue is an attack surface. An adversary who can induce
rule firings — and the poison check in `mavo/rules.py` exists because feed
manipulation costs nothing to attempt — can spend the recipient's attention
until a real alarm is ignored. A budget enforced *per rule share and again on
the total* (`DecisionPolicy` refuses construction when shares exceed the
total; `plan_policy` refuses when measured demand plus 25% headroom exceeds
it) means the failure mode is a loud refusal at build time, not a quiet
over-notification at 02:00. Two rules each cleared at two per week produce
four per week; the arithmetic that destroys the channel is the arithmetic the
constructor checks.

## The regime split, or what an average hid

Sprint 2 measured the missile conjunction at **recall 0.47** and recorded a
failure. Sprint 3 partitioned the positives by means of attack and found the
average was two populations [measured, on the synthetic history the gate runs
against]:

| Population | fired / crossings | recall |
| --- | --- | --- |
| missile nights | 7 / 7 | 1.00 |
| drone nights | 0 / 8 | 0.00 |
| pooled | 7 / 15 | 0.47 |

The rule was not mediocre; it was perfect at one job and blind to another, and
a pooled recall cannot express that — the same aggregation failure family as
Simpson's paradox, though here it is masking rather than reversal. The
consequences are structural, not cosmetic:

- one rule per **regime** (defined by transit time, not munition taxonomy:
  what differs is how many minutes a warning buys, roughly a factor of five);
- each regime scored **only against its own crossings**
  (`evaluate.run_regime` excludes the other kind's nights from the table
  rather than counting them as negatives — a missile rule silent on a drone
  night has declined a job, not made an error; the cost is sample size and it
  is paid openly);
- crossings served by **no** regime are counted and printed as a coverage
  gap, never folded into the denominator, because absorbing them would
  manufacture recall out of scope-shrinking — unknown resolving to clear, one
  layer up.

The drone regime currently fails its gate and is demoted to the observation
tier (D-009): nothing in oblast-level alert state distinguishes a drone night
that ends in a crossing from one that does not, which is why ADS-B is a
prerequisite for any drone-tier alarm rather than an enrichment (T14).

## Why there is no model

Roughly a dozen positive events. A logistic regression with three predictors
fitted to twelve positives has ~4 events per parameter against a commonly
cited floor of 10–20; a tree or boosted ensemble is worse. Any of them would
interpolate the training positives and validate beautifully on resubstitution,
which is precisely the failure this project measured its way out of once
already: a candidate covariate survived visual inspection of the attack-density
series and died only under a proper directional test on 738 attack nights and
87,093 munitions (Rayleigh R = 0.013, p = 0.95; D-002, permanently excluded).
The lesson was not "test better", it was **structural**: with this event count,
flexibility is the enemy. Rules are therefore explicit predicates with legible thresholds. A
threshold can be argued with; a weight cannot.

## Design and holdout

The real-message corpus (60,680 posts, 118 days) was split **by post id,
before any message content was read**: design 80.0%, holdout 20.0%, boundary
on a page edge because a page is the indivisible unit on disk (D-012, D-012a,
frozen). The sprint-7 classifier is built on the design window; the holdout
buys one honest evaluation and is spent the moment it is read. Moving the
boundary after seeing a result is that same null repeated with more data, and
the decision log says so in those words.

## What this machinery does not compute

There is no probability of impact anywhere in this codebase, and a lint
(`no_probability_claim`) fails the build if a function of that shape appears.
The honest output is: *a named rule fired at a named time, and here is what
that rule has historically been worth* — a contingency table, an interval, an
exact p-value, a lead-time median, each with a provenance label. Converting
that into P(crossing tonight) would require a model of the adversary's intent,
and no such model is available to this system at any sample size.

## Stated weaknesses

Recorded here rather than left for a reviewer to find, in the order they
bite:

1. **Multiple comparisons.** Six candidate rules are scored against p ≤ 0.05
   with no correction. The family-wise error rate at six independent tests is
   ≈ 0.26; the rules are correlated (they share conjuncts), which lowers it,
   but the number printed is per-rule and a reader should know that. The
   mitigation is structural rather than arithmetic: the gate is three
   conditions, not one, and the holdout exists precisely to catch a rule that
   passed the design window by luck. A Bonferroni-style correction is a
   one-line change if rule generation ever becomes automated; while rules are
   hand-written and few, the holdout is the stronger control [inference].
2. **Power.** With ~12 positives, a true recall of 0.9 is measured with an
   interval wide enough to include values that would fail the gate, and vice
   versa. The gate's verdicts on real data will be provisional in both
   directions, and the Wilson interval is printed so that nobody mistakes a
   point estimate for a finding.
3. **Synthetic validation only, so far.** Every number the gate has produced
   to date validates the *machinery* against a generator with known ground
   truth. `STATUS.json` says this in its `note` field; no gate verdict on
   synthetic history is evidence about the world, and the CLI prints that
   sentence on every run.
4. **The budget is unmeasured.** 2/week is a guess about a recipient nobody
   has asked (T11). Every downstream allocation inherits that label.
