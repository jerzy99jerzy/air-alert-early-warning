# THREAT-MODEL

```
Document:  docs/THREAT-MODEL.md, version 2.0
Audience:  a contributor adding a control, and anyone trying to break this
Companion: MECHANISMS (how each control works), tests/harness/CATALOGUE.md (the
           scripted attack per row), METHODOLOGY (what was found by trying)
Note:      every row carries a control or a **named acceptance**, and every
           acceptance carries the trigger that would reopen it. An accepted risk
           with no trigger is an unaddressed one with better manners
```

## Contents

1. [Who benefits from the output being wrong](#who-benefits-from-the-output-being-wrong)
2. [Rows](#rows)
3. [Residual, stated rather than hidden](#residual-stated-rather-than-hidden)
4. [What the maintainer can do](#what-the-maintainer-can-do)


Adversaries against this tool, not against the world. Rows are numbered MT1
upward with no gaps, each carrying either a control or a named acceptance, and
the test that measures it. `tools/docs_audit.py` fails on a gap or a count that
disagrees with `STATUS.json`.

An accepted risk is not an unaddressed one. It has a trigger that would reopen
it, and where possible a harness attack that asserts the acceptance, so that
forgetting it costs a deliberate test change.

## Who benefits from the output being wrong

An actor conducting incursions benefits in both directions. A false negative
removes warning. A sustained false-positive rate removes attention, which is
cheaper to induce and lasts longer.

## Rows

| Row | Threat | Control or acceptance | Measured by |
| --- | --- | --- | --- |
| MT1 | A source reports implausibly broad simultaneous activation, manufacturing an alarm | Poison suppression: eight or more distinct areas inside 120 seconds suppresses every rule | `test_rules.py::test_poisoned_feed_is_suppressed_entirely`, harness A1 |
| MT2 | A source goes silent during a real event and silence reads as safety, or speaks ambiguously and the ambiguity reads as safety | `AlertState.UNKNOWN` and `AlertState.PARTIAL_CLEAR` are distinct states; `is_clear` is affirmative, never the negation of ACTIVE, and the lint enumerates the enum rather than naming states | `test_schema.py::test_unknown_is_not_the_safe_state`, `test_sprint5.py::test_f26_a_partial_all_clear_never_resolves_to_clear`, harness A2 |
| MT3 | A single fabricated alert in one border oblast raises an alarm | Alarm tier requires the conjunction; one area cannot raise one | `test_rules.py::test_border_only_does_not_fire_the_conjunction`, harness A3 |
| MT4 | Attention exhaustion: an adversary induces sub-threshold conditions until the recipient stops reading | Alarm rate is a hard gate condition, not a quality metric, and the budget belongs to the recipient | `test_baserate.py::test_gate_fails_a_rule_that_fires_too_often`, harness A4 |
| MT5 | Budget laundering: several rules each cleared at the full budget produce a multiple of it | `DecisionPolicy` refuses to allocate more than it holds; the allocator raises rather than trimming | `test_sprint3.py::test_f7_budget_cannot_be_allocated_twice`, harness A5 |
| MT6 | A partial policy reads as complete because unserved crossings left the denominator | Coverage gaps are counted by kind, exposed as `has_coverage_gap`, and printed | `test_sprint3.py::test_f8_partial_policy_reports_its_gap`, harness A6 |
| MT7 | Hostile input converts into an outage: a malformed payload crashes the collector during the window that matters | Contract: `ThreatSource.poll` absorbs every content failure and reports it. Measured on the fixture and Telegram adapters; the API adapters do not exist yet | harness A7 and A9, `test_telegram.py::test_hostile_bodies_do_not_raise` |
| MT8 | Re-polling an unchanged feed multiplies rows until replay stops reconstructing the past | Idempotence by content hash, which excludes `ts_ingest` | `test_store.py::test_repoll_with_new_ingest_time_does_not_duplicate`, harness A8 |
| MT9 | Correlated upstream failure. alerts.in.ua and api.ukrainealarm.com both draw on the same Ajax Telegram channel, so two-source agreement is not independent confirmation | **Accepted, named.** Two sources protect against transport failure only. Trigger to reopen: either service moving to its own acquisition, or the ADS-B channel landing as a genuinely independent observation | not testable in-tree; recorded in `docs/DECISIONS.md` D-010 |
| MT10 | Access revoked without cause. Both Ukrainian feeds grant access revocable at any time with no notice, and the ukrainealarm contract changes unilaterally by being reposted | **Accepted, named.** Mitigated by more than one source and by hashing the contract on each run (T12). Trigger to reopen: a Polish channel with a stated availability commitment | T12 acceptance test, not yet implemented |
| MT11 | An unreachable source is read as a quiet one, so an outage looks like an empty sky | `SourceUnavailable` is raised only for reachability; content failures never produce it. The two paths cannot be confused by a caller | harness A10, `test_telegram.py::test_an_unreachable_source_refuses_rather_than_returning_nothing` |
| MT12 | The page is a window of roughly twenty messages. During a mass alert the channel emits more than that between two polls, and the skipped messages leave no trace, so an overflow reads as a quiet channel | Post ids are compared across polls and the skipped count is reported. Where it cannot be measured, on a first poll or a page without ids, it is reported as unknown rather than zero | harness A11, `test_sprint5.py::test_f27_a_skipped_window_is_counted` |
| MT13 | The live page carries each message's timestamp in its footer, after the text. A page-wide scan that assumes the opposite order pairs message N's time with message N+1's text: every `ts_source` one message late, silently, during exactly the mass alerts that matter (F50). Not an attacker's move but the same damage as one: a systematic falsification of the input the lead-time claim rests on | Messages are isolated by their `data-post` anchor and the timestamp is searched within the block only, so the pairing cannot cross a message boundary by construction. The page fixture is a captured live order, not a synthetic one written to the parser's assumption | harness A12, `test_telegram.py::test_f50_footer_time_pairs_with_its_own_message` |

## Residual, stated rather than hidden

A source that is subtly late rather than silent degrades lead time without
tripping anything. Not currently detected. T5 plans a rolling latency
distribution with an alert on drift.

The output channel does not exist yet, so its threats (a compromised publishing
path sending arbitrary warnings to a trusting audience) are not modelled here.
They land with the channel, in the same version, or the channel does not land.
`docs/MOBILE.md` drafts the rows they will become.

*Amended 0.7.0.0.* That deferral was written while the plan misstated the
project as private-circle only (F53). At the project's actual scope, a public
warning system, the same compromise is a mass-notification event whose harm is
not proportional to recipient count: a false airspace alarm arriving at once
across a region is an incident in its own right. The deferral stands, because
modelling a channel that does not exist produces rows nothing can test, but the
priority does not: these rows are a precondition of the public tier rather than
a follow-up to it, and `docs/MVP.md` Audience D states them as blockers.

## What the maintainer can do

A single maintainer cannot notice a structural claim going stale, which is why
`tests/lint_*.py` and `tools/*_audit.py` assert structure rather than trusting
review. The specific failure being guarded against is documentation describing a
protection the tree no longer implements.
