"""Run the full pipeline once and dump every artifact the UI needs.

The demo must never depend on a live computation succeeding on stage, so the
whole pipeline runs here and writes self-contained JSON. The API serves these
directly; a live re-run is available but is never the critical path.

Everything is reprojected to WGS84 on the way out, because MapLibre wants
lon/lat and the engine works in UTM.

    PYTHONPATH=backend python scripts/build_demo.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from bhoomisetu.crs import utm_to_geodetic
from bhoomisetu.evaluation.metrics import (
    classification_report, coverage_at_precision, reliability_curve,
)
from bhoomisetu.georef.coarse import coarse_align
from bhoomisetu.georef.transform import ThinPlateSpline
from bhoomisetu.matching.assign import assign_matches
from bhoomisetu.matching.features import (
    FieldMap, build_feature_matrix, generate_candidates,
)
from bhoomisetu.matching.model import ParcelMatcher
from bhoomisetu.synth.corruption import (
    SQM_PER_BIGHA, CorruptionConfig, corrupt_cadastre,
)
from bhoomisetu.synth.generator import CityConfig, generate_city
from bhoomisetu.targeting.planner import SurveyPlanner
from bhoomisetu.targeting.uncertainty import UncertaintyField
from bhoomisetu.topology.cleaner import clean_layer, diagnose

OUT = ROOT / "data" / "demo"
OUT.mkdir(parents=True, exist_ok=True)
ZONE = 44          # Chandausi sits in UTM 44N

LEGACY_FIELDS = FieldMap(khasra="KHSRA_NUM", owner="KHATEDAR_NM",
                         area="AREA_BIGHA", land_use="LU_CODE", ward="WARD",
                         area_scale=SQM_PER_BIGHA)
TRUTH_FIELDS = FieldMap()


def _largest_polygon(geom):
    """Gap filling can union a parcel into a MultiPolygon or
    GeometryCollection. Keep the largest polygonal part; the rest are
    slivers that the cleaner already accounted for."""
    t = geom.geom_type
    if t == "Polygon":
        return geom
    if t in ("MultiPolygon", "GeometryCollection"):
        polys = [g for g in geom.geoms if g.geom_type == "Polygon" and g.area > 0]
        if polys:
            return max(polys, key=lambda g: g.area)
    return None


def to_wgs(geom):
    """UTM polygon -> WGS84 ring coordinates for GeoJSON."""
    poly = _largest_polygon(geom)
    if poly is None:
        return None
    xs, ys = np.array(poly.exterior.coords).T
    lon, lat = utm_to_geodetic(xs, ys, ZONE)
    return [[float(a), float(b)] for a, b in zip(lon, lat)]


def pt_wgs(x, y):
    lon, lat = utm_to_geodetic(np.array([x]), np.array([y]), ZONE)
    return [float(lon[0]), float(lat[0])]


def layer_fc(layer, extra=None):
    feats = []
    dropped = 0
    for f in layer:
        ring = to_wgs(f.geometry)
        if ring is None or len(ring) < 4:
            dropped += 1
            continue
        props = {k: v for k, v in f.attrs.items() if not k.startswith("_")}
        props["fid"] = f.fid
        if extra and f.fid in extra:
            props.update(extra[f.fid])
        feats.append({
            "type": "Feature",
            "properties": props,
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        })
    if dropped:
        print(f"      (dropped {dropped} non-polygonal geometries)")
    return {"type": "FeatureCollection", "features": feats}


def write(name, obj):
    p = OUT / name
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, separators=(",", ":"))
    print(f"  {name:<34} {p.stat().st_size/1024:8.1f} KB")


def main():
    t_start = time.time()
    stages = []

    def stage(name, fn):
        t = time.time()
        r = fn()
        dt = time.time() - t
        stages.append({"name": name, "seconds": round(dt, 2)})
        print(f"[{dt:6.2f}s] {name}")
        return r

    print("=" * 70)
    print("BUILDING DEMO ARTIFACTS")
    print("=" * 70)

    # ---- 1. ground truth + damage -----------------------------------
    city = stage("generate city", lambda: generate_city(CityConfig(seed=42)))
    truth = city["parcels"]
    legacy, key = stage("inject damage",
                        lambda: corrupt_cadastre(truth, CorruptionConfig(seed=7)))
    tmap = truth.by_id()

    def positional_rmse(layer):
        lm = layer.by_id()
        e = []
        for fid, tids in key.correspondence.items():
            if len(tids) != 1 or fid not in lm:
                continue
            a, b = lm[fid].geometry.centroid, tmap[tids[0]].geometry.centroid
            e.append(np.hypot(a.x - b.x, a.y - b.y))
        e = np.array(e)
        e = e[e < np.percentile(e, 99)]
        return float(np.sqrt((e ** 2).mean()))

    rmse_raw = positional_rmse(legacy)

    # ---- 2. coarse georeference -------------------------------------
    al = stage("coarse georeference",
               lambda: coarse_align(legacy, truth, max_shift=60.0))
    aligned = al.apply_layer(legacy)
    for a, b in zip(aligned.features, legacy.features):
        a.fid = b.fid
    rmse_coarse = positional_rmse(aligned)

    # residual vectors BEFORE alignment — the "show the problem" layer
    residuals = []
    lmap = legacy.by_id()
    for fid, tids in key.correspondence.items():
        if len(tids) != 1 or fid not in lmap:
            continue
        a = lmap[fid].geometry.centroid
        b = tmap[tids[0]].geometry.centroid
        d = float(np.hypot(b.x - a.x, b.y - a.y))
        if d > 40:
            continue
        residuals.append({
            "from": pt_wgs(a.x, a.y), "to": pt_wgs(b.x, b.y),
            "m": round(d, 2), "fid": fid,
        })

    # ---- 3. match ----------------------------------------------------
    cand = stage("blocking",
                 lambda: generate_candidates(aligned, truth, search_radius=18.0))
    X = stage("features",
              lambda: build_feature_matrix(cand, LEGACY_FIELDS, TRUTH_FIELDS))
    tf = [f.fid for f in truth]
    lf = [f.fid for f in aligned]
    y = np.zeros(len(cand.pairs), dtype=int)
    for i, (a, b) in enumerate(cand.pairs):
        if tf[b] in key.correspondence.get(lf[a], []):
            y[i] = 1
    n_true = sum(len(v) for v in key.correspondence.values())
    blocking_recall = float(y.sum()) / max(n_true, 1)

    model = ParcelMatcher(n_rounds=400)
    stage("train matcher",
          lambda: model.fit(X, y, cand.pairs[:, 0], seed=1, verbose=False))
    p = model.predict_proba(X)
    rep = classification_report(y, p, 0.5)

    imp = model.feature_importance("gain")
    GEOM = {"iou", "sym_diff_norm", "centroid_dist", "centroid_dist_norm",
            "area_ratio", "hausdorff_norm", "sig_dist", "src_frac_in_tgt",
            "tgt_frac_in_src", "d_compactness", "d_rectangularity",
            "d_elongation", "vertex_ratio"}
    geom_share = sum(v for k, v in imp if k in GEOM)

    res = stage("assign", lambda: assign_matches(cand, p, aligned, truth))

    # ---- 4. topology --------------------------------------------------
    pre = diagnose(aligned)
    cleaned, trep = stage("topology repair",
                          lambda: clean_layer(aligned, snap_tolerance=0.60))

    # ---- 5. uncertainty + targeting ------------------------------------
    amap = aligned.by_id()
    obs_xy, obs_res = [], []
    for m in res.matches:
        if m.relation != "one_to_one" or m.confidence < 0.9:
            continue
        s, t = amap.get(m.src_fid), tmap.get(m.tgt_fids[0])
        if s is None or t is None:
            continue
        a, b = s.geometry.centroid, t.geometry.centroid
        obs_xy.append([a.x, a.y])
        obs_res.append([b.x - a.x, b.y - a.y])
    obs_xy, obs_res = np.array(obs_xy), np.array(obs_res)

    fieldm = stage("fit GP", lambda: UncertaintyField().fit(obs_xy, obs_res))
    parcel_xy = np.array([[f.geometry.centroid.x, f.geometry.centroid.y]
                          for f in aligned])
    cands = SurveyPlanner.candidates_from_parcels(aligned.geometries(), 1500)
    planner = SurveyPlanner(fieldm)
    plan = stage("plan survey",
                 lambda: planner.plan(parcel_xy, cands, k=40,
                                      parcel_fids=[f.fid for f in aligned]))

    # posterior-variance grid for the heatmap
    minx, miny = parcel_xy.min(axis=0) - 40
    maxx, maxy = parcel_xy.max(axis=0) + 40
    gx = np.linspace(minx, maxx, 60)
    gy = np.linspace(miny, maxy, 60)
    GX, GY = np.meshgrid(gx, gy)
    grid = np.column_stack([GX.ravel(), GY.ravel()])
    sel = np.array([[q.x, q.y] for q in plan.points]) if plan.points else None
    sd_before = fieldm.posterior_sd(grid, None)
    sd_after = fieldm.posterior_sd(grid, sel) if sel is not None else sd_before
    uncertainty = []
    for i in range(len(grid)):
        lon, lat = pt_wgs(grid[i, 0], grid[i, 1])
        uncertainty.append([round(lon, 6), round(lat, 6),
                            round(float(sd_before[i]), 3),
                            round(float(sd_after[i]), 3)])

    # validate the plan for real
    def achieved(control):
        if control is None or len(control) < 3:
            return float("nan")
        sp, dp = [], []
        for cx, cy in control:
            j = int(np.argmin(((parcel_xy - [cx, cy]) ** 2).sum(axis=1)))
            fid = aligned[j].fid
            tids = key.correspondence.get(fid, [])
            if len(tids) != 1:
                continue
            a = aligned[j].geometry.centroid
            b = tmap[tids[0]].geometry.centroid
            sp.append([a.x, a.y]); dp.append([b.x, b.y])
        if len(sp) < 3:
            return float("nan")
        tps = ThinPlateSpline.fit(np.array(sp), np.array(dp), smoothing=1e-3)
        w = aligned.map_geometry(tps.apply_geometry)
        for a, b in zip(w.features, aligned.features):
            a.fid = b.fid
        return positional_rmse(w)

    rng = np.random.default_rng(0)
    rand = cands[rng.choice(len(cands), len(plan.points), replace=False)]
    ach_opt = stage("validate plan (optimised)", lambda: achieved(sel))
    ach_rand = stage("validate plan (random)", lambda: achieved(rand))

    # ---- 6. conflicts + audit ------------------------------------------
    conflicts = []
    for m in res.matches:
        s = amap.get(m.src_fid)
        if s is None:
            continue
        cls = "confirmed"
        detail = ""
        if m.relation == "split":
            cls = "subdivision"
            detail = f"{m.evidence.get('n_parts','?')} parts, coverage {m.evidence.get('coverage',0):.2f}"
        elif m.relation == "merge":
            cls = "amalgamation"
            detail = f"{m.evidence.get('n_parts','?')} references merged"
        elif m.confidence < 0.85:
            cls = "unresolved"
            detail = "below auto-accept threshold"
        elif m.evidence.get("ambiguous"):
            cls = "positional_conflict"
            detail = f"{m.evidence.get('n_candidates', 0)} competing candidates"
        if cls == "confirmed":
            continue
        c = s.geometry.centroid
        conflicts.append({
            "id": f"C{len(conflicts)+1:04d}",
            "fid": m.src_fid, "ref": m.tgt_fids,
            "class": cls, "confidence": round(float(m.confidence), 4),
            "detail": detail, "area_sqm": round(s.geometry.area, 1),
            "khasra": s.attrs.get("KHSRA_NUM"),
            "owner": s.attrs.get("KHATEDAR_NM"),
            "at": pt_wgs(c.x, c.y), "status": "open",
        })
    for fid in res.unmatched_source:
        s = amap.get(fid)
        if s is None:
            continue
        c = s.geometry.centroid
        conflicts.append({
            "id": f"C{len(conflicts)+1:04d}", "fid": fid, "ref": [],
            "class": "missing_reference", "confidence": 0.0,
            "detail": "no candidate above p=0.10 — new or spurious parcel",
            "area_sqm": round(s.geometry.area, 1),
            "khasra": s.attrs.get("KHSRA_NUM"),
            "owner": s.attrs.get("KHATEDAR_NM"),
            "at": pt_wgs(c.x, c.y), "status": "open",
        })
    conflicts.sort(key=lambda c: -(c["area_sqm"] * (1 - c["confidence"])))

    # ---- 7. write ------------------------------------------------------
    print("\nwriting artifacts:")
    conf_by_fid = {m.src_fid: {"confidence": round(float(m.confidence), 4),
                               "relation": m.relation}
                   for m in res.matches}

    write("reference.geojson", layer_fc(truth))
    write("legacy.geojson", layer_fc(legacy))
    write("aligned.geojson", layer_fc(aligned, conf_by_fid))
    write("harmonized.geojson", layer_fc(cleaned, conf_by_fid))
    write("govt_land.geojson", layer_fc(city["govt_land"]))
    write("residuals.json", residuals)
    write("conflicts.json", conflicts)
    write("uncertainty.json",
          {"grid": uncertainty, "n": 60,
           "bounds": [*pt_wgs(minx, miny), *pt_wgs(maxx, maxy)]})
    write("survey_plan.json", {
        "points": [{**pt.to_geojson()["properties"],
                    "at": pt_wgs(pt.x, pt.y)} for pt in plan.points],
        "rmse_before": round(plan.rmse_before, 4),
        "rmse_after": round(plan.rmse_after, 4),
        "achieved": round(ach_opt, 4) if np.isfinite(ach_opt) else None,
        "achieved_random": round(ach_rand, 4) if np.isfinite(ach_rand) else None,
        "baseline": round(rmse_coarse, 4),
        "gain_curve": plan.gain_curve(),
        "hyper": plan.hyper,
        "n_parcels": plan.n_parcels,
        "stopped_because": plan.stopped_because,
    })

    metrics = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "runtime_s": round(time.time() - t_start, 1),
        "stages": stages,
        "counts": {
            "reference": len(truth), "legacy": len(legacy),
            "buildings": len(city["buildings"]), "govt": len(city["govt_land"]),
            "candidate_pairs": int(len(cand.pairs)),
            "conflicts": len(conflicts),
        },
        "georef": {
            "rmse_raw": round(rmse_raw, 4),
            "rmse_coarse": round(rmse_coarse, 4),
            "displacement_m": round(al.displacement_m, 3),
            "rotation_deg": round(al.rotation_deg, 4),
            "scale": round(al.scale, 6),
            "inliers": int(al.n_inliers),
        },
        "matching": {
            "blocking_recall": round(blocking_recall, 4),
            "f1": round(rep["f1"], 4), "precision": round(rep["precision"], 4),
            "recall": round(rep["recall"], 4),
            "roc_auc": round(rep["roc_auc"], 4),
            "ece": round(rep["ece"], 5), "brier": round(rep["brier"], 5),
            "tp": rep["tp"], "fp": rep["fp"], "fn": rep["fn"], "tn": rep["tn"],
            "geometry_share": round(geom_share, 4),
            "feature_importance": [{"name": k, "gain": round(v, 5)}
                                   for k, v in imp[:14]],
            "reliability": [
                {"lo": r[0], "hi": r[1], "n": r[2],
                 "mean_p": None if r[2] == 0 else round(r[3], 4),
                 "observed": None if r[2] == 0 else round(r[4], 4)}
                for r in reliability_curve(y, p, 10)
            ],
            "coverage_at_99": round(coverage_at_precision(y, p, 0.99)[0], 4),
        },
        "assignment": res.by_relation(),
        "topology": {
            "invalid_before": trep.invalid_before, "invalid_after": trep.invalid_after,
            "overlaps_before": trep.overlaps_before, "overlaps_after": trep.overlaps_after,
            "overlap_area_before": round(trep.overlap_area_before, 1),
            "overlap_area_after": round(trep.overlap_area_after, 1),
            "gaps_before": trep.gaps_before, "gaps_after": trep.gaps_after,
            "total_before": trep.total_errors_before,
            "total_after": trep.total_errors_after,
            "vertices_snapped": trep.vertices_snapped,
            "residual_slivers": trep.residual_slivers,
            "refused_to_fill": trep.residual_missing_parcels,
            "harness_deleted": len(key.missing_truth_fids),
            "area_before": round(trep.area_before, 1),
            "area_after": round(trep.area_after, 1),
            "area_drift_pct": round(trep.area_drift_pct, 4),
        },
        "targeting": {
            "n_points": len(plan.points),
            "rmse_baseline": round(rmse_coarse, 4),
            "rmse_predicted": round(plan.rmse_after, 4),
            "rmse_achieved": round(ach_opt, 4) if np.isfinite(ach_opt) else None,
            "rmse_random": round(ach_rand, 4) if np.isfinite(ach_rand) else None,
            "vs_random_pct": (round(100 * (1 - ach_opt / ach_rand), 1)
                              if np.isfinite(ach_opt) and np.isfinite(ach_rand)
                              else None),
            "lengthscale_m": round(fieldm.hyper.lengthscale, 1),
        },
    }
    write("metrics.json", metrics)

    print(f"\ntotal {time.time()-t_start:.1f}s -> {OUT}")
    print(f"\nKEY RESULTS")
    print(f"  georef      {rmse_raw:.2f} m -> {rmse_coarse:.2f} m")
    print(f"  matching    F1 {rep['f1']:.4f}  ECE {rep['ece']:.5f}  "
          f"geometry {geom_share*100:.1f}%")
    print(f"  topology    {trep.total_errors_before} -> {trep.total_errors_after}")
    print(f"  targeting   {rmse_coarse:.2f} -> {ach_opt:.2f} m "
          f"(random {ach_rand:.2f})")
    print(f"  conflicts   {len(conflicts)}")


if __name__ == "__main__":
    main()
