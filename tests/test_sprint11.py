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
