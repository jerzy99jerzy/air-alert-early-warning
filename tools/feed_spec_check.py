"""The two editions of FEED-SPEC must be one document in two languages.

`docs/FEED-SPEC.md` is read by a ministry; `docs/FEED-SPEC-PL.md` is the
edition that ministry reads in its own language. A sentence changed in one
and not the other is a document that says two things, and nothing a reader
can see tells them which. `brief_check.py` holds the two briefs together
figure for figure; this check holds the two specifications together on
everything that is language-neutral, which is more than figures:

- the version line, which must be the same version and the same date;
- the headings, level for level and number for number, in the same order;
- per section, the number of bold-lead paragraphs, table rows, list items and
  fenced blocks, because a property dropped from one edition drops one of
  each and this is where it shows;
- the fenced blocks themselves: a JSON or XML example is identical in both,
  a mermaid diagram has the same shape (the labels may differ), a prose box
  is counted;
- every inline code span, as a multiset, with the four provenance labels
  mapped between the languages, because a field name in backticks is the same
  string in any language and a different one is a different claim;
- every figure, through `brief_check.figures`, which already knows that
  `48,540` and `48 540` are one number and that dates and clock times are
  not quantities;
- every cited identifier (`D-`, `F-`, `F-S`, `T`) and every URL, as sets.

What it cannot check is meaning. A faithful translation and a wrong one have
the same shape; the check catches the drift that happens by accident - an
edit made in one file on a Tuesday - and leaves the drift that happens on
purpose to the person making it, who then has to make it twice.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ENGLISH = ROOT / "docs" / "FEED-SPEC.md"
POLISH = ROOT / "docs" / "FEED-SPEC-PL.md"

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_NUMBER = re.compile(r"^(\d+[a-z]?(?:\.\d+)?)\.?\s")
_FENCE = re.compile(r"^```(\w*)\s*$")
_CODE_SPAN = re.compile(r"`([^`\n]+)`")
_LABEL = re.compile(
    r"^\[(measured|reported|inference|unknown|zmierzone|raportowane|wniosek|nieustalone)"
    r"(?::[^\]]*)?\]$"
)
_LABEL_EN = {
    "zmierzone": "measured", "raportowane": "reported",
    "wniosek": "inference", "nieustalone": "unknown",
}
_IDENTIFIER = re.compile(r"\b(?:D-\d+|F(?:-S)?\d+|T\d+[a-z]?)\b")
_URL = re.compile(r"https?://[^\s)>\]]+")
_VERSION_LINE = re.compile(r"^Version:\s+(\S+)\s+/\s+(\S+)\s*$", re.M)


def _brief_check() -> Any:
    """`figures` and `dates` come from the check that already normalises them."""
    path = ROOT / "tools" / "brief_check.py"
    spec = importlib.util.spec_from_file_location("_brief_check_for_feed_spec", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _fences(text: str) -> tuple[list[tuple[str, str]], str]:
    """Every fenced block as (info string, body), and the text without them."""
    blocks: list[tuple[str, str]] = []
    kept: list[str] = []
    info: str | None = None
    body: list[str] = []
    for line in text.split("\n"):
        fence = _FENCE.match(line)
        if fence and info is None:
            info = fence.group(1)
            body = []
            continue
        if fence and info is not None:
            blocks.append((info, "\n".join(body)))
            info = None
            continue
        if info is not None:
            body.append(line)
        else:
            kept.append(line)
    return blocks, "\n".join(kept)


def _sections(text: str) -> list[tuple[str, dict[str, int]]]:
    """Each heading as (key, counts). The key is level and number, not words."""
    out: list[tuple[str, dict[str, int]]] = []
    key = "preamble"
    counts: dict[str, int] = Counter()
    # Paragraph starts are what is compared, not lines: the two languages
    # wrap differently, so a bold phrase or a year can open a line in one
    # edition and sit mid-line in the other. A paragraph opens after a blank
    # line or a heading; a numbered item also continues a numbered list.
    at_paragraph_start = True
    after_numbered_item = False
    for line in text.split("\n"):
        heading = _HEADING.match(line)
        if heading:
            out.append((key, dict(counts)))
            level, title = heading.groups()
            number = _NUMBER.match(title)
            key = f"h{len(level)}:{number.group(1) if number else '-'}"
            counts = Counter()
            at_paragraph_start = True
            after_numbered_item = False
            continue
        if line.startswith("**") and at_paragraph_start:
            counts["bold-lead paragraphs"] += 1
        if line.startswith("|"):
            counts["table rows"] += 1
        numbered = re.match(r"^\d{1,2}\.\s", line) is not None
        if line.startswith("- ") or (numbered and (at_paragraph_start or after_numbered_item)):
            counts["list items"] += 1
            after_numbered_item = numbered
        elif line.strip() and not line.startswith(" "):
            after_numbered_item = False
        if _FENCE.match(line):
            counts["fence lines"] += 1
        at_paragraph_start = not line.strip()
    out.append((key, dict(counts)))
    return out


def _code_spans(text: str, polish: bool) -> Counter[str]:
    spans: Counter[str] = Counter()
    for span in _CODE_SPAN.findall(text):
        label = _LABEL.match(span)
        if label:
            word = label.group(1)
            spans[f"[{_LABEL_EN.get(word, word)}]"] += 1
        else:
            spans[span] += 1
    return spans


def check() -> list[str]:
    problems: list[str] = []
    for path in (ENGLISH, POLISH):
        if not path.exists():
            return [f"{path.name} is missing"]
    english = ENGLISH.read_text(encoding="utf-8")
    polish = POLISH.read_text(encoding="utf-8")

    en_version = _VERSION_LINE.search(english)
    pl_version = _VERSION_LINE.search(polish)
    if en_version is None or pl_version is None:
        problems.append("a Version line is missing from one edition")
    elif en_version.groups() != pl_version.groups():
        problems.append(
            f"the editions carry different versions: {en_version.group(0)!r} "
            f"against {pl_version.group(0)!r}")

    en_blocks, en_body = _fences(english)
    pl_blocks, pl_body = _fences(polish)

    en_sections = _sections(en_body)
    pl_sections = _sections(pl_body)
    en_keys = [key for key, _ in en_sections]
    pl_keys = [key for key, _ in pl_sections]
    if en_keys != pl_keys:
        problems.append(
            f"the headings differ: {len(en_keys)} in English "
            f"({', '.join(en_keys)}) against {len(pl_keys)} in Polish "
            f"({', '.join(pl_keys)})")
    else:
        for (key, en_counts), (_, pl_counts) in zip(en_sections, pl_sections, strict=True):
            for what in sorted(set(en_counts) | set(pl_counts)):
                a, b = en_counts.get(what, 0), pl_counts.get(what, 0)
                if a != b:
                    problems.append(
                        f"section {key}: {a} {what} in English, {b} in Polish")

    if len(en_blocks) != len(pl_blocks):
        problems.append(
            f"{len(en_blocks)} fenced blocks in English, {len(pl_blocks)} in Polish")
    else:
        for index, ((en_info, en_text), (pl_info, pl_text)) in enumerate(
                zip(en_blocks, pl_blocks, strict=True), start=1):
            if en_info != pl_info:
                problems.append(
                    f"fenced block {index}: language {en_info!r} in English, "
                    f"{pl_info!r} in Polish")
            elif en_info == "mermaid":
                if (en_text.count("-->") != pl_text.count("-->")
                        or en_text.count("\n") != pl_text.count("\n")):
                    problems.append(
                        f"fenced block {index}: the mermaid diagrams differ in shape")
            elif en_info and en_text != pl_text:
                problems.append(
                    f"fenced block {index} ({en_info}): the two editions carry "
                    f"different content; an example is the same bytes in both")

    en_spans = _code_spans(en_body, polish=False)
    pl_spans = _code_spans(pl_body, polish=True)
    for span in sorted(set(en_spans) | set(pl_spans)):
        a, b = en_spans[span], pl_spans[span]
        if a != b:
            problems.append(
                f"the code span `{span}` appears {a} time(s) in English and "
                f"{b} in Polish")

    # Identifiers are compared as names below; their digits are not figures.
    brief = _brief_check()
    en_figures: Counter[str] = brief.figures(_IDENTIFIER.sub(" ", en_body), polish=False)
    pl_figures: Counter[str] = brief.figures(_IDENTIFIER.sub(" ", pl_body), polish=True)
    for value in sorted(set(en_figures) | set(pl_figures), key=float):
        a, b = en_figures[value], pl_figures[value]
        if a != b:
            problems.append(
                f"the figure {value} appears {a} time(s) in English and {b} in "
                f"Polish; the two are the same document")

    for name, pattern in (("identifier", _IDENTIFIER), ("URL", _URL)):
        en_set = set(pattern.findall(english))
        pl_set = set(pattern.findall(polish))
        for item in sorted(en_set - pl_set):
            problems.append(f"the {name} {item} is cited in English only")
        for item in sorted(pl_set - en_set):
            problems.append(f"the {name} {item} is cited in Polish only")
    return problems


def main() -> int:
    problems = check()
    for problem in problems:
        print(f"feed-spec-check: {problem}", file=sys.stderr)
    if problems:
        return 1
    print("feed-spec-check: the two editions of FEED-SPEC agree section for "
          "section, figure for figure, span for span")
    return 0


if __name__ == "__main__":
    sys.exit(main())
