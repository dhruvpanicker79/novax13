"""End-to-end verification of the BhoomiSetu engine.

One command that proves every stage works and prints the numbers that go on
the slides. Run after any environment change:

    PYTHONPATH=backend python scripts/verify_all.py

Stages 1-7 re-verify the ported engine. Stage 8 is the one that matters most:
it validates the survey-targeting USP by actually *placing* the recommended
points, re-running georeferencing, and comparing the achieved error reduction
against what the planner predicted -- and against random placement, which is
the honest control. A prediction is a claim; a verified prediction is evidence.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from bhoomisetu.crs import epsg_for_utm, geodetic_to_utm, utm_to_geodetic
from bhoomisetu.evaluation.metrics import (
    classification_report, coverage_at_precision,
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

LEGACY_FIELDS = FieldMap(khasra="KHSRA_NUM", owner="KHATEDAR_NM",
                         area="AREA_BIGHA", land_use="LU_CODE", ward="WARD",
                         area_scale=SQM_PER_BIGHA)
TRUTH_FIELDS = FieldMap()

FAILURES: list[str] = []


def head(n, title):
    print(f"\n{'=' * 74}\n{n}. {title}\n{'=' * 74}")


def check(label, ok, detail=""):
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}{'  ' + detail if detail else ''}")
    if not ok:
        FAILURES.append(label)
    return ok


# ---------------------------------------------------------------- 1. CRS
head(1, "CRS ENGINE")
LON, LAT = 78.7749, 28.4515                       # Chandausi, NAKSHA pilot
e, n, z = geodetic_to_utm(LON, LAT)
lo, la = utm_to_geodetic(e, n, z)
rt = np.hypot((lo - LON) * 111_320 * np.cos(np.radians(LAT)),
              (la - LAT) * 110_570)
print(f"  Chandausi -> UTM {z}N ({epsg_for_utm(z)})  E={e:,.2f}  N={n:,.2f}")
check("round-trip < 1 mm", rt < 1e-3, f"{rt*1000:.4f} mm")
e0, _, _ = geodetic_to_utm(75.0, 20.0, zone=43)
check("central meridian == 500000 m exactly", abs(e0 - 500_000) < 1e-6)

try:
    import pyproj
    tr = pyproj.Transformer.from_crs("EPSG:4326", epsg_for_utm(z), always_xy=True)
    pe, pn = tr.transform(LON, LAT)
    delta = np.hypot(pe - e, pn - n)
    check("agrees with pyproj < 1 mm", delta < 1e-3, f"{delta*1000:.4f} mm")
    print("         (our from-scratch Snyder implementation is now verified "
          "against the reference library)")
except ImportError:
    print("  [skip] pyproj unavailable — cannot cross-validate CRS here")

# ---------------------------------------------- 2. generator + 3. corruption
head(2, "SYNTHETIC CITY (ground truth)")
t0 = time.time()
city = generate_city(CityConfig(seed=42))
truth = city["parcels"]
print(f"  parcels {len(truth):,}  buildings {len(city['buildings']):,}  "
      f"roads {len(city['roads'])}  govt {len(city['govt_land'])}  "
      f"({time.time()-t0:.1f}s)")
d = diagnose(truth)
check("all geometries valid", d.invalid_before == 0, f"{d.invalid_before} invalid")
check("no overlaps in ground truth", d.overlaps_before == 0,
      f"{d.overlaps_before} overlapping pairs")

head(3, "DAMAGE HARNESS")
legacy, key = corrupt_cadastre(truth, CorruptionConfig(seed=7))
rel: dict[str, int] = {}
for r in key.relation.values():
    rel[r] = rel.get(r, 0) + 1
print(f"  legacy parcels {len(legacy):,}   relations {rel}")
print(f"  injected: {len(key.injected_slivers)} slivers, "
      f"{len(key.injected_overlaps)} overlaps, "
      f"{len(key.injected_bowties)} self-intersections, "
      f"{len(key.missing_truth_fids)} parcels deleted")
check("damage actually applied", len(key.injected_overlaps) > 0 and
      len(key.missing_truth_fids) > 0)

tmap = truth.by_id()
lmap = legacy.by_id()


def positional_rmse(layer, robust=True):
    """RMSE of 1:1 parcel centroids against ground truth."""
    errs = []
    lm = layer.by_id()
    for fid, tids in key.correspondence.items():
        if len(tids) != 1 or fid not in lm:
            continue
        a, b = lm[fid].geometry.centroid, tmap[tids[0]].geometry.centroid
        errs.append(np.hypot(a.x - b.x, a.y - b.y))
    errs = np.array(errs)
    if robust:                       # drop bow-tie centroids, which are junk
        errs = errs[errs < np.percentile(errs, 99)]
    return float(np.sqrt((errs ** 2).mean())), errs


rmse_raw, _ = positional_rmse(legacy)
print(f"  uncorrected positional RMSE: {rmse_raw:.3f} m")

# ------------------------------------------------------- 4. coarse georef
head(4, "COARSE GEOREFERENCING")
t0 = time.time()
al = coarse_align(legacy, truth, max_shift=60.0)
aligned = al.apply_layer(legacy)
for a, b in zip(aligned.features, legacy.features):
    a.fid = b.fid
print(f"  displacement {al.displacement_m:.2f} m  rot {al.rotation_deg:+.3f}deg  "
      f"scale {al.scale:.5f}  inliers {al.n_inliers:,}  ({time.time()-t0:.1f}s)")
rmse_coarse, _ = positional_rmse(aligned)
print(f"  positional RMSE  {rmse_raw:.3f} m -> {rmse_coarse:.3f} m")
check("coarse alignment reduces error", rmse_coarse < rmse_raw * 0.6,
      f"{100*(1-rmse_coarse/rmse_raw):.1f}% reduction")

# ------------------------------------------------------------ 5. matching
head(5, "MATCHING MODEL")
t0 = time.time()
cand = generate_candidates(aligned, truth, search_radius=18.0)
X = build_feature_matrix(cand, LEGACY_FIELDS, TRUTH_FIELDS)
tf = [f.fid for f in truth]
lf = [f.fid for f in aligned]
y = np.zeros(len(cand.pairs), dtype=int)
for i, (a, b) in enumerate(cand.pairs):
    if tf[b] in key.correspondence.get(lf[a], []):
        y[i] = 1
n_true = sum(len(v) for v in key.correspondence.values())
blocking = int(y.sum()) / max(n_true, 1)
print(f"  {len(cand.pairs):,} candidate pairs, {int(y.sum()):,} positives "
      f"({time.time()-t0:.0f}s)")
check("blocking recall >= 0.98", blocking >= 0.98, f"{blocking:.4f}")

model = ParcelMatcher(n_rounds=400)
model.fit(X, y, cand.pairs[:, 0], seed=1, verbose=False)
p = model.predict_proba(X)
rep = classification_report(y, p, 0.5)
print(f"  F1 {rep['f1']:.4f}   ROC AUC {rep['roc_auc']:.4f}   "
      f"ECE {rep['ece']:.4f}   Brier {rep['brier']:.4f}")
check("F1 >= 0.90", rep["f1"] >= 0.90)
check("calibration ECE <= 0.02", rep["ece"] <= 0.02)

imp = dict(model.feature_importance("gain"))
GEOM = {"iou", "sym_diff_norm", "centroid_dist", "centroid_dist_norm",
        "area_ratio", "hausdorff_norm", "sig_dist", "src_frac_in_tgt",
        "tgt_frac_in_src", "d_compactness", "d_rectangularity",
        "d_elongation", "vertex_ratio"}
geom_share = sum(v for k, v in imp.items() if k in GEOM)
print("  top features: " + ", ".join(
    f"{k} {v*100:.1f}%" for k, v in list(model.feature_importance("gain"))[:5]))
check("geometry drives the model (>=70% gain)", geom_share >= 0.70,
      f"{geom_share*100:.1f}% geometric — not an identifier join")

cov, thr, ach = coverage_at_precision(y, p, 0.99)
print(f"  auto-accept at 99% precision: {cov*100:.1f}% of pairs (p>={thr:.3f})")

# ---------------------------------------------------------- 6. assignment
head(6, "GLOBAL ASSIGNMENT")
res = assign_matches(cand, p, aligned, truth)
considered = exact = 0
for fid, tids in key.correspondence.items():
    if not tids:
        continue
    considered += 1
    if set(res.src_to_tgt().get(fid, [])) == set(tids):
        exact += 1
spur = [f for f, r in key.relation.items() if r == "spurious"]
caught = sum(1 for f in spur if f in set(res.unmatched_source))
print(f"  relations {res.by_relation()}")
check("exact set match >= 0.85", exact / considered >= 0.85,
      f"{exact/considered*100:.2f}%")
check("spurious parcels rejected >= 0.95", caught / max(len(spur), 1) >= 0.95,
      f"{caught}/{len(spur)}")

# ------------------------------------------------------------ 7. topology
head(7, "TOPOLOGY CORRECTION")
t0 = time.time()
cleaned, trep = clean_layer(aligned, snap_tolerance=0.60)
print(trep.summary())
print(f"  ({time.time()-t0:.1f}s)")
reduction = 1 - trep.total_errors_after / max(trep.total_errors_before, 1)
check("topology errors reduced >= 90%", reduction >= 0.90,
      f"{reduction*100:.1f}%")
check("no invalid geometry remains", trep.invalid_after == 0)
check("refuses to fill parcel-sized holes",
      trep.residual_missing_parcels > 0,
      f"{trep.residual_missing_parcels} flagged for survey "
      f"(harness deleted {len(key.missing_truth_fids)})")

# ------------------------------------------- 8. THE USP: survey targeting
head(8, "SURVEY TARGETING  (the USP — predicted vs achieved)")

# Observed residuals at confidently matched parcels: this is what a real
# deployment would have after georeferencing against whatever control exists.
obs_xy, obs_res = [], []
amap = aligned.by_id()
for m in res.matches:
    if m.relation != "one_to_one" or m.confidence < 0.9:
        continue
    src = amap.get(m.src_fid)
    tgt = tmap.get(m.tgt_fids[0])
    if src is None or tgt is None:
        continue
    a, b = src.geometry.centroid, tgt.geometry.centroid
    obs_xy.append([a.x, a.y])
    obs_res.append([b.x - a.x, b.y - a.y])
obs_xy = np.array(obs_xy)
obs_res = np.array(obs_res)
print(f"  fitting GP on {len(obs_xy):,} observed residuals")

fieldm = UncertaintyField().fit(obs_xy, obs_res)
print(f"  {fieldm.hyper}")
check("lengthscale is physically plausible (5-500 m)",
      5 <= fieldm.hyper.lengthscale <= 500,
      f"{fieldm.hyper.lengthscale:.1f} m")

parcel_xy = np.array([[f.geometry.centroid.x, f.geometry.centroid.y]
                      for f in aligned])
cands = SurveyPlanner.candidates_from_parcels(aligned.geometries(),
                                              max_candidates=1500)
planner = SurveyPlanner(fieldm)
t0 = time.time()
plan = planner.plan(parcel_xy, cands, k=40,
                    parcel_fids=[f.fid for f in aligned])
print(f"\n{plan.summary()}")
print(f"  planned in {time.time()-t0:.1f}s")
check("plan returns points", len(plan.points) > 0, f"{len(plan.points)} points")
check("predicted RMSE improves", plan.rmse_after < plan.rmse_before,
      f"{plan.improvement_pct:.1f}%")
check("marginal gains are non-increasing (submodularity)",
      all(plan.points[i].marginal_gain >= plan.points[i + 1].marginal_gain - 1e-9
          for i in range(len(plan.points) - 1)))


def achieved_rmse(control_xy):
    """Actually place control at these locations and measure the real result.

    We know ground truth, so we can look up the true displacement at each
    recommended point, use them as thin-plate-spline control, warp the layer,
    and measure the residual error that genuinely remains.
    """
    if len(control_xy) < 3:
        return float("nan")
    src_pts, dst_pts = [], []
    for cx, cy in control_xy:
        j = int(np.argmin(((parcel_xy - [cx, cy]) ** 2).sum(axis=1)))
        fid = aligned[j].fid
        tids = key.correspondence.get(fid, [])
        if len(tids) != 1:
            continue
        a = aligned[j].geometry.centroid
        b = tmap[tids[0]].geometry.centroid
        src_pts.append([a.x, a.y])
        dst_pts.append([b.x, b.y])
    if len(src_pts) < 3:
        return float("nan")
    tps = ThinPlateSpline.fit(np.array(src_pts), np.array(dst_pts),
                             smoothing=1e-3)
    warped = aligned.map_geometry(tps.apply_geometry)
    for a, b in zip(warped.features, aligned.features):
        a.fid = b.fid
    return positional_rmse(warped)[0]


sel = np.array([[pt.x, pt.y] for pt in plan.points])
rng = np.random.default_rng(0)
rand = cands[rng.choice(len(cands), len(sel), replace=False)]

ach_opt = achieved_rmse(sel)
ach_rand = achieved_rmse(rand)

print(f"\n  {'':<34}{'RMSE (m)':>10}")
print(f"  {'before any new control':<34}{rmse_coarse:>10.3f}")
print(f"  {'PREDICTED after 40 points':<34}{plan.rmse_after:>10.3f}")
print(f"  {'ACHIEVED after 40 points':<34}{ach_opt:>10.3f}")
print(f"  {'ACHIEVED with 40 RANDOM points':<34}{ach_rand:>10.3f}")

check("optimised placement beats random",
      np.isfinite(ach_opt) and np.isfinite(ach_rand) and ach_opt < ach_rand,
      f"{100*(1-ach_opt/ach_rand):.1f}% better than random")
check("achieved improves on the starting point",
      np.isfinite(ach_opt) and ach_opt < rmse_coarse,
      f"{rmse_coarse:.3f} -> {ach_opt:.3f} m")

# ------------------------------------------------------------- summary
print(f"\n{'=' * 74}")
if FAILURES:
    print(f"{len(FAILURES)} CHECK(S) FAILED:")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("ALL CHECKS PASSED")
print("=" * 74)
