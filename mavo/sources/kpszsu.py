"""The Ukrainian Air Force's morning summaries on `@kpszsu`, read into figures.

**The bound this module works inside** (D-056, the operator's rule of
2026-09-18). MAVO publishes nothing about the air war that the Air Force did
not publish itself. So this reader never estimates, never fills a gap from
another source and never computes a rate: it reads the figures the summary
states, keeps a count the summary does not state as unknown, and flags any
reading whose own arithmetic does not close. The one piece of arithmetic it
does is on their figures alone: a single unnumbered item closed by their own
total, marked as derived.

**Written on a corpus, not on a template.** The rules below were forced by 98
summary messages from 2026-06-24 to 2026-09-22 and by eighteen of them read by
hand, and each rule names what it cost to learn:

- three shapes: prose; a list after `противник атакував:`; and a combined
  report recognised by its inventory `Усього ... зафіксовано N засобів`, not
  by its opening phrase, which on 01.08 was not the one the other four used;
- counts written as words (`одну`, `шістьма`, `8-ма`), which a digits-only
  reader drops without a sound;
- designations carrying digits (`Х-101`, `3М22`, `S8000`, `KN-23`) that are
  never counts;
- parentheses holding shares (`64 із них - реактивні`), never counts;
- the figure opening a section is that section's total, not a type;
- one phrase naming several items, only the first of them counted: each later
  item of a different class is kept, with its count unknown.

**What this cannot tell you.** Whether a shape the 91 nights do not hold will
read correctly. The checks make a new shape loud rather than readable, and the
launched side of a night without an inventory has no total to check against:
there it is held by the recordings in the suite and by the rule that nothing
is shot down in greater numbers than it was launched, and by nothing else.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from mavo.sources.telegram import _BLOCK, _TEXT, _TIME, POST_ID, _parse_timestamp, _strip
from mavo.transport import Transport

FEED = "kpszsu"
SOURCE_URL = "https://t.me/s/kpszsu"
POST_URL = "https://t.me/kpszsu/{post_id}"

#: Bumped whenever a rule below changes what a message reads as, and stored on
#: every row, so a figure read by an older rule can be told apart from a
#: figure read by this one. Versions 1 to 4 were a script outside the tree.
READER_VERSION = 5

#: The Air Force states its times in Kyiv time and names the night by the
#: Kyiv date it ends on.
KYIV = ZoneInfo("Europe/Kyiv")

#: Every case of one to ten, and `обидва`. A form missing here is a count read
#: as unknown, never as zero: `однієї ракети Онікс` (post 71719) was one until
#: the genitive feminine was added.
_WORDS = {
    **dict.fromkeys(("один", "одна", "одне", "одну", "одного", "одної", "однієї", "одному",
                     "одній", "одним", "однією"), 1),
    **dict.fromkeys(("два", "дві", "двох", "двом", "двома", "обидва", "обидві", "обох",
                     "обом", "обома"), 2),
    **dict.fromkeys(("три", "трьох", "трьом", "трьома"), 3),
    **dict.fromkeys(("чотири", "чотирьох", "чотирьом", "чотирма"), 4),
    **dict.fromkeys(("п'ять", "п'яти", "п'ятьом", "п'ятьма", "п'ятьох"), 5),
    **dict.fromkeys(("шість", "шести", "шістьом", "шістьма", "шістьох"), 6),
    **dict.fromkeys(("сім", "семи", "сімом", "сьома", "сімома", "сімох"), 7),
    **dict.fromkeys(("вісім", "восьми", "вісьмом", "вісьмома", "восьма", "вісьмох"), 8),
    **dict.fromkeys(("дев'ять", "дев'яти", "дев'ятьом", "дев'ятьма", "дев'ятьох"), 9),
    **dict.fromkeys(("десять", "десяти", "десятьом", "десятьма", "десятьох"), 10),
}
_MONTHS = {
    "січня": 1, "лютого": 2, "березня": 3, "квітня": 4, "травня": 5, "червня": 6,
    "липня": 7, "серпня": 8, "вересня": 9, "жовтня": 10, "листопада": 11, "грудня": 12,
}

#: The class vocabulary, an open enum mirroring the source's words (the rule
#: D-050 took for alert levels). Matched at the start of a word, so a stem
#: cannot fire inside an unrelated word; `каб` is matched as a whole word.
_CLASSES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("banderol", ("бандероль", "бандерол", "дань-т", "s8000")),
    ("drone", ("бпла", "дрон", "безпілотник", "shahed", "гербера", "італмас")),
    ("ballistic", ("балістичн",)),
    ("anti_ship", ("протикорабельн",)),
    ("anti_radar", ("протирадіолокаційн",)),
    ("cruise", ("крилат", "калібр", "х-101")),
    # `зенітними керованими ракетами С-400` (post 71936): a surface-to-air
    # missile fired at the ground. Ahead of `air_launched` in the text, so the
    # first hit names it rather than `керован`.
    ("sam", ("зенітн",)),
    ("air_launched", ("керован",)),
    ("kab", ("авіаційних бомб",)),
)
_CLASS_PATTERNS = tuple(
    (name, re.compile(r"(?<![\w'])" + re.escape(key), re.I))
    for name, keys in _CLASSES
    for key in keys
) + (("kab", re.compile(r"(?<![\w'])каб(?!\w)", re.I)),)

#: Items that are named inside a drone item as its kinds (`Shahed, Гербера,
#: S8000 "Бандероль"`) rather than as items of their own.
_DRONE_FAMILY = frozenset({"drone", "banderol"})

_APPROX = frozenset({"близько", "понад", "більше", "майже", "до"})
#: Words showing that a figure counts targets, locations or units rather than
#: a type of weapon: a section total (`збито/подавлено 177 цілей: ...`) or a
#: count of places.
_NOT_A_TYPE = ("ціл", "засоб", "локаці", "одиниц")
_MISSILE_WORD = "ракет"

_REFUSE_FIRST = "уточнена інформація"
_NIGHT = "у ніч на"
_DAY = "протягом дня"
_HEAD = "збито/подавлено"
_ATTACKED = "противник атакував"
_MASSED = "завдав масованого комбінованого удару"
_INVENTORY = re.compile(r"усього[^\n]{0,160}?зафіксовано[^\n]{0,40}?засоб")
_TOTALS = "зафіксовано"
_REPELLED = "повітряний напад відбивали"
_FIX = "зафіксовано влучання"
_DEBRIS = "падіння"
_ALSO = "а також"
_CONTINUES = "атака триває"
_USED = "ворог застосував"
_NOT_REACHED = "не досяг"
_DIRECTIONS = ("основні напрямки удару", "основний напрямок удару")

_TOKEN = re.compile(r"[\w'/\-:.]+")
_HYBRID = re.compile(r"^(\d{1,4})-(ма|ома|мя)$")
_STAMP = re.compile(r"станом на (\d{1,2})[:.](\d{2})")
_DATE = re.compile(r"(?:у ніч на|протягом дня)\s+(\d{1,2})\s+([а-яіїєґ']+)")
_LOCATIONS = re.compile(r"(\S+)\s+локаці")
_GLUED = re.compile(r"(?<=[\u0430-\u044f\u0456\u0457\u0454\u0491])(?=\d)")
_SENTENCE_END = re.compile(r"[а-яіїєґ']\.\s+[А-ЯІЇЄҐ]")
#: Where one named item may end and the next begin inside a phrase.
_SUB = re.compile(r",|;|\.\s|\n| та ")

_QUOTES = (("\u2019", "'"), ("\u02bc", "'"), ("\u00a0", " "), ("\u2018", "'"),
           ("\u201c", '"'), ("\u201d", '"'), ("\u00ab", '"'), ("\u00bb", '"'))


@dataclass(frozen=True, slots=True)
class Item:
    """One class of weapon as the summary names it."""

    cls: str
    count: int | None
    text: str
    approx: bool = False
    derived: bool = False


@dataclass(frozen=True, slots=True)
class Headline:
    """The first line: a total, or missiles and drones, or one of them unnumbered."""

    total: int | None = None
    missiles: int | None = None
    drones: int | None = None
    unnumbered: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Inventory:
    """What the radio-technical troops registered, published on combined nights only."""

    assets: int
    missiles: int
    drones: int


@dataclass(frozen=True, slots=True)
class NotReached:
    """Their sentence saying some weapons did not reach their targets, verbatim."""

    text: str
    count: int | None


@dataclass(frozen=True, slots=True)
class Tally:
    """One summary as read. `checks` is empty when its arithmetic closes."""

    kind: str
    shape: str
    night: date | None
    as_of: datetime | None
    headline: Headline
    launched_total: Inventory | None
    launched: tuple[Item, ...]
    downed: tuple[Item, ...]
    impacts: tuple[Item, ...]
    hit_locations: int | None
    debris_locations: int | None
    directions: str | None
    not_reached: NotReached | None
    attack_continues: bool
    checks: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """Whether every check held."""
        return not self.checks


@dataclass(frozen=True, slots=True)
class Message:
    """One channel post with text and an aware time."""

    post_id: int
    posted_at: datetime
    text: str

    @property
    def source_url(self) -> str:
        """The post's own address, the citation a figure carries."""
        return POST_URL.format(post_id=self.post_id)


