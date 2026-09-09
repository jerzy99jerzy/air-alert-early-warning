# ENGINEERING.md

**Portable engineering standard. Copy into any repository.**

Version 1.2, 2026-09-09. Distilled from several single-maintainer repositories
and from what went wrong in each. The 1.2 edition removes the names of the
repositories the rules were learned in: a rule that needs its origin named to
be understood is not yet a rule, and the defects below are described by their
class so they can be recognised in a tree that has never heard of the ones they
were first found in.

Nothing here is aspiration. Every rule exists because its absence produced a
specific defect that shipped, and the defect is described so the rule can be
argued with rather than obeyed.

---

**These are single-maintainer repositories.** That is why the gate lives in
`make verify` rather than in a review process, and why there is no issue
tracker ceremony below. There is a pull-request step, and it exists for a
different reason than review: it is the mechanism that makes the gate
impossible to bypass rather than merely expected to run. Where a rule
substitutes for a second pair of eyes, it says so.

---

# Part I. What a repository looks like

## 0. The one principle

**A claim the repository makes about itself should be executable.** A sentence
drifts silently; a test drifts loudly.

This is the newest rule and the one that generalises furthest. It was learned
the expensive way: a README claimed the tool could not see one class of data
while the tree shipped a query that enumerated exactly that data. Three code
reviews missed it, because all three reviewed code and the divergence was
between the code and the prose describing the code. It was found by a
question.

Everything below is an application of this principle to a different surface.

---

## 1. Repository skeleton

Create in this order. The order matters: it is descending order of how
expensive the thing becomes to add later.

```
<repo>/
├── README.md              # thesis, scope, what it will NOT tell you, layout
├── ENGINEERING.md         # this file
├── CONTRIBUTING.md        # invariants a contributor must not break
├── SECURITY.md            # how to report a defect in the guarantees
├── LICENSE / NOTICE       # decided at creation, not at v0.7
├── CHANGELOG.md           # every release, including the ones folded into others
├── TODO.md                # open items, each with a status and acceptance test
├── Makefile               # `verify` is the only gate anyone needs to know
├── pyproject.toml         # single source of dependency truth
├── <package>/             # ONE namespace, never five top-level directories
├── tests/
│   ├── conftest.py
│   ├── fixtures/
│   ├── test_<domain>.py   # behaviour by area
│   ├── test_sprint<N>.py  # regression, one file per sprint
│   └── lint_*.py          # executable claims about the repo itself
├── docs/
│   ├── ARCHITECTURE.md    # what talks to what, with a block index
│   ├── MECHANISMS.md      # how each mechanism works
│   ├── METHODOLOGY.md     # what may be claimed, plus the defect log
│   ├── THREAT-MODEL.md    # adversaries against this tool
│   ├── MVP.md             # release criteria per audience
│   └── report.md          # generated output stays lowercase
└── .github/
    ├── workflows/ci.yml           # calls `make verify`, nothing else
    └── pull_request_template.md   # the self-review checklist, section 2
```

**Naming convention, and the reason.** Design documents are `UPPERCASE.md`,
generated artefacts are `lowercase.md`. The case is not decoration: it tells a
reader at a glance whether a file is authored or produced, and therefore
whether editing it is meaningful. `report.md` is regenerated on every run;
editing it is a mistake the filename should discourage.

**One namespace package.** Five top-level directories named for what they did
planted five collision candidates in `site-packages` on every install. Slug
stays descriptive (a search term), console scripts stay grouped by prefix
(typed by hand), the import path is a namespace and must be unique rather than
descriptive. Fixing this at v0.10 cost a breaking change and surfaced two
latent path bugs; at v0.1 it costs nothing.

**Data policy, decided at creation.** Three tiers, and the boundary is enforced
by code rather than by care:

| Tier | Lives | Committed |
| --- | --- | --- |
| Raw, per-subject records | `data/raw/`, git-ignored | never |
| Aggregates, counts only | `data/aggregates/` | yes |
| Generated documents | `docs/report.*` | yes, regenerable |

The rule that makes it hold: **the path from raw to committed runs through
counting and then through a guard, and there is no other path.** The guard is
a function that refuses any per-subject identifier - a hostname, a message
author, whatever the subject is in that repository - and it is called on every
path that writes an aggregate. Write the `.gitignore` for these three tiers in
the first commit, because retrofitting it means rewriting history.

