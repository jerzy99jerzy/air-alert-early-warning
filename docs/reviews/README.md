# Reviews

One review per **major release**, meaning a change to the second version
component: 0.19.x to 0.20.0.0 needs one, 0.20.0.0 to 0.20.1.0 does not
(D-021). `tools/docs_audit.py` fails the gate when a major release has no
file here, so this is a rule with a reader rather than a sentence in four
documents.

## Releases with no review, named rather than left to be counted

Twelve major releases shipped without one, and no file will ever be written
for them. A review is a reading of a tree by somebody who does not yet know
what they will find; producing one now from the changelog would be a document
asserting that something was examined when it was not, which is the
fabrication this repository's whole apparatus exists against.

`0.1.0`, `0.2.0.0`, `0.7.0.0`, `0.8.0.0`, `0.9.0.0`, `0.10.0.0`, `0.11.0.0`,
`0.12.0.0`, `0.14.0.0`, `0.16.0.0`, `0.17.0.0`, `0.18.0.0`, `0.19.0.0`.

**0.19.0.0 is a different case from the rest.** It opens a run of five
releases worked in one sitting, and the code that run introduced is reviewed
in `0.20.0.0.md`, which read the whole thing. Writing a separate file for the
first release of the run would split one reading across two documents to
satisfy a counter, which is the sort of compliance this repository is supposed
to be able to spot.

**0.16.0.0 is the one worth noting.** It was reviewed, thoroughly, and the
review became `SESSION-2026-08-10.md` and a handoff document rather than a
file here. The work happened; the filing did not. That is the shape of F79 in
one release.

## Filed late

`0.13.0.0`, `0.15.0.0` and `0.20.0.0` were reviewed at the time and brought in
at 0.20.1.0, each carrying a note saying so. Their text is as it was written,
because editing a review after the fact to read better is the same failure as
writing one after the fact.
