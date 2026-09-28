"""Synthetic urban cadastre generator.

The problem statement ships no dataset, so we build our own *ground truth* --
a city whose correct answer we know exactly. Everything downstream is then
measurable: we corrupt a copy of this city (see :mod:`kshetra.synth.corruption`),
run the harmonisation pipeline, and score how much of the damage was recovered.

The layout follows how Indian urban land actually subdivides:

* an irregular road grid defines blocks;
* each block is a parent *khasra*, recursively split into sub-divided plots
  numbered ``<parent>/<child>``;
* buildings sit inside plots with a setback and a coverage ratio;
* recorded area in the revenue record deliberately drifts from the surveyed
  geometric area, exactly as it does in practice.

Nothing here touches the network, so the demo dataset is reproducible offline
from a seed alone.
"""
from __future__ import annotations

import numpy as np
from shapely.affinity import rotate as shp_rotate
from shapely.geometry import Polygon, box

from kshetra.crs import geodetic_to_utm
from kshetra.layers import Feature, Layer, Provenance

__all__ = ["CityConfig", "generate_city"]

# Chandausi, Sambhal district, Uttar Pradesh: the NAKSHA pilot launch site.
ANCHOR_LON, ANCHOR_LAT = 78.7749, 28.4515

_FIRST = [
    "Ramesh", "Suresh", "Mahesh", "Rajesh", "Dinesh", "Anil", "Sunil", "Vijay",
    "Ajay", "Sanjay", "Manoj", "Rakesh", "Mukesh", "Pankaj", "Deepak", "Ashok",
    "Kamla", "Sunita", "Geeta", "Sita", "Rekha", "Anita", "Savitri", "Pushpa",
    "Mohammed", "Abdul", "Iqbal", "Farhan", "Salim", "Nasir", "Shabana", "Ayesha",
]
_LAST = [
    "Kumar", "Singh", "Sharma", "Verma", "Gupta", "Yadav", "Pal", "Saxena",
    "Agarwal", "Mishra", "Tiwari", "Chauhan", "Rathore", "Ansari", "Khan",
    "Qureshi", "Prajapati", "Maurya", "Kashyap", "Nigam",
]
_RELATION = ["s/o", "w/o", "d/o"]

# Land-use codes as they appear in north Indian revenue records.
LAND_USE = ["residential", "commercial", "mixed", "institutional", "gair_mumkin"]


class CityConfig:
    """Knobs for the generated city."""

    def __init__(
        self,
        seed: int = 42,
        blocks_x: int = 7,
        blocks_y: int = 6,
        block_size_m: float = 110.0,
        block_jitter: float = 0.22,
        road_width_m: float = 9.0,
        main_road_width_m: float = 18.0,
        min_plot_area_m2: float = 90.0,
        max_plot_area_m2: float = 320.0,
        setback_m: float = 1.6,
        building_coverage: tuple[float, float] = (0.45, 0.82),
        vacant_fraction: float = 0.09,
        area_record_drift: float = 0.035,
    ):
        self.seed = seed
        self.blocks_x = blocks_x
        self.blocks_y = blocks_y
        self.block_size_m = block_size_m
        self.block_jitter = block_jitter
        self.road_width_m = road_width_m
        self.main_road_width_m = main_road_width_m
        self.min_plot_area_m2 = min_plot_area_m2
        self.max_plot_area_m2 = max_plot_area_m2
        self.setback_m = setback_m
        self.building_coverage = building_coverage
        self.vacant_fraction = vacant_fraction
        self.area_record_drift = area_record_drift


def _road_positions(rng, n: int, size: float, jitter: float) -> np.ndarray:
    """Irregular road grid: cumulative spacing with multiplicative jitter."""
    spacings = size * (1.0 + rng.uniform(-jitter, jitter, size=n))
    return np.concatenate([[0.0], np.cumsum(spacings)])