Secrets: never in the tree, never in a fixture, never in a test. A fixture that
needs a credential generates one at runtime. Every repository that touches an
API should assume its raw store is the most sensitive thing on the disk and
treat it accordingly.

**Codenames.** Documentation and conversation may use a codename. The slug
stays machine-boring. Whether the codename becomes the package name is a
per-repo decision, but it must be stated in the README rather than left
implicit, because that is where the inconsistency lives otherwise.

---

## 2. The single gate

`make verify` runs everything, and **CI calls `make verify` rather than
restating its steps.**

A workflow that lists checks individually drifts the moment a check is added to
the Makefile. This shipped: two lints were added to `verify` and were
local-only for a day, while the Makefile comment said "everything CI runs". The
rule is a consequence: if it is not in `verify`, it does not run anywhere.

Minimum contents of `verify`:

| Target | Fails the build when |
| --- | --- |
| `coverage` | unit tests fail, or coverage drops below the floor |
| `lint` | style or types regress (`ruff check`, `mypy <package>`) |
| `lint-limitations` | a claim in the README no longer matches the tree |
| domain lints | the repository's own invariants are violated |

**Three additions, each paid for by a defect.**

| Target | Fails the build when | Bought by |
| --- | --- | --- |
| `contract-check` | the file another repository consumes stops holding its shape | a consumer's map drew nothing while its list drew everything, for a release, because the join field carried a display name |
| `todo-index` | the backlog's own summary disagrees with the backlog, or an open task has no tier | a count nobody checks is a count everybody quotes; it happened twice before the check existed |
| `lint-mermaid`, extended | a diagram ships as ASCII art | a convention that lived in four documents and had no reader |

**The pattern behind all three, and it is the one worth taking away: a rule
without a reader is a preference.** Every one of them existed as an intention
first, was written down, and was broken by the next person who had not read
the file it was written in. Writing it down is step one of two.

**Coverage is a floor, not a target.** Set it in `pyproject.toml`, at roughly
the current level minus a few points, and raise it when a sprint genuinely
raises coverage. A target invites tests written for the number; a floor only
prevents regression.

**An empty test suite must fail the gate, not pass it.** A fresh `make verify`
on a repo with no tests exits green by default, because pytest treats "nothing
collected" as success. That is the same failure class as unknown-resolves-safe:
absence read as success. Configure pytest so zero collected tests is a failure
(it exits 5 on no tests; do not swallow that), and set the coverage floor above
zero from the first commit. A gate that passes an empty repo is not a gate, and
this shipped in the first draft of this very document's starter kit.

**Type checking and style are not optional.** `ruff` and `mypy` run in CI in
every repository, and a repository where they do not is a gap with no
justification. Converge upward.

**Test on the version you develop on.** One CI pinned an interpreter two
minor versions older than the one the work happened on. Use a matrix with both
ends of the supported range.

**Verify the gate against a real consumer, not only against itself.** One
repository took ownership of a schema on the argument that its own gate could
exercise it, then shipped a release where nothing did. The defect was found by
running the *consumer's* code over a file the producer wrote, by hand, one
release later. If another repository depends on an artifact this one produces,
the producing gate encodes what the consumer needs, and does so **without
importing the consumer**: importing it would rebuild the coupling the split
was for.

### The gate is enforced by the forge, not by habit

Added at 1.2. Until then "tag only after CI is green" held on the maintainer's
discipline, which is to say it was a preference with a good record. Branch
protection on `main` turns it into a mechanism:

- **A pull request is required, with zero required approvals.** The forge does
  not count an approval of one's own pull request, so any other value blocks
  everything. The value of the step is not the approve button.
- **The status checks of every interpreter in the matrix are required.** The
  merge button is disabled until they pass. Order is enforced by the mechanism
  and not by memory.
- **Force pushes and deletions are blocked.** A published tag never moves
  (section 7) and neither does the branch it was cut from.
- **Squash is the only merge.** The convention is one commit per release with
  its changelog entry; a merge commit or a rebase splits that into several and
  "tag on the full hash" stops having an obvious target.
- **The administrator bypass stays on, documented.** This ceremony knows
  releases that were withdrawn within a day. A door that exists and is written
  down is better than one that is forced under pressure.
- **"Require branches up to date" is decided per repository by what CI
  costs.** Free minutes: turn it on, it is the only setting that catches a
  green branch merged onto a `main` that moved. Metered minutes: leave it off
  and keep branches short-lived, because every refresh is a full run.

