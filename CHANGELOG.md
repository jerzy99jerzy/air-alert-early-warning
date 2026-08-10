# Changelog

All notable changes to this project. Entries state the defect, not the change.

**Releases 0.1.0 to 0.3.1.0 have no tags, and that is a debt rather than an
oversight.** They predate this repository being under version control, so the
first tagged release is 0.3.2.0. The alternative was reconstructing commits to
hang the earlier tags on, which would make the history lie about when the code
existed; a stated debt is cheaper and true. Their artefacts exist only as
hand-assembled archives with a `MANIFEST.sha256`.

**0.5.0.0 and 0.5.1.0 also carry no tags.** They were cut and verified but never
pushed: the corpus retrieval work moved fast enough that three releases happened
between one push and the next, and reconstructing commits for tree states that
were never published would be inventing history to satisfy a rule the rule does
not ask for. Their entries stay below because the defects they record are real.
The first tag after 0.4.0.0 is v0.5.2.0.

## 0.19.1.0 - 2026-08-10

**The map mockup was a grid of rectangles, in the document whose argument is
that a map reads as a measurement.**

- **Redrawn from the site's own geometry asset**, through the site's own
  projection: Natural Earth 10m outlines, all 25 oblasts, the Polish border
  where the border is. The shapes in the document are now the shapes on the
  page. Alert states in it remain sample data and the caption says so.
- ** 2.1 states the map as a requirement rather than a
  feature.** A page that answers "which raion" with a name and a distance asks
  a reader at half past three to hold Ukrainian administrative geography in
  their head. The interval says how far; only the map says where.
- **The control panel is documented in the order it appears**: zoom out, zoom
  in, "Przy granicy", "Cała Ukraina". The two presets are the map's two jobs:
  the working view at the border, and the context view that is the reason all
  25 oblasts are carried rather than the six the distance list needs.
- **The geometry's own verification is quoted rather than assumed**: 22 checks
  against external values, the shared border measured at 24 parallels with a
  worst offset of 3.9 km, every marker anchor confirmed inside its polygon.
  Including the failure that produced the rule: mixing 10m admin-1 with 50m
  admin-0 once put the two sides of the border 59 km apart.

## 0.19.0.0 - 2026-08-10

**The contract was joined on a display name, and the consumer's map drew
nothing.** Found by running the site's own code over a file this repository
produced, rather than by reading either.

- **F74: `oblast` carried `Львівська` where the consumer indexes `lviv`.**
  Measured against `mavo-site` 1.2.0.0: **0 markers, 4 of 4 areas
  unplaceable.** The distance list would have rendered completely, because it
  prints the field rather than joining on it, so the failure was a page showing
  areas under alert beside an empty map, with nothing saying why. A reader
  takes the map for the truth. `oblast` is now the ASCII slug and `oblast_name`
  the register name, two fields because they answer to different readers.
- **D-020 was ownership without a control, and this is the control.** Moving
  the contract to the producer one release earlier did not move the consumer's
  vocabulary. The slug came from `oblast_slug()`, which already existed and
  already agreed with the consumer on 22 of 23 oblasts. The twenty-third,
  `kyiv` against `kyiv-city`/`kyiv-oblast`, is a real administrative
  distinction this project does not make, and the consumer maps it: a producer
  that learns its consumer's vocabulary has taken the coupling back.
- **`recent_7d` and `window_days`: the trailing window MAVO was assumed to
  compute and did not.** The site built a whole visual layer on a field its own
  audit recorded as a contract for data that might not exist. It exists now.
  Counts declarations rather than days under alert, because an area under one
  six-day alert is one declaration and shading it as the busiest oblast on the
  map would be the opposite of what the layer is for.
- **`source_last_message_at`**, distinct from `generated_at`. A consumer
  showing only the latter would tell a reader the page is fresh while the feed
  behind it is hours old.
- **Schema bumped to v2**, and this is the first exercise of the rule
  `docs/FEED-SPEC.md` section 3 asks of everybody else. `oblast` changed
  meaning, so the version had to move; a consumer pinned to v1 refuses rather
  than misreads.
- **`docs/WEBAPP.md` 2.0 and a map mockup.** The document described the page
  and omitted its largest surface. It now carries what a marker means, why
  nothing translates across the map, why the uncertainty field scales with the
  map while the badge does not, and why there is no tile server. Every claim in
  it was read out of `mavo-site` 1.2.0.0 rather than remembered.
- **F75: the terminal announced a schema version the file did not carry.**
  `contract=... v=1` was printed from a literal that had been correct until
  this release moved the schema. Caught by reading the output of the release
  smoke test, not by a check, because the file was right and only the message
  was wrong. A constant copied into a message has a shelf life nobody writes
  down.
- **The map mockup is drawn from the site's own geometry asset**, through the
  site's own projection, rather than sketched. The first attempt was a grid of
  rectangles, which is a diagram wearing a map's clothes in a document whose
  argument is that a map reads as a measurement. `docs/WEBAPP.md` 2.1 also
  states the map as a requirement rather than a feature: a page that answers
  "which raion" with a name and a number asks a reader at half past three to
  hold Ukrainian administrative geography in their head, and almost nobody can.
- **Recorded, not fixed: MAVO publishes no raion centroids**, so every marker
  is oblast-anchored and two raions under alert in one oblast render as one
  marker. Honest and coarse. The fix is a centroid column beside the distance
  column.

## 0.18.0.0 - 2026-08-10

**The web tier gets a document, a heartbeat and mockups; the ADS-B thread gets
an honest task.** Sprint continues from S8, which stays partial.

- **`mavo report --watch`: the heartbeat as a loop rather than a cron line.**
  Writes the contract every cycle whether or not the picture changed. Stops on
  the first of three named conditions and says which, the way `mavo backfill`
  does since F46. **A failure to read the store publishes blindness rather
  than skipping the write**, which is the one place in this codebase where
  reintroducing silence-means-safety would be easiest. Held by three
  mutation-verified regressions, one per stop condition.
- **What cron would not have given:** a process that can report how many of
  its cycles were blind. A dead cron job cannot report anything about itself,
  and the count is the number an operator needs.
- **`docs/WEBAPP.md`**, the web tier's counterpart to `docs/MOBILE.md`: the
  contract field by field with the trap in each, three feed states with the
  sentence each must produce, the palette rule that replaced "no red" after a
  measured theme-inversion failure, and what the page must never say. The
  clause about `kind` is the one worth arguing with: the tables cover roughly
  one alert in ten (F71), so the missing icon is the common case and a legend
  implying otherwise would turn a parser limitation into a safety claim.
- **Three mockups, versioned as SVG rather than pasted as screenshots**
  (`docs/assets/webapp-state-{ok,quiet,blind}.svg`). Generated from sample
  data, deterministic, so a design change is a diff rather than a memory. No
  number in them is a measurement and the caption on each says so.
- **T42: the operating intensity of the Jasionka hub, from ADS-B.** Registered
  in 0.16.1.0, and the premise it was registered under was false: ADS-B cannot
  see the drone tier. What it can see is how hard the logistics hub is working,
  which has diagnostic value during a war. Reported, never scored (D-019), and
  the semantics are load-bearing: the count is a lower bound on *transmitting*
  aircraft, so a high number means something and a low number means nothing.
  Acceptance requires a base rate before anything is published.
- **The README names its author.** Apache-2.0 waives neither attribution nor
  the warranty disclaimer, and for warning software the second matters more
  than the first: pre-alpha, never delivered a warning to anyone, classifier
  0 of 20 on real messages. Anyone deploying it for someone else's safety is
  taking a decision the author has not taken.

## 0.17.0.0 - 2026-08-10

**Sprint S8, partial and recorded as partial.** The report composes, the
command runs, the contract file is written by the producer instead of guessed
at by the consumer. The exit criterion in `docs/MVP.md` is a hand-checked
sample of real messages (T36), which is not done, so the sprint is not closed.

- **`mavo/report.py`: the picture at one moment, with its own blindness in
  it.** `compose()` folds the event log into the current state per area;
  `render_text()` prints it for a person; `to_contract()` and
  `write_contract()` publish `state.json`. The feed state leads the output
  rather than trailing it, because a reader who stops after one line must have
  read whether the picture can be trusted.
- **Three feed states, and the exit code carries them.** `ok` is 0, `degraded`
  is 5, `blind` is 6. A wrapper that reads only the status cannot treat a dead
  pipeline as a quiet sky, which is the failure D-015 revision 1 moved from
  backlog into the core.
- **The all-clear asymmetry is now executable.** An area affirmatively cleared
  leaves the list; an area whose state is unknown stays on it as `unknown`.
  Held by a regression verified red against a fold that drops both.
- **Staleness is measured and printed, and null is never zero.** A store with
  nothing in it reports an observation age of `unknown`, not `0`, in both the
  text and the JSON.
- **The western list sorts by the nearest edge, not the centre.** The first
  version of that test used a pair of areas the two orderings agreed on, so
  the mutation passed it. The pair in the test now was found by searching the
  distance table for an inversion: Sarnenskyi is nearer by edge (162.2 against
  162.9) and further by centre (206.7 against 202.9), so a centre sort hides
  the closer area. **Two of the five mutations passed on first run**, and both
  tests were rewritten rather than the mutations being declared unrealistic.
- **`write_contract` is atomic and unconditional.** Written through `mkstemp`
  in the target directory, fsynced, then renamed, because rename is the atomic
  operation and rename is only atomic within a filesystem. Written on every
  cycle whether or not anything changed: a file that is only rewritten on a
  change is indistinguishable, to its reader, from a producer that died during
  a quiet hour (`docs/FEED-SPEC.md` section 4, applied to this project's own
  output for the first time).
- **D-020: the contract belongs to the producer.** The companion site had an
  adapter that imported MAVO, walked the event store and read attributes off
  the domain types, with the binding labelled `[inference]` because it had
  never run against the package. That puts the schema in the hands of the
  party that cannot check it: a rename in `AreaRef` passes this gate, ships,
  and breaks a web page nobody is watching. MAVO now writes the file its own
  gate exercises, and the site's adapter becomes dead code to delete rather
  than a second path to maintain.
- **`AreaTable.by_code()`**, because a stored event identifies an area by its
  register code while the table was only indexed by the channel's tag. Built
  lazily, since most callers never need that direction.
- **`docs/MANUAL.md` section 4.7**, which the gate demanded: `manual_audit`
  fails on a command with no section, and did.

## 0.16.1.0 - 2026-08-10

