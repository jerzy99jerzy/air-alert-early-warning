"""The corpus reader, pinned where it now lives (0.31.0.0).

`read_snapshot_messages` moved from `tools/kind_coverage.py` into the package
so a second tool could use it without copying it. The published measurements in
`docs/METHODOLOGY.md` were taken with this code, and the corpus is tier 1 and
not in the tree, so no test here can confirm the move left those figures
unchanged. What a test can do is stop the next edit from changing the reader
quietly, and that is what these are for.

Each case below was chosen to fail against a plausible wrong implementation
rather than to exercise the happy path: the deduplication, the filename filter,
the tag stripping and the ordering are all things a rewrite would get subtly
wrong while still parsing the fixture.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from mavo.backfill import read_snapshot_messages


def _block(post_id: int, stamp: str, text: str) -> str:
    return (f'data-post="air_alert_ua/{post_id}"'
            f'<time datetime="{stamp}"></time>'
            f'<div class="tgme_widget_message_text js-message_text">{text}</div>')


def _write(directory: Path, name: str, *blocks: str) -> None:
    (directory / name).write_text("".join(blocks), encoding="utf-8")


def test_messages_are_returned_in_timestamp_order(tmp_path: Path) -> None:
    _write(tmp_path, "page-1-100.html",
           _block(2, "2026-08-01T21:00:00+00:00", "second"),
           _block(1, "2026-08-01T20:00:00+00:00", "first"))
    messages = read_snapshot_messages(tmp_path)
    assert [text.strip() for _, text in messages] == ["first", "second"]


def test_a_post_seen_twice_is_kept_once(tmp_path: Path) -> None:
    """Snapshots overlap by design; the reader must not double-count.

    The count matters: every share in the published measurements has this
    number underneath it, and a reader that counts a post twice inflates the
    denominator of everything at once.
    """
    _write(tmp_path, "page-1-100.html", _block(7, "2026-08-01T20:00:00+00:00", "once"))
    _write(tmp_path, "page-2-200.html", _block(7, "2026-08-01T20:00:00+00:00", "once"))
    assert len(read_snapshot_messages(tmp_path)) == 1


def test_files_not_matching_the_snapshot_name_are_ignored(tmp_path: Path) -> None:
    _write(tmp_path, "page-1-100.html", _block(1, "2026-08-01T20:00:00+00:00", "kept"))
    _write(tmp_path, "page-notes.html", _block(2, "2026-08-01T20:00:00+00:00", "ignored"))
    assert [text.strip() for _, text in read_snapshot_messages(tmp_path)] == ["kept"]


def test_markup_inside_the_message_is_stripped(tmp_path: Path) -> None:
    _write(tmp_path, "page-1-100.html",
           _block(1, "2026-08-01T20:00:00+00:00",
                  'Тривога <a href="x">#Харків_район</a><b>!</b>'))
    _, text = read_snapshot_messages(tmp_path)[0]
    assert "<" not in text and ">" not in text
    assert "#Харків_район" in text


def test_a_block_missing_its_timestamp_is_dropped_not_guessed(tmp_path: Path) -> None:
    """No timestamp, no message. Substituting the file's own mtime or `now`
    would put a real message at a wrong moment, which is worse than losing it:
    a wrong timestamp joins against the wrong alerts.

    Two shapes, because they hit different guards and the first version of this
    test only reached one. A block with no `<time>` element at all is rejected
    by the same check that rejects a block with no text; a block whose `<time>`
    is present but unparseable is the one that reaches the timestamp guard, and
    a mutation replacing that guard with `now` survived until this second case
    existed.
    """
    _write(tmp_path, "page-1-100.html",
           'data-post="air_alert_ua/1"'
           '<div class="tgme_widget_message_text js-message_text">no time element</div>',
           'data-post="air_alert_ua/2"'
           '<time datetime="not-a-timestamp"></time>'
           '<div class="tgme_widget_message_text js-message_text">unparseable time</div>',
           _block(3, "2026-08-01T20:00:00+00:00", "has time"))
    messages = read_snapshot_messages(tmp_path)
    assert [text.strip() for _, text in messages] == ["has time"]


def test_timestamps_are_parsed_rather_than_returned_as_text(tmp_path: Path) -> None:
    _write(tmp_path, "page-1-100.html", _block(1, "2026-08-01T20:30:00+00:00", "x"))
    stamp, _ = read_snapshot_messages(tmp_path)[0]
    assert isinstance(stamp, datetime)
    assert stamp.tzinfo is not None, "a naive timestamp would compare wrongly against alerts"


def test_an_empty_directory_returns_nothing_rather_than_failing(tmp_path: Path) -> None:
    assert read_snapshot_messages(tmp_path) == []
