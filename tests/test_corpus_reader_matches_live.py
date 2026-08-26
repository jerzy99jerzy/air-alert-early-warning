"""F121: the corpus is read with a different text normalisation than the channel.

`read_snapshot_messages` strips tags and stops. `_strip`, which every live poll
goes through, additionally turns `<br>` into a newline and decodes HTML
entities. So the text every published corpus measurement was taken against is
not the text the classifier ever sees, and the divergence runs in **both
directions** on a single message:

    corpus reader : '&#33; Відбій тривоги в #Кам&#39;янець-Подільський_район'
    live reader   : "! Відбій\\nтривоги в #Кам'янець-Подільський_район"
    state         : CLEAR   /  None
    tags          : ()      /  ("Кам'янець-Подільський_район",)

The corpus **over-reads states**, because a marker broken by `<br>` is rejoined
with a space, and **under-reads areas**, because an undecoded entity breaks the
tag pattern. The two do not cancel; they bias different measurements in
different directions, and `kind_coverage_1h`, `kind_join_coverage_1h`, the
`unmapped_tags` pile and the whole `KIND_MARKERS` table repaired under F71 rest
on the corpus side of it.

**Why this survived.** `read_snapshot_messages` was moved into the package at
0.31.0.0 under the argument that a copied reader is two readers that can
disagree, and its docstring says "One reader, one answer". The move fixed the
*duplication* and left the *divergence*: the tree holds six page-walking loops
and two normalisations, and the family using `_strip` (`consistency_check`,
`label_sample`, `register_probe`, `threshold_sweep`, `west_activity`) never met
the family that does not (`kind_coverage`, `unmapped_tags`, `vocab_gaps`).
`tests/test_backfill_reader.py` pins the reader against a fixture with no
entities and no `<br>`, which is a fixture written by the implementation rather
than against it.

**What this file does not claim.** How often the corpus actually carries either
shape is not measured here and cannot be: the corpus is tier 1 and not in the
tree. Three of the 127 rows in `tag_map.csv` carry an apostrophe `[measured]`;
whether the channel serves those as `&#39;` is unknown. The mechanism is what
is pinned, and the frequency is the operator's measurement to take.
"""

from __future__ import annotations

from pathlib import Path

from mavo.areas import parse_tags
from mavo.backfill import read_snapshot_messages
from mavo.sources.telegram import _BLOCK, _TEXT, _strip, classify_state

STAMP = "2026-08-01T20:00:00+00:00"


def _page(post_id: int, text: str) -> str:
    """One block in the live footer-time order: text first, `<time>` after."""
    return (
        f'<div class="tgme_widget_message" data-post="air_alert_ua/{post_id}">'
        f'<div class="tgme_widget_message_text js-message_text">{text}</div>'
        f'<a class="tgme_widget_message_date"><time datetime="{STAMP}"></time></a>'
        f"</div>"
    )


def _live(page: str) -> str:
    """The text the live poll would classify, taken through the live path."""
    block = _BLOCK.findall(page)[0]
    match = _TEXT.search(block)
    assert match is not None
    return _strip(match.group(1)).strip()


def _corpus(tmp_path: Path, page: str) -> str:
    (tmp_path / "page-000000001-000000001.html").write_text(page, encoding="utf-8")
    return read_snapshot_messages(tmp_path)[0][1].strip()


def test_a_line_break_inside_a_marker_reads_the_same_both_ways(tmp_path: Path) -> None:
    """`Відбій<br>тривоги` is one word away from being an all-clear.

    The live reader breaks the line and the marker `відбій тривоги` does not
    match; the corpus reader joins it with a space and it does. A corpus that
    finds all-clears the pipeline would not find inflates every state-derived
    share on the safe-looking side. Verified red at 0.39.1.0.
    """
    page = _page(1, "🟢 Відбій<br/>тривоги в #Львівський_район")
    corpus, live = _corpus(tmp_path, page), _live(page)
    assert classify_state(corpus) == classify_state(live)


def test_an_entity_in_a_tag_reads_the_same_both_ways(tmp_path: Path) -> None:
    """An undecoded `&#39;` breaks the tag pattern at the apostrophe.

    The live reader decodes it and resolves the area; the corpus reader does
    not and resolves nothing, so the tag lands in the unmapped pile as a name
    the register does not hold. Three of the 127 rows in `tag_map.csv` carry an
    apostrophe. Verified red at 0.39.1.0.
    """
    page = _page(2, "Повітряна тривога #Кам&#39;янець-Подільський_район")
    corpus, live = _corpus(tmp_path, page), _live(page)
    assert parse_tags(corpus) == parse_tags(live)


def test_the_two_readers_return_the_same_text(tmp_path: Path) -> None:
    """The general claim, rather than two instances of it.

    `read_snapshot_messages` exists so that measurements over the corpus
    describe the pipeline. That holds only if the text is the same text, so
    this asserts the strings rather than any consequence of them: a future
    divergence in a shape nobody has thought of fails here without needing its
    own case.
    """
    page = _page(3, "🔴 Загроза<br/>БпЛА &amp; КАБ #Ковельський_район")
    assert _corpus(tmp_path, page) == _live(page)


def test_a_decoded_entity_cannot_resurrect_a_tag(tmp_path: Path) -> None:
    """Decoding runs after stripping, and the corpus reader inherits that order.

    `&lt;b&gt;` must survive as visible text rather than become markup the
    stripper has already run past. This is the property `_strip`'s docstring
    names, and it is asserted on the corpus side because that is where it was
    absent.
    """
    page = _page(4, "тривога &lt;b&gt; #Львівський_район")
    corpus = _corpus(tmp_path, page)
    assert "<b>" in corpus, "the entity is decoded"
    assert corpus == _live(page)