What the step gives a single maintainer, in order of value: the diff seen once
as a stranger sees it, in the Files-changed view, before it is on `main`; the
10-20 paragraph change description kept beside the commit, searchable, rather
than in a chat; and the checklist in `.github/pull_request_template.md`, whose
every line comes from a defect this repository shipped. The self-review in that
view is the one step no machine performs, and it is the one that found the two
most dangerous errors of the session in which this section was designed - both
of which would have passed every gate, because a gate reads neither a calendar
nor the window of an aggregate.

What the step does not carry: issues. `TODO.md` has a gate (`todo-index`), the
decision log has one (`decision-ids`), and an issue tracker has none a build
can read. An empty issues tab is a decision, not neglect.

One trap worth knowing. A repository that verifies a manifest of digests in CI
will see that check fail on a pull request whose base has moved, because the
checkout is the merge ref and the merged tree carries files the branch's
manifest never listed. The message is about digests; the cause is a stale
branch. With "require up to date" on, the signal arrives before it surprises.

### Dependencies and cost

**Every new runtime dependency is justified in the changelog entry that adds
it.** A tool whose pitch is auditability is weakened by a dependency tree
nobody can audit; two runtime dependencies is a decision, and zero is a better
one where the standard library reaches. Development dependencies are cheaper
and still not free.

**A correct artefact nobody can afford is not a deliverable.** This was written
about detection queries, where a search that returns the right answer and costs
a fortune to schedule is not deployable content, but it generalises: a pipeline
run that takes six hours, a report that is forty megabytes, a check that adds
two minutes to every commit. Cost is a property of the deliverable, and it
should be measured before the thing is called done rather than discovered by the
person paying for it.

### Hygiene jobs (no interpreter needed)

Cheap, and each one exists because it went wrong:

- **No tracked `*.patch` / `*.diff`.** Transfer artefacts committed by
  reflex; more than one repository has carried them in its root.
- **No absolute developer paths** (`/Users/...`, `/home/...`) in tracked source.
- **Tag matches declared version.** A tag whose artefacts were built from a
  different version string happened twice in one day.

---

### Test data is chosen by the implementation unless you choose it

Three times in two sprints, a mutation survived a test that named it. Every
time the cause was the same and none of them was carelessness about the
assertion:

- A distance sort was tested on a pair of areas where sorting by nearest edge
  and sorting by centre give the same order. The mutation swapped the key and
  the test passed. The pair that separates them was found by searching the
  table for an inversion.
- A per-region counter was tested on a region with one subdivision, so
  counting subdivisions and counting episodes were indistinguishable. The real
  data has regions with seven.
- An inversion guard used a phrase carrying the marker in an inflected form, so
  the marker never matched and the ordering under test never ran.

**The question that catches all three: what data would make the wrong
implementation pass this test, and is my data that data?** Convenient data is
usually the implementation's data, because both were written by the same
person on the same afternoon. Where a table or a corpus exists, pick the case
by searching it rather than by imagining it.

## 3. Test density and shape

**One regression test file per sprint, named for the sprint.** `test_sprint9.py`
is not a category, it is a date stamp: it tells a reader which release the cases
in it were written against, and its docstring explains the defect class. Domain
files (`test_pipeline.py`, `test_collection.py`) hold behaviour; sprint files
hold "this specific thing was broken and must not return".

**A regression test must be verified to fail against the previous release, not
assumed to.** Unpack the last tag into a scratch directory, drop the new test
file in, run it, confirm red. A regression test that passes against the buggy
version documents nothing and is worse than none, because it implies coverage
that does not exist. This is fifteen minutes per sprint and it has caught
mis-scoped tests more than once.

**Density guidance, from what actually held up:**

| Code | Expectation |
| --- | --- |
| Enforcement of a stated guarantee (guards, scope, provenance) | every branch, both directions, plus an adversarial case |
| Parsers over untrusted input | malformed, truncated, hostile, oversized; must never raise |
| Classification with a tri-state | one test per state, and one asserting unknown is not the safe state |
| Orchestration and CLI wiring | smoke level; argparse wrappers exercised through their callees |
| Generated output | that it contains what it claims and nothing it promised to exclude |

Roughly 75-80% line coverage is what this shape produces naturally. Chasing 95%
means testing argparse.

