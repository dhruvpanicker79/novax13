"""Does the planner's predicted RMSE match what the correction achieves?

Compares two correctors against the same predicted variance:
  TPS   -- exact-interpolating spline (what we used before)
  GP    -- posterior mean of the same model that produced the prediction
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import numpy as np
from kshetra.georef.coarse import coarse_align
from kshetra.georef.transform import ThinPlateSpline
from kshetra.matching.assign import assign_matches
from kshetra.matching.features import FieldMap, build_feature_matrix, generate_candidates
from kshetra.matching.model import ParcelMatcher
from kshetra.synth.corruption import SQM_PER_BIGHA, CorruptionConfig, corrupt_cadastre
from kshetra.synth.generator import CityConfig, generate_city
from kshetra.targeting.planner import SurveyPlanner
from kshetra.targeting.uncertainty import UncertaintyField

LF = FieldMap(khasra="KHSRA_NUM", owner="KHATEDAR_NM", area="AREA_BIGHA",
              land_use="LU_CODE", ward="WARD", area_scale=SQM_PER_BIGHA)

city = generate_city(CityConfig(seed=42))
truth = city["parcels"]; tmap = truth.by_id()
legacy, key = corrupt_cadastre(truth, CorruptionConfig(seed=7))
al = coarse_align(legacy, truth, max_shift=60.0)
aligned = al.apply_layer(legacy)
for a, b in zip(aligned.features, legacy.features): a.fid = b.fid

cand = generate_candidates(aligned, truth, search_radius=18.0)
X = build_feature_matrix(cand, LF, FieldMap())
tf = [f.fid for f in truth]; lf = [f.fid for f in aligned]
y = np.zeros(len(cand.pairs), dtype=int)
for i, (a, b) in enumerate(cand.pairs):
    if tf[b] in key.correspondence.get(lf[a], []): y[i] = 1
model = ParcelMatcher(n_rounds=400).fit(X, y, cand.pairs[:, 0], seed=1, verbose=False)
res = assign_matches(cand, model.predict_proba(X), aligned, truth)

amap = aligned.by_id()
obs_xy, obs_res, fids = [], [], []
for m in res.matches:
    if m.relation != "one_to_one" or m.confidence < 0.9: continue
    s, t = amap.get(m.src_fid), tmap.get(m.tgt_fids[0])
    if s is None or t is None: continue
    a, b = s.geometry.centroid, t.geometry.centroid
    obs_xy.append([a.x, a.y]); obs_res.append([b.x - a.x, b.y - a.y]); fids.append(m.src_fid)
obs_xy = np.array(obs_xy); obs_res = np.array(obs_res)

field = UncertaintyField().fit(obs_xy, obs_res)
print(f"GP: {field.hyper}\n")

parcel_xy = np.array([[f.geometry.centroid.x, f.geometry.centroid.y] for f in aligned])
true_disp = {}
for fid, tids in key.correspondence.items():
    if len(tids) != 1 or fid not in amap: continue
    a, b = amap[fid].geometry.centroid, tmap[tids[0]].geometry.centroid
    true_disp[fid] = (b.x - a.x, b.y - a.y)

idx_ok = [i for i, f in enumerate(aligned.features) if f.fid in true_disp]
P = parcel_xy[idx_ok]
D = np.array([true_disp[aligned[i].fid] for i in idx_ok])

def rmse_of(resid):
    return float(np.sqrt((resid ** 2).sum(axis=1).mean()))

base = rmse_of(D)
cands = SurveyPlanner.candidates_from_parcels(aligned.geometries(), 1500)
planner = SurveyPlanner(field)

print("irreducible floor (per-parcel noise): "
      f"{field.irreducible_rmse():.3f} m")
print()
print(f"{'K':>4}{'predicted':>12}{'GP achieved':>14}{'ratio':>9}"
      f"{'TPS achieved':>15}{'random GP':>12}")
print("-" * 68)
rng = np.random.default_rng(0)
for K in (10, 20, 40, 80):
    plan = planner.plan(P, cands, k=K, parcel_fids=[aligned[i].fid for i in idx_ok],
                        min_gain_ratio=0.0)
    if not plan.points: continue
    sel = np.array([[p.x, p.y] for p in plan.points])

    # control values: true displacement at the nearest parcel to each point
    def ctrl(pts):
        xs, vs = [], []
        for cx, cy in pts:
            j = int(np.argmin(((P - [cx, cy]) ** 2).sum(axis=1)))
            xs.append(P[j]); vs.append(D[j])
        return np.array(xs), np.array(vs)

    cx, cv = ctrl(sel)
    gp_pred = field.posterior_mean(P, cx, cv)
    gp_ach = rmse_of(D - gp_pred)

    tps = ThinPlateSpline.fit(cx, cx + cv, smoothing=1e-3)
    tps_ach = rmse_of(D - (tps.apply(P) - P))

    rx, rv = ctrl(cands[rng.choice(len(cands), len(sel), replace=False)])
    rnd_ach = rmse_of(D - field.posterior_mean(P, rx, rv))

    print(f"{len(plan.points):>4}{plan.rmse_after:>12.3f}{gp_ach:>14.3f}"
          f"{gp_ach / max(plan.rmse_after, 1e-9):>9.2f}"
          f"{tps_ach:>15.3f}{rnd_ach:>12.3f}")

print(f"\nbaseline (no control): {base:.3f} m")