**The gate said pins held while nine documents disagreed with theirs, and the
README claimed a check on its own tables that did not exist.** A documentation
release: no package code changes, and what changes is what the repository
asserts about itself.

- **F71: the threat-kind tables cover one alert in ten, measured rather than
  assumed.** `tools/kind_coverage.py`, built one release earlier for exactly
  this question, was run against 61,041 messages: coverage 0.128, join_coverage
  0.104, and 36,697 of 42,910 alerts leaving the join as UNKNOWN. Of 2,392
  declarations, 25 were MISSILE. The channel announces ballistics as
  `Загроза балістики`, a form carrying no declaration marker, so the only rule
  that has ever passed the gate on its own regime (7 of 7) is invisible to the
  join almost every time it applies. Four failure modes are recorded with the
  corpus text that produces each. Logged rather than repaired: the repair needs
  this measurement as its reference point.
- **TTL is not the binding constraint, and knowing that removes a piece of
  work.** Coverage moves from 0.128 to 0.127 between a one-hour and a
  twenty-four-hour TTL. The parser's reach binds; tuning the TTL would have
  been effort spent on the wrong term.
- **A guessed risk was wrong in its direction, which is recorded too.** The
  marker `небезпека` was flagged in 0.16.0.0 as possibly over-broad. It has
  zero hits: dead, not wide.
- **F72: nine documents disagreed with their pins while `docs-audit` printed
  that pins held.** `docs/FEED-SPEC.md` declared 1.0 against a pin of 1.3,
  `docs/MVP.md` 3.0 against 3.2, seven more by one or two minor versions.
  `check_every_document_is_pinned` compares the set of documents against the
  tree and never reads a version marker - and its own docstring said so, which
  makes this an unguarded pin whose failure mode was written down in the file
  that needed the guard. `check_document_versions_match_their_pins` is that
  guard, held by five regressions.
- **F73: the README said its tables were recounted on every run.** They were
  not. 0.6.2.0 closed one edge of the triangle, comparing STATUS.json against
  the tree, and the paragraph above the table announced the whole of it. Every
  row of both tables was stale, including 206 tests, 96.14% coverage and 49
  defects sitting twelve lines below enforced badges reading 208, 96.16% and
  51. `check_readme_tables_match_the_pins` reads rows by label, reports a
  missing label rather than skipping it, and fails on the pre-repair README.
- **D-019 records the OpenSky decision with the objection it rejected.**
  Aggregate counts of transmitting military aircraft may be published;
  positions, callsigns and addresses may not. The published figure is a lower
  bound on transmitters and carries that framing in the field itself, because a
  low count means nothing and transponder silence plausibly correlates with the
  situations a reader most wants to know about. The counterargument raised in
  review, that this inverts the argument of `docs/FEED-SPEC.md` section 5, is
  recorded and rejected rather than omitted.
- **D-015 is revised: warning infrastructure, not a reporting instrument
  alone.** The epistemic boundary does not move - no crossing prediction, and
  the 0 of 22 result stands. The standard does move. A reporting instrument
  that goes quiet has missing data; warning infrastructure that goes quiet
  tells its reader the sky is calm, so heartbeat, staleness and an explicit
  blind state become core requirements, end-to-end latency becomes a measured
  property, and T6 and T11 stop being formalities.
- **T7 is resolved after six releases of deferral, as scope rather than
  compliance.** Repository visibility is not an Audience C criterion: the two
  remaining blockers describe the quality of what a reader finds, not whether a
  reader may find it. A tree that must be complete before it is visible cannot
  be reviewed before it is complete, and the reviews are where F72, F73 and the
  0.16.0.0 audit came from.
- **T20 is done, and the assumption underneath it was false.** The OpenSky
  account exists and one authenticated read is measured (token 276 ms, states
  275 ms, one credit per call on the western box). The task was recorded as
  gating the drone tier. ADS-B cannot see the drone tier: Shahed-type munitions
  and missiles carry no transponder, and the feed shows only what chooses to be
  seen. The premise is corrected in place rather than deleted.
- **Fifty-four em-dashes replaced across the tree**, leaving the changelog and
  the release reviews untouched because those are records rather than prose
  under maintenance. `docs/MANUAL.md` needed fifteen contents anchors updated
  with them, since the separator participates in GitHub's anchor rules.

## 0.16.0.0 - 2026-08-10

Review release. No new capability: two defects found by auditing what the
previous two releases took for granted, and three claims demoted from assertion
to labelled assumption.

**F69, the inventory writer ate the freeze record beside it.**
`corpus_inventory.py --write-status` replaced `STATUS.json`'s `corpus` block
instead of merging into it and erased the D-012a holdout boundary, with the gate
passing because nothing read those fields. Repaired on both sides: ownership by
explicit list in `patch_corpus_block()`, and
`docs_audit.check_the_holdout_boundary_survives_in_the_corpus_block` as the
reader those fields never had. Two regressions, both verified red.

**F70, one counter for two different events.** `JoinReport.resolved` merged
"the message named the kind itself" with "the join supplied one", so `coverage`
took credit for regimes the join never touched. Split into `carried` and
`joined`, with `join_coverage` as the join's own figure; `resolved` survives as
their sum.

**Claims demoted to their actual provenance.** The threat-kind marker tables in
`mavo/sources/telegram.py` now carry `[assumption, unmeasured]` and name the two
failures a corpus review must look for, an over-broad `небезпека` and a lift
phrasing that inverts into a declaration; `tools/kind_coverage.py --sample N`
prints classified messages and near-misses from a seeded draw so that review can
happen before any coverage figure is quoted. T41's MTProto latency is an
inference from the protocol rather than a property, and its citation of D-010 no
longer claims a shared upstream that D-010 deliberately does not assert.

**In the 0.13.0.0 line, carried forward.** Three of four `border_distance.py`
spot checks are now measured against an independent border geometry rather than
against the author's recollection (Lviv 57.2, Lutsk 85.4, Uzhhorod 51.6 km,
each within 1.1 km of this tool); the Natural Earth positional error and the
sphericity cost are measured (median 0.0, p95 1.6, max 2.6 km; at most +0.31%)
rather than quoted from general knowledge; and the border-touching regression's
docstring no longer states as proven a geographic fact its assertion does not
test.

## 0.15.0.0 - 2026-08-09

**F68. The corpus was lost, and it had no inventory to lose it against.** Sixty
thousand posts, one copy, no checksum, no location recorded, under every
measurement this project publishes. The tree had a `MANIFEST.sha256` over its
own source files and nothing over the data those files analyse. Tier 1 means not
committed; it had been read as not tracked at all.

- `tools/corpus_inventory.py` writes `data/aggregates/corpus_manifest.csv`: one
  row per snapshot with id range, message count, byte size and SHA-256, and a
  header carrying the aggregate digest, the id range, the contiguity verdict and
  the date. Three separate questions kept in three separate columns: the digest
  answers *is this the same corpus*, contiguity answers *is it complete*,
  id_range answers *is it the right window*.
- `--write-status` patches the `corpus` block in `STATUS.json` from the
  inventory, because a figure retyped by hand from a measurement is a figure
  from memory with extra steps.
- **`docs_audit` now refuses a corpus-derived measurement with no inventory.**
  Any design-window figure in `STATUS.json` requires the manifest to exist and
  to agree with the pinned block. The rule is executable rather than remembered,
  which is the only kind this project keeps.
- **This release ships with that check red on purpose.** The corpus is being
  re-collected as it is written; the gate goes green when the inventory exists,
  and not before. A release that stayed green while its evidence base was
  unidentifiable would be the defect wearing the fix as a costume.

Recovery is possible because Telegram addresses posts by id: the same range
yields the same pages, so this is the same corpus fetched twice rather than a
new dataset. Whether it *is* the same is now a question with an answer, which is
the whole point of the release.

**Three backlog items and one decision, all from the same afternoon.** The
re-collection raised the question of what request rate the source tolerates
(T39), and the observation that a strike is measured in seconds rather than
minutes reframed it: polling is the wrong instrument for seconds however fast it
runs, and MTProto is a push interface that removes the interval entirely (T41).
Both are downstream of a number nobody has: how late the channel already is
relative to publication (T40). D-018 separates the two axes a move to cloud infrastructure gets confused
between: collection is one stream and does not scale, delivery does and arrives
with M2, and a host is an availability decision — with the consequence that a
change of address class restarts T39's ladder rather than continuing it. D-017
records what was refused along the way —
rotating addresses to raise throughput, which would measure a limit we do not
intend to approach, make availability depend on concealment, and cost the
standing to ask Polish institutions for an honestly consumable feed.

## 0.14.0.0 - 2026-08-09

**Sprint 9, T16. The means of attack becomes its own stream, and the regime
split becomes able to fire on real input.**

- **F67. Every regime rule was unsatisfiable on live data.** `kind` was read off
  the alert message; the channel emits it as a separate message, tied to a
  hromada, with its own lifetime, exactly as F25 recorded in sprint 4. Measured
  on the twenty real messages held as fixtures: 15 carry an alert state, 4 carry
  a kind marker, none carry both. The regime split is this project's central
  finding, and on real input it had nothing to split by.
- `KindEvent` and `KindState` in the schema, a `kind_events` table beside the
  alert table rather than a discriminator column on it, and `mavo/kinds.py`
  holding the index and the join. The join runs before the rules, so the rules
  are unchanged and still know nothing about where `kind` came from.
- **Ambiguity resolves to unknown.** Two kinds live over one oblast at the same
  moment, which is a mixed strike, leaves the alert UNKNOWN and counts the case.
  Picking the first, the newest or the more dangerous would each be a
  fabrication with a rationale attached.
- **The source outranks the assumption.** A declaration expires after
  `DEFAULT_KIND_TTL`, six hours, because one whose lift never arrives would
  otherwise stay attached to an oblast forever. A lift that does arrive is
  honoured whenever it arrives, even past the TTL: a number written in this
  repository does not get to shorten a statement made by the channel. The first
  draft of `KindIndex.active` capped it and that inversion is recorded in the
  code.
- Threat-kind messages previously parsed as nothing and were counted as
  unparsed. They now have a reader, so part of the old parse-failure rate was
  never failure.
- `tools/kind_coverage.py`: the measurement that decides whether any of this has
  coverage. It prints declaration counts, the declaration-to-lift interval
  distribution that replaces the assumed TTL, and join coverage at five
  candidate TTLs. **It cannot run here**: the corpus is tier-1 data and is not in
  the tree. Until it has been run against `data/raw`, the honest claim is that
  the regime split *can* fire, not that it *will*.

## 0.13.0.0 - 2026-08-09