def _subdivide(rect: Polygon, rng, cfg: CityConfig, depth: int = 0) -> list[Polygon]:
    """Recursively split a block into plots along its longer axis.

    Mirrors real subdivision: a holding is halved, the halves are halved again,
    and the process stops once plots reach a saleable size. The split ratio is
    jittered so plots are not suspiciously uniform.
    """
    if depth > 7:
        return [rect]
    area = rect.area
    if area <= cfg.max_plot_area_m2:
        if area < cfg.min_plot_area_m2 * 1.6 or rng.random() < 0.35:
            return [rect]

    minx, miny, maxx, maxy = rect.bounds
    w, h = maxx - minx, maxy - miny
    # A split that would create a plot below the minimum is not worth making.
    if min(w, h) < 6.0 or area < cfg.min_plot_area_m2 * 2:
        return [rect]

    ratio = float(np.clip(rng.normal(0.5, 0.11), 0.28, 0.72))
    if w >= h:
        cut = minx + w * ratio
        a = box(minx, miny, cut, maxy)
        b = box(cut, miny, maxx, maxy)
    else:
        cut = miny + h * ratio
        a = box(minx, miny, maxx, cut)
        b = box(minx, cut, maxx, maxy)

    return _subdivide(a, rng, cfg, depth + 1) + _subdivide(b, rng, cfg, depth + 1)


def _owner(rng) -> str:
    return (f"{rng.choice(_FIRST)} {rng.choice(_LAST)} "
            f"{rng.choice(_RELATION)} {rng.choice(_FIRST)} {rng.choice(_LAST)}")


def _ulpin(easting: float, northing: float, zone: int) -> str:
    """A ULPIN-style 14-character parcel identifier derived from position.

    ULPIN (the 'Bhu-Aadhaar') is designed to be generated from the parcel's
    geo-coordinates so that the identifier is stable and globally unique. This
    is a faithful *shape* for that identifier, not the official algorithm.
    """
    code = f"{zone:02d}{int(easting) % 1_000_000:06d}{int(northing) % 1_000_000:06d}"
    return code[:14]


