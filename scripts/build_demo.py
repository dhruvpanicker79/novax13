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

from shapely.affinity import scale as shp_scale, translate as shp_translate

from kshetra.attributes.schema_match import match_schema
from kshetra.change.detect import (
    build_dossier, detect_change, detect_encroachment)
from kshetra.conflict.resolve import Claim, SourceProfile, resolve_parcel
from kshetra.crs import utm_to_geodetic
from kshetra.evaluation.metrics import (
    classification_report, coverage_at_precision, reliability_curve,
)
from kshetra.georef.coarse import coarse_align
from kshetra.layers import Feature, Layer
from kshetra.georef.transform import ThinPlateSpline
from kshetra.matching.assign import assign_matches
from kshetra.matching.features import (
    FieldMap, build_feature_matrix, generate_candidates,
)
from kshetra.matching.model import ParcelMatcher
from kshetra.synth.corruption import (
    SQM_PER_BIGHA, CorruptionConfig, corrupt_cadastre,
)
from kshetra.synth.generator import CityConfig, generate_city
from kshetra.targeting.planner import SurveyPlanner
from kshetra.targeting.uncertainty import UncertaintyField
from kshetra.topology.cleaner import clean_layer, diagnose

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

    # Prediction scale measured on a DIFFERENT city by
    # scripts/calibrate_targeting.py. Raw maximum-likelihood hyperparameters
    # under-attribute variance to the per-parcel noise term, so the unscaled
    # prediction is optimistic by a roughly constant factor.
    calib_path = ROOT / "data" / "demo" / "targeting_calibration.json"
    pred_scale, calib_note = 1.0, "uncalibrated"
    if calib_path.exists():
        _c = json.loads(calib_path.read_text(encoding="utf-8"))
        pred_scale = float(_c.get("prediction_scale", 1.0))
        calib_note = str(_c.get("note", ""))

    fieldm = stage("fit GP",
                   lambda: UncertaintyField(prediction_scale=pred_scale)
                   .fit(obs_xy, obs_res))
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
    def achieved(control_xy):
        """Place control at these locations and measure what really remains.

        Correction uses the GP posterior mean -- the same model that produced
        the prediction. Correcting with a different interpolator would make
        predicted and achieved describe two different estimators, which is what
        made the earlier numbers disagree.
        """
        if control_xy is None or len(control_xy) < 3:
            return float("nan")
        cx, cv = [], []
        for qx, qy in control_xy:
            j = int(np.argmin(((parcel_xy - [qx, qy]) ** 2).sum(axis=1)))
            fid = aligned[j].fid
            tids = key.correspondence.get(fid, [])
            if len(tids) != 1:
                continue
            a = aligned[j].geometry.centroid
            b = tmap[tids[0]].geometry.centroid
            cx.append([a.x, a.y])
            cv.append([b.x - a.x, b.y - a.y])
        if len(cx) < 3:
            return float("nan")

        # true displacement at every parcel with a 1:1 counterpart
        idx, true_d = [], []
        for i, f in enumerate(aligned.features):
            tids = key.correspondence.get(f.fid, [])
            if len(tids) != 1:
                continue
            a = f.geometry.centroid
            b = tmap[tids[0]].geometry.centroid
            idx.append(i)
            true_d.append([b.x - a.x, b.y - a.y])
        if not idx:
            return float("nan")
        Q = parcel_xy[idx]
        D = np.array(true_d)
        pred = fieldm.posterior_mean(Q, np.array(cx), np.array(cv))
        resid = D - pred
        return float(np.sqrt((resid ** 2).sum(axis=1).mean()))

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

    # ---- 6b. schema auto-matching -------------------------------------
    sm = stage("schema match", lambda: match_schema(
        [f.attrs for f in legacy],
        geometric_areas=[f.geometry.area for f in legacy]))
    CANON = ["khasra", "owner", "area", "land_use", "tenure", "ward", "ulpin"]
    schema_out = {
        "columns": sorted({k for f in legacy for k in f.attrs}),
        "fields": [
            {
                "canonical": c,
                "column": sm.guesses[c].column if c in sm.guesses else None,
                "confidence": round(sm.guesses[c].confidence, 4) if c in sm.guesses else 0,
                "evidence": sm.guesses[c].evidence if c in sm.guesses else "",
                "alternatives": [[a, round(b, 3)] for a, b in
                                 (sm.guesses[c].alternatives if c in sm.guesses else [])],
            }
            for c in CANON
        ],
        "area_unit": sm.area_unit,
        "area_scale": sm.area_scale,
        "area_unit_confidence": round(sm.area_unit_confidence, 4),
        "area_unit_evidence": sm.area_unit_evidence,
        "unmapped": sm.unmapped_columns,
    }

    # ---- 6c. change detection + encroachment ---------------------------
    # A later epoch with a KNOWN set of changes, including deliberate
    # unauthorised construction on public land. The generator never puts
    # buildings on government blocks, so without injecting them there is
    # nothing to detect and the encroachment claim would go untested.
    def build_epoch():
        rng2 = np.random.default_rng(3)
        b0 = city["buildings"]
        t1 = Layer("buildings_t1", crs=b0.crs)
        h0, h1 = {}, {}
        for f in b0:
            h0[f.fid] = float(f.attrs.get("height_m", 6.0))
            r = rng2.random()
            if r < 0.010:
                continue                                    # demolished
            g, h = f.geometry, h0[f.fid]
            if r < 0.035:
                g = shp_scale(g, 1.28, 1.28, origin="centroid")
            elif r < 0.055:
                h += 3 * 3.1                                # storeys added
            h1[f.fid] = h
            t1.add(Feature(f.fid, g, dict(f.attrs)))
        for kk in range(22):                                # new construction
            src = b0[int(rng2.integers(0, len(b0)))]
            g = shp_translate(src.geometry, rng2.uniform(14, 26), rng2.uniform(14, 26))
            fid = "N%03d" % kk
            t1.add(Feature(fid, g, {"height_m": 6.2, "injected": "new"}))
            h1[fid] = 6.2
        for gi, gf in enumerate(city["govt_land"]):         # encroachment
            ring = gf.geometry.exterior
            for e in range(3):
                src = b0[int(rng2.integers(0, len(b0)))]
                sc = src.geometry.centroid
                # Put the building ON the boundary, so it straddles it the way
                # unauthorised construction actually creeps over an edge. A
                # structure sitting neatly in the middle of a park is not what
                # the severity gradation is meant to describe.
                t = float(rng2.uniform(0, 1))
                bp = ring.interpolate(t, normalized=True)
                # Nudge across the line by a fraction of the building's own size
                w = src.geometry.bounds[2] - src.geometry.bounds[0]
                push = rng2.uniform(-0.45, 0.35) * w
                g = shp_translate(src.geometry,
                                  bp.x - sc.x + push, bp.y - sc.y + push * 0.4)
                fid = "E%d%d" % (gi, e)
                t1.add(Feature(fid, g, {"height_m": 5.8, "injected": "encroach"}))
                h1[fid] = 5.8
        return t1, h0, h1

    t1, h0, h1 = stage("build epoch t1", build_epoch)
    chg = stage("change detection",
                lambda: detect_change(city["buildings"], t1, h0, h1,
                                      "2023 survey", "2025 drone"))
    chg.encroachments = stage("encroachment",
                              lambda: detect_encroachment(t1, city["govt_land"]))

    change_out = {
        "epoch_from": chg.epoch_from,
        "epoch_to": chg.epoch_to,
        "dsm_available": chg.dsm_available,
        "counts": chg.counts(),
        "encroached_sqm": round(chg.encroached_area(), 1),
        "events": [
            {"kind": e.kind, "fid": e.fid, "area_sqm": e.area_sqm,
             "delta_sqm": e.delta_sqm, "confidence": round(e.confidence, 3),
             "height_delta_m": e.height_delta_m, "storeys_delta": e.storeys_delta,
             "at": pt_wgs(e.at[0], e.at[1]), "note": e.note}
            for e in chg.events[:400]
        ],
        "encroachments": [
            {"building_fid": e.building_fid, "govt_fid": e.govt_fid,
             "category": e.govt_category, "sqm": e.encroached_sqm,
             "fraction": e.fraction_of_building, "severity": e.severity,
             "confidence": round(e.confidence, 3), "at": pt_wgs(e.at[0], e.at[1])}
            for e in chg.encroachments
        ],
    }
    if chg.encroachments:
        d = build_dossier(chg.encroachments[0])
        loc = d["location"]
        d["location"] = pt_wgs(loc[0], loc[1])
        change_out["sample_dossier"] = d
    else:
        change_out["sample_dossier"] = None

    t1_fc = layer_fc(t1)

    # ---- 6d. conflict resolution, worked examples -----------------------
    GNSS = SourceProfile("gnss_cors", "GNSS/CORS control", 0.03, 2026)
    DRONE = SourceProfile("drone_ori", "Drone ORI 5 cm", 0.10, 2025)
    MSAI = SourceProfile("ms_ai", "MS AI footprints", 1.20, 2024)
    MUNI = SourceProfile("municipal", "Municipal GIS", 2.50, 2019)
    LEGACY = SourceProfile("legacy", "Legacy sheet 1987", 6.00, 1987,
                           authority=frozenset({"owner", "tenure", "khasra"}))
    REVENUE = SourceProfile("revenue", "Revenue record", 8.00, 2023,
                            authority=frozenset({"owner", "tenure", "khasra", "ulpin"}))

    def res_case(fid, claims, title):
        pr = resolve_parcel(fid, claims)
        return {
            "fid": fid,
            "title": title,
            "claims": [{"source": c.source.source_id, "label": c.source.label,
                        "field": c.field, "value": c.value,
                        "sigma_m": c.source.accuracy_m,
                        "vintage": c.source.vintage,
                        "authority": sorted(c.source.authority)} for c in claims],
            "resolutions": [
                {"field": f, "value": r.value, "source": r.source_id,
                 "rule": r.rule, "confidence": round(r.confidence, 3),
                 "agreement": round(r.agreement, 3), "note": r.note}
                for f, r in pr.resolutions.items()],
            "transitive": pr.transitive_conflicts,
            "needs_human": pr.needs_human,
            "reason": pr.reason,
        }

    conflict_cases = [
        res_case("P00142", [Claim(GNSS, "area_sqm", 142.8),
                            Claim(LEGACY, "area_sqm", 149.5),
                            Claim(MSAI, "area_sqm", 144.1)],
                 "Precise control is not averaged into a paper sheet"),
        res_case("P00288", [Claim(DRONE, "owner", "UNKNOWN"),
                            Claim(REVENUE, "owner", "Ramesh Kumar s/o Suresh Kumar"),
                            Claim(LEGACY, "owner", "Ramesh Kr. s/o Suresh Kr.")],
                 "Ownership follows legal authority, not measurement accuracy"),
        res_case("P00391", [Claim(REVENUE, "owner", "Sunita Devi w/o Mahesh Pal"),
                            Claim(LEGACY, "owner", "Imran Ansari s/o Abdul Ansari")],
                 "A genuine ownership dispute goes to a human"),
        res_case("P00417", [Claim(GNSS, "area_sqm", 100.0),
                            Claim(DRONE, "area_sqm", 118.0),
                            Claim(MUNI, "area_sqm", 139.0)],
                 "Transitive inconsistency no pairwise check can see"),
        res_case("P00502", [Claim(DRONE, "area_sqm", 210.4),
                            Claim(MSAI, "area_sqm", 210.9),
                            Claim(MUNI, "area_sqm", 209.8)],
                 "Sources concur within their error bars"),
    ]

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
        "irreducible_m": round(fieldm.irreducible_rmse(), 4),
        "prediction_scale": round(pred_scale, 4),
        "calibration_note": calib_note,
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
    write("schema.json", schema_out)
    write("change.json", change_out)
    write("buildings_t1.geojson", t1_fc)
    write("resolutions.json", conflict_cases)

    metrics["schema"] = {
        "mapped": sum(1 for f in schema_out["fields"] if f["column"]),
        "total": len(schema_out["fields"]),
        "area_unit": sm.area_unit,
        "area_unit_confidence": round(sm.area_unit_confidence, 4),
    }
    metrics["change"] = dict(chg.counts())
    metrics["change"]["encroached_sqm"] = round(chg.encroached_area(), 1)
    metrics["change"]["dsm_available"] = chg.dsm_available
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
    print(f"  schema      {metrics['schema']['mapped']}/{metrics['schema']['total']}"
          f" columns, area unit {sm.area_unit}"
          f" ({sm.area_unit_confidence:.2f})")
    print(f"  change      {chg.summary()}")


if __name__ == "__main__":
    main()
