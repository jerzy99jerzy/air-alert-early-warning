"""T32. Distance from each area to the Polish border, computed offline.

Writes `data/reference/border_km.csv`. Run when either source is refreshed;
never in the warning path, which is the whole point of D-016: no key, no rate
limit, and no third party learning which raions a Polish user asks about at
three in the morning.

## What is computed, and what is not

**Computed:** the geodesic distance from the area's registered centre point to
the nearest point on the Polish state border, and the radius of a disc with the
same area as the area itself. From those two, an interval: the true
nearest-edge distance cannot be smaller than `centre - radius` and cannot be
larger than `centre + radius`.

**Not computed: the nearest-edge distance itself.** That needs the area's
polygon, and no polygon source reachable from here carries KATOTTG codes. The
gap is not cosmetic: Sambirskyi raion touches Poland, so its true distance is
zero while its centre sits 14 km away. An interval that contains zero says
"this area may reach the border"; a single number saying 14 km would say
something false with a decimal point on it.

This is a deliberate deviation from T32's own acceptance criterion, which asked
for one scalar. Recorded rather than quietly taken: the replacement is harder to
produce and harder to quote, not easier, which is the only condition under which
this project permits a criterion to move after the fact.

## Sources, and why these

`--register`: `data/out/katottg.csv` from `github.com/alexbabintsev/ua-geo`, MIT,
which joins the state KATOTTG register to OpenStreetMap relations and publishes
a centre point and an area for each. The join is theirs and is trusted as
*reported*, not measured here; what is measured here is the distance.

`--border`: `data/reference/poland_outline.json`, which is the Poland feature
of `ne_10m_admin_0_countries.geojson` from Natural Earth
(`github.com/nvkelso/natural-earth-vector`), public domain, extracted unmodified
and vendored at 33 KB so this measurement is reproducible from the tree alone. Nominal scale
1:10,000,000, so its own positional error is of order a kilometre — two orders
below the centroid uncertainty above, which is why refining it would be work
spent on the wrong term.

The register is not vendored: 4 MB of national codifier against a 2.8 kLOC
package, and it is refreshed on someone else's schedule. Its SHA-256 goes into
the output header instead, so a rerun that produces different numbers can be
told apart from a rerun against different inputs.

## Method

Point-to-great-circle-arc distance on a sphere of radius 6371.0088 km, clamped
to each segment, minimised over every vertex pair of the Polish outline. No
projection, no external dependency. Sphericity costs under 0.5% at these
distances, which is inside the rounding.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "reference" / "border_km.csv"
POLAND_OUTLINE = ROOT / "data" / "reference" / "poland_outline.json"
TAG_MAP = ROOT / "data" / "reference" / "tag_map.csv"

EARTH_RADIUS_KM = 6371.0088

Vector = tuple[float, float, float]

# Verified by hand against independent knowledge of these places before the
# column was trusted anywhere, as T32 requires. Each is a settlement whose
# distance to Poland is checkable on any map; the tolerance is wide because the
# check is for a wrong method, not a wrong decimal.
SPOT_CHECKS: tuple[tuple[str, float, float, float, float], ...] = (
    ("Lviv", 24.0316, 49.8397, 50.0, 70.0),
    ("Uzhhorod", 22.2879, 48.6208, 40.0, 70.0),
    # 75-100 and not the 90-130 first written here: that range was an estimate
    # rather than a check, and the tool caught it at 85.1 km. Confirmed against
    # a flat-earth cross-check (86.4 km) and the nearest border vertex
    # (24.130, 50.869) before the bound was widened. Widening a bound because
    # the measurement disagreed is only allowed when the bound is what was
    # wrong, and it is recorded here so the next reader can dispute it.
    ("Lutsk", 25.3424, 50.7472, 75.0, 100.0),
    ("Kyiv", 30.5234, 50.4501, 420.0, 480.0),
)


def to_unit_vector(lon: float, lat: float) -> Vector:
    lon_r, lat_r = math.radians(lon), math.radians(lat)
    return (
        math.cos(lat_r) * math.cos(lon_r),
        math.cos(lat_r) * math.sin(lon_r),
        math.sin(lat_r),
    )


def _angle(a: Vector, b: Vector) -> float:
    dot = max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]))
    return math.acos(dot)


def _cross(a: Vector, b: Vector) -> Vector:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def distance_to_arc_km(point: Vector, start: Vector, end: Vector) -> float:
    """Distance from ``point`` to the great-circle arc ``start``-``end``.

    Clamped to the segment: when the foot of the perpendicular falls outside it,
    the nearer endpoint wins. Without the clamp a segment would attract points
    beyond its own ends and the border would appear to extend past its corners.
    """
    normal = _cross(start, end)
    magnitude = math.sqrt(sum(component * component for component in normal))
    if magnitude == 0.0:
        return _angle(point, start) * EARTH_RADIUS_KM
    normal = (normal[0] / magnitude, normal[1] / magnitude, normal[2] / magnitude)

    height = point[0] * normal[0] + point[1] * normal[1] + point[2] * normal[2]
    foot_raw = (
        point[0] - height * normal[0],
        point[1] - height * normal[1],
        point[2] - height * normal[2],
    )
    foot_magnitude = math.sqrt(sum(component * component for component in foot_raw))
    if foot_magnitude == 0.0:
        return _angle(point, start) * EARTH_RADIUS_KM
    foot = (
        foot_raw[0] / foot_magnitude,
        foot_raw[1] / foot_magnitude,
        foot_raw[2] / foot_magnitude,
    )

    span = _angle(start, end)
    if abs(_angle(start, foot) + _angle(foot, end) - span) < 1e-9:
        return abs(math.asin(max(-1.0, min(1.0, height)))) * EARTH_RADIUS_KM
    return min(_angle(point, start), _angle(point, end)) * EARTH_RADIUS_KM


def polish_outline(path: Path) -> list[Vector]:
    """Every vertex of Poland's national outline, as unit vectors.

    The whole outline rather than the Ukrainian segment alone: which stretch of
    border is nearest is the question, not an input to it, and an area in
    Zakarpattia can be nearer to the Slovak-facing corner than to anything on
    the Ukrainian frontier.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    poland = next(
        feature
        for feature in data["features"]
        if feature["properties"].get("ADM0_A3") == "POL"
    )
    geometry = poland["geometry"]
    rings: Iterable[list[list[float]]] = (
        geometry["coordinates"]
        if geometry["type"] == "Polygon"
        else [ring for polygon in geometry["coordinates"] for ring in polygon]
    )
    return [to_unit_vector(lon, lat) for ring in rings for lon, lat in ring]


