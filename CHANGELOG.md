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

## 0.32.1.0 - 2026-08-14

**Two items that were living in a handover file outside version control.**

- **T57: production runs older code than `main`, and nothing here said so.**
  The collector on `vm-mavo` was last installed before 0.28.1.0, so F98 is not
  deployed and its fetch timeout means 20 s per resolved address rather than
  10 s for the whole fetch - measured at 20.12 s in the journal on 2026-08-13.
  `docs/DEPLOYMENT.md` described F98 as a repair and nothing recorded that the
  repair was not on the host. Measurements are being read off that host and
  written into this repository, which is why this is tier 1 despite changing no
  code.
- **`docs/DEPLOYMENT.md` 1.4 gains a state, not just a shape.** A table of what
  is installed against what `main` holds, and the rule the handover paid an
  hour for: the version string is not evidence of an install, because a
  reissued archive under an already-built version number makes `pip` report
  success against a host running different code. Grep the installed module for
  a string the release added.
- **T58: S7 against T31, T33 and T34.** The tolerance in `todo_index.py` is
  visible, reasoned and self-removing, and it is not a decision. Either the
  `MVP.md` row is amended again or the three tasks are reassigned; whichever,
  it gets a `DECISIONS.md` entry. The third outcome, tolerating it
  indefinitely, is what the task exists to prevent.

## 0.32.0.0 - 2026-08-14

**Two instruments for the question the map keeps answering with "unknown", and
a correction to where that question was filed.**

- **`tools/unmapped_tags.py`, P1.** `tag_map.csv` holds 127 rows built from the
  design window, 48,540 messages over 99 nights. The corpus is 61,041 over 118
  days, so tags appearing only outside the window are absent from the map **by
  construction**. This reads `AreaTable.resolve_all`'s second element across
  the corpus and reports what those tags cost: how many distinct ones, how many
  messages, and how many of those messages carry a kind marker that the join
  therefore never sees.
- **`docs/METHODOLOGY.md` filed the artillery near-misses under T34, and T34 is
  a different population.** T34 is the 321 design-window messages carrying **no
  tag**. `Загроза артобстрілу` over `Покровська територіальна громада` carries
  a tag the map does not hold. No task covered that, so the work looked
  scheduled and was not. Corrected, and T56 opened.
- **`tools/api_kind_compare.py`, P4.** Compares the API's `alert_type` against
  the join's `kind` over the same oblasts. It refuses the framing that would
  make it valuable and wrong: the API, `alerts.in.ua` and the channel share one
  upstream, so this is two parsers over one text. Agreement is not
  corroboration; disagreement is the finding, because at least one reader is
  then wrong about a message that can be read.
- **The corpus reader moved into the package.** `read_snapshot_messages` was
  local to `kind_coverage`; a second tool needed it and `tools/` cannot become
  an importable package without failing `check_single_namespace`. Copying it
  would have made two readers that can disagree about what the corpus contains
  while both report confidently. Seven regressions pin it, five mutants
  verified red - one of which survived the first attempt because the fixture
  reached the wrong guard, which is this repository's recurring shape and is
  recorded as such.

## 0.31.0.0 - 2026-08-14

**A gate whose scope had stopped covering what it promised, and a count that
agreed only with a copy of itself.**

- **The egress lint scanned half the tree.** `docs/DEPLOYMENT.md` section 2
  states the egress inventory "completely" and says a lint fails the build if a
  second module acquires reach, "which is what makes the table above checkable
  rather than aspirational". `network_reach_is_one_file` scanned `mavo/` only,
  so `tools/` - which the `Makefile` calls "inside the net", and where half of
  STATUS.json's measured numbers are produced - was outside it. Nothing had
  slipped through; the scope was narrower than the claim. Widened, and verified
  red against a planted import on both sides.
- **`decisions_recorded` was not counted from the decision log.**
  `defects_logged` has been derived from METHODOLOGY and cross-checked against
  the README badge since 0.6.0.0. Its sibling was compared against a README row
  and nothing else, so two hand-typed numbers agreed with each other. Both said
  27 against a log holding 25 entries.
- **`D-025` is cited and does not exist.** `docs/WEBAPP.md` gives it as the
  reason publication went ahead without T6, the legal position, and says the
  reason "is in the decision entry". There is no such entry, and none for
  D-023 either. The new check names D-025 in `CITED_WITHOUT_AN_ENTRY` rather
  than deleting the citation, and fails if the entry appears or if the citation
  goes away, so the finding cannot rot in either direction. **Resolving it is
  the operator's, and it is the strongest claim in this repository resting on
  the weakest evidence.**
- **D-027's outstanding measurement is taken.** One uninterrupted hour after
  `AccuracySec=1s`: 107 intervals, all 31 to 36 s, mean 33.06 against a nominal
  30 plus 5 of jitter, against 33 to 60 s before. The drop-in's stated
  mechanism holds and the margin in that entry is a bound rather than an
  estimate.
- **D-028, the ADS-B sampler.** Sixty seconds, raw state vectors rather than
  derived landings, eight days of retention, and a row per poll attempt beside
  the observations so a dead sampler and a quiet sky are not the same empty
  set. Collection only; D-019 still governs publication and is unchanged.
- **`docs/FEED-SPEC.md` 1.5.** Two properties from the same week, both learned
  by building rather than by specifying: nine, that a consumer facing a feed
  with no heartbeat owes itself an attempt log, with the rule that a failed
  poll records null and an empty one records zero; and ten, that a metered feed
  must state its meter, because otherwise the consumer's own coverage is
  unknown to the consumer.

## 0.30.0.0 - 2026-08-13

**T40's instrument: how late the channel is, measurable at last.**

- **`tools/latency.py`.** Reads `ts_source` against `ts_ingest` across both
  streams in the store and reports the distribution T40's acceptance names:
  median, p90, p99, max, count, window, with the poll interval printed beside
  them.
- **It refuses a window under seven days.** The acceptance asks for a week, and
  a distribution over one afternoon is an anecdote with percentiles on it. This
  repository already owns one of those and the defect log says what it cost.
  `--allow-short` prints anyway, marked `NOT A T40 MEASUREMENT`.
- **It never calls the lag the channel's latency.** What is measured is the
  source's delay plus the web view's plus our own poll interval, and only the
  third is known. The upstream figure is reported as an upper bound and carries
  an `[inference]` label.
- **Negative lags are reported rather than clamped**, because a post received
  before its own timestamp is two clocks disagreeing, which is a finding about
  the instrument and not an outlier to be tidied away.
- **Percentiles are nearest-rank**, so every printed figure is an observation
  that happened rather than an interpolation between two that did.
