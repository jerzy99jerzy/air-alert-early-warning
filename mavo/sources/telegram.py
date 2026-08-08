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
    """

    messages: int = 0
    parsed: int = 0
    unparsed: tuple[str, ...] = field(default_factory=tuple)

    @property
    def unparsed_count(self) -> int:
        """How many messages matched no pattern."""
        return len(self.unparsed)


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

    if any(marker in lowered for marker in CLEAR_MARKERS):
        state = AlertState.CLEAR
    elif any(marker in lowered for marker in START_MARKERS):
        state = AlertState.ACTIVE
    else:
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

    def poll(self) -> Sequence[ThreatEvent]:
        """Fetch and parse. Never raises on content, only on an unreachable source.

        A malformed body yields an empty result with an unparsed count, because a
        parser that raises converts a hostile string into an outage during
        exactly the window that matters.
        """
        body = self.transport.fetch(self.url)
        now = datetime.now(UTC)

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
            messages=len(found), parsed=len(events), unparsed=tuple(unparsed)
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
