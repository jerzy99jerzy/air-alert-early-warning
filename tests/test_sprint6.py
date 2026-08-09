"""Sprint 6 regression: the corpus is retrieved, not awaited.

Until this sprint the repository held that the corpus could only be collected
forward in time. That was true of `mavo collect` and false of the channel: the
web preview pages backwards, measured on 2026-08-09 against 321,498 posts with a
page size of exactly 20.

The defect class here is not the wrong belief. It is that the belief was written
into the schedule (T19, D-011) after one probe whose negative result would have
looked identical to a null result, and nothing re-probed it for two sprints
(F44). These tests pin the acquisition behaviour that replaced it.
"""

from __future__ import annotations

from pathlib import Path

from mavo.backfill import (
    backfill,
    contiguity_gaps,
    fetch_page,
    lowest_on_disk,
    page_url,
)
from mavo.transport import FailingTransport, StubTransport, Transport

TXT = '<div class="tgme_widget_message_text js-message_text">'


def _page(ids: list[int]) -> str:
    return "".join(
        f'<div class="tgme_widget_message" data-post="air_alert_ua/{post}">'
        f'<time datetime="2026-08-0{1 + (post % 9)}T21:00:00+00:00"></time>'
        f"{TXT}Львівська область<br/>Повітряна тривога</div></div>"
        for post in ids
    )


class WalkingTransport:
    """Serves twenty-post pages, honouring `before`, like the live preview."""

    def __init__(self, newest: int, oldest: int = 0, page_size: int = 20) -> None:
        self.newest = newest
        self.oldest = oldest
        self.page_size = page_size
        self.calls: list[str] = []

    def fetch(self, url: str) -> str:
        self.calls.append(url)
        before = self.newest + 1
        if "?before=" in url:
            before = int(url.split("?before=")[1])
        last = min(self.newest, before - 1)
        first = last - self.page_size + 1
        if last < self.oldest:
            return "<html>no posts</html>"
        return _page(list(range(max(first, self.oldest), last + 1)))


def test_the_url_carries_the_cursor_and_the_first_page_does_not() -> None:
    assert page_url("https://example.invalid/s/c", None) == "https://example.invalid/s/c"
    assert page_url("https://example.invalid/s/c", 300000).endswith("?before=300000")


def test_backfill_walks_backwards_and_writes_pages_verbatim(tmp_path: Path) -> None:
    transport = WalkingTransport(newest=1000)
    report = backfill(transport, tmp_path, max_pages=3, delay_s=0, sleep=lambda _: None)
    assert report.pages == 3
    assert report.posts == 60
    assert report.lowest_id == 941
    assert report.highest_id == 1000
    written = sorted(tmp_path.glob("page-*.html"))
    assert len(written) == 3
    # Verbatim: what the transport returned is what is on disk, unparsed. The
    # corpus exists because the parser is wrong, so a corpus filtered through the
    # parser is not evidence.
    assert 'data-post="air_alert_ua/1000"' in written[-1].read_text(encoding="utf-8")


def test_backfill_is_idempotent_across_runs(tmp_path: Path) -> None:
    # Named by id range rather than by clock time, so the same evidence fetched
    # twice is one file rather than two.
    first = backfill(WalkingTransport(newest=1000), tmp_path, max_pages=2,
                     delay_s=0, sleep=lambda _: None)
    second = backfill(WalkingTransport(newest=1000), tmp_path, max_pages=2,
                      delay_s=0, sleep=lambda _: None)
    assert len(first.written) == 2
    assert second.written == ()
    assert second.skipped_existing == 2
    assert len(list(tmp_path.glob("page-*.html"))) == 2


def test_backfill_refuses_a_cursor_that_does_not_move(tmp_path: Path) -> None:
    # The first probe of this feature asked `before=1000000` against a channel
    # whose newest post was 321498, got the newest page back, and could not tell
    # "the parameter works" from "the parameter is ignored" (F44). A loop that
    # retries here reports a page count that is true and a coverage that is not.
    stuck: Transport = StubTransport(_page(list(range(981, 1001))))
    report = backfill(stuck, tmp_path, max_pages=10, before=500,
                      delay_s=0, sleep=lambda _: None)
    assert report.pages == 0
    assert "did not move backwards" in report.stopped_because


def test_backfill_stops_at_the_start_of_history_and_says_so(tmp_path: Path) -> None:
    report = backfill(WalkingTransport(newest=1000, oldest=961), tmp_path,
                      max_pages=10, delay_s=0, sleep=lambda _: None)
    assert report.pages == 2
    assert "start of history" in report.stopped_because