**Summary coverage does not see the branch production runs on.** A suite at
95% carried, for eleven releases, two uncovered lines in the one adapter every
poll goes through: the branches for a key present in both the previous and the
current observation, which is the steady state and the most executed code in
the tree. The tests walked a key appearing and a key disappearing, never a key
that simply is. Found by reading the missing-lines list of the file, not the
percentage. Once a release, read that list for the modules the scheduler
touches most.

**A tool that enforces a practice is tested against a fresh repo, not the one
it grew in.** The starter kit for this document passed every check inside the
mature repository it was extracted from and failed four ways on an empty one:
`make verify` went green with no tests, a lint crashed instead of guiding, and
the "generic" CI still named another repository's targets. Found by running it
on a bare directory, which is the only place its assumptions are visible. Any
portable artefact is probed in the environment it claims to support before it
is shipped, exactly as any parser is probed on hostile input.

**Adversarial fixtures earn more than clean ones.** A model validated against
an adversarial world learns something; the clean world only ever confirms the
obvious. Ship fixtures in three flavours - clean, partial, hostile - and ship
the generator as a CLI command rather than a test helper, so someone can run
the repository with no data of their own.

---

## 4. Provenance and the tri-state

**Four labels on every load-bearing claim**, in code, in output records and in
generated documents:

| Label | Means |
| --- | --- |
| `measured` | read from an artefact without interpretation |
| `reported` | supplied by an interested party; each field parsed by us, the completeness is their claim |
| `inference` | derived from observable proxies |
| `speculation` | explicitly uncertain, carried rather than resolved |

`reported` is the one most repositories omit and the one that matters
commercially: it is the difference between "we measured your estate" and "we
measured what you handed us". A composite inherits the weakest label of its
inputs.

**Unknown is never the safe state.** An unrecognised algorithm, an unresolvable
version, an absent threshold: all resolve to `None` and are reported as
unknown. Returning `False` inflates the flattering number silently, which is
the single worst failure mode for any tool whose product is a measurement. This
shipped once and is now checked on every new input path, because it recurs by
default: `False` is what a naive implementation returns.

**Version comparison uses a zero-padded numeric key, never string comparison.**
`"3.5"` sorts below `"3.10"`. This also shipped once.

---

## 5. MVP separate from sprints

These answer different questions and conflating them is why projects run
indefinitely.

**`TODO.md` says what is not done.** Every item carries a status
(`ready` / `blocked-external` / `decision` / `debt`), the blocker where one
exists, and **an acceptance test**, so "done" is not a matter of opinion.

**`docs/MVP.md` says what finished means, per audience.** One project went
eight sprints without this and the cost was invisible until it was named: a
codebase always yields another defect, so without exit criteria every sprint
can be justified as the next one, indefinitely.

Define one MVP per plausible buyer, each with its own definition of done, its
own distance estimate, and its own blockers. Then note which blockers are
engineering and which are access, purchase or decision, because **the second
kind does not shrink by writing code** and that distinction is the one most
often blurred. In that same project, three consecutive sprints were reviews of
its own code while five external blockers sat untouched; naming it changed the
next decision.

**Amend release criteria in the same commit that meets them.** A criterion that
moves because it turned out to be inconvenient is a scope change and gets
recorded as one, with its reason. Quietly editing it is how a project starts
adjusting the measurement to flatter the result.

---

## 6. Sprint discipline

A sprint has a defect class or a capability, not a list of chores.

1. **Establish the baseline.** `make verify` green before touching anything. If
   it is not green, that is the sprint.
2. **Probe rather than read.** Every review that found something real found it
   by running a probe against the code, not by reading it. Three guard defects,
   a k-anonymity failure in a chart, an address-family gap: all empirical, all
   invisible to careful reading.
3. **Fix, then generalise.** Fix the instance, then ask what class it belongs
   to and close the class. The dead allowlist entry became a test that fails on
   any unreachable entry; the stale README claim became `lint_limitations.py`.
4. **Write the regression test and verify it fails against the last tag.**
5. **Review your own diff before packaging.** Self-review after the work
   catches roughly one real defect per sprint: a site-packages sentinel, a
   misleading `granularity` field, a counter that would have leaked host
   identity. Since 1.2 this step has a place - the pull request's diff view -
   rather than a moment.
6. **Record the defect in `docs/METHODOLOGY.md`**, with what it was, why it
   survived, and what class it belongs to. The defect log is the most
   persuasive document in the repository for a technical reader, because
   nobody fakes those.
7. **One release per sprint**: version bump, changelog entry, tag, artefacts
   built from the tag.

