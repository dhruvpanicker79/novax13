"""Controlled degradation of a ground-truth cadastre.

This is the scientific core of the project. Because we generate the ground
truth ourselves, we can damage a copy of it in precisely known ways and then
measure how much of that damage the harmonisation pipeline recovers. Every
headline number in the evaluation comes from here.

The damage model is not arbitrary. Each stage reproduces a failure mode that
is documented in real cadastral modernisation work:

===========================  =====================================================
Stage                        Real-world cause
===========================  =====================================================
Similarity misregistration   Sheet georeferenced from too few, poorly spread GCPs
Smooth non-linear warp       Paper shrinkage, scanner distortion, map-sheet join
Vertex jitter                Manual digitisation from a paper sheet
Vertex decimation            Generalisation during digitisation
Sliver / gap injection       Independent digitising of adjacent parcels
Overlap injection            Double-counted boundaries between survey epochs
Self-intersection            Careless digitising, unclosed rings
Attribute schema drift       Every department names its columns differently
Owner-name corruption        Transliteration variance, typos, abbreviation
Area unit drift              Records kept in bigha / biswa / sq yards, not m2
Split / merge / missing      Subdivision and amalgamation since the last survey
===========================  =====================================================
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

from kshetra.geometry import safe_polygon
from kshetra.layers import Feature, Layer, Provenance

__all__ = ["CorruptionConfig", "CorruptionTruth", "corrupt_cadastre"]


# Department-style column names, as encountered across Indian revenue systems.
SCHEMA_ALIASES = {
    "khasra_no": "KHSRA_NUM",
    "owner_name": "KHATEDAR_NM",
    "recorded_area_sqm": "AREA_BIGHA",
    "land_use": "LU_CODE",
    "tenure": "TENURE_TYP",
    "ward_no": "WARD",
    "ulpin": "PARCEL_UID",
}

# 1 bigha (pucca, UP) = 3025 sq yards = 2529.3 m2. Records in many north
# Indian districts are still maintained in bigha/biswa rather than m2.
SQM_PER_BIGHA = 2529.285


@dataclass
class CorruptionConfig:
    seed: int = 7
    # --- geometric ---
    shift_m: tuple[float, float] = (6.5, -4.2)
    rotation_deg: float = 0.85
    scale: float = 1.0016
    warp_amplitude_m: float = 2.4
    warp_control_points: int = 9
    vertex_jitter_m: float = 0.35
    decimate_prob: float = 0.10
    # --- topology ---
    sliver_fraction: float = 0.06
    sliver_shrink_m: float = 0.45
    overlap_fraction: float = 0.05
    overlap_grow_m: float = 0.55
    bowtie_fraction: float = 0.012
    duplicate_vertex_fraction: float = 0.04
    # --- attributes ---
    rename_schema: bool = True
    area_in_bigha: bool = True
    owner_typo_fraction: float = 0.14
    missing_attr_fraction: float = 0.05
    # Fraction of blocks whose parent khasra series is entirely renumbered, as
    # happens after a resurvey. This is what makes the identifier unusable as a
    # join key and forces genuine spatial matching -- without it a model will
    # simply learn to join on khasra_no and the geometry is never used.
    khasra_renumber_block_fraction: float = 0.45
    # Fraction of owners that differ because the property genuinely changed
    # hands since the legacy survey. No amount of fuzzy matching recovers these.
    owner_changed_fraction: float = 0.12
    # --- records ---
    split_fraction: float = 0.04
    merge_fraction: float = 0.03
    missing_record_fraction: float = 0.025
    spurious_fraction: float = 0.02


@dataclass
class CorruptionTruth:
    """Everything we did, so the evaluator can score recovery exactly."""
    applied_shift: tuple[float, float] = (0.0, 0.0)
    applied_rotation_deg: float = 0.0
    applied_scale: float = 1.0
    warp_centres: np.ndarray | None = None
    warp_vectors: np.ndarray | None = None
    # legacy_fid -> list of ground-truth fids it corresponds to
    correspondence: dict[str, list[str]] = field(default_factory=dict)
    # legacy_fid -> one of: one_to_one, split, merge, spurious
    relation: dict[str, str] = field(default_factory=dict)
    missing_truth_fids: list[str] = field(default_factory=list)
    injected_slivers: list[str] = field(default_factory=list)
    injected_overlaps: list[str] = field(default_factory=list)
    injected_bowties: list[str] = field(default_factory=list)
    schema_map: dict[str, str] = field(default_factory=dict)

    def n_real(self) -> int:
        return sum(1 for r in self.relation.values() if r != "spurious")


# --------------------------------------------------------------------------
# geometric damage
# --------------------------------------------------------------------------
def _similarity_matrix(shift, rot_deg, scale, origin):
    th = np.radians(rot_deg)
    c, s = np.cos(th) * scale, np.sin(th) * scale

    def fn(pts: np.ndarray) -> np.ndarray:
        p = np.asarray(pts, dtype=float)
        x = p[:, 0] - origin[0]
        y = p[:, 1] - origin[1]
        return np.column_stack([
            c * x - s * y + origin[0] + shift[0],
            s * x + c * y + origin[1] + shift[1],
        ])

    return fn


def _rbf_warp(centres: np.ndarray, vectors: np.ndarray, sigma: float):
    """Smooth non-linear displacement field (Gaussian RBF).

    Models paper shrinkage and scanner distortion: displacement varies
    smoothly across the sheet rather than jumping between parcels.
    """
    def fn(pts: np.ndarray) -> np.ndarray:
        p = np.asarray(pts, dtype=float)
        d2 = ((p[:, None, :] - centres[None, :, :]) ** 2).sum(axis=-1)
        w = np.exp(-d2 / (2 * sigma ** 2))
        return p + w @ vectors

    return fn


def _warp_polygon(poly: Polygon, fns, rng, cfg: CorruptionConfig) -> Polygon:
    coords = np.array(poly.exterior.coords)
    for fn in fns:
        coords = fn(coords)
    if cfg.vertex_jitter_m > 0:
        coords = coords + rng.normal(0, cfg.vertex_jitter_m, size=coords.shape)
    # Keep the ring closed after jittering.
    coords[-1] = coords[0]

    if cfg.decimate_prob > 0 and len(coords) > 6:
        keep = rng.random(len(coords)) > cfg.decimate_prob
        keep[0] = keep[-1] = True
        if keep.sum() >= 4:
            coords = coords[keep]
            coords[-1] = coords[0]

    return safe_polygon(Polygon(coords))


def _inject_bowtie(poly: Polygon, rng) -> Polygon:
    """Swap two adjacent vertices to create a self-intersecting ring."""
    coords = list(poly.exterior.coords)[:-1]
    if len(coords) < 4:
        return poly
    i = int(rng.integers(0, len(coords) - 1))
    coords[i], coords[i + 1] = coords[i + 1], coords[i]
    return Polygon(coords + [coords[0]])


def _duplicate_vertices(poly: Polygon, rng) -> Polygon:
    coords = list(poly.exterior.coords)
    i = int(rng.integers(0, max(1, len(coords) - 1)))
    coords.insert(i, coords[i])
    return Polygon(coords)


# --------------------------------------------------------------------------
# attribute damage
# --------------------------------------------------------------------------
_TRANSLIT = [
    ("Mohammed", "Mohd."), ("Kumar", "Kr."), ("Singh", "Sing"),
    ("Sharma", "Sarma"), ("Verma", "Varma"), ("Gupta", "Gupt"),
    ("Qureshi", "Kureshi"), ("Chauhan", "Chouhan"), ("Yadav", "Jadav"),
    ("Agarwal", "Aggarwal"), ("Mishra", "Misra"), ("Ansari", "Ansaari"),
    ("s/o", "S/O"), ("w/o", "W/O"), ("d/o", "D/O"),
]


def _corrupt_name(name: str, rng) -> str:
    """Realistic name corruption: transliteration variants, then typos.

    Indian revenue records are transcribed from Devanagari/Urdu by hand, so
    the same person routinely appears under several romanisations. Pure
    string equality fails; fuzzy matching is mandatory.
    """
    out = name
    for a, b in _TRANSLIT:
        if a in out and rng.random() < 0.55:
            out = out.replace(a, b)
    if rng.random() < 0.35 and len(out) > 6:
        i = int(rng.integers(1, len(out) - 1))
        mode = rng.random()
        if mode < 0.4:                      # drop a character
            out = out[:i] + out[i + 1:]
        elif mode < 0.7:                    # transpose
            out = out[:i] + out[i + 1] + out[i] + out[i + 2:]
        else:                               # double a character
            out = out[:i] + out[i] + out[i:]
    if rng.random() < 0.18:
        out = out.upper()
    return out


_UNREL_FIRST = ["Ramesh","Suresh","Naveen","Pooja","Kavita","Imran","Farida",
                "Devendra","Harish","Neelam","Shakeel","Bhupendra"]
_UNREL_REL = ["s/o", "w/o", "d/o"]
_UNREL_LAST = ["Srivastava","Bhardwaj","Rastogi","Dixit","Joshi","Sheikh",
               "Goswami","Tomar","Bisht","Pandey"]


def _owner_unrelated(rng) -> str:
    """A completely different owner: the plot changed hands since the survey."""
    return (f"{rng.choice(_UNREL_FIRST)} {rng.choice(_UNREL_LAST)} "
            f"{rng.choice(_UNREL_REL)} {rng.choice(_UNREL_FIRST)} "
            f"{rng.choice(_UNREL_LAST)}")


# --------------------------------------------------------------------------
# main entry point
# --------------------------------------------------------------------------
def corrupt_cadastre(truth: Layer, cfg: CorruptionConfig | None = None
                     ) -> tuple[Layer, CorruptionTruth]:
    """Produce a realistic 'legacy cadastral layer' plus the recovery key.

    Returns ``(legacy_layer, truth_record)``.
    """
    cfg = cfg or CorruptionConfig()
    rng = np.random.default_rng(cfg.seed)
    rec = CorruptionTruth()

    geoms = truth.geometries()
    all_bounds = unary_union([g.envelope for g in geoms]).bounds
    origin = ((all_bounds[0] + all_bounds[2]) / 2,
              (all_bounds[1] + all_bounds[3]) / 2)
    extent = max(all_bounds[2] - all_bounds[0], all_bounds[3] - all_bounds[1])

    # --- build the geometric distortion pipeline ------------------------
    sim = _similarity_matrix(cfg.shift_m, cfg.rotation_deg, cfg.scale, origin)
    rec.applied_shift = cfg.shift_m
    rec.applied_rotation_deg = cfg.rotation_deg
    rec.applied_scale = cfg.scale

    n_c = cfg.warp_control_points
    centres = np.column_stack([
        rng.uniform(all_bounds[0], all_bounds[2], n_c),
        rng.uniform(all_bounds[1], all_bounds[3], n_c),
    ])
    vectors = rng.normal(0, cfg.warp_amplitude_m, size=(n_c, 2))
    warp = _rbf_warp(centres, vectors, sigma=extent / 4.0)
    rec.warp_centres, rec.warp_vectors = centres, vectors

    fns = [sim, warp]

    # --- decide record-level fate for every ground-truth parcel ---------
    n = len(truth)
    idx = np.arange(n)
    rng.shuffle(idx)
    n_split = int(n * cfg.split_fraction)
    n_merge = int(n * cfg.merge_fraction) * 2   # merges consume pairs
    n_miss = int(n * cfg.missing_record_fraction)

    split_ids = set(idx[:n_split].tolist())
    merge_pool = idx[n_split:n_split + n_merge].tolist()
    missing_ids = set(idx[n_split + n_merge:n_split + n_merge + n_miss].tolist())

    # Only merge parcels that actually touch, otherwise the merge is nonsense.
    merge_pairs = []
    used = set()
    by_block: dict[tuple, list[int]] = {}
    for i in merge_pool:
        f = truth[i]
        by_block.setdefault((f.get("block_i"), f.get("block_j")), []).append(i)
    for members in by_block.values():
        for a, b in zip(members[0::2], members[1::2]):
            ga, gb = truth[a].geometry, truth[b].geometry
            if ga.buffer(0.6).intersects(gb) and a not in used and b not in used:
                merge_pairs.append((a, b))
                used.update((a, b))

    legacy = Layer(
        "parcels_legacy", crs=truth.crs,
        provenance=Provenance(
            "legacy_cadastre", "Legacy cadastral sheet (digitised)",
            accuracy_m=6.0, vintage=1987, authority=True),
    )
    if cfg.rename_schema:
        rec.schema_map = dict(SCHEMA_ALIASES)

    # --- resurvey renumbering -------------------------------------------
    # Whole blocks get a fresh khasra series, as happens after a resurvey.
    # Without this the identifier remains a perfect join key and any matcher
    # trained on the data learns to ignore geometry entirely.
    blocks = {(f.get("block_i"), f.get("block_j")) for f in truth}
    renumbered_blocks = {
        b for b in blocks if rng.random() < cfg.khasra_renumber_block_fraction
    }
    parent_remap: dict[str, str] = {}
    for f in truth:
        b = (f.get("block_i"), f.get("block_j"))
        parent = str(f.get("parent_khasra"))
        if b in renumbered_blocks and parent not in parent_remap:
            parent_remap[parent] = str(int(rng.integers(2000, 9999)))

    def build_attrs(feat, rng) -> dict:
        src_attrs = feat.attrs
        out = {}
        for k, v in src_attrs.items():
            if k in ("block_i", "block_j", "parent_khasra", "area_sqm"):
                continue
            key = SCHEMA_ALIASES.get(k, k.upper()) if cfg.rename_schema else k

            if k == "khasra_no":
                parent = str(src_attrs.get("parent_khasra"))
                if parent in parent_remap:
                    child = str(v).split("/")[-1]
                    v = f"{parent_remap[parent]}/{child}"

            if k == "owner_name":
                if rng.random() < cfg.owner_changed_fraction:
                    # Property genuinely sold since the legacy survey: the name
                    # is different, not merely misspelt. Unrecoverable by any
                    # string metric, and the model must learn to tolerate it.
                    v = _owner_unrelated(rng)
                elif rng.random() < cfg.owner_typo_fraction:
                    v = _corrupt_name(str(v), rng)

            if k == "recorded_area_sqm" and cfg.area_in_bigha:
                v = round(float(v) / SQM_PER_BIGHA, 4)
            if rng.random() < cfg.missing_attr_fraction:
                v = None
            out[key] = v
        return out

    lid = 0

    def new_fid() -> str:
        nonlocal lid
        lid += 1
        return f"L{lid:05d}"

    merged_lookup = {a: pair for pair in merge_pairs for a in pair}
    emitted_merges = set()

    for i, feat in enumerate(truth):
        if i in missing_ids:
            rec.missing_truth_fids.append(feat.fid)
            continue

        # --- merge: two ground-truth parcels become one legacy parcel ---
        if i in merged_lookup:
            pair = merged_lookup[i]
            if pair in emitted_merges:
                continue
            emitted_merges.add(pair)
            a, b = pair
            geom = safe_polygon(unary_union(
                [truth[a].geometry, truth[b].geometry]).buffer(0))
            if geom.geom_type != "Polygon":
                geom = truth[a].geometry
            g = _warp_polygon(geom, fns, rng, cfg)
            fid = new_fid()
            attrs = build_attrs(truth[a], rng)
            legacy.add(Feature(fid, g, attrs))
            rec.correspondence[fid] = [truth[a].fid, truth[b].fid]
            rec.relation[fid] = "merge"
            continue

        # --- split: one ground-truth parcel becomes two legacy parcels ---
        if i in split_ids:
            minx, miny, maxx, maxy = feat.geometry.bounds
            w, h = maxx - minx, maxy - miny
            r = float(np.clip(rng.normal(0.5, 0.08), 0.3, 0.7))
            if w >= h:
                halves = [Polygon([(minx, miny), (minx + w * r, miny),
                                   (minx + w * r, maxy), (minx, maxy)]),
                          Polygon([(minx + w * r, miny), (maxx, miny),
                                   (maxx, maxy), (minx + w * r, maxy)])]
            else:
                halves = [Polygon([(minx, miny), (maxx, miny),
                                   (maxx, miny + h * r), (minx, miny + h * r)]),
                          Polygon([(minx, miny + h * r), (maxx, miny + h * r),
                                   (maxx, maxy), (minx, maxy)])]
            for part, half in enumerate(halves, start=1):
                clipped = safe_polygon(half.intersection(feat.geometry))
                if clipped.is_empty or clipped.area < 5:
                    continue
                if clipped.geom_type != "Polygon":
                    clipped = max(clipped.geoms, key=lambda g: g.area)
                g = _warp_polygon(clipped, fns, rng, cfg)
                fid = new_fid()
                attrs = build_attrs(feat, rng)
                key = "KHSRA_NUM" if cfg.rename_schema else "khasra_no"
                if attrs.get(key):
                    attrs[key] = f"{attrs[key]}-{part}"
                legacy.add(Feature(fid, g, attrs))
                rec.correspondence[fid] = [feat.fid]
                rec.relation[fid] = "split"
            continue

        # --- ordinary one-to-one parcel -------------------------------
        g = _warp_polygon(feat.geometry, fns, rng, cfg)

        roll = rng.random()
        if roll < cfg.sliver_fraction:
            shrunk = g.buffer(-cfg.sliver_shrink_m)
            if not shrunk.is_empty and shrunk.area > 5:
                g = safe_polygon(shrunk if shrunk.geom_type == "Polygon"
                                 else max(shrunk.geoms, key=lambda x: x.area))
                rec.injected_slivers.append(f"L{lid + 1:05d}")
        elif roll < cfg.sliver_fraction + cfg.overlap_fraction:
            grown = g.buffer(cfg.overlap_grow_m)
            if grown.geom_type == "Polygon":
                g = safe_polygon(grown)
                rec.injected_overlaps.append(f"L{lid + 1:05d}")

        if rng.random() < cfg.bowtie_fraction:
            g = _inject_bowtie(g, rng)
            rec.injected_bowties.append(f"L{lid + 1:05d}")
        if rng.random() < cfg.duplicate_vertex_fraction:
            g = _duplicate_vertices(g, rng)

        fid = new_fid()
        legacy.add(Feature(fid, g, build_attrs(feat, rng)))
        rec.correspondence[fid] = [feat.fid]
        rec.relation[fid] = "one_to_one"

    # --- spurious parcels with no ground-truth counterpart --------------
    n_spur = int(len(legacy) * cfg.spurious_fraction)
    for _ in range(n_spur):
        cx = rng.uniform(all_bounds[0], all_bounds[2])
        cy = rng.uniform(all_bounds[1], all_bounds[3])
        w, h = rng.uniform(8, 18), rng.uniform(8, 18)
        g = Polygon([(cx, cy), (cx + w, cy), (cx + w, cy + h), (cx, cy + h)])
        fid = new_fid()
        legacy.add(Feature(fid, g, {
            (SCHEMA_ALIASES["khasra_no"] if cfg.rename_schema else "khasra_no"):
                f"{int(rng.integers(900, 999))}/{int(rng.integers(1, 9))}",
            (SCHEMA_ALIASES["owner_name"] if cfg.rename_schema else "owner_name"):
                "UNKNOWN",
        }))
        rec.correspondence[fid] = []
        rec.relation[fid] = "spurious"

    return legacy, rec
