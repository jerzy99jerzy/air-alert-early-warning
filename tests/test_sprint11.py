"""F71 repair: the four forms the kind tables refused, and the ones they still do.

The measurement that motivated this is in `docs/METHODOLOGY.md` under F71:
threat-kind join coverage 0.128 over 61,041 messages, and MISSILE resolving on
25 of 2,392 declarations because the channel announces ballistics in a form
carrying no declare marker.

Every case below uses text quoted in that entry or a form found while testing
the repair. **Which is also the limit of what these tests establish**: they
show the parser now accepts forms it demonstrably refused, and they say
nothing about how much of the corpus that recovers. The measurement that
answers the second question is T45, and it needs the corpus.

Mutations named in a docstring were run against a scratch copy carrying that
mutation and observed red. The rest are ordinary regressions.
"""

from __future__ import annotations

from mavo.areas import AreaTable
from mavo.schema import KindState, ThreatKind
from mavo.sources.telegram import classify_kind_message

TAG = "#Самбірський_район"


def _kind(text: str) -> tuple[ThreatKind, KindState] | None:
    """The single classification for a message, or None when it was refused."""
    table = AreaTable.from_csv()
    resolved = classify_kind_message(f"{text} {TAG}", table)
    if not resolved:
        return None
    _code, _oblast, kind, state = resolved[0]
    return kind, state


def test_a_kamikaze_drone_attack_is_a_drone_declaration() -> None:
    """F71 failure mode one: the declare marker hit and no kind existed.

    Mutation: remove `дрон` from KIND_MARKERS.
    """
    assert _kind("Атака дронів-камікадзе") == (ThreatKind.DRONE, KindState.DECLARED)


def test_the_short_ballistic_form_is_a_missile_declaration() -> None:
    """F71 failure mode two, and the most expensive one.

    The channel announces ballistics as `Загроза балістики`, which carried no
    declare marker while the table listed only the longer
    `загроза застосування` and `загроза удар`. MISSILE therefore resolved on
    1.0% of declarations, and the missile rule is the only one that has ever
    passed its own regime gate.

    Mutation: restore the two long declare markers in place of `загроза`.
    """
    assert _kind("Загроза балістики") == (ThreatKind.MISSILE, KindState.DECLARED)


def test_the_adjectival_ballistic_form_also_resolves() -> None:
    """`балістичного озброєння` is not a superstring of `балістик`.

    Found while testing this repair rather than by the measurement that
    prompted it: the stem was one letter too long and missed every adjectival
    form. Mutation: lengthen the stem back to `балістик`.
    """
    assert _kind("Загроза застосування балістичного озброєння") == (
        ThreatKind.MISSILE,
        KindState.DECLARED,
    )


def test_guided_bombs_resolve_in_both_the_long_and_the_short_form() -> None:
    """F71 failure modes three and four: `Загроза керованих авіабомб` / `КАБ`."""
    assert _kind("Загроза керованих авіабомб") == (
        ThreatKind.GLIDE_BOMB,
        KindState.DECLARED,
    )
    assert _kind("Загроза КАБ") == (ThreatKind.GLIDE_BOMB, KindState.DECLARED)


def test_an_artillery_lift_is_classified_rather_than_discarded() -> None:
    """A means of attack the source names must have somewhere to land.

    `Відбій загрози артобстрілу` was refused entirely because artillery had no
    member in `ThreatKind`, so a message the channel plainly made was thrown
    away rather than classified. Mutation: remove ARTILLERY from the enum's
    marker entries.
    """
    assert _kind("Відбій загрози артобстрілу") == (
        ThreatKind.ARTILLERY,
        KindState.LIFTED,
    )


def test_artillery_carries_no_timing_regime_and_reaches_no_rule() -> None:
    """Reported, never alarmed, and the reason is geography rather than caution.

    `Regime` names MISSILE and DRONE explicitly and the rules compare with
    `is`, so an artillery event cannot reach an alarm rule. Artillery does not
    range to the Polish border, and giving it a regime would invent one for a
    threat this project cannot warn anyone about.
    """
    from mavo.policy import Regime

    kinds = {regime.threat_kind for regime in Regime}
    assert ThreatKind.ARTILLERY not in kinds


def test_a_declare_marker_alone_resolves_nothing() -> None:
    """`загроза` is broad, and breadth is bounded on the other side.

    A declaration needs a declare marker *and* exactly one kind marker, so the
    short marker cannot turn an unrelated sentence into a classification.
    Mutation: accept a declaration when no kind marker is present.
    """
    assert _kind("Загроза минула, дякуємо за увагу") is None


def test_a_lift_naming_no_means_is_refused_rather_than_guessed() -> None:
    """`Відбій загрози` with no means named is not a lift of anything known."""
    assert _kind("Відбій загрози") is None


