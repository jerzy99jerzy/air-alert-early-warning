"""Retrieve channel history backwards, one twenty-message page at a time.

Until 0.5.0.0 this repository held that the corpus could only be collected
forward in time, because the channel page is a window. That was a claim about
`mavo collect`, not about the channel, and it was wrong: the web preview accepts
a `before` parameter and pages backwards through the full history. Measured
2026-08-09 against the live channel, which reported 321,498 posts and a page size
of exactly 20.

The consequence is a reordering, not an optimisation. A corpus that must be
awaited sets the schedule; a corpus that can be fetched does not.

This module writes raw pages and nothing else. It does not parse, classify or
store events, because the reason the corpus exists is that the parser is wrong
(F23), and a corpus filtered through the thing it is meant to fix is not
evidence. Parsing happens later, from disk, as many times as the redesign needs.
"""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from mavo.errors import SourceUnavailable
from mavo.sources.telegram import _BLOCK, _TEXT, _TIME, CHANNEL_URL, POST_ID, _parse_timestamp
from mavo.transport import Transport

# Measured, not assumed: the preview served exactly 20 posts per page on
# 2026-08-09. Treated as an observation rather than a constant, so a page that
# comes back a different size is visible rather than silently absorbed.
OBSERVED_PAGE_SIZE = 20

# Deliberately slow. The tolerated rate is unknown, and the cost of finding out
# by being blocked is losing access to the only corpus this project has.
DEFAULT_DELAY_S = 1.0

_TIMESTAMP = re.compile(r'<time[^>]*datetime="([^"]+)"')

# The one grammar for snapshot names. `_snapshot_path` writes it and every
# reader parses it with this pattern; five tools carried their own copy of
# this regex, which is the drift class F36 names, one character at a time.
SNAPSHOT_NAME = re.compile(r"page-(\d+)-(\d+)\.html$")


@dataclass(frozen=True, slots=True)
class Page:
    """One fetched page of history, before anything has been parsed out of it."""

    first_id: int
    last_id: int
    body: str
    timestamps: tuple[str, ...] = field(default_factory=tuple)

    @property
    def size(self) -> int:
        """How many posts this page carried."""
        return self.last_id - self.first_id + 1

    @property
    def post_count(self) -> int:
        """How many post ids were actually present, which may be fewer."""
        return len(set(POST_ID.findall(self.body)))


@dataclass(frozen=True, slots=True)
class BackfillReport:
    """What a backfill run retrieved, and where it stopped.

    ``stopped_because`` is always populated. A run that ends without a stated
    reason is indistinguishable from a run that was interrupted, and this
    repository has already shipped one defect of that shape (F27).
    """

    pages: int
    posts: int
    lowest_id: int | None
    highest_id: int | None
    earliest_ts: str | None
    latest_ts: str | None
    written: tuple[Path, ...]
    skipped_existing: int
    stopped_because: str

    def summary(self) -> str:
        """One block, with unknown printed as unknown."""
        span = (
            f"{self.earliest_ts} to {self.latest_ts}"
            if self.earliest_ts and self.latest_ts
            else "unknown"
        )
        return (
            f"pages={self.pages} posts={self.posts} "
            f"ids={self.lowest_id}..{self.highest_id} span={span}\n"
            f"written={len(self.written)} already_on_disk={self.skipped_existing}\n"
            f"stopped: {self.stopped_because}"
        )


def page_url(channel_url: str, before: int | None) -> str:
    """URL for one page of history, or the newest page when ``before`` is None."""
    return channel_url if before is None else f"{channel_url}?before={before}"


def fetch_page(transport: Transport, channel_url: str, before: int | None) -> Page | None:
    """Fetch one page. None when the page carries no posts at all.

    Returning None rather than an empty ``Page`` keeps "the channel ended" and
    "the page was unreadable" from collapsing into one value; the caller decides
    which it was from the surrounding context and records it.
    """
    body = transport.fetch(page_url(channel_url, before))
    ids = sorted({int(found) for found in POST_ID.findall(body)})
    if not ids:
        return None
    return Page(
        first_id=ids[0],
        last_id=ids[-1],
        body=body,
        timestamps=tuple(_TIMESTAMP.findall(body)),
    )


def _snapshot_path(directory: Path, page: Page) -> Path:
    """Deterministic name, so a re-run recognises what it already has.

    Keyed by the id range rather than by fetch time: the same page fetched twice
    is the same evidence, and naming it by clock time would turn idempotence into
    duplication.
    """
    return directory / f"page-{page.first_id:09d}-{page.last_id:09d}.html"


