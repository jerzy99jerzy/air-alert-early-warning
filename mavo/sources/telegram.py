"""Public Telegram channel adapter.

Both Ukrainian APIs draw on the same public channel, so this adapter reaches the
shared upstream directly and removes the API tokens from the critical path. It
buys no independence: a wrong or silent upstream is wrong or silent here too.
See threat-model row MT9.

**What is tested and what is not.** Parsing, classification, hostile input and
idempotence are tested against an injected transport. That a live channel emits
the shapes `PATTERNS` expects is **not** tested and cannot be from here. Every
message that matches nothing is counted as unparsed and reported, never dropped,
so the gap between the table and reality is visible in the output instead of
being silently absorbed.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from mavo.errors import SourceUnavailable
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind
from mavo.transport import Transport

CHANNEL_URL = "https://t.me/s/air_alert_ua"

_MESSAGE = re.compile(
    r'<time[^>]*datetime="([^"]+)"[^>]*>.*?'
    r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
    re.S,
)
# F27. The page serves a window of roughly twenty messages, so a poll interval
# that is comfortable at rest can skip messages during a mass alert. The post id
# is the only thing that makes a skip observable; without it a gap and a quiet
# channel are the same picture.
_POST_ID = re.compile(r'data-post="[^"/]+/(\d+)"')
_TAG = re.compile(r"<[^>]+>")
_ENTITY = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'", "<br/>": "\n"}

# Area patterns. Unverified against live traffic; see the module docstring.
AREAS: dict[str, str] = {
    "волин": "volyn",
    "льв": "lviv",
    "закарпат": "zakarpattia",
    "рівнен": "rivne",
    "тернопіль": "ternopil",
    "тернопіл": "ternopil",
    "івано-франків": "ivano-frankivsk",
}

START_MARKERS = ("повітряна тривога", "оголошено тривогу")
CLEAR_MARKERS = ("відбій тривоги", "відбій повітряної тривоги")

# F26. An all-clear that says the alert continues. The channel emits this as a
# yellow message; reading it as CLEAR would be actively wrong, and reading it as
# UNKNOWN would discard the fact that the source spoke.
CONTINUES_MARKERS = ("тривога ще триває", "тривога триває")

KIND_MARKERS: dict[str, ThreatKind] = {
    "балістик": ThreatKind.MISSILE,
    "ракет": ThreatKind.MISSILE,
    "бпла": ThreatKind.DRONE,
    "шахед": ThreatKind.DRONE,
    "кабів": ThreatKind.GLIDE_BOMB,
    "каб": ThreatKind.GLIDE_BOMB,
}


@dataclass(frozen=True, slots=True)
class ParseReport:
    """What the last poll understood, and what it did not.

    Unparsed messages are counted rather than discarded, because a silent drop
    turns a stale pattern table into an apparently quiet channel.

    ``skipped`` is the number of messages that passed between this poll and the
    previous one without being seen. **None means unknown, never zero.** It is
    unknown on the first poll of a source, because there is no baseline to
    measure against, and on any page that carries no post ids. Printing zero in
    either case would be the flattering default this project exists to refuse.
    """

    messages: int = 0
    parsed: int = 0
    unparsed: tuple[str, ...] = field(default_factory=tuple)
    first_id: int | None = None
    last_id: int | None = None
    skipped: int | None = None

    @property
    def unparsed_count(self) -> int:
        """How many messages matched no pattern."""
        return len(self.unparsed)

    @property
    def gap_is_known(self) -> bool:
        """Whether the skipped count is a measurement rather than an absence."""
        return self.skipped is not None

    def window_line(self) -> str:
        """One line describing the window, with unknown printed as unknown."""
        if self.skipped is None:
            return "skipped=unknown"
        return f"skipped={self.skipped}"


def _strip(html: str) -> str:
    text = html
    for entity, char in _ENTITY.items():
        text = text.replace(entity, char)
    return _TAG.sub(" ", text)


def _parse_timestamp(raw: str) -> datetime | None:
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def classify_state(text: str) -> AlertState | None:
    """Map one message to a state, or None when no state marker is present.

    Split out of ``classify`` in sprint 5 so the state layer can be measured
    independently of the area layer, which currently matches nothing (F23). It
    was the one layer of three that was already correct on real content, and it
    was only testable through a conjunct that fails.

    The partial check runs first and is decisive. A message carrying both an
    all-clear marker and a continuation marker is a contradiction, and the
    weaker reading has to win: a state that means "we were told the alert
    continues" must never be reachable from the branch that means "clear".
    """
    lowered = text.lower()
    has_clear = any(marker in lowered for marker in CLEAR_MARKERS)
    if has_clear and any(marker in lowered for marker in CONTINUES_MARKERS):
        return AlertState.PARTIAL_CLEAR
    if has_clear:
        return AlertState.CLEAR
    if any(marker in lowered for marker in START_MARKERS):
        return AlertState.ACTIVE
    return None


def classify(text: str) -> tuple[str, AlertState, ThreatKind] | None:
    """Map one message to an area, a state and a means. None when nothing matches.

    Returns None rather than a default: an unclassified message is unknown, and
    an unknown that resolves to a state is the defect this project is built
    around.
    """
    lowered = text.lower()

    area = next((code for pattern, code in AREAS.items() if pattern in lowered), None)
    if area is None:
        return None

    state = classify_state(text)
    if state is None:
        return None

    kind = next(
        (value for pattern, value in KIND_MARKERS.items() if pattern in lowered),
        ThreatKind.UNKNOWN,
    )
    return area, state, kind


class TelegramChannelSource:
    """A ``ThreatSource`` over a public Telegram channel page."""

    source_id = "telegram"

    def __init__(self, transport: Transport, url: str = CHANNEL_URL) -> None:
        self.transport = transport
        self.url = url
        self.report = ParseReport()
        self._last_id: int | None = None

    def _window(self, body: str) -> tuple[int | None, int | None, int | None]:
        """Post-id bounds of this page and how many messages were skipped.

        Returns ``None`` for the skipped count whenever it cannot be measured
        rather than assuming continuity. The two cases are a first poll, which
        has no baseline, and a page without post ids, which is what a hostile or
        restructured page looks like.
        """
        ids = sorted(int(found) for found in _POST_ID.findall(body))
        if not ids:
            return None, None, None
        first, last = ids[0], ids[-1]
        skipped: int | None = None
        if self._last_id is not None:
            skipped = max(0, first - self._last_id - 1)
        self._last_id = max(last, self._last_id or last)
        return first, last, skipped

    def poll(self) -> Sequence[ThreatEvent]:
        """Fetch and parse. Never raises on content, only on an unreachable source.

        A malformed body yields an empty result with an unparsed count, because a
        parser that raises converts a hostile string into an outage during
        exactly the window that matters.
        """
        body = self.transport.fetch(self.url)
        now = datetime.now(UTC)
        first_id, last_id, skipped = self._window(body)

        events: list[ThreatEvent] = []
        unparsed: list[str] = []
        found = _MESSAGE.findall(body)

        for raw_time, raw_html in found:
            text = _strip(raw_html).strip()
            ts = _parse_timestamp(raw_time)
            classified = classify(text)
            if ts is None or classified is None:
                unparsed.append(text[:120])
                continue
            area, state, kind = classified
            events.append(
                ThreatEvent(
                    area_id=area,
                    state=state,
                    ts_source=ts,
                    ts_ingest=now,
                    source_id=self.source_id,
                    kind=kind,
                    provenance=Provenance.REPORTED,
                    raw_fields={"text": text[:200]},
                )
            )

        self.report = ParseReport(
            messages=len(found),
            parsed=len(events),
            unparsed=tuple(unparsed),
            first_id=first_id,
            last_id=last_id,
            skipped=skipped,
        )
        return events


def probe(transport: Transport, url: str = CHANNEL_URL) -> tuple[ParseReport, float]:
    """One fetch, reporting what was understood and how long it took.

    Latency is returned rather than logged because it is subtracted directly
    from the warning budget: in the missile regime the whole budget is about six
    minutes.
    """
    source = TelegramChannelSource(transport, url)
    started = datetime.now(UTC)
    try:
        source.poll()
    except SourceUnavailable:
        raise
    elapsed = (datetime.now(UTC) - started).total_seconds()
    return source.report, elapsed
