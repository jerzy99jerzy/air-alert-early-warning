"""F87 regressions: the fingerprint promise, given a mechanism.

The module docstring of `tools/label_sample.py` promised from its first
version that `score` recomputes the draw's fingerprint and reports a mismatch
rather than tolerating it. Nothing implemented the comparison: the draw
printed a hash to a terminal, and a terminal is not a reader. The same class
the 0.21.4.0 handover names six times over - a rule written down and enforced
by nobody is a preference.

These tests run the tool through its `main` the way an operator does, over a
synthetic corpus below the real holdout boundary, with the real tag map.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from tools.label_sample import _sidecar, main

# The real boundary in STATUS.json is 309380; everything here sits below it.
PAGE = (
    '<div class="tgme_widget_message" data-post="air_alert_ua/{i}">'
    '<div class="tgme_widget_message_text js-message_text">'
    "Повітряна тривога {tag}"
    "</div>"
    '<time datetime="2026-05-01T0{h}:00:00+00:00"></time></div>'
)

WESTERN = "#Самбірський_район"
FRONT = "#Харківський_район"
UNKNOWN = "#Вигаданський_район"


def _corpus(directory: Path) -> Path:
    tags = [WESTERN, WESTERN, WESTERN, FRONT, FRONT, FRONT, UNKNOWN]
    body = "".join(
        PAGE.format(i=300001 + n, tag=tag, h=n) for n, tag in enumerate(tags)
    )
    (directory / "page-300001-300007.html").write_text(body, encoding="utf-8")
    return directory


def _draw(tmp_path: Path, seed: int = 1) -> Path:
    out = tmp_path / "sample.csv"
    code = main([
        "draw", "--corpus", str(_corpus(tmp_path)),
        "--map", "data/reference/tag_map.csv",
        "--out", str(out), "--size", "5", "--seed", str(seed),
    ])
    assert code == 0
    return out


def _fill(out: Path) -> None:
    with out.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["area_ok"] = row["kind_ok"] = row["distance_ok"] = "y"
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_the_post_id_column_carries_the_channels_own_ids(tmp_path: Path) -> None:
    """A row number is not a post id, and the docstring said post ids.

    Mutation: restore the 1..N enumeration.
    """
    out = _draw(tmp_path)
    with out.open(encoding="utf-8") as handle:
        ids = [int(row["post_id"]) for row in csv.DictReader(handle)]
    assert all(300001 <= post_id <= 300007 for post_id in ids), ids


def test_the_draw_writes_a_record_and_an_untouched_file_scores(tmp_path: Path) -> None:
    """The record beside the CSV is the reader the fingerprint never had."""
    out = _draw(tmp_path)
    record = _sidecar(out)
    assert record.is_file()
    recorded = json.loads(record.read_text(encoding="utf-8"))
    assert recorded["seed"] == 1
    assert len(recorded["fingerprint"]) == 16
    _fill(out)
    assert main(["score", "--in", str(out)]) == 0


def test_a_file_whose_rows_left_the_draw_is_refused(tmp_path: Path) -> None:
    """F87: a rate over rows that are not the drawn rows measures nobody
    knows what.

    A row is deleted after the draw - the shape of a labeller quietly dropping
    the message they could not judge - and `score` must refuse rather than
    report a rate over the remainder. Mutation: skip the comparison.
    """
    out = _draw(tmp_path)
    _fill(out)
    with out.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows[:-1])
    assert main(["score", "--in", str(out)]) == 2


def test_the_same_seed_redraws_the_same_fingerprint(tmp_path: Path) -> None:
    """Reproducibility is the fingerprint's whole claim; a draw that hashes
    differently on the same seed and corpus would make the record noise."""
    first = json.loads(_sidecar(_draw(tmp_path, seed=7)).read_text(encoding="utf-8"))
    second = json.loads(_sidecar(_draw(tmp_path, seed=7)).read_text(encoding="utf-8"))
    assert first["fingerprint"] == second["fingerprint"]