def nearest_km(point: Vector, outline: list[Vector]) -> float:
    return min(
        distance_to_arc_km(point, outline[index], outline[index + 1])
        for index in range(len(outline) - 1)
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(register: Path, border: Path) -> tuple[list[dict[str, str]], list[str]]:
    outline = polish_outline(border)
    problems: list[str] = []

    for name, lon, lat, low, high in SPOT_CHECKS:
        measured = nearest_km(to_unit_vector(lon, lat), outline)
        if not low <= measured <= high:
            problems.append(
                f"spot check {name}: {measured:.1f} km outside the hand-verified "
                f"range {low}-{high} km. The method is wrong, not the decimal"
            )

    with register.open(encoding="utf-8") as handle:
        geometry = {row["code"]: row for row in csv.DictReader(handle)}
    with TAG_MAP.open(encoding="utf-8") as handle:
        tags = list(csv.DictReader(handle))

    rows: list[dict[str, str]] = []
    for tag in tags:
        code = tag["katottg_code"]
        if not code:
            # No register code, no geometry, no distance. Printed nowhere rather
            # than printed as zero.
            continue
        found = geometry.get(code)
        if found is None:
            problems.append(f"{tag['tag']}: code {code} has no geometry in the register")
            continue
        centre = nearest_km(to_unit_vector(float(found["lon"]), float(found["lat"])), outline)
        area_km2 = float(found["area_km2"]) if found.get("area_km2") else None
        if area_km2 is None or area_km2 <= 0:
            problems.append(f"{tag['tag']}: no area, so no interval can be stated")
            continue
        radius = math.sqrt(area_km2 / math.pi)
        rows.append(
            {
                "tag": tag["tag"],
                "katottg_code": code,
                "centre_km": f"{centre:.1f}",
                "radius_km": f"{radius:.1f}",
                "lower_km": f"{max(0.0, centre - radius):.1f}",
                "upper_km": f"{centre + radius:.1f}",
            }
        )
    return rows, problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", type=Path, required=True)
    parser.add_argument("--border", type=Path, default=POLAND_OUTLINE)
    parser.add_argument("--out", type=Path, default=OUTPUT)
    arguments = parser.parse_args()

    rows, problems = build(arguments.register, arguments.border)
    for problem in problems:
        print(f"border-distance: {problem}")
    if problems:
        return 1

    header = (
        "# Distance from each area's registered centre to the Polish border, in km.\n"
        "# NOT the nearest-edge distance: use the interval, never centre_km alone.\n"
        f"# register  sha256:{digest(arguments.register)}  ua-geo data/out/katottg.csv\n"
        f"# border    sha256:{digest(arguments.border)}  natural earth 10m admin_0 countries\n"
        "# method    tools/border_distance.py, geodesic point-to-arc, R=6371.0088 km\n"
    )
    with arguments.out.open("w", encoding="utf-8", newline="") as handle:
        handle.write(header)
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "tag", "katottg_code", "centre_km", "radius_km", "lower_km", "upper_km",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"border-distance: {len(rows)} areas written to {arguments.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
