"""Does schema matching recover the field map we currently hand-supply?"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from kshetra.attributes.schema_match import match_schema
from kshetra.synth.corruption import CorruptionConfig, corrupt_cadastre
from kshetra.synth.generator import CityConfig, generate_city

city = generate_city(CityConfig(seed=42))
legacy, key = corrupt_cadastre(city["parcels"], CorruptionConfig(seed=7))

records = [f.attrs for f in legacy]
areas = [f.geometry.area for f in legacy]

print(f"columns seen: {sorted({k for r in records for k in r})}\n")
sm = match_schema(records, geometric_areas=areas)
print(sm.summary())

TRUTH = {"khasra": "KHSRA_NUM", "owner": "KHATEDAR_NM", "area": "AREA_BIGHA",
         "land_use": "LU_CODE", "tenure": "TENURE_TYP", "ward": "WARD",
         "ulpin": "PARCEL_UID"}
print("\nvs the hand-supplied map:")
ok = 0
for k, want in TRUTH.items():
    got = sm.guesses.get(k).column if sm.guesses.get(k) else None
    mark = "ok  " if got == want else "MISS"
    if got == want: ok += 1
    print(f"  [{mark}] {k:<10} expected {want:<14} got {got}")
print(f"\n{ok}/{len(TRUTH)} columns mapped correctly")
print(f"area unit: {sm.area_unit} (truth: bigha, 2529.285 m2)")
fm = sm.to_field_map()
print(f"FieldMap scale: {fm.area_scale:.4f}")
