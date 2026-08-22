"""The Polish civil-warning stream, read as a record and not as an alarm.

RSO (`Regionalny System Ostrzegania`) publishes an XML feed run for MSWiA by
TVP.

**Two different things share the abbreviation RCB, and until 0.38.0.0 this
docstring conflated them.** *Alert RCB*, the statutory SMS, is not in this
feed and has no feed of its own: the Government Centre for Security hands text
and scope to the mobile operators and they broadcast, and its own FAQ states
that the alert is not part of RSO. *RCB communiques* are a different object.
Since April 2024 that body has published into this feed and is, with MSWiA,
the named author of the nationwide ones `[reported: MSWiA's own page; the
date shipped at 0.38.0.0 as 2026 and was wrong by two years, F112]`.

So this module does read RCB, some of the time, and cannot tell when. The
payload carries voivodeship scope and no issuer field `[n=1 fixture]`, so a
communique written by the Government Centre for Security and one written by a
voivodeship crisis centre arrive indistinguishable. That is a property of the
feed, it is the next entry FEED-SPEC needs, and it is not something a parser
can repair.

**What this is for.** The project has no labelled outcome variable. Every
question it asks about western episodes -- was that night different, does a
raid near the border mean anything on this side of it -- has no right-hand
side to be measured against. A state-issued communique with a date, a scope
and an issuer is exactly that missing column.

**What it must never become.** A live warning layer on the map. A reader who
sees Polish warnings drawn beside Ukrainian ones will read an absent warning
as no warning, and this instrument is structurally later than the SMS that
arrives on the same reader's phone automatically and by statute. Such a layer
would add a way to be misled by absence and subtract nothing.

**Where this renders, decided** (D-033, T68). In text, in a block below the
map, never as a layer on it, and always beneath a sentence saying this is not
a warning channel. **Under the name of the feed it was read from and never
under `RCB`.** The two are different institutions publishing different things,
this module reads only one of them, and a page that says otherwise asserts a
source it does not have.

**Nothing is filtered by category** (D-034). An allowlist of recognised
categories would drop a communique of a category nobody anticipated, which is
this project's founding failure reached by a different route: the reader is
told about a quiet country because our own vocabulary was short. Classification
orders what is shown; it never decides what exists.

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
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from xml.etree import ElementTree

from mavo.errors import SourceUnavailable
from mavo.transport import Transport

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

    **`items_on_page` is named for what it measures and not for what the feed
    calls it.** The attribute is `totalItems`, and on a paged request it is not
    a total: measured 2026-08-22, pages 1 and 2 both reported 20 while the
    unpaged request over the same category set reported 156. A caller deriving
    a page count from it divides 20 by 20, reads one page of eight, and gets a
    partial answer shaped exactly like a complete one. **The stop condition is
    an empty page**, which page 9 returned with status 200 while page 8 held
    16 rows. An empty page is a real answer; the attempt log is what keeps it
    distinguishable from a refusal.
    """

    communiques: tuple[Communique, ...] = ()
    items_on_page: int | None = None
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
    on_page = _int(_attr(pagination, "totalItems")) if pagination is not None else None
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
        items_on_page=on_page,
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


#: What the store calls rows read from this endpoint. Not an issuer: the feed
#: names none, and this project has measured that the body publishing the
#: statutory SMS publishes no feed at all. This string says which endpoint the
#: bytes came from and claims nothing further.
FEED = "rso"


#: The five categories, from `/kategorie?_format=xml` (fetched 2026-08-22).
#: **A category is a property of the query and not of the record**: no
#: communique carries one, measured over 156 messages, so the only way a
#: consumer knows what a row is, is to remember which address returned it.
CATEGORIES = (
    "ogolne",
    "meteorologiczne",
    "hydrologiczne",
    "informacje-drogowe",
    "stany-wod",
)

#: **`wszystkie` does not mean all, and there is no address that does.**
#: Measured 2026-08-22: the five categories hold 461 distinct communiques
#: between them and no two share one, while `wszystkie/wszystkie` returns 156.
#: The 305 missing rows are `stany-wod`, dropped without a word anywhere in the
#: payload or the publisher's documentation. A collector that reads
#: `wszystkie` reads two thirds of the feed and cannot tell.
#:
#: This constant is therefore a template and not an address. A caller
#: enumerates `CATEGORIES`; there is no shortcut and this comment exists so
#: nobody reintroduces one.
PAGE_URL = "https://komunikaty.tvp.pl/komunikatyxml/wszystkie/{category}/{page}?_format=xml"

#: The slug vocabularies, each its own document.
PROVINCES_URL = "https://komunikaty.tvp.pl/wojewodztwa?_format=xml"
CATEGORIES_URL = "https://komunikaty.tvp.pl/kategorie?_format=xml"


def page_url(category: str, page: int = 1) -> str:
    """One page of one category. Pages are 1-based; page 0 suppresses paging.

    Refuses a category outside the published vocabulary rather than building
    an address the endpoint will answer with something unexpected. The five
    slugs are a measured list, not a guess, and a sixth appearing is a change
    in the feed that a caller should hear about rather than absorb.
    """
    if category not in CATEGORIES:
        raise SourceUnavailable(
            f"{category!r} is not one of the published RSO categories "
            f"({', '.join(CATEGORIES)}); read {CATEGORIES_URL} before adding one"
        )
    return PAGE_URL.format(category=category, page=page)


def poll_once(transport: Transport, url: str) -> tuple[Page, float]:
    """Fetch one page and parse it. Returns the page and the seconds it took.

    Bytes rather than text at the parser boundary, so `parse_page` keeps its
    doctype refusal and its ceiling. The transport hands back a decoded string,
    so the length checked here is the length of the document as decoded and not
    the length that arrived on the wire; the ceiling is therefore a second line
    of defence rather than the first, and it is kept because the first one
    lives in a different module and can change without this one noticing.
    """
    started = time.monotonic()
    body = transport.fetch(url)
    page = parse_page(body.encode("utf-8"))
    return page, time.monotonic() - started
