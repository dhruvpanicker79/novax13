"""Change detection + encroachment against a known-modified epoch."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import numpy as np
from shapely.affinity import scale as shp_scale, translate
from kshetra.change.detect import (
    build_dossier, detect_change, detect_encroachment)
from kshetra.layers import Feature, Layer
from kshetra.synth.generator import CityConfig, generate_city

city = generate_city(CityConfig(seed=42))
b0 = city["buildings"]
rng = np.random.default_rng(3)

# Build epoch t1 with a KNOWN set of changes so detection can be scored.
t1 = Layer("buildings_t1", crs=b0.crs)
h0, h1 = {}, {}
truth = {"new": [], "demolished": [], "extended": [], "heightened": []}
for i, f in enumerate(b0):
    h0[f.fid] = float(f.attrs.get("height_m", 6.0))
    r = rng.random()
    if r < 0.010:                                  # demolished
        truth["demolished"].append(f.fid); continue
    g, h = f.geometry, h0[f.fid]
    if r < 0.035:                                  # extended
        g = shp_scale(g, 1.28, 1.28, origin="centroid")
        truth["extended"].append(f.fid)
    elif r < 0.055:                                # extra storeys, same footprint
        h += 3 * 3.1
        truth["heightened"].append(f.fid)
    h1[f.fid] = h
    t1.add(Feature(f.fid, g, dict(f.attrs)))

for k in range(22):                                # genuinely new buildings
    src = b0[int(rng.integers(0, len(b0)))]
    g = translate(src.geometry, rng.uniform(14, 26), rng.uniform(14, 26))
    fid = f"N{k:03d}"
    t1.add(Feature(fid, g, {"height_m": 6.2})); h1[fid] = 6.2
    truth["new"].append(fid)

rep = detect_change(b0, t1, h0, h1, "2023 survey", "2025 drone")
print(rep.summary()); print()
print(f"{'kind':<12}{'detected':>9}{'injected':>10}")
for k in ("new", "demolished", "extended", "heightened"):
    print(f"{k:<12}{rep.counts().get(k,0):>9}{len(truth[k]):>10}")

det_new = {e.fid for e in rep.events if e.kind == "new"}
tp = len(det_new & set(truth["new"]))
print(f"\nnew-building precision {tp}/{len(det_new)}  recall {tp}/{len(truth['new'])}")

enc = detect_encroachment(t1, city["govt_land"])
print(f"\nencroachments: {len(enc)}  total {sum(e.encroached_sqm for e in enc):.0f} m2")
for e in enc[:6]:
    print(f"  {e.building_fid}  {e.encroached_sqm:8.1f} m2  "
          f"{e.fraction_of_building*100:5.1f}% of building  {e.severity:<11} "
          f"on {e.govt_category}")

print("\n--- sample dossier ---")
if enc:
    print(json.dumps(build_dossier(enc[0]), indent=1)[:760])
