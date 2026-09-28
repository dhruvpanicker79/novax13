"""Exercise the API, with attention to the things that must NOT work.

Redaction and permission checks are only real if the negative cases fail, so
this asserts on refusals as much as on successes.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from api.main import app

c = TestClient(app)
FAILS = []


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{'  ' + detail if detail else ''}")
    if not ok:
        FAILS.append(label)


def hdr(role):
    return {"X-Role": role}


print("=" * 72)
print("1. HEALTH + METRICS")
print("=" * 72)
r = c.get("/health")
check("health 200", r.status_code == 200, str(r.json().get("status")))
r = c.get("/api/metrics")
m = r.json()
check("metrics served", r.status_code == 200,
      f"F1 {m['matching']['f1']}, ECE {m['matching']['ece']}")

print("\n" + "=" * 72)
print("2. RBAC REDACTION  (owner names are personal data)")
print("=" * 72)
pub = c.get("/api/layers/harmonized?limit=3", headers=hdr("public")).json()
teh = c.get("/api/layers/harmonized?limit=3", headers=hdr("tehsildar")).json()
p0, t0 = pub["features"][0]["properties"], teh["features"][0]["properties"]
check("public does NOT receive owner", "KHATEDAR_NM" not in p0,
      f"keys: {sorted(k for k in p0 if not k.startswith('_'))}")
check("public is told what was withheld", "_redacted" in p0,
      str(p0.get("_redacted")))
check("tehsildar DOES receive owner", "KHATEDAR_NM" in t0,
      str(t0.get("KHATEDAR_NM"))[:34])
sur = c.get("/api/layers/harmonized?limit=1", headers=hdr("surveyor")).json()
s0 = sur["features"][0]["properties"]
check("surveyor sees tenure but not owner",
      "TENURE_TYP" in s0 and "KHATEDAR_NM" not in s0)
check("unknown role rejected",
      c.get("/api/layers/harmonized", headers=hdr("mayor")).status_code == 400)

print("\n" + "=" * 72)
print("3. PERMISSIONS  (who may act on a flagged conflict)")
print("=" * 72)
cid = c.get("/api/conflicts?limit=1").json()["conflicts"][0]["id"]
r = c.post(f"/api/conflicts/{cid}/review",
           json={"action": "accept", "reason": "verified against GNSS control"},
           headers=hdr("public"))
check("public may NOT accept", r.status_code == 403, r.json().get("detail", "")[:58])
r = c.post(f"/api/conflicts/{cid}/review",
           json={"action": "accept", "reason": "verified against GNSS control"},
           headers=hdr("surveyor"))
check("surveyor may NOT accept", r.status_code == 403)
r = c.post(f"/api/conflicts/{cid}/review",
           json={"action": "accept", "reason": "verified against GNSS control"},
           headers=hdr("tehsildar"))
check("tehsildar MAY accept", r.status_code == 200,
      f"audit seq {r.json().get('audit_seq')}")
r = c.post(f"/api/conflicts/{cid}/review",
           json={"action": "accept", "reason": "x"}, headers=hdr("tehsildar"))
check("empty reason rejected", r.status_code == 422)

print("\n" + "=" * 72)
print("4. AUDIT CHAIN  (server-side, verifiable)")
print("=" * 72)
v = c.get("/api/audit/verify").json()
check("chain intact", v["intact"], v["detail"])
a = c.get("/api/audit").json()
check("entries recorded", a["count"] >= 1, f"{a['count']} entries")
last = a["entries"][-1]
check("before/after captured", last.get("before") is not None,
      f"{last['action']} on {last['target']}")
r = c.post("/api/audit/tamper-demo", json={"seq": 1, "new_value": "forged"},
           headers=hdr("public"))
check("tamper demo refused for public", r.status_code == 403)
r = c.post("/api/audit/tamper-demo", json={"seq": 1, "new_value": "forged"},
           headers=hdr("tehsildar"))
td = r.json()
check("tampering breaks the chain", td.get("intact") is False,
      f"broken at {td.get('broken_at')} ({td.get('kind')})")
check("chain restored after reload", td.get("restored") is True)

print("\n" + "=" * 72)
print("5. EXPORT")
print("=" * 72)
r = c.get("/api/export/geojson", headers=hdr("public"))
check("public may NOT download exports", r.status_code == 403)
r = c.get("/api/export", headers=hdr("clerk")).json()
avail = [f["id"] for f in r["formats"] if f["available"]]
check("formats available", len(avail) >= 4, ", ".join(avail))
r = c.get("/api/export/pdf", headers=hdr("clerk"))
check("clerk may download the PDF", r.status_code == 200,
      f"{len(r.content) / 1024:.1f} KB")

print("\n" + "=" * 72)
print("6. OGC API - FEATURES")
print("=" * 72)
check("landing page", c.get("/ogc").status_code == 200)
cf = c.get("/ogc/conformance").json()
check("declares conformance classes", len(cf["conformsTo"]) >= 2)
cols = c.get("/ogc/collections").json()["collections"]
check("collections listed", len(cols) >= 4,
      ", ".join(x["id"] for x in cols))
it = c.get("/ogc/collections/harmonized/items?limit=5", headers=hdr("public"))
j = it.json()
check("items are geo+json", it.headers["content-type"].startswith("application/geo+json"))
check("numberMatched reported", j["numberMatched"] > 3000, str(j["numberMatched"]))
check("OGC path redacts too",
      "KHATEDAR_NM" not in j["features"][0]["properties"])

print("\n" + "=" * 72)
if FAILS:
    print(f"{len(FAILS)} CHECK(S) FAILED:")
    for f in FAILS:
        print(f"  - {f}")
    sys.exit(1)
print("ALL API CHECKS PASSED")
print("=" * 72)