- **A naive timestamp is dropped, not assumed to be UTC** (F61's class), and a
  store where every row is naive is a refusal rather than an empty report.
- `docs/CHANNEL.md` gains section 8a: the instrument, the three properties that
  decide what the number will mean, and the empty table waiting for the row.
  Until that row is filled, the argument that thirty seconds is a defensible
  poll interval rests on an unmeasured assumption about the term it is compared
  against, and the section says so.
- Eleven regressions. **The measurement is not in this release**: it needs a
  week of a live collector, which is a host and a calendar rather than an
  afternoon of typing.

## 0.29.0.0 - 2026-08-13

**A documentation pass, and the README learns to speak to two readers.**

- **The README opens for a reader who is not an engineer.** Five new sections
  before the thesis: what the system does in a minute, one alert followed from
  the channel to a line on a map, what it will not do, a glossary of the terms
  the rest of the document uses without introduction, and the questions people
  actually ask. Nothing below them changed and nothing in them softens a claim:
  the status line, the unmeasured western correctness rate and the defect log
  are stated in plain words as plainly as they are stated in technical ones. A
  reader who stops after the glossary has an accurate picture rather than a
  flattering one.
- **`docs/WEBAPP.md` catches up with the consumer, and says it fell behind
  twice.** It described `mavo-site` 4.1.0.0 while the site had shipped through
  4.12.0.0 and been publicly reachable since 2026-08-12. Its "what gates
  publication" section listed three blockers as open; two of them are not, and
  publication went ahead with the third open under D-025. The section now
  records what happened rather than what was planned.
- **`docs/DEPLOYMENT.md` records what actually runs.** Thirty seconds plus
  jitter under D-027, the timer measuring from activation with an `AccuracySec`
  default larger than the interval it paces, and the measured consequence that
  a failed fetch costs its own wall clock rather than one interval.
- **The check that does not exist is named in the file that needs it.** Nothing
  fails when `docs/WEBAPP.md` falls behind the consumer, and it has now done so
  twice. A weaker but honest check is proposed there; it is not built, and
  saying so in the document is the minimum a rule without a gate check earns.

## 0.28.2.0 - 2026-08-13

**Sprint status stops being three documents' opinion.** Review R-4 of the
0.23.1.0 archive found `STATUS.json` counting nine sprints shipped, `TODO.md`
declaring S8 partial and open, and `docs/MANUAL.md` speaking of sprint 6 in
the future tense.

- **`shipped_sprints` is now `sprint_test_files`.** F93 established six
  releases ago that the field means "a regression file exists" and not "the
  sprint met its exit criterion". The reconciliation stayed in the defect log
  while the misleading name stayed in the file a reader opens first.
- **`todo_index --check` fails when the plan and the backlog disagree.** The
  sprint TODO declares open cannot be one `docs/MVP.md` gives a closing
  window, and a sprint the plan closes cannot still carry open tasks.
- **One real disagreement is named rather than resolved by this release.**
  MVP.md closes S7 while T31, T33 and T34 still carry it. Whether the row is
  amended or the tasks are reassigned is a decision, and the frozen list that
  holds it carries the reason and is itself checked: an entry that stops being
  a disagreement fails the gate rather than aging into an exemption.
- **The sentence the check reads is load bearing**, so rephrasing it fails the
  gate instead of quietly disabling the check.

## 0.28.1.0 - 2026-08-13

**The ten-second timeout took twenty seconds, twice, on the production host.**

- **F98: `timeout_s` bounded each socket operation, not the fetch.** `urlopen`
  hands the value to the socket, where the connect, the TLS handshake and the
  read are each allowed the full amount, and `socket.create_connection` applies
  it again to every resolved address. The collector host is IPv6-only, so the
  address that cannot work is tried at full price first. The number now names a
  deadline for the whole fetch: `connect_within` spends one budget across the
  addresses, and the connection hands the read whatever the connect left.
- **The diagnostic that would have caught it had been correct for two
  releases.** T55 put the elapsed time in every refusal at 0.26.0.0. The
  evidence was in the journal; the question "does the bound hold" was not being
  asked of it.
- **D-027 carries a correction rather than a rewrite.** Its deciding
  arithmetic - two failures costing 90 seconds against a 600-second staleness
  threshold - assumed a failure costs one interval. It costs its own wall
  clock too, and that wall clock was double the constant. The decision survives
  with a smaller margin, and the entry now says that the margin is an estimate
  until the host reports a measured cadence.
- **What is still unbounded, stated rather than discovered later:**
  `getaddrinfo`. Bounding a resolver needs a thread inside the network seam,
  which is a larger change than this defect justifies.

## 0.28.0.0 - 2026-08-13

**A second view of the same alerts, built as a measuring instrument and unable
to become a source. And the poll interval drops to thirty seconds.**

- **`mavo/sources/ukrainealarm.py` reads `api.ukrainealarm.com`.** It has no
  `poll`, does not implement `ThreatSource`, and its reading has no
  `content_hash`: the only way it reaches `state.json` is if somebody writes
  that adapter deliberately, and the module docstring argues with them first.
  **The API and the channel share an upstream**, so two of them agreeing says
  the views agree and nothing about whether the origin is right. Any sentence
  reading "two sources confirm" would be false.
- **What it is for, and neither number exists today.** End-to-end latency from
  a state change at the source to a rendered report, which is T40 and one of
  two things between here and beta. And coverage: how many alerts the API
  reports that the parser did not, and the reverse, which no amount of
  hand-labelling produces because a labeller reads the same messages.
- **The region vocabulary had to be reconciled.** The API appends a word the
  channel's hashtags do not; joining without stripping it produced an empty
  slug for every region, which would have reported the parser missing
  everything - the most flattering possible error for the API and the most
  damning for the thing being measured.
- **Kyiv city gets no oblast, on purpose.** Inventing an administrative
  mapping here is what F90 and T44 exist to prevent.
- **A record the adapter cannot read is kept and marked**, never skipped: a
  coverage measurement whose denominator quietly shrinks flatters whichever
  side it was built to test. A missing timestamp is `None` and never `now`,
  for the same reason.
- **The architecture check earned its place.** The first version opened its
  own urllib connection and `test_the_network_seam_is_one_file` failed in the
  same run. `Transport.fetch` gained an optional `headers` argument instead,
  so the API key goes through the one seam and travels in a header rather than
  in a URL, where it would reach every proxy log on the way.
- **D-027: the poll interval goes to thirty seconds.** The floor on
  channel-to-render latency halves from about sixty seconds to fifteen, and
  more importantly a run of two failures now costs 90 seconds of blindness
  instead of 390 against a 600-second staleness threshold. Ten requests in
  fifty seconds all returned 200 when measured, which is evidence about a
  burst rather than a sustained rate, and the entry says so. **The unreachable
  rate is the number that would reopen it**, and T55 made that readable a
  release ago.

## 0.27.1.0 - 2026-08-13

**D-026: beta stops depending on anyone asking for it, and the status
paragraph stops describing the operator's private correspondence.**

- **The beta definition loses its middle clause.** It read "delivering to
  people who asked", written when the only imagined delivery was a push to two
  named phones. The site has been publicly reachable since 2026-08-12; who
  visits it is not a property of the instrument and does not shrink by writing
  code. Beta is now the reporting instrument, live, with its correctness and
  latency measured and published.
- **T11 still gates push delivery**, and `docs/MVP.md` section 3 keeps it
  there. Waking somebody's phone at three in the morning requires that they
  asked; a page they chose to open does not. The two were one clause because
  the project once had one delivery path.
- **The README status paragraph no longer mentions who has or has not been
  contacted.** That was the operator's correspondence, not a property of the
  code, and a public repository is the wrong place for it.
- What still blocks beta is unchanged and is stated in the same paragraph:
  correctness measured on western areas (T36) and end-to-end latency as a
  distribution (T40).

## 0.27.0.0 - 2026-08-13

**T46, partial: a message shape the parser had been failing on every poll for a
day.**

- **`КАБ напрямок Краматорськ` was unparsed roughly seven hundred times.** Two
  in every twenty-message window, on the production host, from 2026-08-11
  until somebody read the journal. It carries a kind marker, no declaration
  word and no alert state, so it failed the declare test and was counted
  rather than resolved - honest and lossy at once, which is what the unparsed
  counter exists to make visible.
- **`напрямок` joins the declare markers**, which is narrower than what T46
  proposed. That entry offers treating a munition's name as a declaration in
  its own right and warns it would classify summaries and after-action
  reports; a direction is a word about something in flight now.
- **The inversion ordering was re-checked rather than assumed**, as T46
  demands: lifts are evaluated first, verified by reading and by a regression
  that puts the new marker inside a lift message.
- **The fixture is verbatim from the production journal**, line break
  mid-word included. A fixture written from the parser's expectations is the
  failure class this repository has logged five times, and this message is the
  reason the marker exists.
- **Status of the marker: [assumption, unmeasured].** One day of live evidence
  says the shape exists and recurs; it says nothing about prevalence across
  118 nights or about false positives. T45's acceptance applies.
- Four mutations verified red: the marker removed, the declare test moved
  ahead of the lift test, the one-kind requirement dropped, and the alert-state
  check moved after the declare test.

## 0.26.0.0 - 2026-08-13

**T55: the refusal now answers the question it is asked.**

- **`[UNREACHABLE]` carries the elapsed seconds and the exception class.** A
  stall that hit the ten-second ceiling and a rejection that bounced in twenty
  milliseconds were the same line in a journal, so the field measurement in
  T39 could close two hypotheses and not choose between what was left. Eleven
  refusals were logged over one night before anybody noticed the line answers
  no question, which is F44 in the diagnostics rather than in the schedule.
- **Monotonic clock, not wall clock.** An NTP step during a ten-second wait
  would otherwise report a negative duration or a wild one, and a diagnostic
  that produces nonsense under load is worse than one that produces nothing.
- **Measured in the command as well as in the transport.** A transport that
  refuses without timing itself would produce a line with no duration, and a
  diagnostic present for one implementation and absent for another teaches a
  reader to stop trusting it.
- Four mutations verified red, including a constant elapsed figure: the
  regression asserts on two different durations rather than on the presence of
  a number, so a build that printed the same value every time fails.
- **One test was rewritten before it shipped.** The first version asserted on
  a string in `cli.py` and would have passed against a build that printed the
  substring in a comment. It runs the command against a refusing transport
  instead.
- **What this does not do.** It does not explain the 11% unreachable rate. It
  makes one night of journal able to explain it, which is a different thing
  and is the measurement T39 still needs.

## 0.25.6.0 - 2026-08-12

**The status paragraph stops making two claims it could no longer support, and
the check that reads it is rebuilt around what it can actually verify.**

- **"Sprints 0 to 9 shipped" was false by the definition in its own sentence.**
  Shipped means the code landed with its regression file; the tree has thirteen
  such files and `STATUS.json` records nine. The field stays wrong on purpose,
  because raising it would assert that three more sprints met their exit
  criteria, which is a larger claim than a test file can carry. The README now
  states the count from the tree and says the field is behind deliberately.
- **"No command polls the channel in a loop yet" was literally true and carried
  a conclusion that had stopped being true.** A collector has run unattended
  against the live channel since 2026-08-11, so S9's seventy-two-hour clause is
  a clock that has started rather than an untouched criterion. The comparison
  "S9 is further from its criterion than S8" was a judgement stated as a fact
  and has not been recomputed since; it is gone rather than reversed.
- **Deployment is stated as its own axis.** The site is public, which meets one
  of beta's three clauses and the cheapest: the instrument is live. Nobody has
  asked for it (T11) and correctness is unmeasured where it counts, because no
  western area has ever been hand-checked and western areas are the only kind
  this product is for (T36). The maturity label stays at pre-alpha: moving it
  because something runs is the confusion between running and measured that
  this repository's defect log largely records.
- **`docs_audit` compares the README against the tree rather than against the
  field.** It also fails when the two disagree and the README does not say the
  field is behind on purpose, which keeps the deliberate wrongness from
  decaying into ordinary drift. Two mutations verified red.

## 0.25.5.0 - 2026-08-12

**The documentation catches up with a week that ended in production.
Documentation only; no code changed.**

- **`docs/FEED-SPEC.md` gains three properties, numbered separately because
  they are weaker claims: each rests on one deployment rather than on a
  corpus.** A cap needs a published flag *and* an independent bound on the
  consumer, because a limit that lives only on the publishing side holds until
  the two versions differ. A window needs its left edge published rather than
  derived, because a device that slept cannot otherwise tell a gap from a
  quiet stretch. A version number needs a stated overlap period, because v3
  was a strict superset of v2 and the consumer still refused it, correctly,
  and the two had to be deployed inside one window.
- **Section 4 gains the measurement that strengthens its own argument.**
  Eleven unreachable polls in ninety-five. The number that matters is not the
  failure rate but that the consumer could tell on every one of them, because
  the channel publishes continuously enough that absence is legible. A feed
  publishing only on transitions would have made all eleven look like a quiet
  sky, and no amount of consumer instrumentation could have recovered the
  difference from outside.
- **README gains the commands an unattended host actually runs** - `collect
  --store`, `report --json --feed --watch` - and a section on what the first
  unsupervised night measured, including the two explanations that were tested
  and closed and the one that stays open.
- **`docs/WEBAPP.md` records what the consumer taught the contract** and that
  the coordinated deployment happened, in five steps no gate on either side
  can check.
- The unfinished half of T50 is named in three documents rather than one: the
  deprecation policy is survivable with one consumer under the same
  authorship, and that is exactly the circumstance a public contract does not
  have.

## 0.25.4.0 - 2026-08-12

**Three tasks recorded from the consumer's wish list, one of them as a
refusal. Backlog only.**

- **T56: is there an alert feed for the Romanian border or the Baltics.**
  Unmeasured, worth an afternoon before it is worth an architecture, and
  measured against FEED-SPEC's five properties like T8a. A negative result
  closes it and goes into `docs/FEED-SPEC.md` beside the Polish finding.
- **T57: a week of the picture, openable.** Counts per day, west against the
  rest, kinds, and the collector's own uptime for the same window, because a
  bar chart of announcements will be read as attack intensity unless the
  instrument's blindness is shown beside it. The Jasionka density chart is its
  second half and waits on T42.
- **T58: road conditions near the border, refused as posed.** A live traffic
  overlay is either the reader's browser talking to Google, which the site's
  D-S16 refuses, or a server redrawing a product whose terms do not allow it.
  Recorded as a refusal with the reason, so it is not rediscovered as an
  oversight, and with the measurement that would reopen it.
- 53 tasks in the backlog. No code changed.

## 0.25.3.0 - 2026-08-12

**Two tier-1 tasks recorded before the deployment window opens. Backlog only.**

- **T54: the staleness machine has never been watched crossing.** Started once
  and abandoned after two minutes against a 600-second threshold; on 2026-08-12
  an IAP failure came six seconds short of demonstrating it by accident. At the
  unreachable rate T39 measured, the degraded state will be reached, and the
  first person to see it should not be a stranger who was sent the link.
- **T55: the refusal does not say how long it waited.** A stall at the timeout
  ceiling and a rejection that bounced in twenty milliseconds look identical in
  the journal. Eleven refusals were logged before anyone noticed the line
  answers no question, which is F44 in the diagnostics rather than in the
  schedule. Explicitly not in scope: a retry, a longer timeout or a different
  interval, each of which would mask the symptom before its cause is known.
- 52 tasks in the backlog, 9 at tier 1. No code changed.

## 0.25.2.0 - 2026-08-12

**T39 gets its first field measurement, and the entry is rewritten around it.
Backlog only; no code changed.**

- **The collector misses roughly one poll in eight.** 9 of 60 over 20:18-22:37
  UTC on 2026-08-11, 11 of 95 over the wider journal, Wilson 6.6-19.6%.
  Consecutive failures happen: the longest run is two and the longest gap
  between successful reads is 7.0 minutes against a 600-second staleness
  threshold. The margin is three minutes, not the eight an independence
  assumption predicted.
- **Two explanations closed.** Source-side rate limiting: ten requests in
  fifty seconds all returned 200 at a median 0.24 s, twenty-six times more
  aggressive than production. The IAP tunnel: the collector reaches the
  channel directly over IPv6 and knows nothing about IAP. The tunnel does drop
  and that is a separate finding about operator access.
- **One left open with a mechanism.** Packet loss on the IPv6 path fits: a
  successful poll takes 0.24-0.45 s against a 10 s timeout, so a failure is a
  stall of an order of magnitude, and a lost SYN retried at 1, 2, 4 and 8
  seconds lands past the ceiling. The 60-packet ping that showed 0% loss had
  45% power against a 1% rate and settles nothing.
- **One claim retracted before it could travel.** The apparent rise from 6.7%
  to 30.8% across the window is Fisher p = 0.145 on nine failures. It was
  written before the arithmetic and is recorded as retracted rather than
  removed.
- **Next step is a diagnostic, not a fix.** `[UNREACHABLE]` does not say how
  long it waited, so a stall at the timeout ceiling and a refusal that bounced
  immediately look identical in the journal: a probe whose outcomes do not
  separate its hypotheses. Changing the interval, adding a retry or raising
  the timeout would each mask the symptom before its cause is known.
- **T39 raised to tier 1.** It stopped being a politeness question about a
  future daemon and became the instrument's own measured blindness, in
  production, on the artefact about to be publicly reachable.

## 0.25.1.0 - 2026-08-12

**The regression the last release shipped without, and two documents that had
fallen behind the things they describe.**

- **The publishing loop was never exercised with a feed.** `--feed` reached
  the CLI and `feed_path` reached `publish`'s signature; the one-shot path had
  a test and the continuous path, which is what production runs, did not. Both
  files are now checked on the second cycle, because a first-cycle-only write
  is indistinguishable from a heartbeat that works, and a negative control
  checks that a loop without `--feed` writes no file nobody asked for.
  Mutation observed red: the `write_feed` call dropped from the loop.
- **`docs/WEBAPP.md` said the consumer was at 1.2.0.0 while it was at
  4.1.0.0.** Four releases, and nothing in this repository's gate could have
  noticed, because the consumer lives in another repository. Recorded rather
  than quietly corrected; the document now describes what the consumer does
  with v3 and why the two deploy together.
- **`docs/DEPLOYMENT.md` said NOT BUILT while a collector had been running
  unattended for a day.** It gains a section describing what is actually
  deployed, including the three steps the schema-v3 window requires and which
  none of them a gate can check: `--feed` in the report unit, both files
  across the push channel, and the forced command pointing at the
  version-controlled `accept-state` rather than the copy on the host.
- **T50 gains a measured fact.** The consumer refuses v2, verified by running
  it, so the deployment window is a property of two programs that exist rather
  than a precaution against something that might happen. The task stays
  partial: the deprecation policy and the size measurement under a mass alert
  are still missing.

## 0.25.0.0 - 2026-08-12

**T50, partial: the contract carries history. Schema v3, and the site cannot
read it yet.**

- **`state.json` v3 adds `events`, a twenty-minute window of every transition,
  and `counts_24h`.** v2 carried the current picture and seven-day counts and
  no history, so a consumer could not build a panel of what happened tonight
  however the page was written. The contract belongs to the producer (D-020),
  so the absence was ours.
- **`feed.json` is a second file over twenty-four hours, from the same
  composition.** Two files rather than one longer window because the costs
  differ: `state.json` is re-read every cycle by every open tab, `feed.json` is
  fetched when a reader opens the history. Roughly 800 events a day is about
  18 KiB gzipped, against 0.3 KiB per cycle for the short window.
- **The stream carries all of Ukraine and both roles.** Filtering to the west
  was drafted and rejected: a quiet twenty minutes in the west while the east
  is burning is a different fact from a quiet night. Filtering to `subject`
  would drop the areas a message names as still under alert, which is the loss
  this repository made once already before T37.
- **The cap is 5,000, not the 200 first proposed.** That 200 rested on a
  figure describing western areas while the stream carries all of them: two
  denominators for one number, the shape of T49. Measured, production ingested
  27 events in 97 minutes on 2026-08-11, about 400 a day. A cap binding every
  day makes `truncated` permanently true and therefore useless.
- **`window_start` is published rather than derived.** A consumer compares it
  against its own last successful read and refuses to render continuity across
  a hole. Twenty minutes is short enough that a phone asleep in a pocket
  crosses it, which is the cost of the operator's choice of window and the
  reason the field exists.
- **The window block is always present, empty or not.** An absent block and an
  empty one read alike to a careless consumer, and at eleven events per twenty
  minutes the empty case is the common case at four in the morning.
- `tools/contract_check.py` reads the stream, the items, the roles, the counts
  and the second file, and its fixture carries a continuation event so the
  role check can fail. Four mutations verified red: filtering to subjects,
  truncating the newest instead of the oldest, widening the window to an hour,
  and dropping `window_start`.
- **Not shipped, and named in T50 rather than rounded off:** the deprecation
  policy for v2, and a size measurement under a mass alert rather than a quiet
  night.
- **This release must not reach production alone.** `mavo-site` 3.0.0.0
  refuses a version it does not know, by design. The producer and the site go
  out in one window.

## 0.24.2.0 - 2026-08-12

**F97: replay dropped a row when a sort-key tie straddled a chunk boundary.**

- **The chunked reader assumed a uniqueness the schema does not provide.**
  Paging resumed on `(ts_source, area_id)` with a strict comparison while the
  only unique key is `content_hash`. Measured: a tied pair placed at rows 500
  and 501 with `CHUNK = 500` gives 501 appended and 500 replayed; the same
  pair away from the boundary gives 402 and 402.
- **The tie is what T37 describes.** One message clears an area and lists the
  same area as still under alert. The row the boundary dropped was the second
  one, which is the one that says the area is still dangerous.
- **The test that named this failure was green.** Its factory built keys that
  never tie, so the data could not tell a tie-safe keyset from a strict one.
  Fifth instance of test data chosen by the implementation.
- **`replay_kinds` was affected identically**, where a tie is two threat kinds
  declared for one area in one second.
- Repair: `(ts_source, area_id, content_hash)`, the hash appended as the final
  SELECT column so reader column indices are untouched. Mutation observed red.

## 0.24.1.0 - 2026-08-11

**Backlog only. Four tasks for the consumer tier, one of which is a producer
change and is the reason the other three cannot start with it.**

- **T50, tier 1: an event stream in the contract, schema v3.** `state.json` v2
  carries the current picture and seven-day counts and no history, so the site
  cannot build a feed of transitions from it however it is written - the
  contract belongs to the producer (D-020). The task is mostly a decision: how
  long a window, given that every reader pays for every event on every two-minute
  poll, and that a file which grows without bound during a mass alert grows
  exactly when the reader is on one bar of signal. Recorded with it: MAVO sees
  about a dozen transitions a day, so a feed panel will read as empty most of
  the night, and a panel that looks broken when it means "nothing is happening"
  repeats this project's oldest failure in a new place.
- **T51, tier 2: geographic layers fetched only when asked for.** Voivodeship
  borders, border-region cities, possibly routes. The budget is already
  measured - 117.4 KiB first visit, and `nginx.conf` records that geometry is
  the difference between eight seconds and twenty-two at 120 kbit/s - so detail
  ships lazily and a reader who never asks pays nothing. **It explicitly does
  not introduce map tiles**: a third party's tiles would send every reader's
  viewport and address to that party, which is what D-016 refused, and
  self-hosted vector tiles would cost the zero-dependency hashed-CSP posture.
  Either way that is a decision entry, not a commit.
- **T52, tier 2: Polish, English and Ukrainian.** Ukrainian is in on
  demographic grounds rather than symmetry: roughly two million Ukrainians live
  in Poland, which makes them the largest single audience this project can
  have, and for them the page is a view of the country their family is in
  rather than an instrument about a neighbour.
- **T53, tier 3: full-width map, fullscreen, theme switch.** Cheap and
  conflict-free; the acceptance is that the reduced-motion refusal and the
  staleness rendering survive, checked by the browser harness rather than by
  looking at it.
- 50 tasks in the backlog. No code changed.

## 0.24.0.0 - 2026-08-11

**F96: the live command polled the channel and dropped what it understood.
There was no path in this product from the channel into the store.**

- **`mavo collect` fetched, parsed, printed a count and discarded the events.**
  `probe()` returned a report and a duration; the events and the declaration
  stream went out of scope with the source. The full flag list of the only
  command that touches the network was `--stub` and `--save-raw`.
- **How it survived is not the usual answer.** Not a rule with no reader, not a
  test pinning the wrong call shape. Every store this project has rendered from
  was filled by hand on a laptop, by `fixture` or by an import that lived in a
  session rather than in the package. The gap was invisible for exactly as long
  as nobody ran the thing unattended - which is shadow mode, which is S9, which
  has never run.
- **Found within an hour of the first real deployment**, by the report writer
  restarting in a loop against a store that did not exist, on a machine whose
  whole purpose was to answer whether that loop can run for 72 hours. The gate
  was green at 310 tests throughout and could not have caught it: the defect is
  a missing edge between two components that are each complete and each tested.
- **`poll_once` returns the source, its events and the elapsed time**; `probe`
  keeps the counting-only reading and delegates rather than reimplementing.
- **`mavo collect --store` appends both streams**, alerts and declarations,
  because they are separate events with separate lifetimes (T16) and storing
  one would produce a store whose kind coverage silently read zero.
- **A store that cannot be written exits 7**, not 0, for the same reason
  `--save-raw` has its own code: a wrapper reading stdout must not mistake a
  lost write for an empty sky. That failure - the store path being a directory -
  is exactly what stopped the first deployment.
- **Idempotence was already there and is now load-bearing.** The store
  deduplicates on content hash, so a poll every two minutes over a twenty-message
  window appends only what is new; the regression asserts the count does not
  grow on a repeated poll, because a log that grew every cycle would record the
  polling rather than the channel.
- **Still one-shot.** Running it on a timer is a deployment decision, and
  `skipped` stays `unknown` on every poll because a fresh source has no baseline
  for post ids. A resident source is what turns that into a measurement.
- 313 tests, coverage 96.48% (Python 3.12.3, sandbox). Mutation observed red:
  storing only the alert stream.

## 0.23.1.0 - 2026-08-11

**F95: a task outlived its reason and kept the reason. T8 is replaced by a
measurement and a decision.**

- **T8 justified itself with "sprint 6 assumes a Polish feed exists to switch
  to".** Sprint 6 closed long ago and `shipped_sprints` reaches 9; the
  acceptance clause still asked what a result "does to sprint 6", a question
  with no addressee. The task was still worth doing and every word explaining
  why was stale.
- **`blocked-external (access)` was false, and the label did the damage.**
  Nothing in T8 needs anyone's permission - RCB posts publicly, and scraping a
  public web preview is the technique that produced this project's entire
  Ukrainian corpus. A wrong status is worse than a wrong priority: priority
  invites argument, status ends it. Six sprints of waiting for nobody.
- **Two unlabelled assertions.** "RSO and NOTAM are machine readable" carried
  no provenance in a repository where every load-bearing claim carries one, and
  neither was reconciled with `docs/FEED-SPEC.md` when that document appeared.
- **The acceptance was unfalsifiable in the positive direction.** "One working
  read" does not say a read of what, resolved to what geography, at what
  latency. FEED-SPEC section 3 defines five properties; T8 measured against
  none of them.
- **T8a**, the measurement: a verdict per Polish source against all five
  properties, with a real read committed as a fixture, an area resolved to a
  TERYT code or an explicit statement that only prose exists, latency by T40's
  method over a week as a distribution, and the absence of a heartbeat stated
  where there is none. **A negative result closes it and is worth as much as a
  positive one** - it is the empirical backing FEED-SPEC currently argues
  without. Tier 2, own action.
- **T8b**, the decision: whether Poland enters scope. Separated because one
  entry was carrying a measurement and a product decision, and the measurement
  was hostage to the decision nobody was making. Gated on T8b's own blockers -
  T8a and T6 - both of which are the project's own rather than external.
- References repointed in `ARCHITECTURE.md`, `DECISIONS.md`, `FEED-SPEC.md` and
  `MVP.md`. The MVP row reading "unresolved access" had inherited T8's false
  label and is corrected in place, with the correction stated rather than the
  words quietly swapped.

## 0.23.0.0 - 2026-08-11

**S9's observability layer, against acceptance written before the code. Five of
seven criteria met, and the two that are not are named rather than the sprint
being rounded up.**

- **`mavo/obs.py` is the sink and the only writer.** One module owns the stage
  vocabulary, the line schema and the file handle, which makes `SCHEMA = 1` a
  single point of change rather than a convention. Lines are one `os.write` on
  an `O_APPEND` descriptor, so a process killed mid-run leaves the last line
  whole or absent, never truncated (F51). Asserted against an actually killed
  child process, not described.
- **Unknown is a value.** `Unknown("first_poll_has_no_baseline")` serialises to
  `null` beside a `*_reason`, and a bare `None` with no reason is dropped from
  the line rather than written - so a consumer can never meet a null and guess
  what it meant. The reader prints `unknown`; a rendering containing
  `skipped=0` fails a test.
- **T24: the sink carries no message text.** Six body-shaped field names are
  redacted by default and the redaction is visible in the line rather than
  silent. A hostile fixture with a canary in every body produces the canary
  nowhere. `MAVO_LOG_BODIES=1` works and writes its own `sink.bodies_enabled`
  line, because a switch that disables an evidential guarantee should leave a
  mark in the record it weakened.
- **Rotation renames, never truncates, and the retention is stated in the
  sink's own first line**, so a reader holding one rotated file learns the
  policy from that file rather than from documentation it may not have. A
  fragment with no `sink.opened` line renders `retention: unknown` instead of
  reading as a complete history.
- **`tools/progress.py` is the reader, and nothing in the pipeline may import
  it.** Enforced by a new `lint_domain` rule and, separately, by a test: a rule
  with one reader survives exactly as long as that reader. A progress indicator
  wired into the run would be a second statement about where the run is, and
  the first thing it would do is disagree with the log.
- **T27: the poll interval is drawn per cycle and recorded.** Default spread
  15%, the draw injectable, every waited interval kept on `PublishReport`. It
  goes in now because adding it later would invalidate every interval
  measurement taken before it, and those measurements are the evidence that
  would justify tightening the poll.
- **Not met, and stated in `docs/OBSERVABILITY.md` beside the criteria:** the
  degradation-notification criterion needs a notifier (S10), and the
  live-view-agreement criterion needs a live view, which waits on `mavo watch`,
  which waits on T25 - a decision rather than an implementation.
- 310 tests, coverage 96.41% (Python 3.12.3, sandbox).

## 0.22.1.0 - 2026-08-11

**F94: a streaming reader held its database connection across every yield, and
the first account of it was wrong.**

- **Found from a terminal, not the suite.** `make verify` on Python 3.14
  printed `ResourceWarning: unclosed database`. `replay` and `replay_kinds`
  yielded from inside `with closing(self._connect())`, so the handle lived as
  long as the generator, and an abandoned iterator kept it.
- **Measured before being repaired, because the first account was a guess.**
  Consumed to exhaustion, 200 times: **0 descriptors held**. Started and
  retained, 100 iterators: **201 held**, of which **102 survived `del` and an
  explicit `gc.collect()`**. So the production path never leaked - `publish`
  and `compose` both consume to exhaustion - and the claim that a 72-hour
  `--watch` would accumulate handles is **retracted**. It was read off the
  shape of the code.
- **Garbage collection is not the backstop.** Half the handles survived a
  forced collection. The mechanism is not asserted; the unreliability is.
- **Repair: chunks of 500 with a connection per chunk**, keyset paged on
  `(ts_source, area_id)` rather than `LIMIT`/`OFFSET`, so a write landing
  between chunks cannot skip or repeat a row. Abandoning a replay now costs one
  chunk of tuples and no handle. Latent when found, in the F62 and F88 family:
  nothing in the tree abandons a replay.
- **Given up, and stated rather than left to be discovered:** a replay is now
  several statements, so a row appended mid-replay can land in a later chunk.
  The single-connection version took no transaction either, so it is not a
  weaker guarantee - only one neither version ever made explicit.
- **The `sys.path` trap, third occurrence in one session.** Two attempts to
  measure the repair reported it ineffective; both ran the probe from outside
  the tree, so the installed package answered. Same failure as the F91
  verification. A probe that does not print `module.__file__` is not a
  measurement of the tree in front of you.
- 291 tests, coverage 96.40% (Python 3.12.3, sandbox). Two mutations observed
  red: the inclusive keyset comparison, and the restored long-lived connection.

## 0.22.0.0 - 2026-08-11

**F90: the live path never reached the table that fixed F23, and the assertion
built to announce that fix was wired to the same wrong path.**

- **Sprint 7 closed F23 in the code and not in the product.** `probe()` is the
  whole live path - `mavo collect` runs it - and it constructed its source
  without an area table. The `None` default selected the sprint 6 oblast-stem
  dict, so the 127-row register map shipped in sprint 7 was opt-in and the
  superseded table was what every live poll ran, for two sprints.
- **The tripwire certified the defect's absence.** Two assertions pinned `0 of
  20` with the message "update this pin and close F23", written so the fix
  could not be made quietly. Both called `classify(message)` with no table.
  They were designed to go red when the gazetteer landed; it landed and they
  stayed green. The README, the limitations list and the licence disclaimer all
  cited that pin as the reason the number could not drift.
- **The true numbers, on the same twenty real messages held since sprint 4:**
  20 of 20 resolve their area to a unique register code, 15 of 20 classify as
  alerts, and the other 5 carry no alert-state marker because they are threat
  declarations belonging to the kind stream. 15 and 5 are disjoint, sum to 20,
  and were both already pinned in `STATUS.json` beside the 0.
- **Repair removes rather than guards.** `AREAS` is deleted, `None` means "load
  the shipped table", and the same missing default that silenced the kind
  stream in `classify_kind_message` is closed with it. A superseded
  implementation left reachable is not a fallback; it is the version that ships
  to whoever forgets an argument.
- **Seven tests went red on the repair, all for one reason.** `PAGE`, the A12
  attack page and the F50 pairing fixture were written as oblast prose with no
  hashtag - a shape this channel does not emit, since 99.34% of its messages
  carry a tag and oblast names appear in 515 of 69,676 occurrences. The
  fixtures had been written to match the implementation. **Third instance this
  session** after F85's cutoff fixture and F82's sample, which makes it the
  dominant failure mode in this repository rather than a recurring accident.
  All three fixtures are rewritten to the live shape.
- **F91, F92, F93: three claims this release's own review made and did not
  measure, two of them already pushed.** F91: the F85 entry, the 0.21.5.0
  changelog and its commit message all say `recent_7d` counts "can move only
  upward"; they can move down, measured 2 to 1 on the operator's machine
  against `d988094` in a worktree, and the regression that would have caught it
  could not exist because every F85 fixture used one area per oblast. F92: the
  F89 entry, whose subject is an inference recorded in the position of a
  measurement, labelled its own inference "measured 2026-08-11" - a run that
  was impossible, since `data/raw` is in no package. F93: `shipped_sprints`
  means a test file exists, not that a sprint met its exit criterion; the
  status paragraph was made to agree with it without that being read, said
  "three sprints from beta" where four remain, and a gate check was added
  enforcing the misleading sentence.
- **One defect entry withdrawn before release rather than shipped.** A draft of
  this release logged 321,498 as a post id standing in for a count of posts, on
  the reasoning that Telegram ids include deletions. The corpus contradicts it:
  61,041 ids span exactly 61,041 posts, no gap across 17% of the sequence. The
  entry is removed, the original sentence restored, and the real open question -
  whether the sequence starts at 1, which one `before=20` request settles - is
  stated with the assumption made visible.
- **The README status paragraph is rewritten and now has a reader.** It said
  "Sprints 0 to 6 shipped" while `STATUS.json` listed nine, "five sprints from
  beta" after S7 closed, and described the corpus as retrievable rather than
  collected. `docs_audit` gains
  `check_the_readme_status_agrees_with_the_shipped_sprints`, which also refuses
  a sprint list with a hole in it, because "0 to N" is only truthful over a
  contiguous list. Mutation observed red.
- **The disclaimer's claim is replaced with a stronger true one.** It said the
  classifier scored 0 of 20; it now says no hand-checked correctness rate
  exists for the western areas this product is built for, which is the actual
  reason not to deploy it for someone else's safety.
- 287 tests, coverage 96.34% (Python 3.12.3, sandbox). `classifier_hit_rate_on_
  real_messages` is removed from `STATUS.json` and replaced by the two figures
  that measure the shipped path.

## 0.21.6.0 - 2026-08-11

**The corpus figure is corrected on measurement, and F89: the discrepancy that
made F81 survive was not unnoticed, it was explained.**

- **61,041, measured.** `corpus_inventory` on the operator's machine: 3,062
  pages, 61,041 distinct posts, ids 260790 to 321830, **199 posts appearing in
  more than one snapshot across 20 files**, no contiguity gaps. Digest
  `sha256:10266cbf...`, **unchanged**. The digest not moving is the part that
  matters: this is the same corpus counted correctly, not a different corpus.
  Corrected in `STATUS.json`, the README, both briefs and the kind-coverage
  section of the methodology.
- **F89: the gap had a story, and the story was wrong.** This document said
  "61,240 messages ... 61,041 messages carried parseable text", presenting the
  difference as unparseable posts. `kind_coverage` keys by post id and had
  always counted distinct posts, and the number of posts without parseable
  text is zero. An unnoticed discrepancy gets found by the first person who
  lines the numbers up; a discrepancy with a plausible explanation beside it
  never gets lined up again. The claim carried no provenance label, which is
  the rule that would have caught it: it was an inference sitting in a
  measurement's position.
- **F88 closed as null on the real corpus.** No snapshot repeats a post id
  inside itself. Recorded as a measured null rather than dropped.
- **Also measured, and it changes a sampling assumption:** western messages are
  1,006 of 42,854 resolved design-window messages, **2.35%**. The figure quoted
  elsewhere, 3.5%, is a share of *tag occurrences*, not of messages, and the
  two are not interchangeable - western alerts routinely name seven raions in
  one message. Both denominators are legitimate; using one number for both is
  not. Logged as T49 rather than corrected blind, because which denominator
  each existing sentence meant has to be read, not assumed.

## 0.21.5.0 - 2026-08-11

**Six defects from the 0.21.4.0 code review, F83 through F88. Two are the
items the review named; four were found by reading the repairs for the case
beside the one they fixed.**

- **F83: the cause of blindness reached nobody.** `publish()` printed the
  store-read failure only when no `on_cycle` callback was installed, and the
  CLI installs one unconditionally, so in the one mode an operator runs the
  loop said `feed=blind` and discarded the reason. Printed unconditionally
  now, on stderr, so a redirected stdout still carries only announcements.
- **F84: a broken observer could stop the heartbeat.** An exception from
  `on_cycle` - a `BrokenPipeError` from an announce print is enough -
  propagated out of `publish()` as a stack trace with no `PublishReport`,
  F46's shape reintroduced through the observability hook, and stopped the
  contract file because a console listener went away. The callback is
  disabled after its first failure, the failure is counted and named in
  `PublishReport.callback_failures`, and publishing continues: the observer
  is not the product, the file is.
- **The loop's tests all fed it a constant**, so a loop that read the store
  once and republished the first picture forever would have passed every one
  of them - the handover's second pattern, in the newest code. A sequence
  regression now drives the loop through active, cleared and unreadable, and
  the hoist mutation was observed red on a scratch copy.
- **F85: the trailing counter lost the episode that outlived the window.**
  The seven-day fold filtered events before folding, so an episode opened
  before the cutoff vanished: the oblast under the longest single alert
  rendered as the quietest, and a close inside the window went unrecorded -
  against the module's own invariant, standing since F76, that the count does
  not understate. The fold now replays the whole log; episodes open at the
  window's edge count once, and only an episode both opened and affirmatively
  closed before the window is outside it. `recent_7d` counts can move only
  upward under this change. The old cutoff regression's fixture was exactly
  the case the counter was wrong about and is replaced by the correct guard.
- **F86: the alert path picked a threat kind by dict insertion order.** An
  alert naming missiles and drones classified as whichever `KIND_MARKERS` row
  was typed first, while `classify_kind_message` refuses the same ambiguity
  three functions up. The alert path now makes the same refusal: exactly one
  named kind resolves, two resolve to UNKNOWN, and one kind in two forms
  still resolves. Corpus frequency of two-kind alerts is unmeasured and
  folded into T45's second run.
- **F87: the fingerprint promised a comparison that did not exist.**
  `label_sample`'s docstring said `score` reports a mismatch; the hash was
  stored nowhere and compared against nothing - a rule with no reader, in the
  instrument built to be hard to fudge. `draw` now writes a draw record
  (seed, fingerprint over post ids, stratum counts) beside the CSV and
  `score` refuses a file whose rows do not match it. The `post_id` column
  carries the channel's real ids rather than a row number, and messages
  refused by `classify` are counted in the draw output instead of silently
  leaving the population. The sample a given seed draws is unchanged, so the
  planned seed 20260810 stands.
- **F88: a post repeated inside one file was counted twice, twice.** The F81
  repair closed the cross-file duplicate and left the within-file one:
  `messages` counted occurrences and `new_messages` counted every repetition
  in the first file as new. Latent - no live page has been observed doing
  this - and closed the way F62 was: deduplicated, and reported rather than
  absorbed.
- 286 tests, coverage 96.22% (Python 3.12.3, sandbox). Every fix verified red
  before repair; named mutations observed red on scratch copies.



## 0.21.4.0 - 2026-08-10

**F81: the corpus total counted 199 posts twice, and two tools had been
disagreeing about it in plain sight.**

- **Two backfill runs produced snapshots on different offsets over the same
  posts.** `page-000321631-000321650.html` beside
  `page-000321650-000321669.html`, ten such pairs from post 321631 to 321829.
  `corpus_inventory` summed per file, so every post in that range was counted
  in both.
- **The arithmetic closes exactly.** The inventory reports 61,240;
  `kind_coverage`, which reads posts rather than files, reported **61,041** on
  the same corpus. The difference is 199, which is the size of the overlap.
  Both numbers were in the repository and neither was questioned.
- **Why it survived.** The inventory checks that a filename agrees with its own
  content, and every one of these files passes: each is internally consistent
  and the problem exists only between files. Contiguity was checked;
  disjointness was not. A snapshot set was treated as a partition with nothing
  testing that it is one.
- **What limits the damage, and it is not a defence.** Every duplicated post is
  above 309380, so all of it is in the holdout. The design window is untouched
  and no measurement so far used a duplicated post. What is wrong is the
  advertised size of the corpus, which is a claim about how much evidence this
  project has.
- **The count is now over distinct post ids**, duplicates are reported rather
  than silently deduplicated, and a `new_messages` column shows which snapshot
  first contributed each post. Verified on a synthetic corpus with a
  constructed overlap.
- **Still owed on the operator's machine:** re-run the inventory and correct
  `STATUS.json`, the README, both briefs and `docs/CHANNEL.md`. Until that
  happens the figure in this repository is 199 too high **and is known to be**,
  which is the state this defect log exists to make visible.

## 0.21.3.0 - 2026-08-10

**The instrument for T36 could not have met T36's acceptance, and nobody would
have noticed from its output.**

- **`label_sample draw` sampled proportionally.** The west is 3.5% of tag
  occurrences, so a fifty-row draw held one or two western messages on
  average, while the acceptance asks for a figure about the areas near the
  border. The sample would have been the right size, with a recorded seed and
  a fingerprint, and about a question nobody asked.
- **Three strata now**: `western`, `front_line`, `unknown_tag`, with half the
  resolved rows western by construction. When the corpus holds fewer western
  messages than requested it says so, rather than returning a short stratum
  quietly.
- **`score` prints no combined rate, deliberately.** Pooling an oversampled
  stratum with a proportional one averages over weights the sampler chose,
  which is neither the rate for the product nor the rate for the channel. The
  western whole-row figure is the one S8 is judged on and it is labelled as
  such.
- **Files drawn before this are refused rather than scored.** Their `resolved`
  stratum is a mixture nobody chose, and scoring it would report a number about
  that mixture.
- **Verified end to end on a synthetic corpus** before hand-off: draw, fill,
  score. The first real run should be a measurement, not a debugging session.

## 0.21.2.0 - 2026-08-10

**F80: a fabricated detail and an overstated adjective, in the document written
to be believed. Both were in prose, which is the one surface here with no
reader in the gate.**

- **A specific incident, unsourced, and carrying a number wrong by a factor of
  two.** The brief opened its origin section with a date, a voivodeship and a
  duration, unlabelled, in a document that promises every figure carries a
  label. Deleted first; then checked. The incident is real and well reported: a
  Kh-101 entered Polish airspace on the night of 29 to 30 July 2026, was
  detected at 03:40, was lost from radar at 03:46 and came down near
  Tarnawa-Kolonia in Lubelskie. **The duration was six minutes, not thirteen**,
  and thirteen was also in **D-015** and in the T39/T40 latency thread, carried
  unsourced since each was written. Both corrected.
- **That is worse than the fabrication it was first taken for.** An unsourceable
  detail is visible the moment somebody asks. A true event with a number wrong
  by a factor of two travels, gets cited by the decision it supports, and reads
  as verified because everything around it is. Deleting the brief's copy would
  have left the two load-bearing ones untouched.
- **The correction strengthens what it corrects.** Six minutes is less room
  than thirteen, and the same reporting supplies the mechanism D-015 could only
  assert: Ukrainian fighters pursued the missiles to the border and their radar
  return was hard to separate from the missiles, which delayed identification
  on the Polish side. The paragraph is restored to both briefs with sources and
  labels.
- **"Checked three independent ways."** The methodology says "checked three
  ways, and the three answer different questions": one independent source, one
  re-check of the same outline simplified differently, and one measurement of
  the source's own error whose own row says it rules out nothing. Restated as
  the methodology states it.
- **Both briefs said 34 open items while the backlog held 35.** The count was
  removed entirely rather than pinned: a figure that changes weekly does not
  belong in a document nobody re-reads weekly.
- **`docs/reviews/0.21.0.0.md` is corrected in place.** It had verified eleven
  figures, found them sound, and concluded that no figure in the brief was
  unsupported. True and irrelevant: the two defects were a fabricated fact and
  an adjective, and neither is a figure. A review that enumerates the checkable
  and reports clean is a review of the checkable, and its summary must say so.
- **`tools/brief_check.py` in the gate**, comparing the figures the two briefs
  share and their pinned values. Deliberately narrow, and the narrowness was
  forced by its first run: Polish decimal commas and English decimal points are
  the same number in two unmatchable spellings, and comparing them produced
  three false positives inside a minute. It now reads whole numbers of four
  digits or more, which is the class that actually drifted.
- **What no check will catch, said rather than assumed.** A fabricated date and
  an overstated adjective are not reachable by any heuristic worth having.
  Both were caught by the operator asking where a claim came from. That is an
  argument for reading prose, not for building a weak check and feeling
  covered.

## 0.21.1.0 - 2026-08-10

**The one requirement where the answer may simply be no now has a task and a
stage table.**

- **T48: the Apple critical-alerts entitlement.** On iOS, waking somebody
  through Do Not Disturb needs an entitlement Apple grants per application, on
  application. `docs/MOBILE.md` opens with "the alarm path must wake a person
  through Do Not Disturb at 02:00", so this is the single item in the
  notification design that an external party can refuse outright.
- **Tracked with stages rather than a status word**, because the lead time is
  entirely outside this project's control and a pending application reads as
  progress for months. The table carries the trigger, the submission, the
  response and the fallback, and says in as many words that a pending
  application is not progress.
- **The progress table states requirements rather than the author's readiness.**
  A public repository saying which accounts and subscriptions its author does
  not hold is publishing a fact about a person, not about the project. What
  Apple's request needs is written as the requirement, and the table tracks
  only the steps that belong to the application itself.
- **Tier 2 and self-service, after the first version of this entry got it
  wrong.** It was filed as blocked-external and tier 3, reasoning that there is
  nothing to apply with because no app exists. Checked afterwards: Apple's
  request is a form needing a developer account, a Team ID, a bundle
  identifier and a description of the use case, and **the app does not have to
  be published or written**. The prerequisite is an account and an identifier,
  which is an hour, not a blocker.
- **The use-case description is the part this project is unusually well placed
  for.** The entitlement is granted on the strength of what the app is for, and
  a public repository with a test suite, a defect log and a written statement
  of what the tool refuses to claim is a stronger case than the unbuilt idea
  most applications describe. The material already exists in `docs/BRIEF.md`.
- **A drift caught in the same release that introduced it.** The first version
  of T48 gave the "call bridge" a row in its progress table and a
  recommendation to exercise it early. That phrase exists in
  `docs/MOBILE.md` as **one clause in parentheses**, with no decision, no
  architecture and no costing behind it; promoting a passing remark to a
  component with a plan is the drift this repository exists to catch, and it
  was caught by the operator rather than by any check.
- **Examined properly, the idea conflicts with three things already written.**
  Phone numbers are personal data, in a project that refused Google map tiles
  so a reader's viewport never reaches a third party (D-016) and keeps client
  addresses out of the access log. A carrier is an external dependency with a
  contract and a bill, under a stdlib-only rule. And telephoning people at
  night is a larger change of class than a push notification, in a system that
  has just decided that moving from reporting to warning needs T6 and T11
  answered first.
- **Nothing about it is decided and T48 no longer pretends otherwise.** What
  happens on a refusal is out of scope until there is a refusal, and the
  options are recorded in `docs/MOBILE.md` for whoever has to choose.

## 0.21.0.0 - 2026-08-10

**The brief was written for somebody who does not write code and read like a
specification with the jargon removed.**

- **Rebuilt from nothing**, 402 lines to 209, thirteen sections to nine. The
  table of contents and the glossary are gone: a reader who needs a glossary is
  reading a document that failed earlier than the glossary.
- **Numbers explained rather than named.** "Base rate", "recall" and
  "confidence interval" no longer appear as terms to learn. What appears is
  "it will fire more than 200 times a year and be right 3 times", and a coin
  that might be loaded but not on twelve tosses.
- **The argument is corrected, and the corrected one is stronger.** The old
  text said a calendar rule tells the reader nothing, which is not quite true
  and is checkable: such a rule does beat chance slightly. The defensible claim
  is that with three events a year the improvement cannot be demonstrated, and
  it has no counter of the form "but it does beat the calendar".
- **The status section described a tree from fifteen releases ago.** It said
  the component that reads a message does not work, citing 0 of 20. That was
  repaired in 0.12.0.0 when the reader moved to the channel's own hashtags. The
  0 of 20 stays as history, because it is the best evidence in the repository
  that reasoning loses to real data, and the current weak point is named
  instead: threat kind resolves in about 20% of alerts.
- **`docs/BRIEF-PL.md`, and it is the original.** The readers this document is
  written for are Polish: a journalist, an analyst, somebody near the border
  deciding whether to pay attention. The English version follows it. Everything
  else in this repository stays in English.

## 0.20.2.0 - 2026-08-10

**Two figures in the README were read as one thing and are three.**

- **57% of days and 3.5% of tag occurrences sat in adjacent paragraphs without
  their units.** One counts days, the other counts times the channel names a
  place; one is somebody else's `[reported]` figure over a period this
  repository did not observe, the other is measured on the corpus. Together
  they read as a contradiction, and read carelessly the second becomes "3.5% of
  the time something is near the border", which it is not.
- **The 57% is not this project's definition of the west, and that is now
  stated.** The source's "western Ukraine" may include Kyiv oblast or
  everything past the Dnipro; this project means the 36 raions of eight oblasts
  as the register lists them. The two have never been compared, so the figure
  is context rather than evidence.
- **A table of the three quantities**, because they are easy to swap: share of
  traffic (measured, 3.5%), share of nights under alert (not measured here),
  and how often anything approaches the border (a dozen events in four years,
  reported, and invisible to this feed at any point).
- **`docs/CHANNEL.md` section 10 accounts for the tags themselves**: 127
  distinct, 118 raions, 7 hromadas, 2 oblasts, every one carrying its unit
  suffix, **zero spelling variants across 69,676 occurrences**, every name in
  the nominative where prose would decline it. That shape reads as a register
  field being formatted rather than a sentence being written, so the tags are
  almost certainly machine-generated, recorded as `[inference]` because nobody
  here has seen the channel's internals.
- **Four things about the tags nobody has checked**, listed rather than
  glossed: who attaches them, whether the tag is the alert's own identity or an
  annotation that could disagree with it, whether one has ever named the wrong
  area, and whether 127 is stable outside the design window. A silent mislabel
  would be invisible to every check here, because the tag is what this
  repository trusts.
- **One tag, two symptoms, connected only once both were written down.**
  `Покровська_територіальна_громада` is the single ambiguous tag, because the
  register holds four Pokrovska hromadas in four oblasts. It is also the tag
  behind the artillery near misses in the threat-kind measurement: those
  messages carry a declare marker and a kind and fail on the area.

## 0.20.1.0 - 2026-08-10

**`docs/reviews/` said one per release and held nine for fifty. The reviews had
been happening; they had been landing somewhere else.**

- **F79.** Reviews were carried out on 0.13.0.0, 0.15.0.0, 0.16.0.0 and
  0.20.0.0 and every one became a session artifact outside the tree. Four
  documents kept describing a record that had stopped being kept, including the
  README a reviewer reads before deciding whether to believe anything else.
  Nine of fifty is not a bookkeeping lapse; it is the difference between
  "reviewed before every push" and "reviewed sometimes, filed rarely".
- **D-021: one review per major release**, meaning a change to the second
  version component. One per release, at five releases in an afternoon, is a
  rule nobody can follow, and a rule nobody can follow is not a stricter
  version of this one.
- **The rule has a reader now.** `check_major_releases_carry_a_review` fails
  the gate on a major release with no file. The twelve that shipped without one
  are a **frozen list** rather than a cutoff date, because a cutoff silently
  absorbs the next skipped review, which is how the first nineteen
  accumulated.
- **Three reviews filed late, unedited**, each carrying a note saying when it
  was written. Editing a review after the fact to read better is the same
  failure as writing one after the fact.
- **Twelve major releases have no review and never will**, and they are named
  in `docs/reviews/README.md`. Producing one now from the changelog would
  assert that a tree was examined when it was not. A fabricated review is worse
  than an absent one, because the absent one is visible.
- **0.19.0.0 is listed among them for a different reason**, stated rather than
  folded in: it opens a run of five releases worked in one sitting, and
  `0.20.0.0.md` reviews that whole run. Splitting one reading into two files to
  satisfy a counter is the compliance this repository is meant to be able to
  spot.

## 0.20.0.0 - 2026-08-10

**Sprint S8, worked to the end of what this side can do, and still partial.
The remaining gap is named rather than rounded off.**

- **The distance column is verified three ways, and they answer different
  questions.** An independent geometry and method (OSM outlines, WGS84
  geodesic) puts three of four spot-check points within 1.1 km. An independent
  simplification of the same Natural Earth outline, the one the companion site
  carries at 1,039 vertices against this repository's 1,332, diverges by at
  most **0.04 km**. The source's own positional error, 183 shared border
  vertices against OSM, is median 0.0 and maximum 2.6 km. So the arithmetic is
  right, the sphere costs +0.31% at worst, the simplification costs two orders
  of magnitude less than the source, and the remaining uncertainty is the
  source's. That half of S8's exit criterion is met.
- **What those checks do not establish**, stated because it is the part the
  product cares about: every one of them measures distance from a *point*, and
  the column publishes an interval for an area's nearest edge, derived from a
  disc of equal area rather than from the polygon. For border raions the
  interval reaches zero and is right by construction; for an oddly shaped raion
  it is an approximation nobody has measured.
- **`tools/label_sample.py` grew the three verdict columns S8 asks for**:
  `area_ok`, `kind_ok`, `distance_ok`, plus a **whole-row** rate beside the
  three, because a reader sees one line and not three fields. A row is wrong if
  any of the three is. A file drawn before this split is refused rather than
  scored against the wrong column.
- **A first hand-checked sample exists and does not close the sprint.** The
  twenty real messages in the tree, rendered as the report would render them,
  judged one at a time: 0 errors on all three dimensions, Wilson [0%, 16.1%].
  **All twenty are eastern.** They resolve to Kharkiv, Dnipropetrovsk,
  Zaporizhzhia and Sumy, which is the traffic this product filters out, and
  the intervals they tested are 700 to 1,000 km wide where an error of tens of
  kilometres is invisible. The intervals that matter reach zero at the border
  and none was tested. They also span twenty-six minutes of one afternoon, so
  they are not independent draws.
- **S8 therefore stays partial in `docs/MVP.md`**, with the gap written into
  the row rather than into a footnote. Zero errors in twenty bounds the true
  rate below 16%, which is compatible with a report wrong on one row in seven.
- **T47 has a patch on the producer's side and a document for the consumer.**
  MAVO classifies four kinds; the site labels three, so glide bombs at 2,104
  declarations and artillery at 934 arrive named and render as *typ nieznany*.
  The producer's gate now fails when a kind is missing from
  `docs/WEBAPP.md`, so a fifth kind cannot reach the consumer silently. The
  labels themselves belong on the consumer's side and the patch says so.

## 0.19.5.0 - 2026-08-10

**The backlog can now be read without reading all of it, and two threat kinds
turned out to arrive named and render as unnamed.**

- **`TODO.md` carries a generated index**: closed against open, split by
  state, by tier and by sprint. Generated by `tools/todo_index.py` and checked
  by the gate, so the summary cannot drift from the list under it, which is
  the F31 and F73 failure applied to a backlog.
- **Three tiers, declared per task rather than inferred.** Tier 1 blocks
  something already promised or is a measurement without which a shipped claim
  is unsupported; tier 2 is real work nothing waits on; tier 3 is worth
  dropping if the project turns. An open task with no tier fails the gate: a
  task nobody has ordered is a decision nobody has made.
- **Where the project actually is, stated at the top of the file.** Sprint S8,
  partial, closed by T36 and the by-hand distance check. The last five
  releases were an audit and its consequences and moved the sprint zero
  distance. Both facts belong in the same sentence, or the next reader infers
  the sprint advanced.
- **T47: MAVO classifies four kinds and the consumer labels three.** Measured
  over the corpus: glide bombs 2,104 declarations and artillery 934, against
  missile 242 and drone 2,756. Both render as "typ nieznany", so three
  thousand declarations arrive named and display as unnamed. "The source said
  nothing" and "the source said something this page has no word for" are
  different facts, and one label for both is the UNKNOWN against PARTIAL_CLEAR
  collapse one layer out.
- **Glide bombs stay a category of their own even though they do not reach
  Poland.** Largest class in the corpus, and they say which oblast is being
  worked over right now. Neither they nor artillery can reach an alarm rule,
  by construction: the regimes name missile and drone explicitly and the rules
  compare by identity.
- **The contract check fails when a threat kind is missing from
  `docs/WEBAPP.md`.** The producer cannot fix the consumer's labels and it can
  stop adding an enum member silently, which is the half it owns.
- **`ENGINEERING.md` 1.1**, with the three gate additions and what each cost,
  a rule that a producing gate encodes its consumer's needs without importing
  the consumer, and a section on test data: three times in two sprints a
  mutation survived a test that named it, every time because the data could
  not distinguish the two implementations. The question that catches it is
  what data would let the wrong implementation pass.

## 0.19.4.0 - 2026-08-10

**T45 ran, and the near-miss pile was worth more than the coverage figure.**

- **The repair is measured**: coverage 0.128 to **0.196**, `join_coverage`
  0.104 to **0.170**, MISSILE 25 to **242** declarations, unparsed down 56%,
  near misses down 46%. ARTILLERY, which had no member before, accounts for
  934. Recorded in `docs/METHODOLOGY.md` with both columns so the improvement
  can be checked rather than taken.
- **TTL is still not the binding constraint**, at 0.196 from one hour to
  twenty-four. Same finding as the first measurement, on a substantially
  different table.
- **The lift table listed one of the channel's four phrasings.** `Відбій
  атаки дронів-камікадзе`, `Відбій атак дронів` and `Відбій по КАБам` were
  being dropped. Widened to `відбій`.
- **An inversion was measured before it was introduced, not after.** The
  obvious next improvement, adding `атак` so `Атака ударних БПЛА` resolves,
  would have turned every lift of the first shape above into a fresh
  DECLARED: an alarm raised by the message announcing its end. Those lifts are
  refused today only because `атака дрон` does not match `атаки дронів`, an
  accident of declension rather than a control. The lift table is therefore
  widened **before** the declare table, never after, and the declare extension
  is deferred to T46 with its own run.
- **`небезпека` removed.** Zero hits at both measurements, on two tables that
  otherwise differ substantially. A marker that has never matched anything is
  a claim about the channel that the channel has refused 61,041 times. A test
  holds it out, so re-adding it is a decision rather than a line.
- **The artillery near misses are not a kind-table problem.** `Загроза
  артобстрілу` over `Покровська територіальна громада` carries a declare
  marker and a kind and fails on the tag, which is not in the 127-row map.
  That is T34 and it measures something else.

## 0.19.3.0 - 2026-08-10

**F71's repair: the kind tables now accept the four forms they were measured
refusing, and a fifth found while testing that.**

- **`загроза` replaces the two longer declare markers.** The channel announces
  ballistics as `Загроза балістики`; the table listed only
  `загроза застосування` and `загроза удар`, which are its superstrings and
  therefore unreachable. That single omission is why MISSILE resolved on 25 of
  2,392 declarations, and why the only rule that has ever passed its own
  regime gate was invisible to the join almost every time it applied.
- **Breadth is bounded on the other side rather than by a longer marker.** A
  declaration needs a declare marker **and** exactly one kind marker, so
  `загроза` on its own resolves nothing. Held by a regression.
- **`дрон` and `авіабомб` added**, closing `Атака дронів-камікадзе` and
  `Загроза керованих авіабомб`.
- **`ThreatKind.ARTILLERY` added, and it carries no timing regime.**
  `Відбій загрози артобстрілу` was refused outright because artillery had
  nowhere to land: a means of attack the source names and the schema cannot
  hold is a message discarded, not classified. `Regime` names MISSILE and
  DRONE explicitly and the rules compare with `is`, so artillery is reported
  and never reaches an alarm rule. That is a geography decision, not caution:
  artillery does not range to the Polish border.
- **F78: `балістик` was one letter too long for the adjectival form.**
  `балістичного озброєння` diverges from the stem at the eighth character, so
  half the ballistic vocabulary was invisible. Found by testing the repair
  against the quoted forms, not by the measurement that motivated it: a second
  cause producing the same symptom does not show up in a number, only in the
  texts. Now `баліст`.
- **Six mutations run, one passed, and the test was rewritten.** The inversion
  test used `Відбій загрози застосування балістики`, which contains `загрози`
  in the genitive and therefore no declare marker, so reversing the lift and
  declare ordering did not fail it. Third time in two sprints that a test
  passed on data unable to distinguish the implementations.
- **The first measurement against real text: four of twenty became five.**
  The pinned means-layer count over the twenty real messages in this
  repository since sprint 4 gained `Атака дронів-камікадзе типу Молнія`, one
  of the four forms F71 recorded, which had been sitting in the fixture
  unmatched the whole time. `real_messages_with_kind_marker` moves 4 to 5 in
  `STATUS.json`. Twenty messages is not a sample for a coverage claim and this
  is not one.
- **The new entries are `[assumption, unmeasured]` and say so.** They are
  derived from five message forms, which is evidence the parser accepts what
  it demonstrably refused and evidence for nothing else. **How much of the
  corpus this recovers is not measured**, and no coverage claim about this
  release should be made until T45 runs on the operator's machine, with the
  near-miss pile reviewed by hand. A table tuned against a number it also
  produces is the failure this project was founded on refusing.

## 0.19.2.0 - 2026-08-10

**An audit of the two releases before it, at the author's request, and it
found more than expected.** Three of the findings are corrections to claims
this repository made about itself.

- **F76: the trailing counter measured how finely an oblast is subdivided.**
  One episode over Lviv oblast produced `alerts_count: 7`, one per raion,
  because the channel declares per raion and the counter added one per
  transition. The consumer shades by that number, so the map would have
  rendered administrative subdivision as intensity and oblasts with more
  raions as systematically darker. An episode now opens when an oblast goes
  from no active raion to one and closes when the last is affirmatively
  cleared; `UNKNOWN` does not close one, because silence is not an all-clear
  inside a counter either.
- **The regression that missed it used one raion.** Second time in one sprint
  that a test passed because its data could not distinguish right from wrong,
  after the distance sort whose two orderings agreed on the chosen pair. A
  test whose data is picked for convenience is a test whose data is picked by
  the implementation.
- **F77: `tests/test_sprint10.py` claimed every test in it was
  mutation-verified.** 40 tests, 22 naming a mutation, 13 actually run against
  one. The sentence was written before any verification happened and survived
  three releases. It cost nothing operationally and everything in standing:
  an unearned assurance makes every earned one need re-reading. The header now
  says which tests are verified and claims nothing about the rest.
- **The claim that the consumer maps `kyiv` was false.** Written in the
  present tense about somebody else's code, in the entry recording F74, which
  is a defect caused by exactly that. Checked afterwards: no `kyiv` in the
  consumer's geometry, no mapping in the package, seven Kyiv-oblast raions
  drawing nothing. Corrected in the log and carried as T44.
- **"A measured failure" about the palette was somebody else's inference.**
  `docs/WEBAPP.md` described the theme-inversion diagnosis as measured. The
  site's own audit records it as an inference from two screenshots, with the
  client never seen and no control image. Relabelled; the design it produced
  stands on its own regardless of which explanation is true.
- **`tools/contract_check.py` runs in the gate.** D-020 moved contract
  ownership here arguing the producer's gate can exercise the schema, and then
  nothing did, which is how F74 shipped. The check composes a report, writes
  the file and asserts what a consumer relies on: the join field is a register
  slug or empty, nulls stay null, a cleared area leaves the list, an
  unresolvable area stays in it. It deliberately does not import the consumer,
  which would rebuild the coupling D-020 removed. Verified by reintroducing
  F74 on a scratch copy: three of its four assertions fire.
- **Every diagram is mermaid, and the rule now has a reader.** A deployment
  diagram shipped as ASCII art into a repository where four documents already
  used mermaid, so the convention existed only in the files that happened to
  follow it. `tests/lint_mermaid.py` fails on a non-mermaid block containing a
  bare arrow that is not a shell command, and `ENGINEERING.md` section 8 says
  why: ASCII does not render on a phone, cannot be diffed usefully, and falls
  out of alignment the moment a label grows.
- **The cost of composing a report is a number now**: 57 ms at 5,000 events,
  211 ms at 20,000, 723 ms at 60,000, linear. Not binding at a 60 s interval,
  and a curve rather than a constant, because the store grows and nothing
  prunes it. Recorded so a latency claim carries this term instead of assuming
  it away.

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
  distinction this project does not make. **The sentence originally written
  here said the consumer maps it, in the present tense, and that was false**:
  checked afterwards, no such mapping exists and seven Kyiv-oblast raions draw
  no marker. Corrected at 0.19.2.0.
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
with M2, and a host is an availability decision - with the consequence that a
change of address class restarts T39's ladder rather than continuing it. D-017
records what was refused along the way -
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