def generate_city(cfg: CityConfig | None = None) -> dict[str, Layer]:
    """Build the ground-truth city.

    Returns a dict of layers: ``parcels``, ``buildings``, ``roads``,
    ``govt_land``. The parcel layer is the authoritative cadastre that all
    accuracy metrics are measured against.
    """
    cfg = cfg or CityConfig()
    rng = np.random.default_rng(cfg.seed)

    origin_e, origin_n, zone = geodetic_to_utm(ANCHOR_LON, ANCHOR_LAT)
    origin_e, origin_n = float(origin_e), float(origin_n)

    xs = _road_positions(rng, cfg.blocks_x, cfg.block_size_m, cfg.block_jitter)
    ys = _road_positions(rng, cfg.blocks_y, cfg.block_size_m, cfg.block_jitter)

    # Two arterial roads get extra width; everything else is a local street.
    main_x = int(rng.integers(1, max(2, cfg.blocks_x - 1)))
    main_y = int(rng.integers(1, max(2, cfg.blocks_y - 1)))

    parcels = Layer(
        "parcels_ground_truth", crs=f"EPSG:{32600 + zone}",
        provenance=Provenance("ground_truth", "Ground truth cadastre",
                              accuracy_m=0.02, vintage=2026, authority=True),
    )
    buildings = Layer(
        "buildings_ground_truth", crs=f"EPSG:{32600 + zone}",
        provenance=Provenance("ground_truth", "Ground truth footprints",
                              accuracy_m=0.02, vintage=2026),
    )
    roads = Layer("roads", crs=f"EPSG:{32600 + zone}")
    govt = Layer(
        "govt_land", crs=f"EPSG:{32600 + zone}",
        provenance=Provenance("municipal", "Government / public land",
                              accuracy_m=0.5, vintage=2024, authority=True),
    )

    # --- roads ----------------------------------------------------------
    total_w = float(xs[-1])
    total_h = float(ys[-1])
    for i, x in enumerate(xs):
        hw = (cfg.main_road_width_m if i == main_x else cfg.road_width_m) / 2
        roads.add(Feature(
            f"road_v{i}",
            box(origin_e + x - hw, origin_n, origin_e + x + hw, origin_n + total_h),
            {"kind": "arterial" if i == main_x else "local", "axis": "NS"},
        ))
    for j, y in enumerate(ys):
        hw = (cfg.main_road_width_m if j == main_y else cfg.road_width_m) / 2
        roads.add(Feature(
            f"road_h{j}",
            box(origin_e, origin_n + y - hw, origin_e + total_w, origin_n + y + hw),
            {"kind": "arterial" if j == main_y else "local", "axis": "EW"},
        ))

    # --- blocks, plots, buildings ---------------------------------------
    khasra_parent = 100
    pid = 0
    bid = 0

    for bi in range(cfg.blocks_x):
        for bj in range(cfg.blocks_y):
            hw_l = (cfg.main_road_width_m if bi == main_x else cfg.road_width_m) / 2
            hw_r = (cfg.main_road_width_m if bi + 1 == main_x else cfg.road_width_m) / 2
            hw_b = (cfg.main_road_width_m if bj == main_y else cfg.road_width_m) / 2
            hw_t = (cfg.main_road_width_m if bj + 1 == main_y else cfg.road_width_m) / 2

            blk = box(
                origin_e + xs[bi] + hw_l, origin_n + ys[bj] + hw_b,
                origin_e + xs[bi + 1] - hw_r, origin_n + ys[bj + 1] - hw_t,
            )
            if blk.area < cfg.min_plot_area_m2:
                continue

            khasra_parent += 1

            # Roughly one block in nine is public land -- a park, school, tank
            # or office. These are the parcels encroachment is measured against.
            if rng.random() < 0.11:
                govt.add(Feature(
                    f"govt_{khasra_parent}", blk,
                    {
                        "khasra_no": f"{khasra_parent}",
                        "owner_name": "State Government",
                        "land_use": "institutional",
                        "category": rng.choice(["park", "school", "tank", "office"]),
                        "area_sqm": round(blk.area, 2),
                    },
                ))
                continue

            # Frontage on an arterial road pushes land use commercial.
            on_arterial = (bi in (main_x - 1, main_x)) or (bj in (main_y - 1, main_y))
            plots = _subdivide(blk, rng, cfg)

            for k, plot in enumerate(plots, start=1):
                if plot.area < cfg.min_plot_area_m2 * 0.5:
                    continue
                pid += 1
                geom_area = plot.area

                if on_arterial and rng.random() < 0.55:
                    use = rng.choice(["commercial", "mixed"], p=[0.62, 0.38])
                elif rng.random() < 0.06:
                    use = "institutional"
                else:
                    use = rng.choice(["residential", "mixed"], p=[0.88, 0.12])

                # Recorded area drifts from surveyed area -- chain-survey error,
                # rounding to local units, and un-recorded encroachment.
                recorded = geom_area * (1.0 + rng.normal(0, cfg.area_record_drift))

                cx, cy = plot.centroid.x, plot.centroid.y
                parcels.add(Feature(
                    f"P{pid:05d}", plot,
                    {
                        "khasra_no": f"{khasra_parent}/{k}",
                        "parent_khasra": str(khasra_parent),
                        "owner_name": _owner(rng),
                        "area_sqm": round(geom_area, 2),
                        "recorded_area_sqm": round(recorded, 2),
                        "land_use": use,
                        "tenure": rng.choice(
                            ["freehold", "leasehold", "abadi"], p=[0.66, 0.20, 0.14]),
                        "ward_no": f"W{(bi // 2) * 3 + (bj // 2) + 1:02d}",
                        "ulpin": _ulpin(cx, cy, zone),
                        "block_i": bi, "block_j": bj,
                    },
                ))

                # --- building inside the plot ---------------------------
                if rng.random() < cfg.vacant_fraction:
                    continue
                pad = plot.buffer(-cfg.setback_m)
                if pad.is_empty or pad.area < 20:
                    continue
                if pad.geom_type == "MultiPolygon":
                    pad = max(pad.geoms, key=lambda g: g.area)

                cover = rng.uniform(*cfg.building_coverage)
                shrink = np.sqrt(cover)
                minx, miny, maxx, maxy = pad.bounds
                w, h = (maxx - minx) * shrink, (maxy - miny) * shrink
                ox = rng.uniform(0, (maxx - minx) - w)
                oy = rng.uniform(0, (maxy - miny) - h)
                fp = box(minx + ox, miny + oy, minx + ox + w, miny + oy + h)
                # Buildings are rarely perfectly axis-aligned on the ground.
                fp = shp_rotate(fp, rng.normal(0, 1.4), origin="centroid")

                bid += 1
                storeys = int(np.clip(rng.poisson(1.6) + 1, 1, 6))
                buildings.add(Feature(
                    f"B{bid:05d}", fp,
                    {
                        "parcel_fid": f"P{pid:05d}",
                        "khasra_no": f"{khasra_parent}/{k}",
                        "storeys": storeys,
                        "height_m": round(storeys * 3.1 + rng.normal(0, 0.4), 2),
                        "roof_type": rng.choice(["rcc", "tin", "tile"],
                                                p=[0.70, 0.20, 0.10]),
                        "area_sqm": round(fp.area, 2),
                        "use": use,
                    },
                ))

    return {"parcels": parcels, "buildings": buildings,
            "roads": roads, "govt_land": govt}