**T32, and sprint 8 closes.** Distance to the Polish border, 127 of 127 areas,
computed offline and stored as a column. `AreaRef.border_km` was `None` for
eight releases; it is now three fields and an interval.

- **The column is an interval, not the scalar the criterion asked for.** The
  register gives a centre point, not a polygon, and a centre point puts
  Самбірський район 14.2 km from a border it shares an edge with. Five areas'
  intervals reach zero. `border_interval` renders `0-46 km`, which tells a
  reader the alert may be at the border and that the report cannot say more; a
  bare `14 km` would tell them something false to one decimal place. Deviation
  from T32 recorded in `TODO.md` and `docs/METHODOLOGY.md` rather than taken
  quietly: a criterion may move only when the replacement is harder, and this
  one is.
- `tools/border_distance.py` regenerates the column from the KATOTTG-to-OSM
  register join published by `ua-geo` (MIT) and `data/reference/poland_outline.json`,
  a 29 KB unmodified extract of the Natural Earth 10m Poland feature, vendored so
  the measurement is reproducible from the tree. Both source checksums and the
  method go in the output header. Geodesic point-to-arc, no projection, no
  runtime dependency; the count stays at zero.
- **A spot check caught the author.** Four settlement distances were written
  down by hand before the run. Lutsk was bounded at 90-130 km from an estimate,
  the tool measured 85.1 km and refused to write the file. A flat-earth
  cross-check gave 86.4 km, so the bound was the error and was widened with that
  reason recorded in the source. The four checks now run in the suite as well as
  in the generator, since the generator runs rarely and the suite runs always.
- A checkout without the generated column still resolves areas and reports every
  distance as `unknown`. The one thing it must not do is fall back to a
  plausible number.

## 0.12.2.0 - 2026-08-09

- **A prediction made in this repository's own working notes was wrong, and the
  correction is better than the guess.** The expectation was that the Government
  Centre for Security published its two catalogue datasets as PDFs, which the
  state technical standard rules inadmissible at every openness level. Measured:
  four resources, XML and HTML, all at **openness level 3**, all declaring an
  update frequency of *not applicable*. The entries are correct under the
  standard; XML is permitted at level 3 and HTML is only discouraged above it.
- **The corrected finding is narrower and harder to answer.** Level 3 is the
  level at which the standard recommends API delivery specifically so data can be
  machine-processed, so the publisher already sits at that threshold and
  publishes files. The gap is therefore not competence, not format and not the
  platform: **alerting messages are not treated as a category of data at all.**
  The category exists on the portal for air quality, with a dynamic API. For
  alerting it does not exist, and the publisher who would own it is already
  present and already compliant.
- That version of the claim cannot be met with "our format is fine" or "we
  cannot do this", because both are consistent with it.

## 0.12.1.0 - 2026-08-09

- **`docs/FEED-SPEC.md` section 3 rewritten around a document that already
  exists.** The Ministry of Digital Affairs publishes a *Standard techniczny*
  defining minimum technical requirements for public data, and four of the five
  properties this project asked for are already in it: re-use without a request,
  TERYT codes rather than prose names (the standard defines a *universal address*
  and states outright that it is not for human reading), ISO 8601 timestamps, and
  API delivery from openness level 3 with JSON per RFC 8259. The specification is
  now a citation with a table showing where each property already lives. A
  request nobody has to invent is much harder to decline than one somebody does.
- **The fifth property is marked as a gap in that standard rather than as a
  demand.** The standard describes how a *dataset* is formatted; a stream needs
  a different guarantee, namely a signal that it is alive. DCAT-AP's
  `accrualPeriodicity` declares an intended update frequency in the metadata and
  says nothing about now. For most public data that costs nothing; for alerting
  it is the difference between a quiet night and a dead system.
- **T8 stops being inconclusive.** The portal's full catalogue metadata was
  downloaded and searched: 1,510,768 resources, 29 datasets matching alarm,
  warning, siren, RCB, civil protection, crisis management or evacuation, and
  none of them a stream. RCB is in the catalogue with two datasets, both
  documents, neither flagged dynamic; IMGW publishes meteorological warnings;
  dynamic feeds exist on the portal, including an air quality API. The absence is
  specific to this category rather than to the publisher or the platform, which
  is a sharper claim than the one the document previously made.
- The limit of that measurement is stated where the figure is: absence from the
  open data catalogue is not absence from the world, and a non-public interface
  would never appear in it.

## 0.12.0.0 - 2026-08-09

**The schedule is removed. It rested on an assumption nobody had measured.**

- `docs/MVP.md` v3.0 gave every sprint a two-week calendar window and beta a
  date of 4 October. Those numbers rested on something never written down and
  never checked: that this project is worked on continuously. It is a weekend
  project, and the parser at the centre of sprint 7 took two afternoons spread
  across the days that were free. **A schedule built on an unmeasured assumption
  is the same defect class this repository removes from its own gate** (D-014,
  the alarm budget), and it is removed for the same reason: the number was
  invented rather than observed. The window column now reads `N/A` and beta has
  no date.
- What survives is what was always true and is checkable: the order of the five
  sprints, the dependency chain, and an exit criterion per sprint that is
  produced by running something rather than by declaring progress.
- **One date stays, and it is not an estimate of effort.** T6, the legal
  position, is due at the beginning of September. It is answered by counsel or
  it is not, and no engineering week shortens it. It carries a date rather than
  a condition deliberately: a condition like "before anyone else receives a
  notification" cannot be checked until it has already happened, which makes it
  an intention rather than a criterion, while a date passes on its own and the
  passing is visible.
- **`docs/FEED-SPEC.md` lands, with a correction to its own first paragraph.**
  The draft claimed four months of consuming the Ukrainian channel. That was the
  span of the corpus, 118 days of history retrieved in a single backfill, not
  the span of the work. Restating a true figure in a context where it means
  something else is the shape of several defects already in this log, and this
  one was caught before the document was published rather than after.
- The README status line says outright that the plan carries no dates and why,
  so that a reader who expects a roadmap is told the reason rather than left to
  infer one.

## 0.11.2.0 - 2026-08-09

**Documentation release, plus the check that would have caught it being wrong.**

- `docs/reviews/0.11.1.0.md`. The external review that produced F61 to F63,
  written to the convention every review session in this repository follows. It
  records what was repaired, the one finding raised and deliberately left for a
  sprint (T38, the border predicates that cannot fire on real input), four
  findings left untouched because each is a measurement or an owner decision,
  and what the review did not do. It describes 0.11.1.0 and is not updated
  afterwards: a review is a record of a moment, not a living document.
- **F64. A pin that nothing compared against the tree.** `STATUS.json` carries a
  `documents` block, eleven checks read `STATUS.json`, and none of them read that
  block against `docs/`. A document could be added unpinned and the gate would
  still print `pins hold` - which is exactly what it did while this release's own
  review document sat unpinned. The block looked like a check and was a sentence
  in JSON. `docs_audit` now compares it against the tree in both directions.
- The coverage figure quoted in the new review names the interpreter that
  measured it, applying that review's own finding about environment-dependent
  pins to its own numbers.

## 0.11.1.0 - 2026-08-09

**External code review.** Three defects found by composing contracts rather than
reading layers, each with a regression verified red before the fix; the lint net
widened to cover its own instruments. Entries F61 to F63 in `docs/METHODOLOGY.md`.

- **F61.** A valid-but-offsetless `datetime` attribute parsed cleanly, crossed
  `poll()` under the never-raise contract, and the store refused the resulting
  event at `append` (F52) - malformed content became an outage one layer up.
  A naive timestamp is now malformed at the parser and takes the unparsed path.
  `test_telegram.py::test_f61_a_naive_content_timestamp_never_becomes_an_event`
  asserts the poll-to-append composition itself.
- **F62.** `UrllibTransport` passed URLs straight to `urlopen`, which also
  speaks `file://`: a latent local-file-read behind constants. Non-http(s)
  schemes are refused as `SourceUnavailable`.
  `test_transport.py::test_f62_a_non_http_scheme_is_refused`.
- **F63.** A duplicated tag in `tag_map.csv` resolved to whichever row came
  later in the file - a contradiction inside the one artifact resolution
  trusts, absorbed by dict assignment. `AreaTable.from_csv` now refuses with
  `DuplicateTag`. `test_areas.py::test_f63_a_duplicate_tag_in_the_map_is_refused`.
- **The gate now audits its own instruments.** `make lint` covered `mavo` and
  `tests` while half the measured numbers in `STATUS.json` are produced in
  `tools/` and `tools/harness_mutation.py` is itself part of `verify`. Ruff and
  mypy now run over `tools` as well; the findings that fell out (three long
  lines, one union-attr) are fixed.
- **Five tools carried their own copy of the snapshot-name regex, two their own
  copy of the tag grammar and the western-oblast list** - the drift class F36
  names, one character at a time. `mavo/backfill.py` now exports
  `SNAPSHOT_NAME` beside the writer that defines the grammar, and the tools
  import `TAG` and `WESTERN_OBLASTS` from `mavo/areas.py` instead of restating
  them.
- `EventStore.append` names its columns instead of depending on schema order,
  and `replay` iterates the cursor instead of materializing the log a line
  after promising an iterator.

Found and deliberately **not** changed, because each is a measurement or an
owner decision rather than a repair: the `area_id` vocabulary split between
KATOTTG codes and the fixture slugs in `BORDER_OBLASTS` (dead today, a mine
under S8), the rules layer importing `Night` from the fixture module, R2's
endpoint-only westward test (changing the predicate changes measured gate
results), and the `content_hash` field separator (changing it breaks the
identity of stored rows). Recorded in the review, not in this log's fixes.

## 0.11.0.0 - 2026-08-09

**Sprint 7 closed.** On an amended criterion, and the amendment is the entry.

- `tools/consistency_check.py`. T36 required a hand-labelled sample because when
  the criterion was written no automated check appeared to exist. One did, and
  it was in the messages all along: the channel writes the area name twice, in
  prose and as a tag, and two independent copies of one fact can be compared by
  a machine. **38,520 of 38,521 comparable design-window messages agree,
  99.997%.** The single disagreement is an oblast-tagged damage report whose
  prose names the raion, correct at both levels. Observed area-resolution
  errors: zero.
- **The criterion change is recorded rather than assumed.** The replacement is
  not easier, which is the only defensible reason to change one after the fact:
  three orders of magnitude more coverage, ±0.02% where a hand sample gives ±5%,
  and weaker in kind because internal consistency is not truth. The residual is
  named: 9,701 messages carry a tag and no prose area, 20% of the corpus, and
  T36 is retargeted at exactly that population instead of retired.
