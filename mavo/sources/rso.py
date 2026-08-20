"""The Polish civil-warning stream, read as a record and not as an alarm.

RSO (`Regionalny System Ostrzegania`) publishes an XML feed run for MSWiA by
TVP. RCB, the body that sends the statutory SMS, publishes no feed at all: it
hands text and scope to the mobile operators and they broadcast, so the only
public trace of an individual RCB alert is a social account and a web page.
This module reads the RSO feed. It does not read RCB, and no amount of parsing
turns one into the other.

**What this is for.** The project has no labelled outcome variable. Every
question it asks about western episodes -- was that night different, does a
raid near the border mean anything on this side of it -- has no right-hand
side to be measured against. A state-issued communique with a date, a scope
and an issuer is exactly that missing column.

**What it must never become.** A live warning layer on the map. A reader who
sees Polish warnings drawn beside Ukrainian ones will read an absent warning
as no warning, and this instrument is structurally later than the SMS that
arrives on the same reader's phone automatically and by statute. Such a layer
would add a way to be misled by absence and subtract nothing. **Where, if
anywhere, this data renders is the operator's decision and is not recorded
yet** `[undecided]`; until it is, this module is a reader with no caller in
the collector, which is the same position `ukrainealarm.py` holds and for a
related reason.

**What the feed does that this project is built to refuse.** Elements arrive
present and empty rather than absent: `<latitude></latitude>` is a field that
said nothing, and an adapter testing presence reads it as a value. Timestamps
arrive with no offset. Both are the null-versus-zero problem in the source
data, one layer earlier than usual.

Three refusals, and each exists because its alternative is silent:

* An unparseable page **is not an empty page.** Returning zero communiques
  from bytes nobody could read would render our own blindness as a quiet
  country, which is the one output this project exists to not produce.
* A naive timestamp **is not converted here.** `to_utc` takes the zone as an
  argument and refuses an hour that a zone maps twice, because a silently
  chosen offset is wrong for one hour of one night a year and nobody finds it.
* An item without an identifier **is dropped and counted.** The count is on
  the page, so a page that lost half its rows cannot read as a short page.

The parser is stdlib-only, like everything else in `mavo/`.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from xml.etree import ElementTree

from mavo.errors import SourceUnavailable

#: Cheapest defence against an entity-expansion payload, and the reason it is
#: cheap: `xml.etree` is documented as unsafe against one, an entity bomb needs
#: an internal DTD subset to declare its entities, and this feed has never
#: carried a doctype. Refusing the construct outright costs a regular
#: expression and removes the class, where a size limit alone only moves it.
DOCTYPE = re.compile(rb"<!DOCTYPE", re.IGNORECASE)

#: A page is 20 items of prose. This ceiling is two orders above the largest
#: page measured (21,418 bytes) and exists so that a redirected or replaced
#: endpoint cannot hand the parser a stream instead of a document.
MAX_BYTES = 4 * 1024 * 1024

#: Fields carried through verbatim as text. `rso_alarm` looks like the severity
#: discriminator and its encoding is undocumented and unverified, so it stays a
#: string: reading it as an integer would assert an ordering nobody has
#: measured.
_TEXT_FIELDS = (
    "title",
    "shortcut",
    "content",
    "rso_alarm",
    "rso_icon",
    "valid_from",
    "valid_to",
    "repetition",
    "longitude",
    "latitude",
    "water_level_value",
    "water_level_warning_status_value",
    "water_level_alarm_status_value",
    "water_level_trend",
    "type",
    "river_name",
    "location_name",
    "created_at",
    "updated_at",
)


class AmbiguousLocalTime(SourceUnavailable):
    """A local time falls in an hour its zone maps twice.

    Raised rather than resolved by picking the earlier instant. The feed emits
    `YYYY-MM-DD HH:MM:SS` with no offset, so on the autumn transition one hour
    of communiques is genuinely two possible instants and no rule inside this
    process can tell them apart. A silently chosen offset is right all but one
    night a year, which is precisely the error profile nobody ever finds.
    """

    code = "refusal.ambiguous_local_time"


@dataclass(frozen=True)
class Province:
    """One voivodeship named by a communique, and possibly one city inside it.

    `city` carries the same empty-versus-absent discipline as everything else:
    the attribute is present and empty on every message measured so far, and
    an empty attribute is not a city.
    """

    slug: str
    name: str
    city: str | None = None


@dataclass(frozen=True)
class Communique:
    """One RSO message, with every field that said nothing reading `None`.

    Timestamps are **text**, deliberately. They arrive without an offset and
    this project does not hold naive times; converting them here would bury
    the choice of zone in a parser. `to_utc` is where that choice is made, by
    a caller that states it.
    """

    id: str
    provinces: tuple[Province, ...] = ()
    fields: dict[str, str | None] = field(default_factory=dict)

    def value(self, name: str) -> str | None:
        """One field, or `None` if the feed carried it empty or not at all.

        Empty and absent are deliberately not distinguished. Both mean the
        feed said nothing, and inventing a difference between them would be a
        claim about the publisher's intent that nobody has measured.
        """
        return self.fields.get(name)

    def digest(self) -> str:
        """Content hash, for idempotence that does not trust `updated_at`.

        `id` is monotonic and looks like a natural key, but `updated_at` moves
        on edits, so a store keyed on the identifier alone cannot tell a
        re-publication from a rewrite. `events` already keys on content for
        the same reason.
        """
        payload = json.dumps(
            {
                "id": self.id,
                "fields": self.fields,
                "provinces": [[p.slug, p.name, p.city] for p in self.provinces],
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Page:
    """One page of the feed, with the rows it could not read counted.

    `unreadable` is on the page rather than logged, because a caller that sees
    only `communiques` cannot tell a short page from a damaged one, and that
    is the same distinction as `gaps` versus `unobserved` one repository over.
    """

    communiques: tuple[Communique, ...] = ()
    total_items: int | None = None
    items_per_page: int | None = None
    unreadable: int = 0


def _text(node: ElementTree.Element | None) -> str | None:
    """Element text, with empty and whitespace-only reading as nothing."""
    if node is None or node.text is None:
        return None
    stripped = node.text.strip()
    return stripped or None


def _attr(node: ElementTree.Element, name: str) -> str | None:
    """Attribute value, with an empty attribute reading as nothing."""
    raw = node.get(name)
    if raw is None:
        return None
    stripped = raw.strip()
    return stripped or None


def _province(node: ElementTree.Element) -> Province | None:
    """One `<province>`, or `None` when it carries no slug to name it by."""
    slug = _attr(node, "slug")
    if slug is None:
        return None
    return Province(slug=slug, name=_text(node) or slug, city=_attr(node, "city"))


def _int(raw: str | None) -> int | None:
    """A pagination figure, or `None` when it is missing or not a number."""
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def parse_page(payload: bytes) -> Page:
    """Read one `?_format=xml` page.

    Refuses with `SourceUnavailable` rather than returning an empty page when
    the bytes are unreadable, oversized, or carry a doctype. The distinction
    is the whole point: an empty page is a real answer the feed gives on a
    quiet day, so it must not also be the answer to a question we failed to
    ask.
    """
    if len(payload) > MAX_BYTES:
        raise SourceUnavailable(f"RSO page is {len(payload)} bytes, over the {MAX_BYTES} ceiling")
    if DOCTYPE.search(payload):
        raise SourceUnavailable("RSO page carries a doctype, which this parser refuses to expand")
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise SourceUnavailable(f"RSO page is not well-formed XML: {exc}") from exc

    pagination = root.find("pagination_info")
    total = _int(_attr(pagination, "totalItems")) if pagination is not None else None
    per_page = _int(_attr(pagination, "itemsPerPage")) if pagination is not None else None

    items: list[Communique] = []
    unreadable = 0
    for node in root.findall("news"):
        identifier = _text(node.find("id"))
        if identifier is None:
            unreadable += 1
            continue
        provinces = tuple(
            p
            for p in (_province(child) for child in node.iterfind("provinces/province"))
            if p is not None
        )
        items.append(
            Communique(
                id=identifier,
                provinces=provinces,
                fields={name: _text(node.find(name)) for name in _TEXT_FIELDS},
            )
        )
    return Page(
        communiques=tuple(items),
        total_items=total,
        items_per_page=per_page,
        unreadable=unreadable,
    )


def to_utc(local: str, zone: str) -> datetime:
    """Convert one naive feed timestamp to UTC, with the zone stated by the caller.

    The zone is an argument and not a constant here because it is a decision
    about the publisher, and a decision written into a default is a decision
    nobody made. Refuses an hour the zone maps twice.
    """
    from zoneinfo import ZoneInfo

    try:
        naive = datetime.strptime(local.strip(), "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise SourceUnavailable(f"RSO timestamp {local!r} is not YYYY-MM-DD HH:MM:SS") from exc
    tz = ZoneInfo(zone)
    earlier = naive.replace(tzinfo=tz, fold=0)
    later = naive.replace(tzinfo=tz, fold=1)
    if earlier.utcoffset() != later.utcoffset():
        raise AmbiguousLocalTime(
            f"RSO timestamp {local!r} falls in an hour {zone} maps twice; "
            "the feed carries no offset to settle it"
        )
    return earlier.astimezone(UTC)