@dataclass(frozen=True, slots=True)
class Reading:
    """A post this reader keeps: a summary read into a tally, or a correction refused.

    `status` is `ok`, `flagged` (read, and a check failed) or `refused` (a
    correction, which is prose written for people and is never read into
    figures).
    """

    message: Message
    status: str
    tally: Tally | None


@dataclass(frozen=True, slots=True)
class Page:
    """What one fetch of the channel held.

    `unreadable` counts posts with text and no aware time, which cannot be
    placed and are counted rather than dropped. Posts that are not summaries
    are counted in `messages` and kept nowhere: the channel is their archive.
    """

    messages: int
    unreadable: int
    first_id: int | None
    last_id: int | None
    readings: tuple[Reading, ...]


@dataclass(frozen=True, slots=True)
class _Mark:
    start: int
    value: int
    approx: bool


def clean(text: str) -> str:
    """Quotes and apostrophes to one form; a digit glued to a Cyrillic word split.

    The corpus writes `на16 локаціях`, and a reader that keeps the glue loses
    the number. Latin-led designations such as `S8000` are left alone.
    """
    for old, new in _QUOTES:
        text = text.replace(old, new)
    return _GLUED.sub(" ", text)


def _strip_parens(text: str) -> str:
    """A parenthesis holds a share, not a count, so it never reaches the reader."""
    return re.sub(r"\([^()]*\)", " ", text)