**Changelog entries state the defect, not the change.** "Fixed underscore
handling" is worthless. "Host identity adjacent to an underscore passed both
guards; `\b` never fires between `_` and a letter; present since sprint 2" tells
a reader what to check in their own code.

---

## 7. Release and transfer

**Never move a published tag.** A tag describing code that has not changed is
correct even when the surrounding metadata is not. Cut a patch release instead
and say in the changelog what happened. This came up twice; both times the
patch was cheaper and more honest than the rewrite.

**Build artefacts from the tag, not from `HEAD`.** `rm -rf dist build
*.egg-info` before `python -m build`, and check `ls dist` shows only the
expected version before publishing. Stale artefacts from the previous version
got as far as an upload attempt once.

**Every hand-assembled patch set carries a `MANIFEST.sha256`**, and the
verification step after unpacking is `shasum -c`, not visual inspection. Two
patch sets in one day arrived incomplete before this rule existed, one of them
carrying a security fix whose changelog entry then claimed a protection the
tree did not have. A security fix that silently fails to arrive is worse than
one never written.

**Renames keep the old reader for a defined window.** When a field, key or
flag is renamed, every read site accepts both for at least two minor releases,
the new name is written, and the changelog states when the old one stops being
read. A store or a config written by an older version must keep working, and
the cost of the compatibility branch is trivial next to a client whose data
silently reclassifies.

**A field that changes meaning must change name; and a consumer counts the
keys it cannot read.** The other half of the rename rule, learned from the
consuming side at 1.2. An upstream added a list to each record and started
bumping an existing timestamp whenever the list changed, so "when this began"
became "when this last changed" with no rename, no version bump and no failed
check. Seven records were dated from their escalation rather than their start
before anyone read the payload. The publisher's duty is the sentence above.
The consumer's is a canary: every key on a record that the parser has no
reading for is counted and printed on the day it lands, because the next
change of this shape will also pass every check that reads only known keys.

**Onboarding is tested, not assumed.** Clone into a fresh directory and follow
the README from zero, noting where you stop. This is the same probe that found
four defects in this document's own starter kit, and it is the only check on
the assumption that a repository is usable by someone without the author's
memory of it. Run it whenever a repository might be handed to somebody, and
before it is shown to anyone whose opinion matters. A repository that only its
author can run is a repository with a bus factor of one, which is fine as a
personal tool and disqualifying as a commercial artefact.

**A changelog entry without a tag is a debt.** If a release is folded into a
later one, say so in the entry rather than leaving a reader to search for a tag
that does not exist.

**A deployment is proven by content, not by a version string.** The number
that proves a host runs the new code is a count taken from the installed
source - a symbol that exists after and not before - and the count is fixed
from the tree *before* the host is read. "Greater than zero" is a soft
condition dressed as a hard one; it was written that way once and corrected
after the fact. And when the store's schema moves, a copy of the store is
taken before the install, or the release does not proceed: a restore point
that exists only in the sentence "the risk was zero" is not a restore point.

---

## 8. Documentation that earns its keep

**`README.md` must contain a "What this will not tell you" section**, and it is
the part a competent reader reads first. Write it in layers rather than as flat
denials: "does not see the data at rest" is simultaneously false and unhelpful
when the honest answer is that the layer is four things and two of them are
out of scope entirely. Then register every bullet in
`tests/lint_limitations.py` so it cannot go stale.

**`docs/THREAT-MODEL.md` models adversaries against the tool**, not against the
world. Include: who benefits from the output being wrong, what an interested
party supplying input can do, what a hostile input can do to the run itself,
and what the delivery chain of the fixes can do. Re-probe the residual risks on
review rather than re-reading them; one threat model overstated two of its own
holes and missed a real one until the claims were tested.

**`docs/ARCHITECTURE.md` keeps a block index**: a table mapping each block in
the diagram to the document section explaining it. Maintained as a table
precisely so a rename leaves a visibly stale row.

**Every diagram is mermaid. No ASCII art, in any document, ever.** Boxes drawn
with dashes and arrows do not render on a phone, cannot be diffed in any way a
reviewer can read, and fall out of alignment the moment a label gets one
character longer. Mermaid is text, so it diffs; it is rendered by the forge, so
it survives a rename; and it is the same notation in every document, so a
reader learns it once.

