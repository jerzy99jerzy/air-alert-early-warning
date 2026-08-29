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
page, and orphaned the last timestamp - a systematic one-message shift in
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

from mavo.areas import CONTINUES, AreaTable, oblast_slug
from mavo.schema import (
    AlertState,
    AreaRole,
    KindEvent,
    KindState,
    Provenance,
    ThreatEvent,
    ThreatKind,
)
from mavo.transport import Transport

CHANNEL_URL = "https://t.me/s/air_alert_ua"

#: The name this feed carries in `feed_attempts` (D-036). Beside
#: `mavo.sources.rso.FEED`, and defined here for the same reason: the
#: string that keys a table of attempts belongs with the adapter that
#: makes them, not with the command that happens to call it today.
FEED = "channel"

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

# The oblast-stem area table lived here until 0.22.0.0 and is deleted rather
# than kept beside its replacement. It scored 0 of 20 against real channel
# content (F23) because the channel names raions and hromadas, and it survived
# sprint 7 as the `areas=None` default - which `probe`, the whole live path,
# selected by omission (F90). A superseded implementation left reachable is not
# a fallback, it is the version that ships to whoever forgets an argument.
# `AreaTable.from_csv()` is the only area table now.

START_MARKERS = ("повітряна тривога", "оголошено тривогу")
CLEAR_MARKERS = ("відбій тривоги", "відбій повітряної тривоги")

# F26. An all-clear that says the alert continues. The channel emits this as a
# yellow message; reading it as CLEAR would be actively wrong, and reading it as
# UNKNOWN would discard the fact that the source spoke.
CONTINUES_MARKERS = ("тривога ще триває", "тривога триває")

