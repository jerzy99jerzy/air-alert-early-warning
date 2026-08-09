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

# The eight oblasts whose alerts can plausibly bear on the Polish side. Not a
# statement about crossings, which nothing here predicts (D-015): a statement
# about which reports are worth a Polish reader's attention at all. 96.5% of tag
# occurrences in the design window are front-line raions 900 km away.
WESTERN_OBLASTS = (
    "Львівська", "Волинська", "Закарпатська", "Івано-Франківська",
    "Тернопільська", "Рівненська", "Хмельницька", "Чернівецька",
)

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

    def western(self, text: str) -> tuple[AreaRef, ...]:
        """Only the areas a Polish reader has reason to be told about."""
        resolved, _unknown = self.resolve_all(text)
        return tuple(area for area in resolved if area.is_western)