- **A message class nobody knew about, found because the check disagreed with
  itself first.** An all-clear can carry a continuation list naming areas where
  the alert is *still running*. The first run compared it against the tag as one
  set and produced 1,203 false disagreements; separating them moved agreement
  from 96.972% to 99.997%. 5.2% of comparable messages carry one, naming 4,064
  areas, and **the pipeline records none of them** (T37). Two rows added to the
  information-loss table in `docs/DATA-FLOW.md`, both marked invisible, which is
  the defect class this project exists to attack.
- **The report's shape is now decided by measurement, not preference.** 86.7% of
  comparable messages name one area; the tail runs to eight and stops there. One
  line is the default form, a list handles 13.3%, and eight fits a phone screen.
- The run before that measured mostly the probe's own regex: `(?:в|у|на)` with
  no word boundary matched the `на` ending `Повітряна`. Third instance in one
  session of an instrument reporting its own defect as a property of the
  material. Repaired by keeping only candidate names the map already knows,
  because `район` is an ordinary noun too and no pattern over that word can tell
  an administrative unit from the area of an old town.
- The one ambiguous tag resolves by context: `Покровська_територіальна_громада`
  appears beside `Нікопольський район` and `Дніпропетровська область`, which
  identifies the Dnipropetrovsk one. 127 of 127 once the row carries that reason
  (T33).
- `AreaTable` gains `tags` and `names` as read-only views, because a probe had
  been reaching into the private mapping for the vocabulary.

## 0.10.3.0 - 2026-08-09

- `tools/label_sample.py`, the instrument T36 needs and the last thing that can
  be built for sprint 7 without a person reading Ukrainian. `draw` writes a
  sample in two strata: messages that resolved to an area, which test whether
  resolution is correct, and messages whose tags resolved to nothing, which test
  whether the unknown-tag path triggers on the right thing. `score` reads the
  labelled file back and reports the error rate with a Wilson interval.
- **The draw is seeded and fingerprinted, and score recomputes the fingerprint.**
  A sample that can be redrawn until the number looks acceptable is not a
  measurement. Changing the seed is allowed and changes the fingerprint;
  changing it silently is what the check makes impossible.
- **`score` refuses a partially filled file.** A sample scored as if complete is
  a measurement of the rows somebody found easy, and refusing is the whole point
  of the check.
- The sample carries message text and therefore defaults under `data/raw/`,
  which is git-ignored: a committed file of channel content is a tier-1 artifact
  under `SECURITY.md` regardless of how public the source is.
- **Harness attack A13 (MT14)** promotes the F60 control from a test verified by
  hand this morning to one the mutation run verifies on every invocation. The
  adversarial reading is what makes it an attack: the channel's vocabulary
  drifts on its own schedule, and one unrecognised tag in a message that names
  an oblast in prose produced a warning naming the wrong place. Twelve attacks,
  eleven mutation-verified.

## 0.10.2.0 - 2026-08-09

- **F60. An unknown tag was overwritten by a prose guess.** The sprint 7
  fallback fired whenever the tag path produced nothing, which is wider than its
  justification: a message carrying a tag the map does not know, and mentioning
  an oblast in prose, resolved to that oblast from the table that scores 0 of 20.
  The unknown tag was reported separately while the event carried the guess.
  Found by running the sprint's own mutation check, whose failure printed
  `assert 'lviv' != 'lviv'` and exposed the wider condition. A message whose tags
  resolve to nothing now returns no classification, so the unknown tag is the
  only outcome, and the fallback is reachable only from untagged messages.
- **The README now states where the information comes from, in full.** One
  signal source, the public channel preview, with no token and no agreement
  behind it; two APIs that are not independent of it (D-010); the state register
  as an offline file under CC-BY (D-016); ADS-B registered as valuable and not
  blocking; and no Polish-side feed found that is both machine-readable and
  timely (T8). Everything the tool says about Ukraine is `reported`, there is
  exactly one source, and losing it is total.
- **A section on why a quiet west is the good news**, because the instinct runs
  the other way. 5.73 episodes a week and 1.56 region-wide means the volume
  regulates itself without the ceiling D-014 removed, a rare message keeps its
  meaning, the filtering is the channel's own and costs nothing, and twenty-two
  region-wide episodes in ninety-nine nights is few enough that a person near the
  border can check the tool from memory. With the honest other half beside it:
  the same quietness makes a predictor impossible to validate, which is why this
  reports instead (D-015, F58).
- Every document in the README table is now a link, and `docs_audit` fails the
  build on a relative link that resolves to nothing. The documentation table is
  the map a reader uses before they trust anything else.

## 0.10.1.0 - 2026-08-09

Sprint 7 shipped, and a negative result recorded beside it.

- **`mavo/areas.py`: area resolution by the channel's own hashtags.** F23's
  repair. `classify` now prefers the tag the channel attached, resolved through
  the versioned 127-row map to a KATOTTG code and an oblast, and falls back to
  the oblast-name table only for the 0.66% of messages carrying no tag (T34).
  The fallback is kept rather than deleted, because deleting it would change
  what an untagged message means before anyone has read one.
- **Unknown tags are reported, never absorbed.** `ParseReport.unknown_tags`
  carries them to the caller. A tag the table does not know is a finding: the
  channel named a new area, or a name drifted (T33). A fallback that mapped it
  onto something plausible would make the day a new raion appears look exactly
  like every other day. It does not raise either, because content must never
  become an outage.
- `AreaRef.border_km` is `None` and stays `None` until S8 measures it (T32).
  Unknown prints as unknown; a caller rendering it as 0 would put a Polish
  reader on the border.
- Ten regressions in `tests/test_areas.py`, mirrored as the sprint's record in
  `tests/test_sprint7.py`. The load-bearing one asserts that a message naming
  one oblast in prose and tagging a raion in another resolves to the tag, which
  is the difference between sprint 7 and no sprint 7.
- **Measured, and against the project's own earlier hope:** the design window
  holds 81 western episodes, 22 of them touching all 36 western raions, and
  Polish sources report no airspace violation on any of the four busiest western
  nights. A predictive rule would have scored 0 of 22. Under D-015 that is not a
  finding against the project, it is the base-rate argument arriving as an
  observation, and it is the strongest available confirmation that the
  predictive framing was correctly dropped one release earlier. Labelled
  `reported, absence of evidence`, with T35 recording the check that would make
  it a measurement.
- The volume figures a western-only report would produce, now in
  `docs/CHANNEL.md`: 5.73 episodes per week, 1.56 of them western-wide. The
  distribution is bimodal, 22 episodes at 36 areas against 39 at one to four,
  which decides that the report needs two message forms rather than one
  parameterised one.
- A correction to this project's own tool: `west_activity` divided episodes by
  *active* nights and reported 11.12 per week. The denominator was the subset in
  which the phenomenon occurs. Corrected to 99 nights throughout, giving 5.73.
- **S7 is not closed, and this release corrects a claim that it was.** Its exit
  criterion has two halves: every tag resolves or is marked unresolved, which is
  met, and a hand-labelled correctness sample, which does not exist (T36).
  Recording the sprint complete on the strength of the countable half is the
  failure the criteria table was written to prevent. The remaining windows are
  pulled forward two weeks and beta moves to 4 October, but **T6's deadline does
  not move**: gaining engineering time buys nothing against a decision blocker,
  which makes it now the most likely cause of a slip.
- `docs/reviews/0.10.1.0.md` covers this release and the four before it in one
  pre-push review, and `docs/MANUAL.md` documents `unknown_tags` as the field to
  watch next.
- The standing assumption that incursions are deliberately organised against the
  Polish border rather than spillover is recorded as **speculation**, used
  nowhere in the code, and present only to stop the predictive framing being
  revived on the grounds that a longer corpus would fix it.

## 0.10.0.0 - 2026-08-09

The source turned out to be structured, and that changes three sprints.

- **`docs/CHANNEL.md`, and it is the most consequential measurement in the
  project so far.** 99.34% of design-window messages carry a hashtag naming the
  area and its unit type: `#Харківський_район`, nominative, spaces as
  underscores, unit word explicit. 127 distinct tags across 99 nights, of which
  126 resolve to a unique code in the Ukrainian state register. The parse
  problem was never vocabulary; nobody had read the structure.
- **F23 is explained rather than only recorded.** The shipped table searched for
  oblast names in message text and scored 0 of 20. The channel emits an oblast
  tag in 515 of 69,676 occurrences and names raions the rest of the time, so the
  table could not have scored above zero. Two sprints had been planned around
  the wrong diagnosis.
- **The east-west split is the product filter, arriving for free.** 2,456 of
  69,676 tag occurrences (3.5%) are western oblasts; the rest are front-line
  raions 900 kilometres from any Polish reader. The channel labels the
  difference itself, so the filter needs no classifier to be trained or trusted,
  and a western-only report has a naturally small volume because the west is
  naturally quiet.
- **F59. A probe presented an arbitrary match as an attribution.** The
  text-matching probe reported 16.56% and attributed its busiest match to Lviv
  oblast; the text was `Миколаївський район`, in Mykolaiv oblast. Two defects:
  the first entry of a colliding stem was printed as geography, and restricting
  the register to western oblasts made a nationally colliding stem look clean. A
  restriction on the register is not a restriction on the text. Corrected lower
  bound 6.06%, and 77 of 445 stems in scope collide somewhere in the country.
- `data/reference/tag_map.csv`: tag, count, unit, register name, oblast, KATOTTG
  code, status, note. Two rules were needed and are recorded in the file rather
  than hidden in code: composite `м_X_та_Yська_територіальна_громада` tags
  resolve on the member after `_та_`, and `#ВолодимирВолинський_район` has no
  register entry because the register renamed it. That second one is why the
  file has a `note` column: **the channel and the register are two
  independently evolving vocabularies** (T33).
- `tools/west_activity.py` measures what a western-only report would have said
  and how often, in episodes rather than messages, because an alert and its
  all-clear are one event. `tools/register_probe.py` keeps its corrected upper
  and lower bounds and its structural axes.
- S7's exit criterion sharpened from a hit rate to two countable things: every
  tag resolves or is explicitly unresolved, and a hand-labelled sample agrees on
  the message the tag sits in. T34 asks what is in the 0.66% of messages with no
  tag at all, which may be administrative posts or may be the ones that matter.
- `NOTICE` carries the CC-BY attribution the register's licence requires, and
  `data/reference/` is named as a committed tier-2 directory for derived lookup
  tables with their provenance.

## 0.9.2.0 - 2026-08-09

