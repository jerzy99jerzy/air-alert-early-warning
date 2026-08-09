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
| A4 | MT4 | A rule with perfect recall that fires on a fifth of all windows | The lift lower bound floor fails it: firing broadly is not information |
| A6 | MT6 | A policy serving one regime scored over both | The coverage gap is counted and printed |
| A7 | MT7 | Malformed, truncated and oversized payloads to a source | `poll` returns without raising. **Fixture path only** |
| A8 | MT8 | The same transition re-polled with a fresh ingest time | The store does not grow |
| A9 | MT7 | Six hostile bodies to the live adapter: empty, non-HTML, bad timestamp, oversized, binary, unknown wording | `poll` returns; nothing raises |
| A10 | MT11 | The source is unreachable rather than quiet | `SourceUnavailable`, never an empty result |
| A11 | MT12 | A mass alert overflows the twenty-message window between two polls | The skipped count is reported; an unmeasurable gap is unknown, never zero |
| A13 | MT14 | A message tagging an area the map does not know, with an oblast named in prose | Classification returns nothing rather than the prose guess; the unknown tag is the only outcome |
| A14 | MT15 | An all-clear whose continuation list names another area as still under alert | Both areas reach the store, the continuation one distinguishable by its role; a single all-clear event fails |
| A12 | MT13 | Two messages in the live footer-time order, exact timestamps asserted | Each event carries its own footer's timestamp; a one-message shift in either direction fails |

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

## Retired attacks

**The budget attack, retired at 0.8.0.0 (its row is gone and its id is not reused).** It asserted that a
policy refuses construction when two regimes each hold the whole of a shared
alarm budget. The budget was removed with D-014, so the refusal it attacked no
longer exists, and a test asserting that a removed feature stays removed passes
for the wrong reason. Rows are removed from the table rather than left as
tombstones, because the table is the list of controls that exist; the
retirement lives here, where it can be read without being mistaken for a
control.