The rule needs a reader or it is a preference. `tests/lint_mermaid.py` fails
on any non-mermaid code block containing a bare arrow that is not a shell
command. The heuristic is deliberately narrow and its false positives are
cheap: making the block mermaid is what the rule asked for anyway. Added after
a deployment diagram shipped as ASCII art into a repository where four
documents already used mermaid. The convention existed and lived only in the
files that happened to follow it, which is not a convention, it is a
coincidence with a good reputation.

**Mermaid diagrams: no semicolons inside statements.** `;` is a statement
separator, and a diagram that fails to parse is invisible to every local check
because the markdown is valid and only the forge renders it. Add a lint.

**A fact changed in one document is changed everywhere it is used in
passing, not only where it is argued.** The repair lands in the section that
argues the point - the FAQ, the diagram node - and misses the sentence three
documents away that uses the old fact as a clause. It happened with a source
that was "silent since" a date through two returns and a second silence, and
the sentence stood in four documents while the rows beside it in the store
said otherwise. The check is a `grep` for the old fact across the tree before
the commit, and the pull-request checklist carries the line.

---

# Part II. How the work runs

Part I describes what a repository should look like. This part describes how to
decide what to do next, which is where the expensive mistakes actually happen.
None of these rules is about code.

---

## 9. Session discipline and choosing work

**Audit work is not sprint work, and counting it as progress is how a plan
rots.** One project spent five releases on an audit and its consequences while
the declared sprint sat partial. That was the right call and it moved the
sprint zero distance. State both facts in the same sentence when reporting, or
the next reader infers the sprint advanced.

**Before a sprint, one question: does this bring the project closer to a
recipient, or does it improve something already built?**

Both are legitimate. The failure is not noticing the ratio. Three consecutive
sprints of reviewing the project's own code, while five external blockers sat
untouched, were each justified on their own terms and each found a real defect.
The pattern was still avoidance, because reviewing your own tree is cognitively
pleasant and buying a domain, standing up a tenant or writing to a contact is
not.

**Work that requires waiting on someone else takes precedence over work in the
editor**, because only the first kind has a window. A code item is available at
midnight in six weeks; a conversation with a prospect is not, and a trial
licence expires.

**Distinguish the two blocker types explicitly in the backlog.** An engineering
blocker shrinks when you write code. An access, purchase or decision blocker
does not shrink at all, no matter how many sprints pass. Counting sprints
toward a goal gated by the second kind is a category error, and it is the most
common way a solo project stalls while feeling productive.

**Releases per session are a signal, not an achievement.** Eight in one day
means the work was available and the discipline held, or it means the editor was
the comfortable place to be. Both look identical from inside. If a session
produces several releases and no external step, name that at the end rather than
counting it as a good day.

**Stop at a coherent state, not at exhaustion.** A repository at a tag with a
green pipeline and an honest changelog can be left for a week. One with a
half-applied patch cannot, and the next session starts by reconstructing state
instead of doing work.

---

## 10. Working with an AI assistant on a repository

This is how these repositories are actually built, so it belongs in the
standard rather than in habit. Every rule below comes from a specific failure in
one session.

**Verify claims about the tree; do not accept them.** An assistant will state
that a module exists, that a fix shipped, or that a test covers a case, with the
same confidence whether or not it checked. That produced, once, a false
statement about an adapter that had never been written, which then travelled
into an email to a prospect. The rule is mechanical: any claim about the
current state of the code is `grep`-verified before it is repeated anywhere
outside the session.

**Keep state in files, not in the thread.** A long session accumulates
assumptions about what is applied where. Two patch sets in one day arrived
incomplete because the assistant packaged files based on a remembered state of
the tree rather than a checked one. The counter-rule is in Part I: every
transfer carries `MANIFEST.sha256` and is verified with `shasum -c` before
commit, not after. A handover document is a starting point for reading the
machine, never a substitute for it: the first commands of a session read the
version installed and the timers running, and the document is corrected to
match, not the other way round.

**Understand the transfer boundary.** The assistant runs in a container with no
access to your disk. Running a command in your terminal is not a channel to it;
a file must be attached, and generating an archive locally is not the same as
delivering it. Several exchanges in one session were spent on this alone.

**Demand probes, not readings.** Every review that found something real found
it by running something. Three disclosure-guard defects, a unique-date
re-identification vector, a CI that had drifted weaker than the Makefile: all
empirical, all invisible to careful reading of the same code. "I reviewed it
and it looks correct" is not a review.

