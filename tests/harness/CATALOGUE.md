# Attack catalogue

One scripted attack per threat-model row. The pass criterion is uniform: the
attack ends in the correct outcome **and** the outcome is observable in what the
product produces, not merely in an exception the test caught.

Convention adopted from `pirx/tests/harness/CATALOGUE.md`, with one honest
difference stated below.

| Attack | Row | What it does | Passes when |
| --- | --- | --- | --- |
| A1 | MT1 | Feed claims every area active within two minutes | Every rule returns None; no alarm can be constructed |
| A2 | MT2 | Feed goes silent mid-night; states become UNKNOWN | No rule fires, and `is_clear(UNKNOWN)` stays false |
| A3 | MT3 | A single border oblast lights up with no vector behind it | The conjunction does not fire |
| A4 | MT4 | A rule with perfect recall that fires on most nights | The gate fails it on alarm rate despite the recall |
| A5 | MT5 | Two regimes each allocated the full budget | Construction refuses with `BudgetOverAllocated` |
| A6 | MT6 | A policy serving one regime scored over both | The coverage gap is counted and printed |
| A7 | MT7 | Malformed, truncated and oversized payloads to a source | `poll` returns without raising. **Fixture path only** |
| A8 | MT8 | The same transition re-polled with a fresh ingest time | The store does not grow |
| A9 | MT7 | Six hostile bodies to the live adapter: empty, non-HTML, bad timestamp, oversized, binary, unknown wording | `poll` returns; nothing raises |
| A10 | MT11 | The source is unreachable rather than quiet | `SourceUnavailable`, never an empty result |
| A11 | MT12 | A mass alert overflows the twenty-message window between two polls | The skipped count is reported; an unmeasurable gap is unknown, never zero |

## The honest difference from `pirx`

Pirx asserts that a refusal appears in the ledger the product wrote, which tests
the deliverable rather than the code path. MAVO has no ledger yet, so A1 to A8
assert on returned values and on printed output. That is a weaker criterion and
it is stated here rather than papered over. A ledger lands with the output
channel, and these assertions tighten in the same version.

A7 exercised the fixture source only, because no live adapter existed. A9 closes
that for the Telegram adapter. The remaining gap is narrower and named: the API
adapters do not exist yet, so MT7 is measured on two implementations of
`ThreatSource`, not on all of them.
