"""Fit the survey-plan prediction scale on one city, test it on another.

The planner's raw predicted RMSE is optimistic by a roughly constant factor,
because maximum-likelihood hyperparameter fitting under-attributes variance to
the per-parcel noise term. The factor is measured here on a training city and
applied to a held-out one, so the correction is validated rather than tuned on
the number it is judged by.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import numpy as np

from kshetra.georef.coarse import coarse_align
from kshetra.matching.assign import assign_matches
from kshetra.matching.features import (
    FieldMap, build_feature_matrix, generate_candidates)
from kshetra.matching.model import ParcelMatcher
from kshetra.synth.corruption import (
    SQM_PER_BIGHA, CorruptionConfig, corrupt_cadastre)
from kshetra.synth.generator import CityConfig, generate_city
from kshetra.targeting.planner import SurveyPlanner
from kshetra.targeting.uncertainty import UncertaintyField

LF = FieldMap(khasra="KHSRA_NUM", owner="KHATEDAR_NM", area="AREA_BIGHA",
              land_use="LU_CODE", ward="WARD", area_scale=SQM_PER_BIGHA)
KS = (10, 20, 40, 80)


def prepare(city_seed: int, corrupt_seed: int, cfg_kw=None):
    city = generate_city(CityConfig(seed=city_seed))
    truth = city["parcels"]
    tmap = truth.by_id()
    legacy, key = corrupt_cadastre(
        truth, CorruptionConfig(seed=corrupt_seed, **(cfg_kw or {})))
    al = coarse_align(legacy, truth, max_shift=60.0)
    aligned = al.apply_layer(legacy)
    for a, b in zip(aligned.features, legacy.features):
        a.fid = b.fid

    cand = generate_candidates(aligned, truth, search_radius=18.0)
    X = build_feature_matrix(cand, LF, FieldMap())
    tf = [f.fid for f in truth]
    lf = [f.fid for f in aligned]
    y = np.zeros(len(cand.pairs), dtype=int)
    for i, (a, b) in enumerate(cand.pairs):
        if tf[b] in key.correspondence.get(lf[a], []):
            y[i] = 1
    model = ParcelMatcher(n_rounds=400).fit(
        X, y, cand.pairs[:, 0], seed=1, verbose=False)
    res = assign_matches(cand, model.predict_proba(X), aligned, truth)

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

    true_disp = {}
    for fid, tids in key.correspondence.items():
        if len(tids) != 1 or fid not in amap:
            continue
        a, b = amap[fid].geometry.centroid, tmap[tids[0]].geometry.centroid
        true_disp[fid] = (b.x - a.x, b.y - a.y)
    idx = [i for i, f in enumerate(aligned.features) if f.fid in true_disp]
    P = np.array([[aligned[i].geometry.centroid.x,
                   aligned[i].geometry.centroid.y] for i in idx])
    D = np.array([true_disp[aligned[i].fid] for i in idx])
    cands = SurveyPlanner.candidates_from_parcels(aligned.geometries(), 1500)
    return np.array(obs_xy), np.array(obs_res), P, D, cands


def rmse(resid):
    return float(np.sqrt((resid ** 2).sum(axis=1).mean()))


def sweep(field, P, D, cands, label):
    planner = SurveyPlanner(field)
    rows = []
    for K in KS:
        plan = planner.plan(P, cands, k=K, min_gain_ratio=0.0)
        if not plan.points:
            continue
        sel = np.array([[p.x, p.y] for p in plan.points])
        cx, cv = [], []
        for qx, qy in sel:
            j = int(np.argmin(((P - [qx, qy]) ** 2).sum(axis=1)))
            cx.append(P[j]); cv.append(D[j])
        ach = rmse(D - field.posterior_mean(P, np.array(cx), np.array(cv)))
        rows.append((len(plan.points), plan.rmse_after, ach))
        print(f"  [{label}] K={len(plan.points):>3}  predicted {plan.rmse_after:6.3f}"
              f"  achieved {ach:6.3f}  ratio {ach / max(plan.rmse_after, 1e-9):5.2f}")
    return rows


print("=" * 72)
print("TRAIN CITY — measuring the prediction scale")
print("=" * 72)
oxy, ore, P, D, C = prepare(42, 7)
field = UncertaintyField().fit(oxy, ore)
print(f"  {field.hyper}")
print(f"  irreducible floor {field.irreducible_rmse():.3f} m")
train_rows = sweep(field, P, D, C, "train")
scale = field.calibrate_prediction([(p, a) for _, p, a in train_rows])
print(f"\n  fitted prediction scale = {scale:.3f}")
print(f"  {field.calibration_note}")

print("\n" + "=" * 72)
print("HELD-OUT CITY — applying it unchanged")
print("=" * 72)
oxy2, ore2, P2, D2, C2 = prepare(
    99, 2024,
    cfg_kw=dict(shift_m=(-9.1, 5.7), rotation_deg=-1.25, scale=0.9987,
                warp_amplitude_m=3.1, vertex_jitter_m=0.45))
field2 = UncertaintyField(prediction_scale=scale).fit(oxy2, ore2)
field2.calibration_note = field.calibration_note
print(f"  {field2.hyper}")
print(f"  irreducible floor {field2.irreducible_rmse():.3f} m")
test_rows = sweep(field2, P2, D2, C2, "test ")

ratios = [a / p for _, p, a in test_rows]
print(f"\n  held-out ratio: median {np.median(ratios):.3f}, "
      f"range {min(ratios):.2f}-{max(ratios):.2f}")
ok = 0.75 <= float(np.median(ratios)) <= 1.35
print(f"  [{'PASS' if ok else 'FAIL'}] calibrated prediction within +/-35% "
      f"on a city it was not fitted on")

out = ROOT / "data" / "demo" / "targeting_calibration.json"
out.write_text(json.dumps({
    "prediction_scale": round(scale, 4),
    "note": field.calibration_note,
    "irreducible_rmse_m": round(field2.irreducible_rmse(), 4),
    "train": [{"k": k, "predicted": round(p, 4), "achieved": round(a, 4)}
              for k, p, a in train_rows],
    "held_out": [{"k": k, "predicted": round(p, 4), "achieved": round(a, 4)}
                 for k, p, a in test_rows],
    "held_out_ratio_median": round(float(np.median(ratios)), 4),
}, indent=1), encoding="utf-8")
print(f"\nwrote {out.relative_to(ROOT)}")
sys.exit(0 if ok else 1)
