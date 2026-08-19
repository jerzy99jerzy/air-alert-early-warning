# The web tier: a page fed by MAVO

Version: 3.0 / 2026-08-19
Status: **built, deployed, and publicly reachable.** `mavo-site` 4.12.0.0 runs
at `https://34.116.232.215.sslip.io/` and carries its own gate (seven checks,
24 mutants, a jsdom browser harness), its own defect log and its own audit.
Everything described here was read out of that package rather than remembered.

**The document has been behind the consumer twice**, at 2.5 and again here: it
said 4.1.0.0 while the site had shipped through 4.12.0.0, including the release
that made the map the page and the one that made a switched-off layer stay off.
Recorded rather than quietly corrected, because a document that keeps reading
plausibly while the thing it describes moves is the failure class this file has
now demonstrated twice. The gate check that would stop a third is named at the
end of this section and does not exist yet.

**This document was four releases behind the consumer until 2.5.** The version
recorded here said 1.2.0.0 while the site had reached 4.1.0.0, which is the
class F72 covers: a document that keeps reading plausibly while the thing it
describes moves. It is recorded rather than quietly corrected, and the reason
it went stale is worth naming - the consumer lives in another repository, so
nothing in this repository's gate can notice when it moves.

**What the consumer does with v3, in one paragraph.** It refuses any version it
does not recognise, including v2, because a page rendering an unfamiliar
payload with familiar assumptions is worse than one saying it cannot read the
file. It renders the twenty-minute window as a transitions panel between the
distance list and the map, with both roles and all of Ukraine, and an empty
window as a sentence rather than a blank list. It compares `window_start`
against its own last successful render and states a gap rather than presenting
a continuous-looking list. It fetches `feed.json` when the reader opens the
history, not on every cycle.

**The consequence for deployment, and it is measured rather than assumed:**
because the consumer refuses v2, producer 0.25.0.0 and site 4.0.0.0 must be
deployed in one window. Shipping the producer alone turns the public page
blind, correctly and uselessly. **This was carried out on 2026-08-12** and
took five steps that no gate on either side can check: the package, the
`--feed` flag in the report unit, the push unit carrying two files, the forced
command on the site host replaced with the version-controlled one, and the
site package. Each is recorded in `docs/DEPLOYMENT.md`.

## What the consumer taught the contract

Three requirements that were not obvious until something read this feed in
production. They are in `docs/FEED-SPEC.md` section 4a as properties six to
eight, argued for a feed this project does not control; here they are stated
as obligations this producer has to its own consumer.

**A cap needs a flag, and the consumer needs its own cap.** The window is
capped at 5,000 with `truncated` published beside it. That is necessary and
not sufficient: the site delegated the bound to this side and rendered
whatever it was given, which measured 5.6 MiB from 20,000 events. The site now
caps independently at 200 rows. A bound that lives only on the publishing side
holds until the day the two versions differ, and they are deployed separately
by hand.

**`window_start` is published because the consumer cannot derive it.** A
device asleep for longer than the window cannot tell a gap from a quiet
stretch, and deriving the edge from `generated_at` works only while two clocks
agree. One field on this side; on the other side it is the difference between
"nothing happened" and "you did not see what happened".