def _words(text: str, limit: int = 80) -> str:
    return " ".join(text.split())[:limit]


def _count(raw: str) -> int | None:
    """A count from one token, or None. Six digits is the most a count can be.

    `isdigit` alone accepts `²`, which `int` refuses, and an unbounded digit
    string hits the interpreter's conversion limit: both would turn hostile
    content into an exception.
    """
    if raw.isascii() and raw.isdigit() and len(raw) <= 6:
        return int(raw)
    hybrid = _HYBRID.match(raw)
    if hybrid:
        return int(hybrid.group(1))
    return _WORDS.get(raw)


def _numbers(text: str) -> list[_Mark]:
    """Every count in `text`, with whether an approximating word precedes it."""
    tokens = list(_TOKEN.finditer(text))
    out: list[_Mark] = []
    for i, token in enumerate(tokens):
        value = _count(token.group().strip(".,;:").lower())
        if value is None:
            continue
        before = tokens[i - 1].group().lower() if i else ""
        out.append(_Mark(token.start(), value, before in _APPROX))
    return out


def classify_words(text: str) -> list[tuple[int, str]]:
    """Class keywords in the order they appear, one entry per hit."""
    hits = [(m.start(), name) for name, pattern in _CLASS_PATTERNS for m in pattern.finditer(text)]
    return sorted(hits)