def test_backfill_records_an_outage_rather_than_reporting_a_short_run(tmp_path: Path) -> None:
    # A run that stops because the source went away must not look like a run that
    # stopped because history ended. Same defect class as MT11.
    report = backfill(FailingTransport(), tmp_path, max_pages=5,
                      delay_s=0, sleep=lambda _: None)
    assert report.pages == 0
    assert "unreachable" in report.stopped_because


def test_backfill_honours_a_stop_id(tmp_path: Path) -> None:
    report = backfill(WalkingTransport(newest=1000), tmp_path, max_pages=50,
                      stop_at_id=960, delay_s=0, sleep=lambda _: None)
    assert report.stopped_because == "reached stop_at_id=960"
    # The page containing the stop id is fetched whole and kept whole. Truncating
    # it would mean writing a partial page to disk under a name that claims a
    # full id range, which is worse than overshooting by nineteen posts.
    assert report.lowest_id == 941


def test_backfill_reports_the_time_span_it_covered(tmp_path: Path) -> None:
    # How far back a page count reaches is a property of channel volume, not of
    # arithmetic. The run measures it instead of the operator estimating it.
    report = backfill(WalkingTransport(newest=1000), tmp_path, max_pages=2,
                      delay_s=0, sleep=lambda _: None)
    assert report.earliest_ts is not None
    assert report.latest_ts is not None
    assert report.earliest_ts <= report.latest_ts


def test_backfill_paces_itself(tmp_path: Path) -> None:
    # The tolerated request rate is unknown and the cost of discovering it by
    # being blocked is losing the only corpus this project has.
    slept: list[float] = []
    backfill(WalkingTransport(newest=1000), tmp_path, max_pages=3,
             delay_s=0.25, sleep=slept.append)
    assert slept == [0.25, 0.25, 0.25]


def test_a_hole_in_the_corpus_is_named_not_summarised(tmp_path: Path) -> None:
    # A census with holes it cannot see is a sample that believes otherwise.
    backfill(WalkingTransport(newest=1000), tmp_path, max_pages=1,
             delay_s=0, sleep=lambda _: None)
    backfill(WalkingTransport(newest=900), tmp_path, max_pages=1,
             delay_s=0, sleep=lambda _: None)
    gaps = list(contiguity_gaps(tmp_path))
    assert gaps == [(901, 980)]


def test_a_complete_walk_reports_no_holes(tmp_path: Path) -> None:
    backfill(WalkingTransport(newest=1000), tmp_path, max_pages=4,
             delay_s=0, sleep=lambda _: None)
    assert list(contiguity_gaps(tmp_path)) == []


def test_a_page_without_posts_is_none_rather_than_empty() -> None:
    # "The channel ended" and "the page was unreadable" must not collapse into
    # one value at the boundary.
    assert fetch_page(StubTransport("<html></html>"), "https://example.invalid", None) is None


def test_the_summary_prints_unknown_when_the_span_is_unknown() -> None:
    # A run that fetched nothing has no time span. It says unknown rather than
    # printing an empty range that reads like a measurement of zero.
    report = backfill(FailingTransport(), Path("/tmp"), max_pages=1,
                      delay_s=0, sleep=lambda _: None)
    assert "span=unknown" in report.summary()


def test_a_malformed_snapshot_name_is_skipped_not_guessed(tmp_path: Path) -> None:
    # Contiguity is computed from filenames. A file that does not carry an id
    # range contributes nothing rather than a guessed one.
    (tmp_path / "page-not-a-range.html").write_text("", encoding="utf-8")
    (tmp_path / "page-000000001-000000020.html").write_text("", encoding="utf-8")
    (tmp_path / "page-00000abc-0000def0.html").write_text("", encoding="utf-8")
    assert list(contiguity_gaps(tmp_path)) == []


def test_the_lowest_id_on_disk_is_found_and_malformed_names_ignored(tmp_path: Path) -> None:
    for name in ("page-000000100-000000119.html", "page-000000060-000000079.html",
                 "page-junk.html", "page-00000abc-0000def0.html"):
        (tmp_path / name).write_text("", encoding="utf-8")
    assert lowest_on_disk(tmp_path) == 60


def test_the_lowest_id_on_an_empty_directory_is_none(tmp_path: Path) -> None:
    # Not zero. There is no lowest id, which is different from a lowest id of 0.
    assert lowest_on_disk(tmp_path) is None
