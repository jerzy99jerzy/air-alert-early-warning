"""The unit word filters prose resolution; the register's refusals are named.

F130. `resolve_prose` read the unit word only when two rows shared a name,
which is one name in the table. For the other 131 it was matched and thrown
away, so `Харківська область` resolved to the Kharkiv city hromada and put the
city's 853-874 km border interval on an oblast-level alert. 583 tests passed
on both sides of that behaviour; these are the ones that could not have.

F131. A row the file marks `ambiguous_4` is dropped from the name index at
load, so a name the register holds and declines printed identically to a name
nobody has seen. Production showed both in one reading: Pokrovska hromada,
alerting with artillery, in the file, reported with the same word as
Vovchansk, which is not in the file at all.

The fixtures here are the live payload's own name strings from the reading of
2026-08-30, not constructed forms: constructing `Харківська область` from a
pattern is how F130's live-defect claim was wrongly made in the first place,
and the API was measured never to send it. The form appears below only as what
it is, a latent input, asserted to stay latent.
"""

from mavo.areas import AreaTable, normalise_name


def table() -> AreaTable:
    return AreaTable.from_csv()


def test_wrong_level_form_resolves_to_nothing_and_is_declined() -> None:
    """`Харківська область`: the name is held, only as a hromada.

    Before F130 this returned the hromada row. Nothing in the live payload
    sends this form; the assertion is that if anything ever does, it becomes a
    visible refusal rather than a wrong border distance.
    """
    resolved, declined = table().resolve_prose_detail("Харківська область")
    assert resolved == ()
    assert normalise_name("Харківська") in declined


def test_the_tiebreak_pair_still_narrows_both_ways() -> None:
    """Zaporizhzhia is the one name two rows share; F130 must not disturb it."""
    t = table()
    oblast = t.resolve_prose("Запорізька область")
    hromada = t.resolve_prose("Запорізька громада")
    assert [a.unit for a in oblast] == ["O"]
    assert [a.unit for a in hromada] == ["H"]
    assert oblast[0].code != hromada[0].code


def test_single_candidate_at_the_right_level_still_resolves() -> None:
    """Donetsk oblast: one row, correct level. Right by check now, not luck."""
    resolved = table().resolve_prose("Донецька область")
    assert [a.unit for a in resolved] == ["O"]


def test_every_row_still_resolves_from_its_own_form() -> None:
    """The guard for the 45-ok class: no correct resolution was lost to F130.

    Each resolvable row, rendered as `{name} {its own unit word}`, must come
    back as itself. This is the sweep that measured 0 lost before the change
    shipped, pinned so it stays 0.
    """
    t = table()
    word = {"P": "район", "H": "громада", "O": "область"}
    for tag in t.tags:
        ref = t.resolve(tag)
        assert ref is not None
        resolved = t.resolve_prose(f"{ref.name} {word[ref.unit]}")
        assert ref in resolved, f"{ref.name} [{ref.unit}] no longer resolves itself"


def test_wrong_level_forms_never_resolve_for_any_row() -> None:
    """The other half of the sweep: the 262 wrong-level pairs stay removed."""
    t = table()
    word = {"P": "район", "H": "громада", "O": "область"}
    for tag in t.tags:
        ref = t.resolve(tag)
        assert ref is not None
        for unit, unit_word in word.items():
            if unit == ref.unit:
                continue
            for hit in t.resolve_prose(f"{ref.name} {unit_word}"):
                assert hit.name != ref.name or hit.unit != ref.unit, (
                    f"{ref.name} [{ref.unit}] resolves under the {unit} word"
                )


def test_ambiguous_row_is_declined_not_absent() -> None:
    """F131, the live half: Pokrovska is in the file and must say so.

    The payload of 2026-08-30 carried `Покровська територіальна громада`
    alerting with artillery. The file holds the row as `ambiguous_4`.
    """
    resolved, declined = table().resolve_prose_detail("Покровська територіальна громада")
    assert resolved == ()
    assert normalise_name("Покровська") in declined


def test_absent_vocabulary_is_silent_in_both_halves() -> None:
    """F131, the control: Vovchansk is not in the file and must say nothing.

    A declined list that fires on absent names is the conflation back with the
    words swapped.
    """
    resolved, declined = table().resolve_prose_detail("Вовчанська територіальна громада")
    assert resolved == ()
    assert declined == ()


def test_load_retains_the_names_it_declines() -> None:
    """`from_csv` keeps the register names of rows it drops from the index."""
    assert normalise_name("Покровська") in table().unresolved_names