def _prose_items(segment: str, *, generic_in_phrases: bool = False) -> list[Item]:
    """The items of a prose enumeration, each count with the class after it.

    A number owns the words up to the next number. Inside them, a phrase that
    names a different class starts a new item whose count was not given, so
    `двома ... Онікс, балістичними ракетами ...` is two items and not one; a
    drone's own kinds (`Гербера`, `"Бандероль"`) stay inside the drone item
    unless `а також` introduces them. A counted phrase that names no class is
    `other`, never the class of a later phrase (post 73939).

    `generic_in_phrases` is for impacts, where `влучання ракети` names a
    missile of no stated class: such a phrase is kept as `other` with its count
    unknown rather than dropped (posts 66637 and 79455).
    """
    seg = _strip_parens(segment)
    marks = _numbers(seg)
    starts = [mark.start for mark in marks] + [len(seg)]
    pieces: list[tuple[_Mark | None, str]] = [(None, seg[: starts[0]])]
    pieces += [(mark, seg[mark.start : starts[i + 1]]) for i, mark in enumerate(marks)]
    found: list[Item] = []
    for mark, piece in pieces:
        phrases = _SUB.split(piece)
        current: Item | None = None
        if mark is not None:
            first = classify_words(phrases[0])
            if not first and any(word in piece.lower() for word in _NOT_A_TYPE):
                continue
            if _NOT_REACHED in phrases[0].lower():
                continue
            current = Item(first[0][1] if first else "other",
                           None if mark.approx else mark.value, _words(phrases[0]), mark.approx)
            found.append(current)
            phrases = phrases[1:]
        elif not classify_words(piece) and _MISSILE_WORD in piece.lower() \
                and not generic_in_phrases:
            found.append(Item("other", None, _words(piece)))
            continue
        for phrase in phrases:
            if _NOT_REACHED in phrase.lower():
                # `ракетою Х-31 не досягла цілі` closes the downed sentence of
                # 67362 and 75536: their category, stored as `not_reached`,
                # and neither downed nor a count this reader may invent.
                continue
            hits = classify_words(phrase)
            if not hits:
                if generic_in_phrases and _MISSILE_WORD in phrase.lower():
                    current = Item("other", None, _words(phrase))
                    found.append(current)
                continue
            name = hits[0][1]
            if current is not None and name == current.cls:
                continue
            introduced = phrase.lower().lstrip(" .").startswith(_ALSO)
            if current is not None and current.cls in _DRONE_FAMILY \
                    and name in _DRONE_FAMILY and not introduced:
                continue
            current = Item(name, None, _words(phrase))
            found.append(current)
    return found


def _list_items(segment: str) -> list[Item]:
    """The list shape: one line per type, and a line may name two types."""
    found: list[Item] = []
    for raw_line in segment.split("\n"):
        line = raw_line.strip()
        if not line.startswith("-"):
            continue
        body = _strip_parens(line.lstrip("-").strip())
        marks, hits = _numbers(body), classify_words(body)
        if len(marks) > 1:
            found.extend(_prose_items(body))
            continue
        if marks and not hits:
            if not any(word in body.lower() for word in _NOT_A_TYPE):
                found.append(Item("other", None if marks[0].approx else marks[0].value,
                                  _words(body), marks[0].approx))
            continue
        if marks:
            found.append(Item(hits[0][1], None if marks[0].approx else marks[0].value,
                              _words(body), marks[0].approx))
            continue
        seen: list[str] = []
        for _position, name in hits:
            if name not in seen:
                seen.append(name)
                found.append(Item(name, None, _words(body)))
    return found


def _segment(low: str, text: str, start: str, ends: tuple[str, ...]) -> str:
    i = low.find(start)
    if i < 0:
        return ""
    stops = [k for k in (low.find(end, i + len(start)) for end in ends) if k >= 0]
    return text[i : min(stops) if stops else len(text)]


def _paragraph(low: str, text: str, start: str) -> str:
    i = low.find(start)
    if i < 0:
        return ""
    j = low.find("\n\n", i)
    return text[i : j if j >= 0 else len(text)]


def _one_sentence(text: str) -> str:
    """Cut at the first full stop that ends a sentence, not at 09.00 or `обл.`"""
    match = _SENTENCE_END.search(text)
    return text[: match.start() + 1] if match else text