**Ask for the correction, not the reassurance.** The useful output is
"your claim X is contradicted by Y", and an assistant will produce it if the
standing instruction is to correct rather than agree. This one is a preference
setting, not a rule of the repository, but it changes what the collaboration is
worth.

**Log the assistant's errors beside the repository's defects, with a class.**
A session that ends with thirteen numbered assistant errors, each with the
instrument that caught it, is a session whose next instance starts knowing
which class recurs. The class that recurs most is the same one across every
session: reasoning from an input that was constructed or assumed rather than
read from the source or the machine. The correction is always the same too - a
fresh reading - and a rule that says so in the log is cheaper than the same
error a fourth time.

---

## 11. Decisions and their conditions for revisit

**`docs/DECISIONS.md` is mandatory, and it records what was rejected.**

A project brief with a section on rejected options - the mass active scan, the
plugin for someone else's scanner - and the reasoning preserved is one of the
more valuable documents in a repository, for two reasons. It stops the same
option being relitigated every few weeks, and it demonstrates operational
judgement to a technical reader more convincingly than any list of what was
built.

One entry per decision:

```markdown
## <what was decided>
Date: <when>. Status: rejected | adopted | superseded by <entry>

**Decision.** <one sentence>

**Reasoning.** <why, in terms that will still make sense out of context>

**What would change this.** <the observation, price, or event that should
reopen it>
```

The last field is the one usually omitted and the one that matters. A decision
without a revisit condition becomes dogma: it stops being a judgement made under
known constraints and becomes a rule nobody remembers the reason for. Writing
"revisit if a client supplies a real export" or "revisit if the price drops
below X" keeps it a decision.

Record the ones that felt obvious too. "We are not building a web UI" is obvious
until three months later, when it is not, and nobody can reconstruct whether it
was considered.

---

## 12. Convergence across repositories

The divergences that recur whenever more than one repository is maintained by
the same hands, and what to do about each:

| Divergence | Recommendation |
| --- | --- |
| Several licences across the set | Each may be right; write one paragraph per repo saying why. An unexplained spread is the first thing a partner asks about |
| Several version schemes | Pick one and hold it. A four-segment scheme where the last segment means "documents only" has held up; the point is one scheme, not which |
| Docs case (`MECHANISMS.md` vs `mechanisms.md`) | Uppercase for design documents, everywhere |
| `ruff`/`mypy` in some repositories | Everywhere |
| An interpreter matrix in some | Everywhere, and include the version you develop on |
| A hygiene job in some | Everywhere, it costs four seconds |
| `docs/MVP.md` in some | Everywhere; it is the cheapest document with the largest effect on how a project ends |
| A changelog with no tags | Every entry has a tag or says which release it was folded into |
| `requirements.txt` beside `pyproject.toml` | Keep one source of truth, or state in the file which one it mirrors |

**The optimisation worth making next:** stop hand-assembling this. The skeleton,
the Makefile, the CI workflow, `lint_limitations.py`, the pull-request template
and the document stubs are mechanical. A template repository or a small
`cookiecutter` turns "remember to add the hygiene job" into a property of every
new repository. Given a handful of repositories and a demonstrated pattern of
the same three things being forgotten, this pays back on the next one.

**The second optimisation:** a check across the set, run occasionally rather
than in CI, that clones each repository and reports which of the rules above
each one fails. Not to enforce uniformity for its own sake, but because the
drift found this way (CI weaker than the Makefile, patch files in a public
root, a changelog with no tags) was all invisible from inside the individual
repositories.

---

## 13. The short version

Twelve rules, if the rest is too long to re-read:

1. A claim about the tool is a test, not a sentence.
2. `make verify` is the only gate; CI calls it rather than restating it, and the forge refuses a merge before it is green.
3. Unknown is never the safe state.
4. A regression test is verified to fail against the previous release.
5. Coverage is a floor, not a target, and the missing-lines list is read for the code the scheduler runs most.
6. `TODO.md` says what is not done; `docs/MVP.md` says what finished means.
7. Access blockers do not shrink by writing code; name which is which, and prefer the work that has a window.
8. Verify what an assistant claims about the tree; never repeat it unchecked.
9. Never move a published tag; every transfer carries a manifest, verified before commit.
10. Record what you rejected, and the condition that would reopen it.
11. Probe, do not read - including the tools that enforce these rules, in the environment they claim to support.
12. A fact changed where it is argued is changed where it is used in passing; a field that changes meaning changes name.