- `tools/register_probe.py`. S7's first question, asked rather than assumed:
  does the state register's wording appear in what the channel actually emits?
  The shipped table keyed on oblasts and scored 0 of 20 (F23); the register
  carries raions and hromadas, and whether its *names* survive the channel's
  *inflection* is empirical. The probe reports the share of design-window
  messages carrying at least one register name, broken down by category and
  oblast, plus how many register entries never appear at all. Both halves are
  printed because a hit rate carried by three stems is a different situation
  from the same rate spread across the register.
- It measures presence, not correctness, and says so twice. Matching is on a
  truncated stem because Ukrainian inflects (`Володимирський` against
  `у Володимирському районі`), which trades precision for recall deliberately:
  the question is whether the vocabulary is there at all, and over-matching
  errs in the direction the hand-labelled sample will catch.
- **The register located and measured** [measured, by retrieving it]:
  `kaminarifox/katottg-json`, `orderDate` 2024-01-19, 31,751 items; restricted
  to the eight western oblasts, 36 raions and 484 hromadas. **It declares no
  licence**, so it cannot be vendored into an Apache-2.0 tree whatever its
  contents. The codifier itself is a Ukrainian government publication and open,
  so T31 now requires the official source with its URL, version and retrieval
  date, and treats the GitHub copy as a cross-check rather than the artifact.
- T31 renamed from KATOTTH to KATOTTG. The earlier spelling followed one English
  transliteration and matched nothing any source publishes, which is a small
  error of the kind that costs an hour to a contributor searching for the file.

## 0.9.1.0 - 2026-08-09

- `docs/MVP.md` rewritten to v3.0 against D-015, with section 1 stating what
  each old criterion was measuring and why the replacement was necessary rather
  than convenient. The paragraph headed "the thing that does not compress" is
  gone with the framing that produced it: crossing scarcity blocked validating a
  predictor and does not block validating a report, so the autumn deadline
  became reachable by narrowing the claim rather than by working faster.
- **Five sprints to beta, dated, with checkable exit criteria.** S7 area
  resolution to 23 Aug, S8 the report to 6 Sep, S9 real time to 20 Sep, S10
  delivery to 4 Oct, S11 hardening to 18 Oct. Each exit criterion is a number
  produced by running something: a measured hit rate, a stated error rate, a
  latency distribution, a delivery time through Do-Not-Disturb, a clean-clone
  `make verify`. Beta is defined in one sentence so it cannot drift, and what
  beta is not is listed beside it.
- The dependency chain is stated so a slip propagates visibly, and T6 is marked
  as the one track no sprint can absorb: if the legal position is not recorded
  by 5 October, beta slips to that date plus two weeks and the slip is reported.
- Backlog statuses realigned: T15 and T31 promoted to the centre of S7, T16 to
  S7 as output rather than a rule feature, T14 and T20 deferred out of the beta
  plan because ADS-B was a prerequisite for an alarm tier that D-015 removed
  from the critical path, T11 restated as the question of whether recipients
  exist rather than a budget calibration.
- Section 9 names the one sprint whose difficulty is genuinely unknown, S7, and
  states the response if the hit rate comes back low: report it and re-plan. A
  report that names the wrong rajon is worse than no report, because it is
  actionable.

## 0.9.0.0 - 2026-08-09

The thesis is restated. This is a scope change, not an edit.

- **D-015. The tool reports a picture; it does not predict a crossing.** Whether
  a munition crosses depends on what air defence brings down, where the debris
  of an intercepted one falls, a drone losing its way, and an adversary's
  choices minutes earlier. None of that is in any feed reachable from here, so a
  predictor would be claiming to see what is not there. What is observable now
  is the Ukrainian-side picture: areas under alert, intensity, named means, and
  kilometres to the border. On 30 July the whole episode lasted thirteen
  minutes, and nothing available to a private person filled the minutes before
  it.
- Consequences, each of which silently changed what other work is worth doing:
  the dozen crossings stop being the target variable, so T28 is deferred and the
  corpus no longer has to be long enough to contain them; the 57% base rate
  stops being the number to beat; the gate applies to an alarm class alone, if
  one is ever built, and the reporting tier is judged on correctness, latency
  and completeness, all measurable on the corpus in hand.
- **D-016. Geocoding is a versioned file, not a service call.** KATOTTH as data
  in the repository, joined to OpenStreetMap geometry, with distance to the
  Polish border precomputed as a column. A commercial API would give the same
  numbers plus a key in the warning path, a rate limit where latency is the
  product, and a third party learning which rajons a Polish user asks about at
  three in the morning. T31 and T32 record the work; area resolution is now the
  core of the product rather than a supporting gazetteer.
- **F58. One corpus was sized for two different requirements.** Sized for
  message variety, which it satisfies, then assumed to be the evidence base for
  scoring a rule against crossings, for which 99 design nights give an expected
  0.81 positives. The single crossing in the corpus period falls in the holdout.
  It took a measurement to see: the threshold sweep produced a cost axis
  immediately and then had nothing to say about recall, and the silence was the
  finding.
- **The measured block in `STATUS.json` is now partly recomputed.**
  `candidate_rules_passing_gate` had read 0 for three releases after D-014 made
  it 1, in the one block that states an outcome rather than a count. The audit
  re-derives that field and the policy firing rate on every run; the rest of the
  block stays a typed claim and the check says so rather than implying more.
  The channel-volume figure now carries both the measurement (514/day over the
  corpus) and the older single-window inference (650/day), labelled separately.

## 0.8.1.0 - 2026-08-09

- `tools/threshold_sweep.py` gains an hourly axis, because the nightly one
  measured flat on the real corpus. Every night in the design window carries
  more than 120 messages, at roughly 490 a night, so a per-night volume
  threshold separates nothing: the channel is loud continuously. The new axes
  take each night's busiest clock hour, filtered and unfiltered. The maximum
  rather than the mean, because a night with one violent hour and eleven quiet
  ones is the shape being looked for and a mean erases exactly that night.
- The first real run also corrected a prediction made in this repository's own
  planning: the area filter was expected to match nothing, on the strength of
  F23's 0-of-20. It matched 1.05%, 510 messages of 48,540. The channel does
  sometimes name an oblast, rarely, and a twenty-message sample was too small to
  see it. The filtered sweeps now print with an explicit warning that at that
  coverage they measure the nights on which the channel happened to name an
  oblast, which is a different population from the nights of western activity.

## 0.8.0.0 - 2026-08-09

The attention budget is gone. A lift floor takes its place.

- **D-014, superseding D-007 and D-008.** The two alarms per week limit is
  removed: not a gate condition, not a constant, not an allocation refused at
  construction. It encoded an assumption about how a recipient behaves at a
  given notification frequency and nobody had measured it. Recipients who care
  leave the tool on and moderate their own push settings; recipients who do not
  will mute it. Modelling that from an armchair and hard-coding the model as a
  refusal is the error this project refuses everywhere else.
- **A lift floor replaces it, because removing the condition exposed what it was
  accidentally doing.** With the rate ceiling gone, a rule firing on every
  campaign night has perfect recall and p = 1e-03 and would pass while telling
  the recipient nothing the date did not. The gate now requires the *lower bound*
  of lift to clear 1.50, which states the requirement directly and states it
  pessimistically, because a positive class of twelve moves a point estimate by a
  factor on one night. Measured: 57% of nights gives 1.01 and fails, 30% gives
  1.92, 14% gives 3.70.
- **What was lost is written down rather than argued away.** Alarm fatigue as an
  attack surface is no longer refused by construction. Harness attack A5 and
  threat-model row MT5 are retired with their controls; A4 is rewritten against
  the new floor and is mutation-verified in the slot the old condition held. The
  trade is stated in D-014 and again in F57.
- **Measured consequence, recorded rather than tuned.** On the adversarial
  synthetic history `R1-border-active` now passes the gate at 2.52 alarms per
  week with a lift lower bound of 1.69. Through 0.7.x nothing passed. The margin
  over the floor is thin and the history is synthetic.
- **F56: a defect entry was itself wrong.** F55 claimed `MAX_ALARMS_PER_WEEK`
  did not exist in the package. It did, in `mavo/baserate.py`; the check that
  found its absence imported it from `mavo.policy` and read one failed import as
  a fact about the package, then replaced a correct citation with a different
  one. Corrected in place with a pointer rather than deleted, because a log whose
  entries can be wrong is only worth reading if the wrong ones are marked.
- T29 records the honest replacement for the removed number: measure mute rate,
  unsubscribe rate and time to first mute from the first week the channel exists.
  If disengagement turns out to be sharply frequency-dependent, a rate condition
  returns to the gate with a measurement behind it, on D-014's own stated terms.

## 0.7.3.0 - 2026-08-09

- `tools/threshold_sweep.py`. The scenario tables argued about feasibility from
  assumed firing rates; this measures the real one. For each candidate
  intensification threshold it reports nights above it, the share of all nights,
  and the implied alarms per week, over the design window only. It refuses every
  page above the boundary frozen in `STATUS.json` and prints how many it refused,
  because a sweep that cannot prove it stayed inside the design window is not
  evidence (D-012a). It writes nothing.
- Two sweeps, because one of them works today and one does not. Volume needs no
  classifier and is usable now. The area-filtered sweep prints its term coverage
  on every run, and when coverage is zero it says so in words instead of
  printing a table of zeros: that output is F23 reporting itself, not a property
  of the nights, and a table of zeros would be a measurement of nothing.
- The tool is silent on recall by construction and says so twice. It knows the
  cost of a threshold and nothing about what the threshold catches, which is
  half the gate. T28 records what is missing: a dated, sourced crossing list.
  The positive class has lived in prose since the beginning, which is enough to
  reason about sample size and not enough to score a rule.

## 0.7.2.0 - 2026-08-09

- `docs/DEPLOYMENT.md`, a plan with open decisions marked as open. The daemon is
  the first component of this project with an identity on a machine: it
  persists, it is scheduled by the operating system, and it makes outbound
  requests on a timer with nobody present. Security tooling forms an opinion
  about that object whether or not anyone declares an intent, so the document
  states the full egress inventory, the endpoint identity work on each platform,
  and what each costs.
- The scheduling shape is called out as the part that goes wrong. A timer-shaped
  job would run, log cleanly and silently deliver none of M0's value: the
  skipped-message counter is computed by comparing post ids between consecutive
  polls of one live source, so a process respawned every minute resolves it to
  `unknown` forever, and that counter is the reason the daemon exists.
