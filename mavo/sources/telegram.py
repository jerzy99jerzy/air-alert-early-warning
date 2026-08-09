"""Public Telegram channel adapter.

Both Ukrainian APIs draw on the same public channel, so this adapter reaches the
shared upstream directly and removes the API tokens from the critical path. It
buys no independence: a wrong or silent upstream is wrong or silent here too.
See threat-model row MT9.

**What is tested and what is not.** Parsing, classification, hostile input and
idempotence are tested against an injected transport. That a live channel emits
the shapes the patterns expect is **not** tested and cannot be from here. Every
message that matches nothing is counted as unparsed and reported, never dropped,
so the gap between the table and reality is visible in the output instead of
being silently absorbed.

**Messages are parsed per block, not by a page-wide scan.** Until 0.6.0.0 a
single regex required ``<time>`` to precede the text div. On the live page the
time element sits in the message *footer*, after the text, so the scan paired
message N's timestamp with message N+1's text, dropped the first text on the
page, and orphaned the last timestamp — a systematic one-message shift in
``ts_source`` on every live poll (F50). The suite did not catch it because the
page fixture was synthetic and written in the regex's order rather than the
channel's: a fixture that encodes the code's assumption measures the code
against itself. Each message is now isolated by its ``data-post`` anchor and its
timestamp and text are located *within* that block, in either order, so the
pairing cannot cross a message boundary by construction. The fixture is a page
in the live footer-time order, and harness attack A12 holds the pairing.
"""

from __future__ import annotations

import html as html_
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from mavo.areas import AreaTable
from mavo.schema import AlertState, Provenance, ThreatEvent, ThreatKind
from mavo.transport import Transport

CHANNEL_URL = "https://t.me/s/air_alert_ua"

# F27. The page serves a window of roughly twenty messages, so a poll interval
# that is comfortable at rest can skip messages during a mass alert. The post id
# is the only thing that makes a skip observable; without it a gap and a quiet
# channel are the same picture.
POST_ID = re.compile(r'data-post="[^"/]+/(\d+)"')

# F50. One message block spans from its data-post anchor to the next (or the end
# of the page). Timestamp and text are searched inside the block only, so the
# pairing is correct in both the live order (text, then time in the footer) and
# the inverted order the old fixture assumed.
_BLOCK = re.compile(r'data-post="[^"/]+/\d+"(.*?)(?=data-post="[^"/]+/\d+"|\Z)', re.S)
_TEXT = re.compile(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', re.S)
_TIME = re.compile(r'<time[^>]*datetime="([^"]+)"')

_TAG = re.compile(r"<[^>]+>")
_BR = re.compile(r"<br\s*/?>", re.I)

# Area patterns. Unverified against live traffic; see the module docstring.
AREAS: dict[str, str] = {
    "волин": "volyn",
    "льв": "lviv",
    "закарпат": "zakarpattia",
    "рівнен": "rivne",
    # "тернопіль" is not listed beside "тернопіл": the longer stem is a
    # superstring of the shorter, so it can never match a text the shorter
    # missed. A dead row in a measured pattern table is noise (F50 review).
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
    # "кабів" is a superstring of "каб" and therefore unreachable; only the
    # shorter stem is kept. The stem is three characters and deliberately so:
    # false hits are a measured question for the corpus, not a guess to encode.
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
    # Sprint 7. Tags the area table did not know. A new tag is a finding, not a
    # fallback (T33): either the channel named a new area or a name drifted, and
    # both are things a reader of this report must be told rather than have
    # absorbed into an unparsed count.
    unknown_tags: tuple[str, ...] = field(default_factory=tuple)

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


def _strip(raw: str) -> str:
    """HTML fragment to text: line breaks kept, tags to spaces, entities decoded.

    ``html.unescape`` replaces a hand-rolled entity map that silently missed
    numeric entities (``&#8217;`` and kin), which Ukrainian text emits. It runs
    *after* tag stripping so a decoded ``&lt;`` cannot resurrect a tag. ``<br>``
    with or without the slash becomes a newline rather than a space, because the
    classifier redesign reads line structure: "рух на місто" is a second line.
    """
    text = _BR.sub("\n", raw)
    text = _TAG.sub(" ", text)
    return html_.unescape(text)


def _parse_timestamp(raw: str) -> datetime | None:
    """An aware datetime, or None. A naive one is None, not a value.

    F61. ``datetime="2026-09-01T21:00:00"`` parses cleanly and yields a naive
    timestamp, which the store refuses at ``append`` (F52). Letting it through
    here converts malformed *content* into an *outage* one layer up, in exactly
    the composition the never-raise contract exists to prevent. The live page
    always carries an offset, so a timestamp without one is malformed by the
    same standard as ``"nonsense"`` and takes the same path: unparsed, counted,
    reported.
    """
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return parsed if parsed.tzinfo is not None else None


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


def classify(
    text: str, areas: AreaTable | None = None
) -> tuple[str, AlertState, ThreatKind] | None:
    """Map one message to an area, a state and a means. None when nothing matches.

    Returns None rather than a default: an unclassified message is unknown, and
    an unknown that resolves to a state is the defect this project is built
    around.

    **Sprint 7 changed where the area comes from.** When an ``AreaTable`` is
    supplied, the area is the first tag the channel itself attached, resolved
    through the versioned map. The oblast-name table below remains only as the
    fallback for messages carrying no tag at all, which is 0.66% of the design
    window and is being read by hand under T34. The fallback is kept rather than
    deleted because deleting it would silently change what an untagged message
    means before anyone has looked at one.
    """
    lowered = text.lower()

    area: str | None = None
    if areas is not None:
        resolved, unknown = areas.resolve_all(text)
        if resolved:
            area = resolved[0].code
        elif unknown:
            # F60. The channel named an area and the map did not know it. Falling
            # back to the oblast table here would answer a question the channel
            # already answered, with a guess drawn from the table that scores 0
            # of 20 (F23), and the unknown tag would leave no mark on the result.
            # The fallback exists for messages with no tags at all, and only for
            # those.
            return None
    if area is None:
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

    def __init__(
        self,
        transport: Transport,
        url: str = CHANNEL_URL,
        areas: AreaTable | None = None,
    ) -> None:
        self.transport = transport
        self.url = url
        self.areas = areas
        self.report = ParseReport()
        self._last_id: int | None = None

    def _window(self, body: str) -> tuple[int | None, int | None, int | None]:
        """Post-id bounds of this page and how many messages were skipped.

        Returns ``None`` for the skipped count whenever it cannot be measured
        rather than assuming continuity. The two cases are a first poll, which
        has no baseline, and a page without post ids, which is what a hostile or
        restructured page looks like.
        """
        ids = sorted(int(found) for found in POST_ID.findall(body))
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
        unknown_tags: list[str] = []
        found = _BLOCK.findall(body)

        for block in found:
            text_match = _TEXT.search(block)
            time_match = _TIME.search(block)
            text = _strip(text_match.group(1)).strip() if text_match else "(no text div)"
            ts = _parse_timestamp(time_match.group(1)) if time_match else None
            if self.areas is not None:
                _resolved, unknown = self.areas.resolve_all(text)
                unknown_tags.extend(tag for tag in unknown if tag not in unknown_tags)
            classified = classify(text, self.areas)
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
            unknown_tags=tuple(unknown_tags),
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
    source.poll()
    elapsed = (datetime.now(UTC) - started).total_seconds()
    return source.report, elapsed