**The version policy is the unfinished half.** v3 is a strict superset of v2
and the consumer still refused it, correctly. With one consumer under the same
authorship that costs a deployment window. A public contract does not have
that luxury, which is why the deprecation policy is named in T50 as missing
rather than treated as done.

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
- [The map](#the-map)
  - [The geometry is real, and this is checkable](#the-geometry-is-real-and-this-is-checkable)
  - [The control panel](#the-control-panel)
  - [What a marker means](#what-a-marker-means)
- [What the map refuses to draw](#what-the-map-refuses-to-draw)
- [The palette, and the failure that produced it](#the-palette-and-the-failure-that-produced-it)
- [Freshness is the browser's job](#freshness-is-the-browsers-job)
- [What the page must never say](#what-the-page-must-never-say)
- [Deployment shape](#deployment-shape)
- [What gated publication, and what actually happened](#what-gated-publication-and-what-actually-happened)
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

Two files, `state.json` and `feed.json`, schema v3. MAVO writes them
(`mavo report --json ... --feed ...`, and `--watch` for the loop); the site
reads them and imports nothing from this package.

**Two files rather than one, and the reason is cost rather than tidiness.**
`state.json` is re-read on every cycle, so whatever it carries is a recurring
charge on a phone that may be on one bar at four in the morning; it therefore
carries the current picture and a twenty-minute window of transitions, about
eleven events. `feed.json` carries the last twenty-four hours, roughly 800
events on a typical day and about 18 KiB gzipped, and a consumer fetches it
when a reader opens the history rather than on every cycle. D-024 records the
decision and the measurements behind it. D-020 records why: the site previously reached into the event store
through an adapter labelled `[inference]`, which put the schema in the hands of
the party that could not check it.

```
mavo report --store /var/lib/mavo/events --json /var/lib/mavo-site/state.json --watch --interval 60
```

| Field | Meaning | The trap |
| --- | --- | --- |
| `v` | Schema version | A reader that ignores it breaks silently on the next bump |
| `generated_at` | When this picture was composed | Not when the source last spoke |
| `valid_for_s` | How long it may be trusted | Currently 600, an assumption rather than a measurement |
| `state` | `ok`, `degraded` or `blind` | The page's headline follows this, not the length of `areas` |
| `observation_age_s` | Age of the newest observation, or `null` | `null` is unknown and must never render as fresh or as `0` |
| `areas[]` | One entry per area not affirmatively cleared | An area missing from the list has been cleared; an area present with `alert: unknown` has not |
| `katottg` | Register code, may be `""` | Empty means the map could not resolve it. Render as unknown, do not drop |
| `oblast` | **ASCII slug** (`lviv`), or `""` | The join field. It carried the register's Cyrillic name until 0.19.0.0, and every area landed in the consumer's `unplaceable` bucket: measured at four of four (F74). **One pair does not join on equality**: this register holds a single `kyiv`, the consumer's geometry splits `kyiv-city` from `kyiv-oblast`, and the consumer resolves `kyiv` onto `kyiv-oblast` in `SLUG_ALIASES`. Named here because the divergence is a property of the contract and not of either implementation; the mapping belongs on the consumer's side, where the distinction is made [measured against `mavo-site` 4.27.1.1, 2026-08-17] |
| `oblast_name` | Register name (`Львівська`) | For display. Never join on it |
| `source_last_message_at` | When the source last spoke, may be `null` | Distinct from `generated_at`. A page showing only the latter tells a reader it is fresh while the feed behind it is hours old |
| `window_days` | The trailing window behind `recent_7d` | A count without its window is a number the reader has to guess about |
| `nearest_7d` | The nearest **raion** under alert in the trailing window, or `null` | 0.33.0.0. Same granularity and same `border_km.csv` row as `areas[]`, so the weekly sentence and the live sentence are comparable by construction. `null` is unknown and must never render as "nothing near". The full block it reduces is `recent_7d_areas` in `feed.json` |
| `feed.json: recent_7d_areas[]` | The trailing window per raion, nearest first, unknown distance last | Carries `episodes`, **not** `alerts_count`. Summing `episodes` across an oblast's areas does not give that oblast's `alerts_count` and must not be used as though it did: one western episode lights every raion at once, so the sum measures how finely the oblast is subdivided (F76). In `feed.json` rather than `state.json` because it is 10.2 KiB for the west and 35.5 KiB for every area the map knows, against a 13,150-byte `state.json` polled every thirty seconds [measured on `vm-mavo`, 2026-08-19] |
| `recent_7d[]` | Per-**oblast** alert count over that window | Counts *declarations*, not days under alert: one six-day alert is one declaration, not six. **This block is at a different granularity from `areas[]`, which is per raion.** An oblast is the parent of the areas, not a coarser measurement of the same place, and the two lists share no key space: `areas[].area_id` is a KATOTTG code, `recent_7d[].oblast` is a slug. **It carries no distance, deliberately.** An oblast-level interval takes its lower bound from one raion and its upper from another, so it describes no single place while wearing the field names of the per-area interval that describes exactly one; a page printing both in adjacent sentences would print two quantities under one name. The weekly distance sentence comes from `nearest_7d` instead. Asserted by `tools/contract_check.py`, not left to this row |
| `border_km_lower` / `_upper` | Interval to the border, may be `null` | A single number here would be false with a decimal point on it |
| `kind` | `missile`, `drone`, `glide_bomb`, `artillery`, `unknown` | Five values, and the consumer currently labels three. See below |
| `events` | The twenty-minute window, **always present** | An absent block and an empty one read alike to a careless reader. Empty means nothing happened, and the page must say so in words |
| `events.window_start` | Left edge of the window | Published rather than derived: a consumer compares it against its own last successful read, and a device that slept through part of the window must not render what it got as continuous |
| `events.window_s` | 1200 | Twenty minutes. A dead collector empties the panel three times faster than an hour would |
| `events.truncated` | Whether the cap bound | `false` on any night measured so far. `true` is a finding about intensity, not a daily artefact |
| `events.items[]` | One entry per transition, oldest first | Carries **both roles**. One message can clear an area and list five others as still under alert; keeping only the subject drops the five that are still dangerous |
| `items[].role` | `subject` or `continuation` | See above. This project has already made that loss once |
| `items[].west` | Whether the area is in the eight western oblasts | A flag to colour by, not a filter applied here: the stream carries all of Ukraine |
| `items[].at` | The source's time for the transition | Not ingest time. The difference is the feed latency |
| `counts_24h` | `west`, `rest`, `total` over the day | The context that keeps a twenty-minute window from being a keyhole: a quiet stream while the east is burning is a different fact from a quiet night |

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
status bar whose colour and sentence follow `state`, a distance list ordered by
the nearest edge of each area, and below it the map.

**The distance list renders server-side and works without JavaScript. The map
does not, and says so** rather than leaving an empty rectangle that reads as a
quiet sky.

## The map

**The map is a requirement, not a feature.** A page for a reader in Hrubieszow
at half past three that answers "which raion" with a name and a number, and
nothing else, is asking that reader to hold Ukrainian administrative geography
in their head. Almost nobody can. The distance interval says how far; only the
map says *where*, and where is half the question. Anything that ships without
it ships without the half the reader cannot supply themselves.

That is also why the distance list, and not the map, is the part that works
without JavaScript: the map is necessary, and it is not sufficient on its own,
so the text version is the floor and the map is what makes the floor legible.

### The geometry is real, and this is checkable

The outlines are Natural Earth 10m admin-1 and admin-0, public domain,
simplified offline by the site's `tools/build_geometry.py` and committed as a
versioned asset. Nothing about them is drawn by hand or approximated for
effect.

The asset is verified rather than trusted [measured, in the site's own gate]:
22 checks against values that did not come from the file, including published
oblast areas, published administrative-centre positions, the extent of Poland,
and a direct measurement of the shared Polish border at 24 parallels, worst
offset 3.9 km. Every marker anchor is confirmed to lie inside its own polygon
by point-in-polygon, at build time and again in the test suite. Both sources
must be at the same Natural Earth scale: mixing 10m admin-1 with 50m admin-0
once put the two sides of the border up to 59 km apart, which is the kind of
error that looks like nothing on screen and is fatal to the one number this
project exists to publish.

**The mockup below is drawn from that same asset through that same
projection**, so the shapes in this document are the shapes on the page. The
alert states in it are sample data; the coastline, the oblast boundaries and
the border are not.

![Web tier, map view](assets/webapp-map.svg)

### The control panel

Four controls, in this order: **zoom out, zoom in, "Przy granicy", "Cała
Ukraina"**. The two presets exist because the map has two jobs that pull in
opposite directions. "Przy granicy" is the working view: the western belt and
the Polish border, which is where a Polish reader's question lives. "Cała
Ukraina" is the context view, and it is the reason the map carries all 25
oblasts rather than the six that matter to the distance list.

Also wired [BUILT]: drag, wheel, pinch, arrow keys, `+` and `-`, and `Home`.
Markers counter-scale, so an icon stays an icon at every zoom instead of
collapsing into a blob, while the uncertainty field does **not** counter-scale,
because it is a geographic extent and shrinking it on zoom-out would understate
it.

### What a marker means

The load-bearing sentence on the whole page. The feed sees declared alert
states for administrative units. It does not see objects. A marker therefore
stands for *an area that has declared an alert of that type*, drawn at the
centre of that area, and two mechanisms make the difference between an area and
a point impossible to miss:

- **The uncertainty field.** A marker anchored to a raion, where a centroid is
  supplied, gets a small field. A marker anchored to a whole oblast gets an
  ellipse the size of that oblast's bounding box. MAVO supplies no raion
  centroids today (T43), so **every marker on the map right now is
  oblast-anchored**, and the ellipse is correspondingly large. That is the
  honest rendering of what the feed knows.
- **No pin, no crosshair, no dot with a tail.** All three are the visual
  vocabulary of a fix, and there is no fix here.

**Five kinds, and the consumer names three.** Measured 2026-08-10 over the
corpus: `drone` 2,756 declarations, `glide_bomb` 2,104, `artillery` 934,
`missile` 242. The site knows `missile`, `drone` and `unknown`, so more than
three thousand declarations arrive named and render as *typ nieznany*. That
collapses two different facts, "the source said nothing" and "the source said
something this page has no word for", which is `AlertState.UNKNOWN` against
`PARTIAL_CLEAR` one layer out. T47 carries the fix.

Glide bombs are worth a category of their own even though they do not reach
Poland: they are the largest class in the corpus and they say which oblast is
being worked over right now. Artillery likewise. Neither can reach an alarm
rule, by construction rather than by policy, because `Regime` names missile
and drone explicitly and the rules compare with `is`.

**Icons carry only what the source named** [BUILT]. Missile and drone glyphs
appear for a declared kind. An active alert whose kind was not parsed gets a
filled disc with a pulse and **no icon**; an unknown state gets a dashed ring
and no icon either. An icon names a thing, and the source did not name it.
Since the kind tables cover roughly one alert in ten (F71), the iconless marker
is the common case, which is why the legend says *alarm, typ nieznany* rather
than leaving a reader to infer that a bare disc is something milder.

**Shading is the trailing window.** Fill saturation is the count of alerts in
that oblast over the last seven days, in five buckets, from `recent_7d` and
`window_days` in the contract. An ongoing alert always beats the trailing
layer: one oblast never carries two markers. The bucket edges (1, 3, 8, 20) are
a display choice made by eye and labelled as such in the site's source; nobody
has checked that they discriminate usefully on real data.

**Animation carries liveness, never motion.** Ripples run on a five-second
radar cadence, the marker breathes, rotor blades spin in place. **Nothing
translates across the map**, because a moving icon is a claim about a track and
there is no track in this feed. Under `prefers-reduced-motion` nothing animates
and every distinction survives in the static forms.

**Where the decisions live** [BUILT]: `map.py::build_overlay` decides which
area gets which marker, which icon, which anchor and how the oblast is shaded,
and it is tested in Python. JavaScript draws and handles pan and zoom, and
decides nothing. Anything the map could lie about is therefore in a language
with a gate around it.

## What the map refuses to draw

- **No tile server.** Every pan would send the visitor's viewport and IP to a
  third party, which is exactly what D-016 refused for MAVO. Geometry is
  Natural Earth, public domain, built offline, served once and cached, so after
  the first load pan and zoom cost nothing and are seen by nobody. The price is
  real and worth stating: no cities, roads or rivers as landmarks. The honest
  alternative, if legibility wins that argument, is self-hosted tiles, which is
  a new operational component and deserves its own decision rather than being
  absorbed into this one.
- **No area the geometry does not know.** An area whose oblast slug does not
  match is collected into `unplaceable` and the page says, under the map, that
  the list is complete and the map is not. That behaviour was itself a defect
  once: the site dropped such areas with a bare `continue` and had a test
  asserting that was correct, which would have shown seven areas under alert in
  the list beside an empty map, with nothing saying why (site audit, section 2).
  A reader takes the map for the truth, because a map looks like a measurement
  and a list looks like an opinion.
- **No claim about position.** Restated on the page below the legend, because
  it is the one misreading the whole design is arranged against.

## The palette, and the failure that produced it

Red `#ff2f45` carries the alert accent, on the author's instruction of
2026-08-10 (D-S03 in the site's log, which reverses that repository's earlier
no-red constraint). The rule that replaced "no red" is narrower and more
useful: **red on the mark, dark everywhere that covers area.**

The reason is an observed failure rather than taste, and the diagnosis under
it is weaker than the failure. What was observed: an earlier amber palette,
carried on the lightness axis, rendered as a bright yellow plate with the
glyph erased on the author's viewing client [reported, from two screenshots].
The explanation offered at the time, that the client rewrites dark themes by
flipping lightness while keeping hue, is **[inference]**: the client, its CSS
and a control image were never seen, and a rendering or screenshot pipeline
with its own transform was never ruled out. The site's own audit says as much
about its D-S02 entry, and this document said "measured" until 0.19.2.0, which
promoted somebody else's inference by quoting it carelessly. The fix was
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

```mermaid
flowchart LR
  channel[Telegram channel] --> collector[MAVO collector]
  collector --> store[(event store)]
  store --> report[mavo report --watch]
  report -->|writes every cycle| state[/state.json/]
  state --> site[mavo-site, separate host]
  site --> reader([reader])
```

The arrow into `state.json` is the only coupling. Everything to its left is
this repository; everything to its right imports nothing from it.

The site never reads the store, never imports `mavo`, and needs no credentials.
Its only input is a file. That is also what makes the failure mode benign: if
the exporter dies, the file stops moving, and the page says `blind` on the
browser's clock without anyone noticing anything.

## What gated publication, and what actually happened

This section listed three blockers and said all three were open. Then the site
was published on 2026-08-12 with one of them still open. The honest record:

- **The privacy page and the first-screen non-claim: both shipped.** The
  non-claim sits above the map and a regression asserts it stays there; the
  privacy page exists at `/privacy` and the footer carries a short version of
  it. The footer also now states that the reader's theme and layer choices are
  kept in their own browser, because a paragraph listing what a site does not
  keep may not be silent about what it does (site D-S26).
- **T11**, two conversations with recipients: **still open.** It gates the
  notification channel, which is the thing that wakes somebody up. It does not
  gate a page a reader chooses to open, and D-026 revised the beta definition
  accordingly.
- **T6**, the legal position: **open, and publication went ahead without it**
  under D-025. That is a decision with a reason, not an oversight, and the
  reason is in the decision entry. Anybody reading this file to learn whether
  the project waits for its own blockers should read it as: not always, and
  when it does not, the decision is written down with its date.

**What the deployed site is, as of 2026-08-13.** Version 4.12.0.0. A tiled base
map with the self-hosted SVG announced as the fallback rather than hidden as
one; the map running the width of the page; a panel of state transitions over
the last day; weather fetched server-side; a visit counter that stores two
numbers a day from a daily-rotated hash. No cookie, no third-party request, no
analytics script.

**The check this file still lacks.** Nothing fails when this document falls
behind the consumer, which it has now done twice. The consumer pins its own
version in its `STATUS.json`; the two repositories do not read each other, and
under D-020 they must not. A weaker check is available and honest: this file
records the consumer version it was written against, and the producer's gate
fails when that string is older than the one in the last `state.json` served,
which the producer does see. Not built. Named here so that the next person to
notice the drift finds a proposal rather than a complaint.

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