- Containers get a case rather than a verdict. Not for dependency isolation, of
  which there is none to isolate, and not as a committed artifact with a base
  image pin that no audit here checks. Yes as an instrument for the T7 onboarding
  probe now, and yes as the unit of deployment at Audience D.
- A defect found by reading rather than running, and recorded as unproven:
  `DirectoryLock` decides liveness with `os.kill(pid, 0)`, and pids are per
  namespace, so two containers on one volume could both hold the lock. T26 is to
  reproduce it before it becomes a threat-model row, and to record the negative
  result if it does not.
- T25 (where the daemon lives), T26 (the lock), T27 (jitter from the first
  commit of M0, because adding it later invalidates the interval measurements
  that would justify tightening the poll).

## 0.7.1.0 - 2026-08-09

- `docs/OBSERVABILITY.md`, a plan and marked as one. Shadow mode's product is a
  record of decisions that were never sent, so at M0 the log stops being a
  diagnostic and becomes the deliverable. A JSONL sink at DEBUG independent of
  console flags, because an audit trail whose completeness depends on which flag
  someone passed is not evidence; a reader that imports the stage vocabulary and
  is imported by nothing, because a progress indicator wired into the run would
  be a second statement about where the run is and would start by disagreeing
  with the log.
- Two constraints in it are this project's own rather than the pattern's. The
  renderer distinguishes three outcomes, not two: a stage that could not measure
  prints `unknown` and a stage that measured nothing prints `0`, and an
  acceptance test fails a rendering that shows `skipped=0`. And the sink carries
  no message text by default, because a log echoing bodies would put holdout
  content in front of the author during ordinary operation and spend the D-012a
  split without a decision to spend it.
- T23 and T24 record the work and the guarantee, with acceptance written before
  the code so it cannot be adjusted to whatever the code turns out to do.

## 0.7.0.0 - 2026-08-09

A scope correction, and the two documentation defects that hid behind it.

- **F53. The notification plan declared public distribution out of scope.** The
  project's target scope is a publicly available warning system, so that
  sentence misstated the destination with the confidence of a decision. It
  survived a full release because everything around it agreed: MVP.md topped out
  at a portfolio artefact, T6 asked counsel about a private circle, and the
  threat model deferred output-channel rows on the strength of a small trusting
  audience. A coherent smaller project that no check could contradict, because
  every check here verifies that documents agree with each other and these did.
- `docs/MVP.md` gains **Audience D, a publicly available warning system**, with
  its blockers typed: the holdout gate, a measured alarm rate from shadow mode,
  a legal position covering strangers rather than a named circle, a budget
  calibrated on more than two conversations, a delivery path with an
  availability target, and a subscription route that is not one Android app in
  English. The gap between C and D is deliberately larger than the gap between
  A and C, because that gap is the honest distance to the point of the project.
- `docs/MOBILE.md` replaces its incorrect closing section with `Sequencing, not
  exclusion` and a new section on what public availability changes: the budget
  becomes a distribution rather than one person's tolerance, blast radius
  replaces individual harm in the threat model, delivery acquires the project's
  first availability target, and accessibility stops being optional.
- **F54. An access blocker outlived the access problem.** Two MVP rows read
  `blocked on the token` after the corpus was retrieved without one, and one of
  them had been satisfied since sprint 4. A row mistyped as `access` is a row
  nobody attacks, which makes the error self-preserving.
- **F55. Two figures were written from memory.** `COMPUTATION.md` cited a
  constant that does not exist in the package, and `MOBILE.md` called an
  inference from one 14.7-hour window a measurement, when the corpus gives a
  real one (~514 posts/day across 118 days). Provenance laundering: a label
  improves as a claim is copied, because the copy keeps the number and drops
  the qualifier. T22 proposes the cheap partial guard.

## 0.6.2.0 - 2026-08-09

Two claims the repository made about itself and did not check.

- **The quickstart now has a real-data path.** Everything a reader could run in
  sixty seconds was synthetic, which flattered the project twice: the numbers
  came from a generator, and the one shipped defect a newcomer would actually
  meet was reachable only by reading the manual. Three commands against the live
  public channel, with the honest expectation stated beside them: roughly twenty
  messages in, almost none parsed, because F23 is real and prints itself.
- **The repository size block is recounted rather than remembered.** The README
  said these figures were measured at each release and pinned; nothing checked
  them, and all four rows were stale by a release or two while reading as
  authoritative. `docs_audit` now recounts the tree and fails on disagreement,
  with the counted definition written into the check rather than left to
  reinterpretation. Same class as F31, in the block that describes the
  repository to a reader who will not open it.
- `docs/ARCHITECTURE.md` gains the design-document row its layout table was
  missing, and its "what is not here" list now points at `docs/MOBILE.md` for
  the output channel and names `mavo watch` as what turns the skipped-message
  counter from `unknown` into a measurement. A section listing absences is only
  useful while the absences are current.

## 0.6.1.0 - 2026-08-09

One document, and the gap it closes is an audience gap rather than a defect.

- `docs/BRIEF.md`. Every document in this repository is written for someone who
  already accepts why the project exists: FOUNDATIONS argues with a contributor,
  COMPUTATION argues with a statistician, THREAT-MODEL argues with an attacker.
  None of them is readable by the person most likely to ask the sharpest
  question, which is someone outside the field who wants to know whether the
  thing works. The brief states the 57% base rate before it states the thesis,
  names the 0-of-20 classifier failure and the measured null in plain
  language, and ends with the six questions that would expose a weak answer.
  Convention adopted from `pirx`, where the brief is the document non-technical
  readers actually finish.
- **D-002 restated as the general rule it always was.** The exclusion was
  documented as a case: one named covariate, tested and rejected. It is now
  documented as the procedure that case established, which is what actually
  binds future work: a candidate covariate is admitted only after a
  pre-registered directional test on the full attack-density series, and one
  that measures null is excluded mechanically rather than left lying around
  looking plausible. The measurement is unchanged and still quoted in full: 738
  attack nights, 87,093 munitions, Rayleigh R = 0.013 with p = 0.95, Spearman
  r = +0.03 with p = 0.44. What is gone from the documents is the variable's
  name, which was doing no analytical work; the terms stay enumerated in
  `tests/lint_limitations.py`, because a guard has to name what it forbids.
  The lint marker and its README bullet are renamed to
  `no_excluded_covariate` accordingly.
- The convention has a rule worth stating: the brief simplifies but never
  flatters. Where it rounds a mechanism, it says so; where a number is a guess,
  it carries the same label it carries in FOUNDATIONS. A brief that reads
  better than the evidence supports is marketing with a repository attached.

## 0.6.0.0 - 2026-08-09

An external review read the tree adversarially and three of its findings were
defects, one of them in the live parse path. Entries state the defect.

- **F50.** The page-parse regex required time-before-text; the live page puts
  the time in the footer, after the text. Every live-parsed event carried the
  previous message's timestamp, the first text on the page was dropped, and the
  suite could not see it because the page fixture was synthetic and written in
  the regex's order - a fixture encoding the code's assumption, F1's class one
  layer down. Parsing is per `data-post` block now, the fixture is the live
  order, and harness A12 (MT13) mutation-verifies the pairing.
- **F51.** Backfill snapshots were written non-atomically, so an interrupt
  mid-write could plant a truncated page whose filename claims the full id
  range - invisible to `--resume` and to `contiguity_gaps`, which reads ranges
  from names. Snapshots now write to scratch and `os.replace`.
- **F52.** The store's replay order (ISO text, lexicographic) was chronological
  only by the accident that no source with a non-UTC offset had ever met the
  naive-datetime fixture generator in one store. The store now normalizes to
  UTC at append and refuses naive timestamps (`NaiveTimestamp`); the content
  hash spells one instant one way regardless of reported offset; the generator
  emits aware-UTC.
- **D-013.** `content_hash` keeps excluding `kind` and text, and the reason is
  now written down: a store is a parser's reading of the raw corpus, rebuilt by
  a new parser rather than appended over - the path where a re-ingest silently
  kept the old parser's rows is closed by convention and by the decision log.
- `is_degraded` joins `is_clear` and `is_actionable`: the docstring had promised
  a degradation predicate that did not exist, which is README-claim drift living
  one file below the lints that catch it. Written by negation in the safe
  direction - a fifth state is degraded, and loud, by default.
- `UrllibTransport` local logic (size cap, exception mapping, lossy decode) was
  untested at 68% coverage; the size cap is a threat-model control and an
  untested control is an unmeasured one. Four tests, no network.
- The defect-count badge is now pinned: STATUS.json against the methodology's
  F-entries, the README badge against the pin.
- Entity decoding via `html.unescape` (the hand map missed numeric entities);
  `<br>` in both spellings becomes a newline, because the sprint-7 classifier
  reads line structure. Two unreachable superstring rows dropped from the
  pattern tables. The directory lock takes creation atomically (`O_EXCL`).
- `docs/COMPUTATION.md` states the statistical machinery the thesis stands on;
  `docs/MOBILE.md` plans the notification channel and its MVP.

## 0.5.5.0 - 2026-08-09

Documentation raised to the level a contributor joining cold actually needs, and
two new checks so the additions cannot rot.

- `docs/MECHANISMS.md` rewritten from eight sections to twenty-five, one per
  mechanism, each with its code location, its constants, **the alternative that
  was rejected and why**, the failure it prevents, and the harness attack that
  guards it. The rejected alternative is the part that was missing: a document
  saying what the code does is a worse document than one saying what it does not
  do and why not.
- `docs/ARCHITECTURE.md` gains a module reference with the public surface and
  invariant of every module, a section naming **the four boundaries** and what
  each one buys, extension points with what landing each one requires, and the
  repository layout beyond the package.
- `docs/METHODOLOGY.md` gains a generated defect index and a section on **the
  four recurring defect classes**. Thirty-two entries reduce to four shapes, and
  a contributor who learns the shapes will recognise the next one faster than
  the last one was recognised.
- `docs/THREAT-MODEL.md`, `docs/MVP.md` and `docs/DECISIONS.md` gain header
  blocks in the same convention as the rest.
- README gains badges, a statistics table, and a reading map by intent. Only the
  CI badge is live; **the static ones are claims**, so `docs_audit` now fails the
  gate when a badge value disagrees with `STATUS.json`. Verified red by inflating
  the coverage badge to 99.90%.
- `docs_audit` also resolves every in-document anchor link. Six documents now
  carry a contents index, which is six new surfaces for the drift class that has
  produced four defects here already. Verified red by renaming a section.
- Statistics pinned in `STATUS.json`: 2,184 lines of package against 4,890 of
  documentation, a ratio that is deliberate.

