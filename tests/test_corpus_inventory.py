"""F68 regressions: a corpus measurement that cannot be identified is not a measurement.

The corpus was lost on 2026-08-09: sixty thousand posts, one copy, no checksum,
no inventory, and every published figure derived from it. Re-collection works
because Telegram addresses posts by id, so the same range yields the same pages.
That is exactly why an inventory is needed rather than optional: without one,
"the second copy is the first one" is an assumption sitting under every number
this project publishes.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.corpus_inventory import aggregate_digest, inventory

PAGE = (
    '<div class="tgme_widget_message" data-post="air_alert_ua/{i}">'
    '<div class="tgme_widget_message_text js-message_text">x</div></div>'
)


def _write(directory: Path, low: int, high: int) -> Path:
    path = directory / f"page-{low}-{high}.html"
    path.write_text("".join(PAGE.format(i=i) for i in (low, high)), encoding="utf-8")
    return path


def test_the_digest_changes_when_any_page_changes(tmp_path: Path) -> None:
    """Otherwise it answers "is this the same corpus" with a shrug."""
    _write(tmp_path, 100, 119)
    before = aggregate_digest(inventory(tmp_path)[0])
    (tmp_path / "page-100-119.html").write_text("tampered", encoding="utf-8")
    assert aggregate_digest(inventory(tmp_path)[0]) != before


def test_the_digest_does_not_depend_on_the_order_pages_are_read(tmp_path: Path) -> None:
    """A filesystem that lists differently must not read as a different corpus."""
    _write(tmp_path, 100, 119)
    _write(tmp_path, 120, 139)
    rows = inventory(tmp_path)[0]
    assert aggregate_digest(rows) == aggregate_digest(list(reversed(rows)))


def test_a_filename_that_lies_about_its_content_is_reported(tmp_path: Path) -> None:
    """Every tool reads the id range off the name; a name that disagrees is unusable."""
    path = tmp_path / "page-100-119.html"
    path.write_text(PAGE.format(i=500), encoding="utf-8")
    _rows, problems = inventory(tmp_path)
    assert problems and "filename says" in problems[0]


def test_the_gate_refuses_a_corpus_measurement_with_no_inventory(tmp_path: Path) -> None:
    """The check that makes F68 uncommittable rather than merely regrettable."""
    from tools.docs_audit import check_corpus_measurements_carry_an_inventory

    status = json.loads((Path(__file__).resolve().parent.parent / "STATUS.json").read_text())
    assert any(key.endswith("_design_window") for key in status["measured"]), (
        "this test asserts on the presence of corpus-derived figures; there are none"
    )
    without = {"measured": {"design_window_messages": 1}}
    assert check_corpus_measurements_carry_an_inventory(without), (
        "a corpus measurement with no inventory passed the gate"
    )


def test_a_status_write_does_not_erase_fields_it_does_not_own() -> None:
    """The write that ate the holdout boundary, made red.

    `--write-status` once did ``status["corpus"] = {...}`` and the D-012a
    freeze record went with it: fields the tool does not own and cannot
    recompute, erased by an update that looked like one. The contract under
    test: inventory-owned fields land, superseded legacy names are retired,
    and everything else — the holdout record first among it — survives.
    """
    from tools.corpus_inventory import SUPERSEDED, patch_corpus_block

    status: dict[str, object] = {
        "corpus": {
            "posts": 60680,
            "post_id_low": 260841,
            "post_id_high": 321520,
            "retrieved": "2026-08-09",
            "contiguous": True,
            "span_days": 118,
            "size_mb": 313,
            "design_window_high_id": 309380,
            "holdout_low_id": 309381,
            "holdout_share": 0.2001,
            "content_read_before_freeze": False,
            "a_field_invented_after_this_test": "must also survive",
        }
    }
    fields: dict[str, object] = {
        "manifest": "data/aggregates/corpus_manifest.csv",
        "pages": 3062,
        "messages": 61240,
        "id_range": "260790..321830",
        "digest": "sha256:deadbeef",
        "contiguity": "no gaps",
        "size_mb": 320,
        "taken_at": "2026-08-10",
    }
    patched, notes = patch_corpus_block(status, fields)
    corpus = patched["corpus"]
    assert isinstance(corpus, dict)

    # The holdout record survives, byte for byte.
    assert corpus["design_window_high_id"] == 309380
    assert corpus["holdout_low_id"] == 309381
    assert corpus["holdout_share"] == 0.2001
    assert corpus["content_read_before_freeze"] is False
    # So does a key this tool has never heard of: ownership is by list, not
    # by acquaintance, or the next foreign field dies the same death.
    assert corpus["a_field_invented_after_this_test"] == "must also survive"
    # Inventory-owned fields are the fresh measurement, not the stale one.
    assert corpus["messages"] == 61240 and corpus["size_mb"] == 320
    # Legacy names are retired, each retirement recorded.
    assert not any(key in corpus for key in SUPERSEDED)
    assert sum("removed" in note for note in notes) == len(SUPERSEDED)


def test_the_gate_refuses_a_corpus_block_missing_the_holdout_record() -> None:
    """The reader the erased fields never had.

    The write in the test above passed the gate because nothing read the
    D-012a fields. This is the reading: a corpus block without the freeze
    record, or with a boundary that is not two adjacent ids, is a red gate.
    """
    from tools.docs_audit import check_the_holdout_boundary_survives_in_the_corpus_block

    eaten = {"corpus": {"pages": 3062, "messages": 61240}}
    assert check_the_holdout_boundary_survives_in_the_corpus_block(eaten), (
        "a corpus block with no holdout record passed the gate"
    )

    torn = {
        "corpus": {
            "design_window_high_id": 309380,
            "holdout_low_id": 309999,
            "holdout_share": 0.2001,
            "content_read_before_freeze": False,
        }
    }
    assert check_the_holdout_boundary_survives_in_the_corpus_block(torn), (
        "a non-adjacent boundary passed the gate"
    )

    intact = {
        "corpus": {
            "design_window_high_id": 309380,
            "holdout_low_id": 309381,
            "holdout_share": 0.2001,
            "content_read_before_freeze": False,
        }
    }
    assert check_the_holdout_boundary_survives_in_the_corpus_block(intact) == []
