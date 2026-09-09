"""`tools/feed_spec_check.py`: the two editions of FEED-SPEC are one document.

Each test below writes a small English and Polish pair into a scratch tree,
introduces one drift of the kind the gate exists for, and asserts the gate
names it. The last test runs the gate on the repository's own pair, so a
drift lands in a red test before it lands in the gate's output.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent

ENGLISH = """# A feed

Version: 3.0 / 2026-09-09
A specification with `state.json` and 48,540 messages `[measured]`.

```
A note box, in prose, which may be any length in either language.
```

## 1. The first section

**One. A property.** With F76 and D-050 and <https://example.invalid/a>.

| Column | Value |
| --- | --- |
| Rows | 127 |

- a bullet with `geocode`
- another with 99.34%

```json
{"generated_at": "2026-09-09T11:21:48+02:00", "valid_for_s": 120}
```

## 2. The second section

**Two. Another.** 4,463 reads, on 2026-09-07 at 06:09 UTC, at 2.5.

```mermaid
stateDiagram-v2
    [*] --> A: begins
    A --> B: changes
```
"""

POLISH = """# Feed

Version: 3.0 / 2026-09-09
Specyfikacja ze `state.json` i 48 540 wiadomościami `[zmierzone]`.

```
Ramka z uwagą, prozą, dowolnej długości w każdym z języków, także
w dwóch liniach.
```

## 1. Pierwsza sekcja

**Pierwsza. Właściwość.** Z F76 i D-050 oraz <https://example.invalid/a>.

| Kolumna | Wartość |
| --- | --- |
| Wiersze | 127 |

- punkt z `geocode`
- drugi z 99,34%

```json
{"generated_at": "2026-09-09T11:21:48+02:00", "valid_for_s": 120}
```

## 2. Druga sekcja

**Druga. Kolejna.** 4 463 odczyty, 2026-09-07 o 06:09 UTC, w 2.5.

```mermaid
stateDiagram-v2
    [*] --> A: zaczyna sie
    A --> B: zmienia sie
```
"""


def _load(tmp_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "_feed_spec_check_under_test", ROOT / "tools" / "feed_spec_check.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.ROOT = ROOT  # brief_check is still loaded from the real tree
    module.ENGLISH = tmp_path / "FEED-SPEC.md"
    module.POLISH = tmp_path / "FEED-SPEC-PL.md"
    return module


def _pair(tmp_path: Path, english: str = ENGLISH, polish: str = POLISH) -> ModuleType:
    (tmp_path / "FEED-SPEC.md").write_text(english, encoding="utf-8")
    (tmp_path / "FEED-SPEC-PL.md").write_text(polish, encoding="utf-8")
    return _load(tmp_path)


def test_a_faithful_pair_passes_and_prose_boxes_may_wrap_differently(tmp_path: Path) -> None:
    assert _pair(tmp_path).check() == []


def test_a_different_version_line_is_named(tmp_path: Path) -> None:
    polish = POLISH.replace("3.0 / 2026-09-09", "2.9 / 2026-09-09")
    findings = _pair(tmp_path, polish=polish).check()
    assert any("different versions" in f for f in findings)


def test_a_figure_changed_in_one_edition_is_named(tmp_path: Path) -> None:
    findings = _pair(tmp_path, polish=POLISH.replace("4 463", "4 464")).check()
    assert any("figure 4463" in f for f in findings)
    assert any("figure 4464" in f for f in findings)


def test_a_property_dropped_from_one_edition_is_named(tmp_path: Path) -> None:
    trimmed = POLISH.replace("**Druga. Kolejna.** ", "")
    findings = _pair(tmp_path, polish=trimmed).check()
    assert findings == ["section h2:2: 1 bold-lead paragraphs in English, 0 in Polish"]


def test_a_missing_heading_is_named(tmp_path: Path) -> None:
    polish = POLISH.replace("## 2. Druga sekcja", "## 3. Druga sekcja")
    findings = _pair(tmp_path, polish=polish).check()
    assert any("headings differ" in f for f in findings)


def test_a_code_span_changed_in_one_edition_is_named(tmp_path: Path) -> None:
    findings = _pair(tmp_path, polish=POLISH.replace("`geocode`", "`geokod`")).check()
    assert "the code span `geocode` appears 1 time(s) in English and 0 in Polish" in findings
    assert "the code span `geokod` appears 0 time(s) in English and 1 in Polish" in findings


def test_the_provenance_labels_are_read_across_the_languages(tmp_path: Path) -> None:
    """`[zmierzone]` is `[measured]`; a label with a note keeps its word."""
    with_note = POLISH.replace("`[zmierzone]`", "`[zmierzone: jeden ładunek]`")
    with_note_en = ENGLISH.replace("`[measured]`", "`[measured: one payload]`")
    assert _pair(tmp_path, english=with_note_en, polish=with_note).check() == []
    findings = _pair(tmp_path, polish=POLISH.replace("`[zmierzone]`", "`[raportowane]`")).check()
    assert any("[measured]" in f for f in findings) and any("[reported]" in f for f in findings)


def test_an_example_block_must_be_the_same_bytes(tmp_path: Path) -> None:
    polish = POLISH.replace('"valid_for_s": 120', '"valid_for_s": 121')
    findings = _pair(tmp_path, polish=polish).check()
    assert any("fenced block 2 (json)" in f for f in findings)


def test_a_diagram_may_differ_in_labels_but_not_in_shape(tmp_path: Path) -> None:
    findings = _pair(tmp_path, polish=POLISH.replace("    A --> B: zmienia sie\n", "")).check()
    assert any("mermaid diagrams differ in shape" in f for f in findings)


def test_an_identifier_or_url_cited_in_one_edition_only_is_named(tmp_path: Path) -> None:
    findings = _pair(tmp_path, polish=POLISH.replace("F76", "F77")).check()
    assert "the identifier F76 is cited in English only" in findings
    assert "the identifier F77 is cited in Polish only" in findings
    english = ENGLISH.replace("example.invalid/a", "example.invalid/b")
    findings = _pair(tmp_path, english=english).check()
    assert any("URL" in f for f in findings)


def test_a_missing_edition_is_one_finding(tmp_path: Path) -> None:
    module = _pair(tmp_path)
    (tmp_path / "FEED-SPEC-PL.md").unlink()
    assert module.check() == ["FEED-SPEC-PL.md is missing"]


def test_the_main_entry_point_reports_and_exits(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    module = _pair(tmp_path)
    assert module.main() == 0
    assert "agree section for section" in capsys.readouterr().out
    module = _pair(tmp_path, polish=POLISH.replace("127", "128"))
    assert module.main() == 1
    assert "feed-spec-check:" in capsys.readouterr().err


def test_the_two_editions_in_this_tree_agree() -> None:
    """The real pair, so a drift is a red test and not only a red gate."""
    spec = importlib.util.spec_from_file_location(
        "_feed_spec_check_real", ROOT / "tools" / "feed_spec_check.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert module.check() == []