def backfill(
    transport: Transport,
    directory: Path,
    *,
    max_pages: int,
    before: int | None = None,
    channel_url: str = CHANNEL_URL,
    delay_s: float = DEFAULT_DELAY_S,
    sleep: Callable[[float], None] = time.sleep,
    stop_at_id: int | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> BackfillReport:
    """Walk history backwards, writing each page verbatim.

    Stops on the first of: ``max_pages`` reached, a page below ``stop_at_id``, a
    page with no posts, a page that does not move backwards, or an unreachable
    source. The reason is recorded either way.

    A page that fails to move backwards is a refusal rather than a retry. The
    alternative is a loop that fetches the same page until the page count runs
    out and then reports a number of pages that is true and a coverage that is
    not.

    An operator interrupting the run is the sixth stop condition and the most
    common one in practice. It was not one of the five until 0.5.3.0, so
    ``KeyboardInterrupt`` travelled through this function and a run that had
    retrieved 1150 pages reported a stack trace instead of saying so (F46).
    """
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    timestamps: list[str] = []
    pages = posts = skipped = 0
    lowest: int | None = None
    highest: int | None = None
    cursor = before
    reason = f"reached max_pages={max_pages}"

    for _ in range(max_pages):
        try:
            page = fetch_page(transport, channel_url, cursor)
        except SourceUnavailable as unreachable:
            reason = f"source unreachable: {unreachable}"
            break
        except KeyboardInterrupt:
            reason = f"interrupted by the operator after {pages} page(s)"
            break
        if page is None:
            reason = "page carried no posts; treating as the start of history"
            break
        if cursor is not None and page.first_id >= cursor:
            reason = (
                f"page did not move backwards (asked before={cursor}, "
                f"got {page.first_id}..{page.last_id})"
            )
            break

        destination = _snapshot_path(directory, page)
        if destination.exists():
            skipped += 1
        else:
            # Atomic: write to a sibling and rename. A plain write interrupted
            # mid-stream leaves a truncated snapshot whose *name* claims the
            # full id range; `--resume` then skips it as already retrieved and
            # `contiguity_gaps`, which reads ranges from names, cannot see the
            # hole. A census with a hole it cannot see is the defect class this
            # module exists to refuse (F51). `os.replace` is atomic on POSIX;
            # the temporary suffix keeps a crashed leftover out of the
            # `page-*.html` glob every reader uses.
            scratch = destination.with_name(destination.name + ".tmp")
            scratch.write_text(page.body, encoding="utf-8")
            os.replace(scratch, destination)
            written.append(destination)

        pages += 1
        posts += page.post_count
        timestamps.extend(page.timestamps)
        lowest = page.first_id if lowest is None else min(lowest, page.first_id)
        highest = page.last_id if highest is None else max(highest, page.last_id)
        cursor = page.first_id
        if progress is not None:
            progress(pages, page.first_id)

        if stop_at_id is not None and page.first_id <= stop_at_id:
            reason = f"reached stop_at_id={stop_at_id}"
            break
        if delay_s > 0:
            try:
                sleep(delay_s)
            except KeyboardInterrupt:
                reason = f"interrupted by the operator after {pages} page(s)"
                break

    ordered = sorted(timestamps)
    return BackfillReport(
        pages=pages,
        posts=posts,
        lowest_id=lowest,
        highest_id=highest,
        earliest_ts=ordered[0] if ordered else None,
        latest_ts=ordered[-1] if ordered else None,
        written=tuple(written),
        skipped_existing=skipped,
        stopped_because=reason,
    )


class DirectoryBusy(RuntimeError):
    """Another process holds this output directory.

    A refusal rather than a warning. Two runs against one directory do not
    corrupt the corpus, because snapshot names are derived from id ranges, but
    they double the request rate against a service whose tolerance for the
    single rate is measured only over a burst (T21). Discovered by doing it
    (F47).
    """


class DirectoryLock:
    """Advisory lock over an output directory, holding the owning pid.

    Advisory rather than enforced by the filesystem: this guards against the
    operator starting a second run, which is what happened, and not against an
    adversary. A stale lock from a killed process is detected by checking
    whether that pid is alive, and is taken over rather than requiring a manual
    cleanup step nobody will remember at 02:00.
    """

    def __init__(self, directory: Path) -> None:
        self.path = directory / ".backfill.lock"
        self.acquired = False

    def _holder(self) -> int | None:
        try:
            return int(self.path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None

    @staticmethod
    def _alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def acquire(self, pid: int | None = None) -> None:
        """Take the lock, or raise ``DirectoryBusy`` naming the holder.

        Creation is ``O_CREAT | O_EXCL``, so two processes racing an absent lock
        cannot both win: exactly one creates the file, the other lands in the
        holder check. The previous check-then-write had that window open; within
        the stated scope (operator error, not an adversary) it never fired, but
        the atomic form costs three lines and closes it outright.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        me = pid or os.getpid()
        try:
            handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            holder = self._holder()
            if holder is not None and holder != me and self._alive(holder):
                raise DirectoryBusy(
                    f"{self.path.parent} is held by pid {holder}. Two runs against one "
                    "directory double the request rate against a service whose tolerance "
                    "was measured over a burst of twenty"
                ) from None
            # Stale (dead pid) or our own: take over rather than demanding a
            # manual cleanup step nobody will remember at 02:00.
            self.path.write_text(str(me), encoding="utf-8")
        else:
            with os.fdopen(handle, "w", encoding="utf-8") as lockfile:
                lockfile.write(str(me))
        self.acquired = True

    def release(self) -> None:
        """Drop the lock if this object took it."""
        if self.acquired:
            self.path.unlink(missing_ok=True)
            self.acquired = False

    def __enter__(self) -> DirectoryLock:
        self.acquire()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()


def lowest_on_disk(directory: Path) -> int | None:
    """Lowest post id already retrieved into ``directory``, or None if empty.

    Resuming is explicit rather than automatic. A command that silently changes
    where it starts based on directory contents is a command whose output cannot
    be read without also reading the directory, and this one is meant to be run
    from a script.
    """
    lowest: int | None = None
    for snapshot in directory.glob("page-*.html"):
        match = SNAPSHOT_NAME.search(snapshot.name)
        if match is None:
            continue
        first = int(match.group(1))
        lowest = first if lowest is None else min(lowest, first)
    return lowest


def contiguity_gaps(directory: Path) -> Iterator[tuple[int, int]]:
    """Yield id ranges present in no snapshot on disk.

    The point of the corpus is that it is a census rather than a sample, and a
    census with holes it cannot see is a sample that believes otherwise. Named
    ranges, not a boolean: a hole of four posts and a hole of four thousand are
    different findings.
    """
    ranges: list[tuple[int, int]] = []
    for snapshot in sorted(directory.glob("page-*.html")):
        match = SNAPSHOT_NAME.search(snapshot.name)
        if match is None:
            continue
        ranges.append((int(match.group(1)), int(match.group(2))))
    ranges.sort()
    for (_, previous_last), (next_first, _) in zip(ranges, ranges[1:], strict=False):
        if next_first > previous_last + 1:
            yield previous_last + 1, next_first - 1


def read_snapshot_messages(directory: Path) -> list[tuple[datetime, str]]:
    """Every message in every snapshot under `directory`, deduplicated by post id.

    Moved into the package at 0.31.0.0 from `tools/kind_coverage.py`, where it
    was the only reader of the corpus. A second tool needed it, `tools/` cannot
    become an importable package without breaking `check_single_namespace`, and
    a copied reader is two readers that can disagree about what the corpus
    contains while both report confidently. One reader, one answer.

    The body is unchanged by the move. The measurements already published from
    `kind_coverage` were taken with this code and are not invalidated by its
    address, but that is an argument and not a re-run: the corpus is tier 1 and
    not in the tree, so no gate here can confirm it. `test_backfill_reader`
    pins the behaviour against a synthetic snapshot so a future edit cannot
    change it silently, which is the part that is checkable.
    """
    seen: dict[str, tuple[datetime, str]] = {}
    for snapshot in sorted(directory.glob("page-*.html")):
        if SNAPSHOT_NAME.search(snapshot.name) is None:
            continue
        body = snapshot.read_text(encoding="utf-8", errors="replace")
        for block in _BLOCK.finditer(body):
            chunk = block.group(0)
            post = re.search(r'data-post="[^/]+/(\d+)"', chunk)
            text_match = _TEXT.search(chunk)
            time_match = _TIME.search(chunk)
            if post is None or text_match is None or time_match is None:
                continue
            ts = _parse_timestamp(time_match.group(1))
            if ts is None:
                continue
            seen[post.group(1)] = (ts, re.sub(r"<[^>]+>", " ", text_match.group(1)))
    return sorted(seen.values())