## 0.5.4.0 - 2026-08-09

The corpus exists, and the boundary is frozen before anything reads it.

- Corpus retrieved: ids 260841 to 321520, 60,680 posts across 3,034 pages,
  2026-04-13 to 2026-08-09, contiguous, 313 MB.
- D-012a computes and freezes the design/holdout boundary at id 309381:
  48,540 posts for design, 12,140 for holdout, 20.0%. Computed
  from post ids with no message content read, which is the only thing that makes
  it a holdout rather than a test set chosen with hindsight.
- **Campaign nights are invisible in a daily count and visible hourly.** Daily
  volume is flat: median 590, max 764, a ratio of 1.29. Hourly volume runs a
  median of 25 against a maximum of 112. Routine alert and all-clear pairs from
  the whole country dominate the daily figure. The redesign must label candidate
  campaign windows by hour; the plan of finding them by day would have found
  nothing and concluded there was nothing to find.
- The hourly tail thins smoothly rather than stopping at a round number, so the
  channel has no throughput ceiling. This matters before anyone computes a
  vector from an activation sequence, because a capped channel would reorder
  and batch under load.
- Daily volume drifts about 20% upward from April to August with no step change,
  so the channel did not alter its format inside the corpus and the older window
  is usable for design.
- F49: the sixfold volume change reported while reading the backfill output was a
  division error, corrected to 25%. Recorded because the wrong number was the
  interesting one, and interesting is how a number reaches a document.

## 0.5.3.0 - 2026-08-09

Three defects in `backfill`, all found by running it against the real channel
for twenty-five minutes rather than by reading it. None of them threatened the
corpus; all three were in what the tool tells the operator.

- F46: interruption was not one of the five stop conditions, so Ctrl-C produced a
  stack trace and a run that had retrieved 1150 pages did not say so. It is now
  the sixth, named in the report like the others. Every stop condition in the
  original list was one the channel produces; the operator was not modelled as a
  source of endings at all.
- F47: two runs could share one output directory silently. The corpus survives it
  because snapshots are named by id range, but the request rate doubles against a
  service whose tolerance is measured only over a burst of twenty. An advisory
  lock carrying the holder's pid now refuses with exit code 6, and takes over
  from a dead holder rather than requiring a cleanup step nobody remembers.
- F48: a 2800-page run printed nothing for twenty-five minutes, so working and
  hung looked the same. Progress goes to stderr every 25 pages; stdout still
  carries only the report, so a redirect yields a clean artefact. `--quiet`
  suppresses it.

## 0.5.2.0 - 2026-08-09

Documentation for contributors. No behaviour changed.

- `docs/FOUNDATIONS.md`: the observations and assumptions the project rests on,
  six assumptions each with its falsifier, the provenance table, and the section
  that says what would make this project stop. Includes the assumption most
  likely to be argued with, that attention is a finite resource owned by the
  recipient, recorded together with the challenge to it rather than as settled.
- `docs/DATA-FLOW.md`: the data architecture. One message from byte to verdict
  across seven stages, the corpus as a parallel pipeline that deliberately stops
  early, the three data tiers, and a closing table of every stage that can lose
  information and how that loss is made visible. Invisible loss is the defect
  class this repository exists to attack, so it gets its own table.
- `docs/ARCHITECTURE.md` restructured as the infrastructure document: components,
  the four dependency rules with what enforces each, process and deployment
  shape, and a section naming what is deliberately absent. Architecture and data
  flow were one document and answered two questions badly.
- `docs/MANUAL.md` gains the header block, contents index and glossary in the
  `pirx` convention, plus a section 9 glossary of twenty-two terms.
- `CONTRIBUTING.md` gains a reading order.

## 0.5.1.0 - 2026-08-09

- `mavo backfill --resume` continues below the lowest id already on disk and
  prints where it started. Without it an interrupted run re-walks everything it
  already holds, which on the 2900-page corpus is the entire run again. It
  refuses rather than choosing when combined with `--before`: two cursors, one
  loop, and a start point that depends on an unprinted argument is a start point
  the output cannot be read without.
- T21 closed with a stated limit. 0.5 s and 0.2 s both measured clean over 20
  requests, with `posts=400` in each, so the service was not silently truncating
  pages. **The default was not lowered.** A burst of 20 does not license a claim
  about a run 145 times longer, and a default is a claim; that is the F44 pattern
  and it is refused here on purpose.
- Channel measurements table added to `docs/METHODOLOGY.md`, including the row
  that says what remains unmeasured.

## 0.5.0.0 - 2026-08-09

Sprint 6, part one. The corpus is retrieved rather than awaited.

- F44: for two sprints this repository held that the corpus could only be
  collected forward in time, because the channel page is a twenty-message
  window. That was true of `mavo collect` and false of the channel: the web
  preview accepts a `before` parameter and pages backwards through the full
  history, 321,498 posts at exactly 20 per page as measured on 2026-08-09. The
  belief shaped T19, D-011, the sprint 5 scope decision and the advice to start
  a cron immediately. The probe that should have caught it asked for posts
  before id 1000000 against a channel whose newest was 321498, where a working
  parameter and an ignored one produce identical output.
- `mavo backfill` walks history backwards and writes each page verbatim, named
  by id range so a re-run resumes rather than duplicates. It parses nothing
  beyond post ids: the corpus exists because the pattern table is wrong, and a
  corpus filtered through that table would not be evidence.
- Contiguity is computed from what is on disk and every hole is printed with its
  id range and size, exit code 5. A corpus with holes it does not name is a
  sample that believes it is a census.
- Five stop conditions, each named in the report: page count exhausted,
  `--stop-at-id` reached, a page with no posts, a page that failed to move
  backwards, an unreachable source. A short run is never silently a short
  history.
- F45: the red-verification probe for this sprint passed against a scratch copy
  of 0.4.0.0 and should not have. The editable install resolved `mavo` to the
  working tree, so the scratch imported the new module. Ninety seconds of
  survival, recorded because the mechanism defeats the repository's standing
  regression rule for every sprint that adds a module. CONTRIBUTING.md now says
  to uninstall first.
- D-012: the design/holdout boundary is declared before any message content is
  read. The holdout is the newest 20% of posts by id. A holdout chosen after
  looking is not a holdout.
- T21 added: the 1.0 second delay is a deliberately conservative guess and is
  labelled as one. Measure the tolerated rate before the large run.

New dependency count: zero.

## 0.4.0.0 - 2026-08-09

Sprint 5. The evidence container before the evidence.

The sprint that was scheduled here was the classifier redesign. It was not run,
because the corpus it needs does not exist yet and twenty messages from twenty
minutes of one evening are a probe, not a design basis (F28, D-011). What can be
built without the corpus is the part of the source layer that decides whether
the corpus, once collected, will be trustworthy.

- F26 closed: `AlertState.PARTIAL_CLEAR`. A message announcing an all-clear
  while saying the alert continues had nowhere to go in a three-state model and
  would have resolved to CLEAR. It is deliberately not folded into UNKNOWN:
  UNKNOWN is silence, PARTIAL_CLEAR is contradiction, and a contradiction is
  evidence while silence is not.
- F27 closed: post ids are compared across polls and the skipped count is
  reported. **Unknown is printed as unknown, never as zero.** A first poll has no
  baseline and a page without ids has no observable, and in both cases claiming
  continuity would be the flattering default. MT12 and harness A11 added.
- `classify_state` split out of `classify`. The state layer was the one of three
  that was correct on real content (15 of 20) and could only be exercised through
  an area conjunct that matches nothing, so it was untestable in practice.
- F14 closed after two slips: the harness is mutation-verified. Ten controls
  disabled one at a time in a scratch tree; the guarding attack must go red.
  `tools/harness_mutation.py`, in `make verify`, measured at roughly 7 seconds.
- F38: A4 did not measure the alarm-rate gate. Its contingency table failed on
  association as well, and its assertion looked for the substring "alarm rate",
  which the *passing* reason also contains. Both halves survived the budget being
  disabled. Found by the mutation run on its first execution.
- F39: A9 did not reach the parser it claimed to test. Its six hostile bodies
  used single-quoted class attributes and the page serves double quotes, so the
  message regex matched nothing and every body was absorbed unparsed. The attack
  passed by not arriving. Present since 0.3.0.0, where it was recorded as
  closing MT7 for the Telegram adapter.
- F40: A11, written in this sprint, tested the unknown-versus-zero decision on
  the one path that returns before reaching it. The tool caught a defect in an
  attack written the same afternoon.
- F41: `ci.yml` carried `hygiene`, `docs-audit` and `manual-audit` as separate
  jobs restating steps `verify` already runs, in a repository whose README says
  CI does not restate the gate. Removed. This is the ENGINEERING section 2 drift
  in the repository that quotes it.
- The lint behind the unknown-not-clear claim now enumerates `AlertState` rather
  than naming UNKNOWN, so the fourth state was covered on the day it landed and
  a fifth would be too.

Documentation audited against the tree in the same release, since three of the
last four releases found a document describing an earlier version of it:

- F42: MT8 cited a test that has never existed under that name. The control was
  tested; the row's account of how was false for three releases. `docs_audit`
  now resolves every `file.py::test_name` cited in `docs/`, the README and the
  catalogue, and was verified red against the defect before it was fixed.
- F43: `ARCHITECTURE.md` omitted the Telegram adapter, the transport layer,
  `policy.py` and `evaluate.py`, and labelled two blocks with sprint numbers the
  schedule had moved past. `lint_mermaid` checks that a diagram parses, not that
  it is true.
- MT2 widened to the fourth state. `SECURITY.md` and `CONTRIBUTING.md` now state
  the state guarantee over the enumeration rather than over a list of names.
  `MECHANISMS.md` gained the two mechanisms this sprint shipped. The manual's
  sprint labels, operational limits and troubleshooting table were corrected.

Not done, and not a slip: the pattern table still scores 0 of 20 and its pins
still hold. The gazetteer (T15) needs a reference dataset this repository does
not have, and the means-as-message-class rework (T16) needs the corpus to answer
how a means message joins an alert by area and time window.

## 0.3.2.1 - 2026-08-08

A transfer defect, not a code change. The tree is identical to 0.3.2.0 except
for the two files 0.3.2.0 was supposed to contain.

- F37: the archive unpacked onto the workstation was the build before last. It
  lacked `data/aggregates/.gitkeep` and the CHANGELOG paragraph recording that
  releases 0.1.0 to 0.3.1.0 carry no tags. The initial commit's message then
  asserted that paragraph was in CHANGELOG.md, which it was not: a commit
  message claiming a document the tree does not contain, which is the same
  class as a changelog entry claiming a protection the code does not implement.
  Survived because the manifest check passed: an archive is internally
  consistent with its own manifest whichever build it came from, so
  `shasum -c` proves completeness and says nothing about currency.