# T16. A threat-kind message is its own class, with its own verbs. "Відбій
# загрози" lifts a means of attack; "Відбій тривоги" clears an alert. The two
# differ by one word and mean different things about different lifetimes, which
# is exactly the kind of distinction this project loses when it reads for the
# marker it expects instead of the one that is there.
#
# Provenance, 0.19.3.0: these tables were written from the F25 examples and the
# author's knowledge of the language, then **measured** by
# `tools/kind_coverage.py` over 61,041 messages on 2026-08-10 (F71). The
# measurement is what the current entries answer to, and it found four ways the
# original table refused messages the channel was plainly making:
#
#   `Атака дронів-камікадзе`      declare marker hit, no kind: `дрон` absent
#   `Загроза балістики`           no declare marker at all: only the longer
#                                 `загроза застосування` / `загроза удар` forms
#                                 were listed
#   `Загроза керованих авіабомб`  same, and `авіабомб` was absent
#   `Відбій загрози артобстрілу`  lift hit, no kind: artillery had no member
#
# The consequence measured before the repair: MISSILE resolved on 25 of 2,392
# declarations, 1.0%, because the channel announces ballistics in the short
# form. The only rule that has ever passed its own regime gate (7 of 7) was
# therefore invisible to the join almost every time it applied.
#
# `загроза` replaces the two longer declare forms rather than joining them:
# they are its superstrings and therefore unreachable, the same reasoning that
# keeps `каб` and drops `кабів`. Breadth is bounded on the other side: a
# declaration needs a declare marker **and** exactly one kind marker, so
# `загроза` on its own resolves nothing.
#
# Lift is evaluated before declaration, so a message containing both reads as a
# lift. That ordering is what keeps the inversion risk named below from firing.
#
# **Status of the new entries: [assumption, unmeasured].** They are derived
# from corpus text quoted in F71, which is evidence for the four forms above
# and evidence for nothing else. The measurement that would replace this label
# is a second `kind_coverage` run on the same corpus, and the acceptance is
# stated in T45: coverage and per-marker hit counts before and after, with
# near-misses reviewed by hand.
#
# Both named risks have now been measured twice, and both are resolved:
# (1) `небезпека` returned **zero** hits on 2026-08-10 and again after the
# repair, on a table that had otherwise changed substantially. Dead rather
# than over-broad, and removed at 0.19.4.0 rather than kept as a hedge: a
# marker that has never matched anything is a claim about the channel that the
# channel keeps refusing.
# (2) the lift table did assume every lift says `відбій загрози`, and the
# near-miss pile showed three other phrasings. Widened to `відбій` at
# 0.19.4.0, which is what makes the ordering below load-bearing rather than
# incidental.
KIND_DECLARE_MARKERS = ("загроза", "атака дрон", "напрямок")
#
# `напрямок` added at 0.27.0.0, from live evidence rather than from the corpus.
#
# **What was measured.** On the production host, every poll between 2026-08-11
# and 2026-08-12 reported two unparsed messages out of twenty, and both were
# the same shape: `🟠 22:05 КАБ напрямок Краматорськ #Донецька_область`. The
# channel names a munition and a direction and no declaration word, so the
# message carried a kind marker, failed the declare test, carried no alert
# state either, and was counted as unparsed on every single poll for a day.
#
# **Why this marker rather than the one T46 proposed.** T46 offers treating
# the name of a munition as a declaration in its own right, and warns that
# doing so would classify summaries and after-action reports. `напрямок`
# is narrower: it is a word about a thing in flight *now*, not a word that
# appears in a retrospective count. The broader claim stays refused.
#
# **The ordering T46 requires re-checking rather than assuming.** Checked by
# reading `classify_kind_message`: `lifting` is evaluated first and the declare
# test runs only under `not lifting`, so a lift message containing `напрямок`
# reads as a lift. The inversion this file has warned about twice cannot fire
# through this entry.
#
# **Status: [assumption, unmeasured].** The prevalence of this shape across the
# corpus is unknown, and so is its false-positive rate. Two messages per
# twenty-message window over one day is evidence that the shape exists and
# recurs, and evidence for nothing about its frequency across 118 nights. The
# measurement that replaces this label is a `kind_coverage` run before and
# after on the same corpus, with near-misses reviewed by hand: the acceptance
# T45 already states, applied to one more marker.
# 0.19.4.0. `відбій` alone, because the channel lifts a threat in at least
# four phrasings and only one of them was listed: `відбій загрози`,
# `відбій атаки дронів-камікадзе`, `відбій атак дронів`, `відбій по КАБам`,
# all measured in the near-miss pile on 2026-08-10. The narrow marker dropped
# the other three.
#
# **This table must stay ahead of the declare table, and the order is a safety
# property rather than a preference.** `Відбій атаки дронів-камікадзе` carries
# no declare marker today only because `атака дрон` does not match `атаки
# дронів`: an accident of declension. The obvious next improvement, adding
# `атак` so that `Атака ударних БПЛА` resolves, would turn every one of those
# lifts into a fresh DECLARED, which is the inversion this file has warned
# about since T16 and the worst failure available here. Lift is evaluated
# first in `classify_kind_message`, so a message carrying both reads as a
# lift; that ordering plus this marker is what makes the declare extension
# safe to consider at all. It is not in this release: it needs its own
# measurement (T45, second run).
KIND_LIFT_MARKERS = ("відбій",)

