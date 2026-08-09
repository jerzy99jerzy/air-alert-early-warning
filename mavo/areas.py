"""Area resolution by the channel's own hashtags.

Sprint 7. The shipped pattern table keyed on oblast names and scored 0 of 20
against real content (F23). The reason, measured at 0.10.0.0 and written up in
`docs/CHANNEL.md`, is that the channel does not name areas in prose: it labels
99.34% of its messages with a hashtag carrying the area and its unit type
explicitly, in the nominative, with underscores for spaces. 127 distinct tags
across 99 nights, 126 of them resolving to a unique code in the Ukrainian state
register.

Resolution is therefore a lookup, not a search. This module owns the lookup and
nothing else: it does not decide states, it does not decide means, and it does
not guess.

**Unknown tags are reported, never absorbed.** A tag the table does not know is
a finding: either the channel has started naming a new area, or a name has
drifted (T33). Returning a default would convert the discovery of a new area
into silence, which is the defect class this repository exists to refuse. The
parse path never raises on it either, because a hostile or novel string must not
become an outage; it is counted and printed.

**Distance to the border is not here yet.** The column that turns a resolved
area into a usable report is S8 (T32). Its absence is visible rather than
papered over: `AreaRef.border_km` is `None` until it is measured, and `None`
means unknown.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from mavo.errors import DuplicateTag

# The eight oblasts whose alerts can plausibly bear on the Polish side. Not a
# statement about crossings, which nothing here predicts (D-015): a statement
# about which reports are worth a Polish reader's attention at all. 96.5% of tag
# occurrences in the design window are front-line raions 900 km away.
WESTERN_OBLASTS = (
    "Львівська", "Волинська", "Закарпатська", "Івано-Франківська",
    "Тернопільська", "Рівненська", "Хмельницька", "Чернівецька",
)

# T38. The register writes an oblast name; the rules reason in slugs. This is
# the one place the two vocabularies are joined, and it is a table rather than a
# transliteration function because a function would invent a slug for a name it
# had never seen and the invented slug would match nothing, silently. A name
# missing from this table resolves to "" — unknown, and visible as unknown.
#
# All 23 oblasts the corpus tags, in the register's nominative spelling.
OBLAST_SLUGS: dict[str, str] = {
    "Вінницька": "vinnytsia",
    "Волинська": "volyn",
    "Дніпропетровська": "dnipropetrovsk",
    "Донецька": "donetsk",
    "Житомирська": "zhytomyr",
    "Закарпатська": "zakarpattia",
    "Запорізька": "zaporizhzhia",
    "Івано-Франківська": "ivano-frankivsk",
    "Київська": "kyiv",
    "Кіровоградська": "kirovohrad",
    "Львівська": "lviv",
    "Миколаївська": "mykolaiv",
    "Одеська": "odesa",
    "Полтавська": "poltava",
    "Рівненська": "rivne",
    "Сумська": "sumy",
    "Тернопільська": "ternopil",
    "Харківська": "kharkiv",
    "Херсонська": "kherson",
    "Хмельницька": "khmelnytskyi",
    "Черкаська": "cherkasy",
    "Чернівецька": "chernivtsi",
    "Чернігівська": "chernihiv",
}


def oblast_slug(name: str) -> str:
    """Canonical slug for a register oblast name, or "" when it is not known.

    Empty is the unknown state and never a match: a rule asking whether an area
    sits in a border oblast gets ``False`` from an unknown, and the emptiness
    stays in the row for a reader to see (T38).
    """
    return OBLAST_SLUGS.get(name.strip(), "")


# T37. An all-clear can carry a continuation list: `Відбій ... Зверніть увагу,
# тривога ще триває у: - Запорізька область - Пологівський район`. Everything
# after this marker names areas where the alert is *still running*, which is the
# opposite of what the message is otherwise announcing. Promoted into the package
# from `tools/consistency_check.py`, where it was measured: reading the two parts
# as one set produced 1,203 false disagreements over the design window, and
# separating them moved tag-prose agreement from 96.972% to 99.997%.
CONTINUES = re.compile(r"тривога\s+ще\s+трива[єе]|ще\s+трива[єе]\s+у")

# Prose names are matched by taking the tokens before a unit word and keeping
# only joins the register already knows. A pattern that decides what *looks*
# like a place is the guess sprint 7 replaced (F59): `район` is also an ordinary
# noun, and `район старої частини` is the old town, not an administrative unit.
UNIT = re.compile(r"\b(район|громад[аи]|област[ьі])\b")
TOKEN = re.compile(r"[\w\u0400-\u04FF’'-]+")

# Nominative, underscores for spaces, unit word explicit. No stemming, because
# the tag is not inflected. The alternative, matching register names in prose,
# was measured at 6.06% against 99.34% for this and needed a truncation length
# that made names collide across oblasts (F59, MECHANISMS section 26).
TAG = re.compile(r"#([\w\u0400-\u04FF’'-]+?)_(район|громада|область)")

DEFAULT_MAP = Path(__file__).resolve().parent.parent / "data" / "reference" / "tag_map.csv"


@dataclass(frozen=True, slots=True)
class AreaRef:
    """One administrative area, as the channel names it and the register codes it."""

    tag: str
    name: str
    unit: str
    oblast: str
    code: str
    border_km: float | None = None

    @property
    def is_western(self) -> bool:
        """True when the oblast is one a Polish reader has reason to care about."""
        return any(term in self.oblast for term in WESTERN_OBLASTS)


def normalise_name(name: str) -> str:
    """Strip everything that differs between the two spellings of one name.

    The tag drops apostrophes and hyphens (``#КамянецьПодільський_район``) where
    the prose keeps them (``Кам'янець-Подільський район``). Reducing both to
    letters is what lets them be compared without a table of spelling variants.
    """
    return re.sub(r"[^\w]", "", name.replace("’", "").replace("'", "")).lower()


def parse_tags(text: str) -> tuple[str, ...]:
    """Every `#Name_unit` tag in a message, in order, without duplicates."""
    seen: dict[str, None] = {}
    for name, unit in TAG.findall(text):
        seen.setdefault(f"{name}_{unit}", None)
    return tuple(seen)


class AreaTable:
    """The 127-row lookup, loaded once from a versioned file.

    Small enough to hold in memory and to read by hand, which is the point: a
    table a person can check is a different artifact from a model they cannot.
    """

    def __init__(self, rows: dict[str, AreaRef], unresolved: frozenset[str]) -> None:
        self._rows = rows
        self.unresolved = unresolved
        # T37. Normalised tag stem to the areas carrying it. A list rather than
        # a value: a stem shared by two areas is ambiguous, and an ambiguous
        # prose name resolves to nothing rather than to whichever row came
        # first. That is the F59 defect, and it is not being repeated one
        # sprint later in a different function.
        self._by_name: dict[str, list[AreaRef]] = {}
        for area in rows.values():
            self._by_name.setdefault(normalise_name(area.tag.rsplit("_", 1)[0]), []).append(area)

    @classmethod
    def from_csv(cls, path: Path | None = None) -> AreaTable:
        """Load the map. Rows without a code are kept as known-but-unresolved.

        A tag the register could not disambiguate is a different thing from a tag
        nobody has seen, and collapsing the two would hide the ambiguity rather
        than carry it.
        """
        source = path or DEFAULT_MAP
        rows: dict[str, AreaRef] = {}
        unresolved: set[str] = set()
        with source.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                tag = row["tag"]
                if tag in rows or tag in unresolved:
                    # F63. Two rows claiming one tag is a contradiction inside
                    # the one artifact resolution trusts. Letting the later row
                    # win silently would resolve it by file order, which is
                    # absorption, not resolution.
                    raise DuplicateTag(f"{source}: tag {tag!r} appears more than once")
                if not row.get("katottg_code") or row.get("status", "").startswith("ambiguous"):
                    unresolved.add(tag)
                    continue
                rows[tag] = AreaRef(
                    tag=tag,
                    name=row["register_name"],
                    unit=row["unit"],
                    oblast=row["oblast"],
                    code=row["katottg_code"],
                )
        return cls(rows, frozenset(unresolved))

    def __len__(self) -> int:
        return len(self._rows)

    @property
    def tags(self) -> tuple[str, ...]:
        """Every tag the table resolves, for callers that need the vocabulary.

        Exposed as a view rather than the mapping, so a caller cannot mutate the
        table it is reading. Added when a cross-check needed the set of known
        names and had been reaching into the private dict to get it.
        """
        return tuple(self._rows)

    @property
    def names(self) -> tuple[str, ...]:
        """Every register name the table resolves to."""
        return tuple(area.name for area in self._rows.values())

    def resolve(self, tag: str) -> AreaRef | None:
        """The area for a tag, or None when the table does not know it."""
        return self._rows.get(tag)

    def resolve_all(self, text: str) -> tuple[tuple[AreaRef, ...], tuple[str, ...]]:
        """Resolved areas and the tags that resolved to nothing.

        The second element is the load-bearing one. A caller that ignores it has
        turned a new area, or a renamed one, into silence.
        """
        found: list[AreaRef] = []
        unknown: list[str] = []
        for tag in parse_tags(text):
            area = self.resolve(tag)
            if area is None:
                unknown.append(tag)
            else:
                found.append(area)
        return tuple(found), tuple(unknown)

    def resolve_prose(self, text: str) -> tuple[AreaRef, ...]:
        """Areas named in prose, verified against names the register knows.

        Up to four tokens before each unit word are joined longest-first and the
        first join the register knows wins. Four covers the longest real form,
        ``м. Харків та Харківська територіальна громада``, and stops well short
        of swallowing a sentence. A unit word with no known name before it is
        ignored, and a name shared by two areas resolves to neither: an
        ambiguous name is unknown, not a coin toss (F59).

        Used for the continuation list, which the channel writes in prose rather
        than as tags, so the tag path cannot see it at all (T37).
        """
        found: dict[str, AreaRef] = {}
        tokens = [(match.group(0), match.end()) for match in TOKEN.finditer(text)]
        ends = {end: index for index, (_word, end) in enumerate(tokens)}
        for unit in UNIT.finditer(text):
            index = ends.get(unit.end())
            if index is None:
                continue
            for span in (4, 3, 2, 1):
                start = index - span
                if start < 0:
                    continue
                candidate = normalise_name("".join(word for word, _e in tokens[start:index]))
                matches = self._by_name.get(candidate)
                if matches is None:
                    continue
                if len(matches) == 1:
                    found.setdefault(matches[0].code, matches[0])
                break
        return tuple(found.values())

    def western(self, text: str) -> tuple[AreaRef, ...]:
        """Only the areas a Polish reader has reason to be told about."""
        resolved, _unknown = self.resolve_all(text)
        return tuple(area for area in resolved if area.is_western)
