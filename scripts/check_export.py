"""Exercise the audit chain and every export writer, including tampering."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from kshetra.audit import AuditLog
from kshetra.export import (
    ExportBundle, export_audit_pdf, export_csv, export_geojson, export_shapefile)

OUT = ROOT / "data" / "export"
DEMO = ROOT / "data" / "demo"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- audit
print("=" * 70)
print("AUDIT CHAIN")
print("=" * 70)
log_path = OUT / "audit.jsonl"
if log_path.exists():
    log_path.unlink()
log = AuditLog(str(log_path))

metrics = json.loads((DEMO / "metrics.json").read_text(encoding="utf-8"))
g, m, t = metrics["georef"], metrics["matching"], metrics["topology"]

log.append("system", "pipeline", "ingest", "chandausi",
           f"{metrics['counts']['legacy']} legacy, {metrics['counts']['reference']} reference parcels")
log.append("system", "pipeline", "schema.match", "legacy",
           f"{metrics['schema']['mapped']}/{metrics['schema']['total']} columns, "
           f"area unit {metrics['schema']['area_unit']}")
log.append("system", "pipeline", "georeference", "legacy",
           f"RMSE {g['rmse_raw']} -> {g['rmse_coarse']} m, {g['inliers']} inliers")
log.append("system", "pipeline", "match", "all",
           f"F1 {m['f1']}, ECE {m['ece']}, geometry {round(m['geometry_share']*100,1)}%")
log.append("system", "pipeline", "topology", "aligned",
           f"{t['total_before']} -> {t['total_after']} errors",
           before={"overlaps": t["overlaps_before"], "area": t["area_before"]},
           after={"overlaps": t["overlaps_after"], "area": t["area_after"]})
log.append("system", "pipeline", "refuse_fill", "gaps",
           f"{t['refused_to_fill']} parcel-sized holes flagged for survey, not filled")
log.append("r.sharma", "tehsildar", "accept", "C0042",
           "boundary confirmed against GNSS control",
           before={"owner": "Ramesh Kr."}, after={"owner": "Ramesh Kumar"})
log.append("r.sharma", "tehsildar", "escalate", "C0117",
           "ownership disputed between revenue record and legacy sheet")

v = log.verify()
print(f"  entries        {len(log)}")
print(f"  intact         {v['intact']}  — {v['detail']}")
print(f"  chain head     {log.head()[:40]}…")

print("\n  tamper demonstration (entry 3 reason altered):")
t2 = log.simulate_tamper(3, "reason", "RMSE 0.01 -> 0.01 m, 9999 inliers")
print(f"    intact       {t2['intact']}")
print(f"    broken at    entry {t2['broken_at']} ({t2['kind']})")
print(f"    {t2['detail']}")
log.load()
print(f"  reloaded from disk, intact = {log.verify()['intact']}")

# ---------------------------------------------------------------- exports
print("\n" + "=" * 70)
print("EXPORTS")
print("=" * 70)
harm = json.loads((DEMO / "harmonized.geojson").read_text(encoding="utf-8"))
feats = harm["features"]
print(f"  source: {len(feats):,} harmonized parcels")

bundle = ExportBundle(str(OUT))

p = export_geojson(feats, str(OUT / "kshetra_harmonized.geojson"))
bundle.add(p); print(f"  geojson    {os.path.getsize(p)/1024:9.1f} KB")

p = export_csv(feats, str(OUT / "kshetra_harmonized.csv"))
bundle.add(p); print(f"  csv        {os.path.getsize(p)/1024:9.1f} KB")

WGS84_WKT = ('GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,'
             '298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]')
sh = export_shapefile(feats, str(OUT / "kshetra_harmonized"), WGS84_WKT)
for ext in (".shp", ".shx", ".dbf", ".prj"):
    f = sh["base"] + ext
    if os.path.exists(f):
        bundle.add(f); print(f"  {ext[1:]:<10} {os.path.getsize(f)/1024:9.1f} KB")
bundle.add(sh["sidecar"])
trunc = {k: v for k, v in sh["fields"].items() if k != v}
print(f"  dbf field names truncated: {trunc if trunc else 'none'}")

p = export_audit_pdf(str(OUT / "kshetra_audit_report.pdf"),
                     log.to_dicts(), metrics, log.verify())
bundle.add(p); print(f"  pdf        {os.path.getsize(p)/1024:9.1f} KB")

mp = bundle.write_manifest(log.head(), metrics)
print(f"  manifest   {os.path.getsize(mp)/1024:9.1f} KB")

man = json.loads(Path(mp).read_text(encoding="utf-8"))
print(f"\n  manifest lists {len(man['files'])} files, each with a sha256")
print(f"  audit_chain_head {man['audit_chain_head'][:40]}…")
print(f"  disclaimer: {man['disclaimer'][:70]}…")
print("\nall exports written to data/export/")