- The manifest is regenerated here. Class fix deferred to 0.4.0.0 as a decision:
  either the manifest carries the version it was built from, or the archive
  filename is not the only place the build is identified.

## 0.3.2.0 - 2026-08-08

Consistency audit. The documentation had drifted from the tree in six places,
each found by re-running the gate and re-reading every claim against it.

- F31: `STATUS.json` pinned coverage at 98.59 while the gate measured 95.33; the
  block's test count had been updated twice while coverage rode along from
  sprint 2, under a note claiming the whole block comes from `make verify`. A
  partially updated measurement block is worse than an unmeasured one.
- F32: the README described the release before last: sprints "0 to 3", "no live
  feed", 89 tests, 8 attacks, MT1 to MT10, a twice-stale harness owner, and a
  layout missing three modules. Every stale sentence sat outside the five claims
  `lint_limitations` registers, which is the gap, not the excuse.
- F33: MT9 cited `docs/DECISIONS.md` D-010, which had never been written.
  D-010 now records the correlated Ukrainian dependency and its revocability,
  with reopen conditions; T13 closes with it. The upstream *direction* (channel
  feeds APIs, or siblings of one chain) is downgraded to a labelled inference in
  METHODOLOGY: correlation is load-bearing and holds either way, relative
  latency does not and gets measured in sprint 5.
- F34: `docs/MVP.md` gated latency measurement on the API token three sections
  above a schedule saying sprint 4 ships ingestion without waiting on anyone.
  Amended and recorded as a scope change.
- F35: F29 claimed the real-content measurement was pinned as assertions; two of
  three layers were, the means layer (4 of 20) stayed prose. Pinned.
- F36: `transport.py` hardcoded `mavo/0.3.0.0` in the User-Agent at 0.3.1.0. The
  constant now derives from `__version__`.
- `mavo collect --save-raw DIR` writes the fetched page verbatim before parsing,
  with its own failure exit code (4). Added now rather than in sprint 5 because
  the corpus (T19) can only be collected forward in time: the page is a
  twenty-message window, and content not saved this week does not exist next
  week. New dependency count: zero.
- T19 (corpus, with a window) and T20 (OpenSky, recategorised to self-service)
  added; T4 narrowed to future adapters after sprint 4 delivered its Telegram
  half.

## 0.3.1.0 - 2026-08-08

The pattern table measured against real channel content. It scored zero.

- F23: the area table matched 0 of 20 real messages. The channel names raions and
  hromadas, never oblasts, and the table was keyed on oblast stems, so it could
  not match by construction. The state layer matched 15 of 20 and was correct;
  the means layer matched 4 of 20.
- F24: a message names an area and nothing else, so mapping raions to oblasts
  needs a gazetteer this repository does not have. The border-oblast rules the
  whole thesis rests on currently have no input.
- F25: means of attack is a separate message class with its own lifetime, not an
  attribute of an alert. `ThreatEvent` models it wrongly.
- F26: a fourth state exists. A yellow all-clear that says the alert continues
  must not resolve to CLEAR.
- F27: the page is a window of roughly twenty messages, so a poll interval that
  is comfortable at rest can skip messages during a mass alert, leaving no trace.
- The measurement is pinned as assertions rather than described in prose. Three
  tests assert the zero hit rate, so F23 cannot be closed quietly: fixing it
  requires flipping a pin.
- Real message content saved verbatim as `tests/fixtures/real_messages.py`.

Nothing was tuned in response. The classifier still scores zero; the redesign is
sprint 5, and shipping a table hastily patched against twenty messages would
repeat the mistake at a smaller scale.

## 0.3.0.0 - 2026-08-08

Sprint 4. Live ingestion, with the access blocker off the critical path.

- `mavo/transport.py` is the only file in the package that reaches the network.
  A test asserts nothing else imports `urllib`, so "what can this thing talk to"
  has one answer in one file.
- `TelegramChannelSource` reads the public channel that is the shared upstream of
  both Ukrainian APIs. It buys no independence, and MT9 says so: a wrong or
  silent upstream is wrong or silent here too. What it buys is data today
  instead of data when someone answers an email.
- F17: a parser that raises converts a hostile string into an outage during the
  only window that matters. Content failures are absorbed and reported;
  `SourceUnavailable` is raised for reachability alone.
- F18: a stale pattern table would make a live channel look quiet. Unmatched
  messages are counted and printed, never dropped, so drift between the table
  and the channel appears in the output rather than as an absence of events.
- MT11 added: an unreachable source is not a quiet one, and `mavo collect` exits
  3 rather than 0 so a wrapper cannot confuse them.
- Harness gains A9 and A10. MT7 is no longer fixture-only.
- Stated limit, not implied away: parsing is tested against an injected
  transport. That a live channel emits the shapes the pattern table expects is
  not tested and cannot be from a test suite.

## 0.2.1.0 - 2026-08-06

Documentation, banner, and alignment with the portfolio standard set by `pirx`.

- Versioning moves to four segments, matching `pirx`. The bump is its own commit.
  Earlier entries keep their three-segment tags; renaming a shipped tag would
  break the only thing a tag is for.
- `docs/MANUAL.md`: operator's manual, written from the first sprint rather than
  at the end. Every section declares BUILT, PARTIAL, NOT BUILT or NARRATIVE, and
  `tools/manual_audit.py` fails the gate when a CLI subcommand has no section.
- `STATUS.json` pins the version and the shipped-sprint set; `tools/docs_audit.py`
  fails when a document's declared version drifts past it.
- Refusals are a type. `mavo/errors.py` carries the taxonomy and there is no
  warning type in this codebase: a condition either refuses or it does not exist.
- `tests/harness/`: scripted attacks, one per threat-model row, asserting the
  correct typed refusal rather than merely an exception.
- Animated banner in `docs/assets/`.

## 0.2.0.0 - 2026-08-06

Sprint 3. Regime split and the shared attention budget.

- F6: a recall figure averaged a rule that was perfect at one job with the same
  rule being blind to another. Sprint 2 reported 0.47 for the missile conjunction
  and called it mediocre; scored per regime it is 7 of 7 on missile nights and 0
  of 8 on drone nights. Present since the rule was written. Found by a probe that
  broke the figure down by scenario before any code was changed.
- F7: two rules each cleared at the full alarm budget produce twice the budget.
  The budget belongs to the recipient, not to the rule, so `gate` now takes an
  allocated share and `DecisionPolicy` refuses to allocate more than it holds.
- F8: an unserved crossing kind excluded from the recall denominator without
  being reported makes a partial policy read as complete. Same defect class as
  unknown resolving to clear, in a different place. `PolicyRun` now counts and
  prints the coverage gap, and a test asserts it appears in the summary.
- F5: the per-regime output printed the rule's own verdict, computed against the
  default budget, beside the regime verdict computed against its allocated share.
  Two contradictory verdicts on one rule. Split into `metrics_line` and
  `summary`.
- Allocation by measured demand refuses rather than trimming. Silently shrinking
  a share to make the sum fit produces a policy that passes its own gate while
  overrunning the recipient, which is worse than refusing to build it.
- Finding, recorded rather than tuned away: the two-regime policy recovers recall
  1.00 but consumes 1.96 of a 2.00 weekly budget. At a 25% headroom requirement
  it needs 2.46 and does not fit. The missile-only policy is comfortable and
  leaves 8 drone crossings served by no regime.
- Not fixed in this sprint: R2 remains inert. The missile conjunction's numbers
  are still indistinguishable from R3's, so the westward-escalation conjunct
  still carries no information. T3 stays open.

## 0.1.0 - 2026-08-05

Sprints 0, 1 and 2. First tag.

### Sprint 0, repository and gate

- `make verify` is the only gate and CI calls it rather than restating its steps.
  A workflow that lists checks individually drifts the moment a check is added to
  the Makefile.
- An empty test suite fails the gate rather than passing it. pytest treats
  "nothing collected" as success and an unset coverage floor as satisfied, so a
  fresh repository goes green with no tests. Same failure class as
  unknown-resolves-safe: absence read as success.
- Data tiers and `.gitignore` written in the first commit, because retrofitting
  them means rewriting history.

### Sprint 1, adapter boundary and store

- `AlertState` is a tri-state and `UNKNOWN` never resolves to `CLEAR`. Written as
  `is_clear()` rather than `state != ACTIVE` at each call site, because the
  negation is the defect: a feed that goes silent has not reported an all-clear.
- Store writes are idempotent by content hash, which excludes `ts_ingest`.
  Without it, re-polling an unchanged transition every 30 seconds multiplies rows
  until the replay no longer reconstructs the past.
- `Provenance.weakest([])` returns SPECULATION, not MEASURED. An empty input
  resolving to the strongest label is the flattering-default failure.

### Sprint 2, base-rate gate

- `baserate.py` is a top-level module rather than a helper inside the decision
  layer, and `tests/lint_domain.py` fails if it moves.
- F1: the synthetic history classified campaign nights as drone-only, so the
  missile rule scored precision 1.000 by construction. Hardened so campaign
  nights carry missile classification a third of the time; measured precision
  moved to 0.054, a twenty-fold overstatement. Present since the generator was
  written, found by running the gate rather than reading the code.
- F2: `tests/lint_limitations.py` failed on its first run against `baserate.py`,
  whose docstring named the excluded variable while explaining the exclusion. The
  term now lives only in `docs/DECISIONS.md` (D-002), which is its single home.
- F3: a regression test written from the defect description rather than the
  mechanism passed against the reverted generator, because two other scenarios
  already satisfied it. A regression test that is not verified red documents
  nothing and implies coverage that does not exist. Rescoped and re-probed.
- F4: the hygiene guard fired on `ENGINEERING.md`, which quotes the developer-path
  pattern in the course of forbidding it. Third use-versus-mention collision in
  one sprint, so the exemption is a named `PATTERN_DEFINING_DOCS` constant rather
  than a second ad-hoc skip.
- Coverage floor set at 95, three points below the measured 98.3. A floor, not a
  target: a target invites tests written for the number.
- Finding, recorded rather than tuned away: all four candidate rules fail the
  gate on the adversarial history. R1 and R2 fail on alarm rate, R3 and the
  conjunction fail on recall. A single rule cannot serve both the missile and the
  drone regime, so the regime split is a requirement rather than a refinement.