def test_two_named_means_still_resolve_to_nothing() -> None:
    """Unchanged by this repair, and deliberately so.

    A message naming both a missile and a drone is not one declaration this
    parser can act on, and picking either would be the arbitrary-match defect
    F59 recorded.
    """
    assert _kind("Загроза балістики та БпЛА") is None


def test_a_lift_wins_over_a_declaration_in_the_same_message() -> None:
    """Lift is evaluated first, which is what bounds the inversion risk.

    A message containing both a lift phrase and a declare marker reads as a
    lift. The alternative, a stale declaration raised by a message announcing
    the end of one, is the worst failure this table has available.

    Mutation: evaluate the declare markers first.

    The first version of this test used `Відбій загрози застосування
    балістики`, which contains `загрози` in the genitive and therefore no
    declare marker at all, so the mutation passed it. The text here carries
    both markers in the forms the tables actually list. Third time in two
    sprints that a test passed on data unable to distinguish the two
    implementations; the pattern is the point.
    """
    assert _kind("Відбій загрози. Загроза балістики більше не актуальна") == (
        ThreatKind.MISSILE,
        KindState.LIFTED,
    )


def test_the_channel_lifts_a_threat_in_four_phrasings_and_all_four_resolve() -> None:
    """0.19.4.0. The lift table listed one of them and dropped the rest.

    All four measured in the near-miss pile on 2026-08-10, after the first
    repair: the narrow `відбій загрози` matched only the first.

    Mutation: narrow the marker back to `відбій загрози`.
    """
    assert _kind("Відбій загрози артобстрілу") == (
        ThreatKind.ARTILLERY,
        KindState.LIFTED,
    )
    assert _kind("Відбій атаки дронів-камікадзе") == (ThreatKind.DRONE, KindState.LIFTED)
    assert _kind("Відбій атак дронів-камікадзе") == (ThreatKind.DRONE, KindState.LIFTED)
    assert _kind("Відбій по КАБам") == (ThreatKind.GLIDE_BOMB, KindState.LIFTED)


def test_a_lift_is_never_read_as_a_fresh_declaration() -> None:
    """The inversion guard, and it exists because the near miss was measured.

    `Відбій атаки дронів-камікадзе` is refused rather than inverted today only
    because `атака дрон` does not match `атаки дронів` - an accident of
    declension, not a control. Adding `атак` to the declare table, which is
    the obvious way to catch `Атака ударних БПЛА`, would turn every lift of
    that shape into a fresh DECLARED: an alarm raised by the message
    announcing its end.

    This test asserts the property rather than the accident. A message
    carrying a lift phrase reads as a lift no matter what else it carries, so
    the declare extension can be considered on its own merits instead of
    silently trading an inversion for coverage.

    Mutation: evaluate the declare markers before the lift markers.
    """
    for text in (
        "Відбій атаки дронів-камікадзе",
        "Відбій загрози застосування балістичного озброєння",
        "Відбій загрози. Загроза балістики більше не актуальна",
    ):
        classified = _kind(text)
        assert classified is not None, text
        assert classified[1] is KindState.LIFTED, f"{text} read as a declaration"


def test_the_dead_marker_is_gone_and_stays_gone() -> None:
    """`небезпека` measured zero hits twice, on two substantially different tables.

    Kept as a hedge it would be a claim about the channel that the channel has
    refused 61,041 times. Removed at 0.19.4.0. The test is here so that
    re-adding it is a decision somebody makes rather than a line somebody
    types.
    """
    from mavo.sources.telegram import KIND_DECLARE_MARKERS

    assert "небезпека" not in KIND_DECLARE_MARKERS


def test_an_alert_naming_two_kinds_reports_unknown_rather_than_the_first_row() -> None:
    """`classify_message` picked the kind by KIND_MARKERS insertion order (F86).

    `classify_kind_message` refuses a message naming two means; the alert path
    beside it resolved the same ambiguity to whichever marker happened to be
    defined first in the table - a semantic decision hidden in a dict's
    insertion order, and one a table reordering would silently change. A
    message naming missiles and drones together now reads as UNKNOWN, the same
    refusal the kind path already makes. A message naming one means in two
    forms (`ракет` beside `баліст`) still resolves, because both rows name the
    same kind. Mutation: restore the first-match `next()`.
    """
    from mavo.schema import AlertState
    from mavo.sources.telegram import classify_message

    table = AreaTable.from_csv()
    both = classify_message(
        f"Повітряна тривога: ракетна небезпека та атака шахедів {TAG}", table
    )
    assert both and both[0].state is AlertState.ACTIVE
    assert both[0].kind is ThreatKind.UNKNOWN, (
        "two named means is not a classification, on the alert path as on the kind path"
    )

    same_kind = classify_message(
        f"Повітряна тривога: балістика, швидкісна ракета {TAG}", table
    )
    assert same_kind and same_kind[0].kind is ThreatKind.MISSILE