def _locations(text: str) -> tuple[int | None, int | None]:
    """Hit locations and debris locations, both counted in locations."""
    parts = clean(text).lower().split(_DEBRIS)

    def count(part: str) -> int | None:
        match = _LOCATIONS.search(part)
        return _count(match.group(1).strip(".,;:")) if match else None

    return count(parts[0]), count(parts[1]) if len(parts) > 1 else None


def headline(line: str) -> Headline:
    """The first line names a total, or missiles and drones, or one of them with
    no numeral at all (`ЗБИТО/ПОДАВЛЕНО РАКЕТУ Х-59 ТА 130 ВОРОЖИХ БПЛА`)."""
    seg = _strip_parens(line)
    low = seg.lower()
    marks = _numbers(seg)
    starts = [mark.start for mark in marks] + [len(seg)]
    total = missiles = drones = None
    for i, mark in enumerate(marks):
        span = low[mark.start : starts[i + 1]]
        if "ціл" in span:
            total = mark.value
        elif "бпла" in span or "безпілот" in span:
            drones = mark.value
        elif _MISSILE_WORD in span:
            missiles = mark.value
    unnumbered = ("missiles",) if _MISSILE_WORD in low[: starts[0]] and missiles is None else ()
    return Headline(total, missiles, drones, unnumbered)


def classify_message(text: str) -> str | None:
    """`night`, `day`, `correction`, or None for a post that is none of them.

    A correction is refused here and never read into figures: the two in the
    corpus are prose with percentages, and one of them carries `у ніч на` in
    mid-sentence, which is exactly what a night summary is recognised by.
    """
    lines = [line for line in clean(text).split("\n") if line.strip()]
    if not lines:
        return None
    first, low = lines[0].lower(), clean(text).lower()
    if _REFUSE_FIRST in first:
        return "correction"
    if _DAY in low and _HEAD in low:
        return "day"
    if _HEAD in first and _NIGHT in low:
        return "night"
    return None


def night_date(low: str, posted_at: datetime) -> date | None:
    """The date the night ends on, from their words, in the year of the post.

    A night named later in the year than the post was written belongs to the
    year before: a summary of 31 December posted on 1 January.
    """
    match = _DATE.search(low)
    if match is None or match.group(2) not in _MONTHS:
        return None
    posted = posted_at.astimezone(KYIV).date()
    try:
        named = date(posted.year, _MONTHS[match.group(2)], int(match.group(1)))
        return named if named <= posted else date(posted.year - 1, named.month, named.day)
    except ValueError:
        return None


def as_of_instant(low: str, posted_at: datetime) -> datetime | None:
    """Their `станом на HH:MM` on the Kyiv date of the post, as UTC."""
    match = _STAMP.search(low)
    if match is None:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        return None
    local = datetime.combine(posted_at.astimezone(KYIV).date(), time(hour, minute), KYIV)
    return local.astimezone(UTC)


def _not_reached(text: str) -> NotReached | None:
    low = text.lower()
    i = low.find(_NOT_REACHED)
    if i < 0:
        return None
    start = max(low.rfind(". ", 0, i) + 2, low.rfind("\n", 0, i) + 1, 0)
    ends = [k for k in (low.find(". ", i), low.find("\n", i)) if k >= 0]
    sentence = _words(text[start : min(ends) + 1 if ends else len(text)], 240)
    # The count is the one in the clause that says it, not the first figure of
    # the sentence: 67362 carries 112 downed drones in the same sentence.
    clause = max(start, low.rfind(",", 0, i) + 1)
    counted = [mark for mark in _numbers(text[clause:i]) if not mark.approx]
    return NotReached(sentence, counted[0].value if counted else None)


