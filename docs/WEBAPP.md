# The web tier: a page fed by MAVO

Version: 1.0 / 2026-08-10
Status: **partly built, in a separate repository.** `mavo-site` 0.1.0.0 exists
and runs; what is built there is marked BUILT below, what is planned is marked
NOT BUILT, and the distinction follows the manual's convention rather than the
author's optimism.

Companion documents: [`MOBILE.md`](MOBILE.md) is the same kind of document for
the notification channel, [`FEED-SPEC.md`](FEED-SPEC.md) is the specification
this tier has to satisfy against itself, and D-020 in
[`DECISIONS.md`](DECISIONS.md) is why the contract file is written here rather
than assembled there.

## Contents

- [Framing: a surface, not the product](#framing-a-surface-not-the-product)
- [The contract, and who owns it](#the-contract-and-who-owns-it)
- [Three states, three different sentences](#three-states-three-different-sentences)
- [What the page looks like](#what-the-page-looks-like)
- [The palette, and the failure that produced it](#the-palette-and-the-failure-that-produced-it)
- [Freshness is the browser's job](#freshness-is-the-browsers-job)
- [What the page must never say](#what-the-page-must-never-say)
- [Deployment shape](#deployment-shape)
- [What gates publication](#what-gates-publication)
- [Open questions](#open-questions)

## Framing: a surface, not the product

MAVO composes a picture. The web tier renders it for a person who has thirty
seconds and no context. It adds no analysis, no scoring, no interpretation, and
it must not be able to: everything it displays comes from one file, and the
file is produced by a gate this repository runs.

This is the same relationship `MOBILE.md` describes for notifications, with one
difference worth stating. A notification arrives at a person who did not ask
for it at that moment; a page is opened by a person who came looking. The page
therefore carries more context and less urgency, and it is the surface where a
reader can be told what the tool does *not* do, which is why the non-claim
lives above the fold rather than in a footer.

## The contract, and who owns it

One file, `state.json`, schema v1. MAVO writes it (`mavo report --json`, and
`--watch` for the loop); the site reads it and imports nothing from this
package. D-020 records why: the site previously reached into the event store
through an adapter labelled `[inference]`, which put the schema in the hands of
the party that could not check it.

```
mavo report --store /var/lib/mavo/events --json /var/lib/mavo-site/state.json --watch --interval 60
```

| Field | Meaning | The trap |
| --- | --- | --- |
| `v` | Schema version | A reader that ignores it breaks silently on v2 |
| `generated_at` | When this picture was composed | Not when the source last spoke |
| `valid_for_s` | How long it may be trusted | Currently 600, an assumption rather than a measurement |
| `state` | `ok`, `degraded` or `blind` | The page's headline follows this, not the length of `areas` |
| `observation_age_s` | Age of the newest observation, or `null` | `null` is unknown and must never render as fresh or as `0` |
| `areas[]` | One entry per area not affirmatively cleared | An area missing from the list has been cleared; an area present with `alert: unknown` has not |
| `katottg` | Register code, may be `""` | Empty means the map could not resolve it. Render as unknown, do not drop |
| `border_km_lower` / `_upper` | Interval to the border, may be `null` | A single number here would be false with a decimal point on it |
| `kind` | `missile`, `drone`, `unknown` | `unknown` for roughly nine alerts in ten (F71). See the caption rule below |

## Three states, three different sentences

The single most important behaviour of this tier, and the one a redesign is
most likely to smooth away. **A quiet feed and a dead feed must not produce the
same page.**

| Feed state | What the page says | What it must not say |
| --- | --- | --- |
| `ok`, areas present | Alert in N raions, nearest interval, time of the picture | Anything about what will cross |
| `ok`, no areas | No western raion is reporting an alert | "All clear", "safe", or a green anything |
| `degraded` | The picture is older than its validity window, with the age | The area list as though current |
| `blind` | Collection is not working; the page does not know what is happening now | An empty list, which reads as calm |

The site already holds this apart in its tests (`test_quiet_and_blind_are_different_words`) [BUILT], and it is the invariant to check first after any visual change.

## What the page looks like

Three mockups, one per state. **These are mockups rather than screenshots:
deterministic SVG generated from sample data, versioned in the tree so a change
to the design is a diff rather than a memory.** No number in them is a
measurement.

Feed healthy, three raions under alert:

![Web tier, feed ok](assets/webapp-state-ok.svg)

Feed healthy, nothing reported. Note that the sentence changes and the colour
leaves, but nothing turns green and no word promises safety:

![Web tier, quiet](assets/webapp-state-quiet.svg)

Collection not working. The alert layer is extinguished rather than empty, and
the headline says the page does not know:

![Web tier, blind](assets/webapp-state-blind.svg)

Layout, described so it survives a rewrite: a header carrying the non-claim, a
status bar whose colour and sentence follow `state`, a schematic map of the
western oblasts with the Polish border on the left edge, and a distance list on
the right ordered by the nearest edge of each area. The map is schematic on
purpose. A precise map invites a reader to measure their own position against
it, which is a use this data does not support.

## The palette, and the failure that produced it

Red `#ff2f45` carries the alert accent, on the author's instruction of
2026-08-10 (D-S03 in the site's log, which reverses that repository's earlier
no-red constraint). The rule that replaced "no red" is narrower and more
useful: **red on the mark, dark everywhere that covers area.**

The reason is a measured failure rather than taste. An earlier amber palette
carried the alert on the lightness axis, and a viewing client that rewrites
dark themes by flipping lightness while keeping hue turned a dark olive plate
into a bright yellow one and erased the glyph on top of it (D-S02). The fix was
an outline sandwich: white halo, saturated disc, near-black rim, white glyph
stroked in near-black. That construction survives the flip because it carries
the mark on *saturation and contrast order* rather than on lightness alone,
and it is the part of the design most worth preserving through any restyle.

The trailing-window layer, the dark red-brown that shows which raions declared
an alert in the last seven days, stays dark and desaturated so that "under
alert now" and "was under alert this week" cannot be confused at a glance.

## Freshness is the browser's job

The page ships `valid_for_s` and `generated_at` into the client and greys
itself out on the browser's own clock. A server that has stopped updating
cannot be relied on to say so, which is the whole point: the reader's machine
does the arithmetic and the page degrades without anyone's help.

The exporter loop writes the file every cycle whether or not anything changed
(`mavo report --watch`) [BUILT, 0.18.0.0]. A file rewritten only on change is
indistinguishable, to its reader, from a producer that died during a quiet
hour.

## What the page must never say

- **A probability of anything.** Nothing in this design computes one.
- **"Take cover", or any instruction.** The tool reports; the reader decides,
  and official channels instruct.
- **A single distance.** Intervals only, and `unknown` where none is known.
- **"No alert" as reassurance.** The absence of a report is not an all-clear,
  and the wording on the quiet page is chosen to say exactly that.
- **A type where none was parsed.** `kind: unknown` renders as "typ nieznany".
  Since the kind tables cover about one alert in ten (F71), the missing icon is
  the common case, and a legend that lets a reader infer "no icon means nothing
  serious" would be turning a parser limitation into a safety claim.

## Deployment shape

Two processes, and the separation is not stylistic. D-018: what scales must not
sit on top of what must not fail. A post that lands well puts thousands of
readers on one machine, and a collection outage during a strike is the failure
this project exists to avoid.

```
MAVO collector  ->  event store  ->  mavo report --watch  ->  state.json
                                                                 |
                                                       mavo-site (separate host)
```

The site never reads the store, never imports `mavo`, and needs no credentials.
Its only input is a file. That is also what makes the failure mode benign: if
the exporter dies, the file stops moving, and the page says `blind` on the
browser's clock without anyone noticing anything.

## What gates publication

Carried rather than resolved here. All three are open.

- **T6**, the legal position covering readers who are strangers. Now gating the
  site as well as the notification channel, and dated early September.
- **T11**, two conversations with recipients. A blocker under D-015 revision 1
  rather than a formality.
- **The privacy page and the first-screen non-claim.** The second is built and
  tested; the first is not written.

## Open questions

- **Does the page need Ukrainian and English, or is Polish enough?** The
  audience argued for in `docs/BRIEF.md` is Polish readers near the border.
  Unresolved, and cheap to get wrong in either direction.
- **Raion-level markers need centroids MAVO does not currently publish.** The
  contract carries `katottg` and the distance interval; a marker needs a point.
  Adding one is a schema bump, not a field slipped in.
- **What the page does at 03:30 on a phone with one bar.** No measurement
  exists of its weight or its behaviour on a slow connection, and "it is
  stdlib and small" is an assumption until somebody times it.
- **Whether the ADS-B hub count (T42) belongs on this page at all.** It is a
  different kind of claim about a different country, and putting it beside the
  alert picture risks a reader reading one as evidence for the other.