KIND_MARKERS: dict[str, ThreatKind] = {
    # `баліст` rather than `балістик`: the channel writes both the noun
    # (`балістики`) and the adjective (`балістичного озброєння`), and the
    # longer stem misses every adjectival form. Found while testing the repair
    # against the forms quoted in F71, which is one form later than the
    # measurement that motivated it.
    "баліст": ThreatKind.MISSILE,
    "ракет": ThreatKind.MISSILE,
    "бпла": ThreatKind.DRONE,
    "шахед": ThreatKind.DRONE,
    "дрон": ThreatKind.DRONE,
    "авіабомб": ThreatKind.GLIDE_BOMB,
    "артобстріл": ThreatKind.ARTILLERY,
    "артилерійськ": ThreatKind.ARTILLERY,
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


def classify_kind_message(
    text: str, areas: AreaTable | None = None
) -> tuple[tuple[str, str, ThreatKind, KindState], ...]:
    """Areas, oblasts and the means of attack a kind message declares or lifts.

    Returns nothing for an alert message, so the two readers cannot both claim
    the same text: a message carrying an alert state is an alert, whatever else
    it mentions. Until 0.14.0.0 these messages parsed as nothing at all and were
    counted as unparsed, which was honest and lossy at the same time.
    """
    lowered = text.lower()
    if classify_state(text) is not None:
        return ()
    lifting = any(marker in lowered for marker in KIND_LIFT_MARKERS)
    if not lifting and not any(marker in lowered for marker in KIND_DECLARE_MARKERS):
        return ()
    kinds = {value for pattern, value in KIND_MARKERS.items() if pattern in lowered}
    if len(kinds) != 1:
        # Naming no means, or two, is not a declaration this can act on. The
        # message is still unparsed rather than resolved to a guess.
        return ()
    kind = next(iter(kinds))
    state = KindState.LIFTED if lifting else KindState.DECLARED

    # F90, same default. A missing table used to silence the kind stream too.
    resolved, _unknown = (areas if areas is not None else AreaTable.from_csv()).resolve_all(text)
    return tuple(
        (ref.code, oblast_slug(ref.oblast), kind, state) for ref in resolved
    )


@dataclass(frozen=True, slots=True)
class AreaMention:
    """One area a message named, with the state and role it named it in."""

    area_id: str
    oblast: str
    state: AlertState
    kind: ThreatKind
    role: AreaRole


def classify_message(text: str, areas: AreaTable | None = None) -> tuple[AreaMention, ...]:
    """Every area a message named, not just the first one (T37).

    Two losses closed here, both measured over the design window and both
    previously invisible in the output rather than reported:

    **A message can name several areas.** 13.3% of comparable messages name two
    to eight, and the pipeline kept the first tag and dropped the rest. Each tag
    is now its own mention.

    **An all-clear can carry a continuation list.** 5.2% of comparable messages
    carry one, naming 4,064 areas in the design window, none of which reached
    the store. The tag names what was cleared; the prose after the continuation
    marker names where the alert is *still running*. They are written in
    different vocabularies - tags for the subject, prose for the list - so the
    tag path could not see the list at all.

    **Where the two overlap, the message contradicts itself and the weaker
    reading wins.** The real message that produced F26 clears one raion and
    lists that same raion as still under alert. That area is ``PARTIAL_CLEAR``,
    exactly as before: one area told two things that do not agree. Splitting it
    into a CLEAR row and an ACTIVE row would replace a stated contradiction with
    two confident claims, one of them wrong.

    Tags are read from the whole text, not from the part before the marker: the
    channel puts them last, after the continuation list, so a positional split
    would file the subject's own tag under the continuation.
    """
    lowered = text.lower()
    has_continues = any(marker in lowered for marker in CONTINUES_MARKERS)
    # The unattributed reading, deliberately not `classify_state`: that function
    # folds any continuation marker into PARTIAL_CLEAR for the whole message,
    # which was the only honest answer while nothing could tell *which* area the
    # continuation was about. Here it can, so the contradiction is resolved per
    # area and PARTIAL_CLEAR is kept for the two cases that are still genuinely
    # contradictory: an area that is both cleared and listed as still running,
    # and a continuation list that resolves to no area at all.
    if any(marker in lowered for marker in CLEAR_MARKERS):
        subject_state: AlertState | None = AlertState.CLEAR
    elif any(marker in lowered for marker in START_MARKERS):
        subject_state = AlertState.ACTIVE
    else:
        subject_state = None
    # F86. One kind or none, never the first row. The old `next()` resolved a
    # message naming two means to whichever marker was defined earlier in
    # KIND_MARKERS - a semantic decision hidden in a dict's insertion order,
    # and the opposite of the refusal `classify_kind_message` makes for the
    # same ambiguity three functions up. A message naming one means in two
    # forms still resolves: the set collapses rows that name the same kind.
    # How often the corpus does this is not measured here; see T45.
    named = {value for pattern, value in KIND_MARKERS.items() if pattern in lowered}
    kind = next(iter(named)) if len(named) == 1 else ThreatKind.UNKNOWN

    # F90. `areas=None` used to mean "fall back to the oblast-stem dict", which
    # made the superseded implementation the default and the shipped register
    # table the opt-in. Every caller that forgot the argument - `probe`, and the
    # two tests built to announce F23's closure - got sprint 6 behaviour and no
    # indication of it. None now means "load the shipped table", so forgetting
    # the argument is slow rather than wrong.
    table = areas if areas is not None else AreaTable.from_csv()
    resolved, unknown = table.resolve_all(text)
    split = CONTINUES.search(text)
    still_running = table.resolve_prose(text[split.end() :]) if split else ()
    continuing = {ref.code for ref in still_running}

    mentions: list[AreaMention] = []
    if resolved and subject_state is not None:
        for ref in resolved:
            contradicted = ref.code in continuing or (has_continues and not still_running)
            state = (
                AlertState.PARTIAL_CLEAR
                if contradicted and subject_state is AlertState.CLEAR
                else subject_state
            )
            mentions.append(
                AreaMention(ref.code, oblast_slug(ref.oblast), state, kind, AreaRole.SUBJECT)
            )
    elif unknown:
        # F60. The channel named an area the map cannot read. Falling through to
        # the prose path here would answer a question the channel already
        # answered, with a guess, and leave the unknown tag no mark on the
        # result. The whole message is refused; the tag is reported separately.
        return ()

    subjects = {mention.area_id for mention in mentions}
    for ref in still_running:
        if ref.code in subjects:
            continue
        # The alert is running there and the message said so. ACTIVE is what the
        # source stated, not an inference from the all-clear next to it.
        mentions.append(
            AreaMention(
                ref.code, oblast_slug(ref.oblast), AlertState.ACTIVE, kind, AreaRole.CONTINUATION
            )
        )
    return tuple(mentions)


def classify(
    text: str, areas: AreaTable | None = None
) -> tuple[str, AlertState, ThreatKind] | None:
    """The first area a message named, or None when it named none.

    Kept as the single-area reading for callers and tests that predate T37, and
    delegating rather than reimplementing: two functions deciding the same thing
    is how the state layer and the area layer drifted apart in the first place.
    A caller that wants everything the message said wants ``classify_message``.
    """
    mentions = classify_message(text, areas)
    if not mentions:
        return None
    first = mentions[0]
    return first.area_id, first.state, first.kind


class TelegramChannelSource:
    """A ``ThreatSource`` over a public Telegram channel page."""

    source_id = "telegram"

    def __init__(
        self,
        transport: Transport,
        url: str = CHANNEL_URL,
        areas: AreaTable | None = None,
        last_seen_id: int | None = None,
    ) -> None:
        self.transport = transport
        self.url = url
        # F90. This used to store the argument as given, and `probe` - the whole
        # live path, the thing `mavo collect` runs - passed nothing, so every
        # live poll ran the pre-sprint-7 oblast dict while the 127-row register
        # table sat unreachable. The default is now the shipped table: an
        # omitted argument costs a CSV read rather than two sprints of
        # capability.
        self.areas = areas if areas is not None else AreaTable.from_csv()
        # T16. The kind stream from the most recent poll, beside the alert
        # stream rather than inside it. Empty until the first poll, like report.
        self.kind_events: tuple[KindEvent, ...] = ()
        self.report = ParseReport()
        # F123. Seeded by the caller when a previous poll's bound is known.
        # `mavo-collect.service` is a `oneshot`, so without a seed this field
        # is None on every invocation the host has ever made and `skipped`
        # reads `unknown` forever - which it did, from deployment until
        # 0.42.0.0. The value comes from `feed_attempts` (D-036).
        self._last_id: int | None = last_seen_id

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
        # Written as `max(last, self._last_id or last)` until 0.42.0.0.
        # **That expression is not wrong and this is not a defect fix**: `or`
        # substitutes `last` when the cursor is None or 0, and `max(last, last)`
        # equals `max(last, 0)` for any positive id, so every input produced the
        # same value. It is rewritten because the `or` reads as a guard against
        # a falsy cursor and guards nothing, and this field is now seeded from
        # outside the process, where a reader has more reason to ask what a
        # zero would do. Checked before rewriting rather than claimed after.
        self._last_id = last if self._last_id is None else max(last, self._last_id)
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
        kind_events: list[KindEvent] = []
        unparsed: list[str] = []
        unknown_tags: list[str] = []
        found = _BLOCK.findall(body)

        for block in found:
            text_match = _TEXT.search(block)
            time_match = _TIME.search(block)
            text = _strip(text_match.group(1)).strip() if text_match else "(no text div)"
            ts = _parse_timestamp(time_match.group(1)) if time_match else None
            _resolved, unknown = self.areas.resolve_all(text)
            unknown_tags.extend(tag for tag in unknown if tag not in unknown_tags)
            declarations = classify_kind_message(text, self.areas)
            if ts is not None and declarations:
                # T16. The second stream. Kept beside `poll`'s return value
                # rather than mixed into it: an alert and a declaration are
                # different events with different lifetimes, and merging them is
                # the modelling error F25 recorded.
                kind_events.extend(
                    KindEvent(
                        area_id=area_id,
                        kind=kind,
                        state=state,
                        ts_source=ts,
                        ts_ingest=now,
                        source_id=self.source_id,
                        oblast=oblast,
                        raw_fields={"text": text[:200]},
                    )
                    for area_id, oblast, kind, state in declarations
                )
                continue
            mentions = classify_message(text, self.areas)
            if ts is None or not mentions:
                unparsed.append(text[:120])
                continue
            # One event per area the message named, not per message (T37). A
            # message naming eight raions is eight transitions; keeping the
            # first was a silent loss of seven.
            events.extend(
                ThreatEvent(
                    area_id=mention.area_id,
                    state=mention.state,
                    ts_source=ts,
                    ts_ingest=now,
                    source_id=self.source_id,
                    kind=mention.kind,
                    provenance=Provenance.REPORTED,
                    raw_fields={"text": text[:200]},
                    oblast=mention.oblast,
                    role=mention.role,
                )
                for mention in mentions
            )

        self.kind_events = tuple(kind_events)
        self.report = ParseReport(
            messages=len(found),
            parsed=len(found) - len(unparsed),
            unparsed=tuple(unparsed),
            first_id=first_id,
            last_id=last_id,
            skipped=skipped,
            unknown_tags=tuple(unknown_tags),
        )
        return events


def poll_once(
    transport: Transport,
    url: str = CHANNEL_URL,
    last_seen_id: int | None = None,
) -> tuple[TelegramChannelSource, Sequence[ThreatEvent], float]:
    """One fetch, returning the source, its events and how long it took.

    **F96.** This exists because `probe` threw the events away. It returned a
    count of what was understood and dropped the understanding, so the only
    live entry point in the product could report on the channel and could not
    record it. The source is returned rather than just the events because the
    declaration stream lives beside them on `source.kind_events`, and a caller
    that stores one and forgets the other has silently halved the record.

    Latency is returned rather than logged because it is subtracted directly
    from the warning budget: in the missile regime the whole budget is about six
    minutes.
    """
    source = TelegramChannelSource(transport, url, last_seen_id=last_seen_id)
    started = datetime.now(UTC)
    events = source.poll()
    elapsed = (datetime.now(UTC) - started).total_seconds()
    return source, events, elapsed


def probe(transport: Transport, url: str = CHANNEL_URL) -> tuple[ParseReport, float]:
    """One fetch, reporting what was understood and how long it took.

    Kept as the counting-only reading for callers that want the report and
    nothing else. It delegates rather than reimplementing: two functions
    polling the channel is how the two would eventually disagree.
    """
    source, _events, elapsed = poll_once(transport, url)
    return source.report, elapsed