def parse(text: str, posted_at: datetime) -> Tally | None:
    """One summary read into a `Tally`, or None when the post is not a summary."""
    kind = classify_message(text)
    if kind not in ("night", "day"):
        return None
    text = clean(text)
    lines = [line for line in text.split("\n") if line.strip()]
    low = text.lower()
    inventory = _INVENTORY.search(low)
    shape = "combined" if inventory else "list" if _ATTACKED + ":" in low else "prose"

    launched_total = None
    if inventory:
        tail_low, tail = low[inventory.start():], text[inventory.start():]
        values = [mark.value for mark in _numbers(_segment(tail_low, tail, _TOTALS, (":",)))]
        if len(values) == 3:
            launched_total = Inventory(values[0], values[1], values[2])
        launched = _list_items(_segment(tail_low, tail, _TOTALS, (_REPELLED,)))
    else:
        seg = _segment(low, text, _ATTACKED, (_REPELLED, "за попередніми даними", _HEAD))
        launched = _list_items(seg) if shape == "list" else _prose_items(seg)
    if kind == "day":
        # The one day tally in the corpus that names a weapon outside its
        # opening sentence says so with `ворог застосував` (post 78115).
        launched += _prose_items(_one_sentence(_segment(low, text, _USED, ("\n",))))

    body = text[len(lines[0]):]
    down_seg = _segment(body.lower(), body, _HEAD, (_FIX, "\n\n\n"))
    downed = _list_items(down_seg) if "\n-" in down_seg else _prose_items(down_seg)

    fix = _one_sentence(_paragraph(low, text, _FIX))
    counted_part = fix
    cut = fix.lower().find("локаці")
    if cut >= 0:
        counted_part = fix[:cut]
        marks = _numbers(counted_part)
        if marks:
            counted_part = counted_part[: marks[-1].start]
    impacts = _prose_items(counted_part, generic_in_phrases=True) if fix else []
    hit_locations, debris_locations = _locations(fix) if fix else (None, None)

    directions = None
    for key in _DIRECTIONS:
        i = low.find(key)
        if i >= 0:
            end = low.find("\n", i)
            directions = _one_sentence(text[i : end if end >= 0 else len(text)]).strip()
            break

    head = Headline() if kind == "day" else headline(lines[0])
    downed_items, checks = _checks(kind, shape, head, launched_total, tuple(launched),
                                   tuple(downed), _MASSED in low)
    night = night_date(low, posted_at)
    if kind == "night" and night is None:
        checks += ("night date not read",)
    return Tally(kind, shape, night, as_of_instant(low, posted_at), head, launched_total,
                 tuple(launched), downed_items, tuple(impacts), hit_locations,
                 debris_locations, directions, _not_reached(text), _CONTINUES in low, checks)


def _checks(kind: str, shape: str, head: Headline, inventory: Inventory | None,
            launched: tuple[Item, ...], downed: tuple[Item, ...],
            massed_phrase: bool) -> tuple[tuple[Item, ...], tuple[str, ...]]:
    """Checks on this reading, each a reason and never a repair.

    They check our reading of their figures, not their figures: a failure means
    the reading is not published as read. One unnumbered downed item is closed
    by their own total and marked derived, which is arithmetic on two figures
    they published; more than one stays unknown.
    """
    if kind == "day":
        return downed, ()
    if not downed:
        return downed, ("no downed items",)
    unknown = [i for i, item in enumerate(downed) if item.count is None]
    known = sum(item.count for item in downed if item.count is not None)
    if head.total is not None and len(unknown) == 1 and head.total - known > 0:
        position = unknown[0]
        downed = downed[:position] + (replace(downed[position], count=head.total - known,
                                              derived=True),) + downed[position + 1:]
        unknown, known = [], head.total
    out: list[str] = []
    if unknown and len(unknown) != len(head.unnumbered):
        out.append(f"{len(unknown)} downed items without a count")
    drones = sum(item.count for item in downed if item.cls == "drone" and item.count is not None)
    if head.total is not None and not unknown and known != head.total:
        out.append(f"headline {head.total} against items {known}")
    if head.drones is not None and drones != head.drones:
        out.append(f"headline drones {head.drones} against items {drones}")
    if head.missiles is not None and known - drones != head.missiles:
        out.append(f"headline missiles {head.missiles} against items {known - drones}")

    if not launched:
        out.append("no launched items")
    if massed_phrase and shape != "combined":
        out.append("massed phrase without an inventory")
    if shape == "combined":
        if inventory is None:
            out.append("inventory not read")
        elif all(item.count is not None for item in launched):
            got = sum(item.count or 0 for item in launched)
            if got != inventory.assets:
                out.append(f"inventory {inventory.assets} against items {got}")
    # Nothing is shot down in greater numbers than it was launched. The only
    # check on the launched side of a night with no inventory, and the one that
    # would have caught 73939, where three missiles were read as three Banderols
    # beside six Banderols downed.
    for name in sorted({item.cls for item in downed} & {item.cls for item in launched}):
        down = [item.count for item in downed if item.cls == name]
        up = [item.count for item in launched if item.cls == name]
        down_known = [count for count in down if count is not None]
        up_known = [count for count in up if count is not None]
        if len(down_known) == len(down) and len(up_known) == len(up) \
                and sum(down_known) > sum(up_known):
            out.append(f"{name}: {sum(down_known)} downed against {sum(up_known)} launched")
    return downed, tuple(out)


