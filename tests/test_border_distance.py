"""T32 regressions: a distance that says what it does not know.

The column exists because a report that names a raion and not a distance is not
yet usable at three in the morning. It is an interval rather than a scalar
because the areas a scalar is most wrong about are the border ones: Sambirskyi
raion touches Poland, so its true distance is zero while its registered centre
sits 14 km away.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from mavo.areas import AreaTable
from tools.border_distance import (
    POLAND_OUTLINE,
    SPOT_CHECKS,
    distance_to_arc_km,
    nearest_km,
    polish_outline,
    to_unit_vector,
)

ABSENT = Path("/tmp/mavo-no-such-distance-file.csv")


@pytest.fixture(scope="module")
def table() -> AreaTable:
    return AreaTable.from_csv()


def test_every_resolved_area_carries_an_interval(table: AreaTable) -> None:
    """127 of 127, or the column is not a column."""
    missing = [tag for tag in table.tags if table.resolve(tag).border_centre_km is None]
    assert missing == [], f"{len(missing)} areas have no distance: {missing[:5]}"


def test_the_interval_contains_the_centre_and_never_goes_negative(table: AreaTable) -> None:
    """A lower bound below zero would be a claim about the other side of the border."""
    for tag in table.tags:
        area = table.resolve(tag)
        assert area.border_lower_km is not None
        assert area.border_upper_km is not None
        assert 0.0 <= area.border_lower_km <= area.border_centre_km <= area.border_upper_km


def test_a_border_touching_raion_admits_it_may_reach_zero(table: AreaTable) -> None:
    """The case the scalar got wrong, asserted by name.

    Sambirskyi, Yavorivskyi, Chervonohradskyi and Volodymyr-Volynskyi raions all
    share an edge with Poland. Any distance column that reports a positive
    minimum for them is reporting something false, however precise it looks.
    """
    for tag in (
        "Самбірський_район",
        "Яворівський_район",
        "Червоноградський_район",
        "ВолодимирВолинський_район",
    ):
        area = table.resolve(tag)
        assert area.border_lower_km == 0.0, f"{tag} claims it cannot reach the border"
        assert area.border_centre_km > 0.0


def test_the_east_is_far_and_the_west_is_near(table: AreaTable) -> None:
    """A sanity ordering no plausible bug survives.

    Every Lviv-oblast area must be nearer to Poland than every Kharkiv-oblast
    one, with no overlap between the two groups' intervals.
    """
    west = [table.resolve(t) for t in table.tags if table.resolve(t).oblast == "Львівська"]
    east = [table.resolve(t) for t in table.tags if table.resolve(t).oblast == "Харківська"]
    assert west and east
    assert max(a.border_upper_km or 0 for a in west) < min(a.border_lower_km or 0 for a in east)


def test_unknown_prints_as_unknown() -> None:
    """No distance file, no distances, and the report says so.

    The sources are not vendored, so a checkout can legitimately lack the
    column. What it must not do is fall back to a plausible number.
    """
    table = AreaTable.from_csv(distance_path=ABSENT)
    area = table.resolve("Львівський_район")
    assert area.border_centre_km is None
    assert area.border_interval == "unknown"


def test_the_spot_checks_still_hold() -> None:
    """T32 asks for a hand-verified check before the column is trusted.

    Running it here as well as in the generator means a source refresh that
    moves the geometry cannot pass unnoticed: the tool is run rarely, the suite
    on every commit.
    """
    outline = polish_outline(POLAND_OUTLINE)
    for name, lon, lat, low, high in SPOT_CHECKS:
        measured = nearest_km(to_unit_vector(lon, lat), outline)
        assert low <= measured <= high, f"{name}: {measured:.1f} km"


def test_the_arc_distance_is_clamped_to_its_segment() -> None:
    """Without the clamp a segment attracts points beyond its own ends.

    A point due east of a short equatorial segment must measure to the segment's
    end, not to the great circle that segment lies on, which would run all the
    way round the planet and read as zero.
    """
    start, end = to_unit_vector(0.0, 0.0), to_unit_vector(1.0, 0.0)
    beyond = to_unit_vector(3.0, 0.0)
    expected = 2.0 * math.radians(1.0) * 6371.0088
    assert distance_to_arc_km(beyond, start, end) == pytest.approx(expected, rel=1e-6)