def launched_sum(tally: Tally) -> int | None:
    """Their launched items added up, or None.

    **Decision 9 lives here.** None for an empty list as well as for a list with
    an unknown count: `all(...)` is true of nothing, and a total derived from
    nothing is a zero the Air Force never published. v3 of this reader stored
    01.08 with an empty launched list and reported the night consistent.
    """
    if not tally.launched or any(item.count is None for item in tally.launched):
        return None
    return sum(item.count or 0 for item in tally.launched)


def downed_total(tally: Tally) -> int | None:
    """Their headline total, or the sum of their two headline figures, or the
    sum of the items when every one of them carries a count; otherwise None."""
    head = tally.headline
    if head.total is not None:
        return head.total
    if head.missiles is not None and head.drones is not None:
        return head.missiles + head.drones
    if not tally.downed or any(item.count is None for item in tally.downed):
        return None
    return sum(item.count or 0 for item in tally.downed)


def read_message(message: Message) -> Reading | None:
    """A reading for a summary or a correction; None for any other post."""
    kind = classify_message(message.text)
    if kind == "correction":
        return Reading(message, "refused", None)
    tally = parse(message.text, message.posted_at)
    if tally is None:
        return None
    return Reading(message, "ok" if tally.ok else "flagged", tally)


def read_page(body: str) -> Page:
    """Every post on one page of the public preview. Never raises on content.

    A post whose id does not fit a count, or whose text has no aware time, is
    counted as unreadable: a summary that cannot be placed in time cannot be
    the latest night, and dropping it would make a malformed page read as a
    quiet one.
    """
    messages = unreadable = 0
    ids: list[int] = []
    readings: list[Reading] = []
    for block in _BLOCK.finditer(body):
        head = POST_ID.match(block.group(0))
        if head is None or len(head.group(1)) > 12:
            unreadable += 1
            continue
        post_id = int(head.group(1))
        messages += 1
        ids.append(post_id)
        text = _TEXT.search(block.group(1))
        if text is None:
            continue
        stamp = _TIME.search(block.group(1))
        posted_at = _parse_timestamp(stamp.group(1)) if stamp else None
        if posted_at is None:
            unreadable += 1
            continue
        reading = read_message(Message(post_id, posted_at.astimezone(UTC),
                                       _strip(text.group(1)).strip()))
        if reading is not None:
            readings.append(reading)
    return Page(messages, unreadable, min(ids) if ids else None, max(ids) if ids else None,
                tuple(readings))


def page_url(before: int | None = None) -> str:
    """The preview's address, or the page of posts older than `before`."""
    return SOURCE_URL if before is None else f"{SOURCE_URL}?before={before}"


def poll_once(transport: Transport, url: str = SOURCE_URL) -> tuple[Page, float]:
    """One fetch, returning the page and how long it took.

    A refusal is `SourceUnavailable` from the transport and propagates, so the
    caller writes it as a refusal rather than as a page that held nothing.
    """
    started = datetime.now(UTC)
    body = transport.fetch(url)
    return read_page(body), (datetime.now(UTC) - started).total_seconds()
