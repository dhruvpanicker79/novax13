"""KSHETRA API.

Serves the harmonized layer, the review queue, the audit chain and the exports,
and exposes an OGC API - Features endpoint so any GIS client can consume the
output directly.

Two things here are not decoration:

**Redaction is server-side.** Owner names are personal data under the DPDP Act
2023. A ``public`` caller never receives them -- not hidden in the UI, not
returned and styled away, simply absent from the response body. Doing it in the
client is not a control, because the client is not trusted.

**The audit chain lives here, not in the browser.** A hash chain computed in
JavaScript proves nothing; anyone can edit it in devtools. Review actions are
appended server-side, and ``/api/audit/verify`` walks the chain and reports the
exact entry where it first breaks.

Run:  PYTHONPATH=backend uvicorn api.main:app --reload --port 8000
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from kshetra.audit import AuditLog  # noqa: E402

DEMO = ROOT / "data" / "demo"
EXPORT = ROOT / "data" / "export"
AUDIT_PATH = ROOT / "data" / "audit" / "audit.jsonl"

app = FastAPI(
    title="KSHETRA",
    description="Automated harmonization of multi-source urban land records",
    version="0.2.0",
)
#: Local dev hosts, plus anything named explicitly at deploy time. Deployed,
#: the UI is served from this same origin and needs no entry here at all --
#: an open allowlist on a service that returns owner names would defeat the
#: redaction below, so the deployed default is to add nothing.
ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173",
                   "http://localhost:8080", "http://127.0.0.1:8080"]
ALLOWED_ORIGINS += [o.strip() for o in
                    os.environ.get("KSHETRA_ALLOWED_ORIGINS", "").split(",")
                    if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

audit = AuditLog(str(AUDIT_PATH))

# --------------------------------------------------------------------------
# roles
# --------------------------------------------------------------------------
Role = Literal["public", "surveyor", "clerk", "tehsildar"]

#: Fields each role may receive. Owner and tenure are personal data and are
#: withheld from the public role entirely.
VISIBLE: dict[str, set[str]] = {
    "public": {"fid", "KHSRA_NUM", "LU_CODE", "WARD", "PARCEL_UID",
               "area_sqm", "confidence", "relation"},
    "surveyor": {"fid", "KHSRA_NUM", "LU_CODE", "WARD", "PARCEL_UID",
                 "area_sqm", "AREA_BIGHA", "confidence", "relation",
                 "TENURE_TYP"},
    "clerk": set(),      # empty set means "everything"
    "tehsildar": set(),
}
#: Actions each role may take on a flagged conflict.
MAY_ACT: dict[str, set[str]] = {
    "public": set(),
    "surveyor": {"survey"},
    "clerk": {"escalate", "survey"},
    "tehsildar": {"accept", "reject", "escalate", "survey"},
}


def get_role(x_role: str = Header(default="public", alias="X-Role")) -> str:
    if x_role not in VISIBLE:
        raise HTTPException(400, f"unknown role '{x_role}'")
    return x_role


def redact_props(props: dict, role: str) -> dict:
    allowed = VISIBLE[role]
    if not allowed:
        return props
    out = {k: v for k, v in props.items() if k in allowed}
    withheld = [k for k in props if k not in allowed]
    if withheld:
        # Say that something was withheld rather than pretending the record is
        # complete; a silently truncated record is worse than a marked one.
        out["_redacted"] = withheld
    return out


def _load(name: str) -> Any:
    p = DEMO / name
    if not p.exists():
        raise HTTPException(
            503, f"{name} not built — run scripts/build_demo.py first")
    return json.loads(p.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# models
# --------------------------------------------------------------------------
class ReviewAction(BaseModel):
    action: Literal["accept", "reject", "escalate", "survey"]
    reason: str = Field(min_length=3, max_length=500)
    actor: str = Field(default="demo.user", max_length=64)


class TamperRequest(BaseModel):
    seq: int = Field(ge=1)
    field_name: str = "reason"
    new_value: str = "tampered"


# --------------------------------------------------------------------------
# meta
# --------------------------------------------------------------------------
@app.get("/health")
def health():
    built = (DEMO / "metrics.json").exists()
    return {"status": "ok" if built else "artifacts missing",
            "artifacts_built": built,
            "audit_entries": len(audit),
            "chain_head": audit.head()}


@app.get("/api/metrics")
def metrics():
    return _load("metrics.json")


@app.get("/api/schema")
def schema():
    return _load("schema.json")


@app.get("/api/survey-plan")
def survey_plan():
    return _load("survey_plan.json")


@app.get("/api/change")
def change():
    return _load("change.json")


@app.get("/api/resolutions")
def resolutions():
    return _load("resolutions.json")


# --------------------------------------------------------------------------
# layers
# --------------------------------------------------------------------------
LAYERS = {
    "harmonized": "harmonized.geojson",
    "reference": "reference.geojson",
    "legacy": "legacy.geojson",
    "aligned": "aligned.geojson",
    "govt": "govt_land.geojson",
    "buildings": "buildings_t1.geojson",
}


@app.get("/api/layers")
def list_layers():
    return {"layers": [
        {"id": k, "file": v, "available": (DEMO / v).exists()}
        for k, v in LAYERS.items()]}


@app.get("/api/layers/{layer_id}")
def get_layer(layer_id: str, role: str = Depends(get_role),
              limit: int = Query(default=0, ge=0, le=20000)):
    if layer_id not in LAYERS:
        raise HTTPException(404, f"unknown layer '{layer_id}'")
    fc = _load(LAYERS[layer_id])
    feats = fc["features"][:limit] if limit else fc["features"]
    return {
        "type": "FeatureCollection",
        "crs": fc.get("crs"),
        "role": role,
        "features": [{**f, "properties": redact_props(f["properties"], role)}
                     for f in feats],
    }


# --------------------------------------------------------------------------
# review queue
# --------------------------------------------------------------------------
@app.get("/api/conflicts")
def conflicts(role: str = Depends(get_role),
              status: str | None = None,
              limit: int = Query(default=500, ge=1, le=5000)):
    items = _load("conflicts.json")
    if status:
        items = [c for c in items if c.get("status") == status]
    out = []
    for c in items[:limit]:
        c = dict(c)
        if not VISIBLE[role] or "KHATEDAR_NM" in VISIBLE[role]:
            pass
        elif role == "public":
            c.pop("owner", None)
            c["_redacted"] = ["owner"]
        out.append(c)
    return {"role": role, "may_act": sorted(MAY_ACT[role]),
            "count": len(out), "conflicts": out}


@app.post("/api/conflicts/{conflict_id}/review")
def review(conflict_id: str, body: ReviewAction, role: str = Depends(get_role)):
    if body.action not in MAY_ACT[role]:
        raise HTTPException(
            403, f"role '{role}' may not '{body.action}'; "
                 f"permitted: {sorted(MAY_ACT[role]) or 'none'}")
    items = _load("conflicts.json")
    target = next((c for c in items if c["id"] == conflict_id), None)
    if target is None:
        raise HTTPException(404, f"no conflict '{conflict_id}'")

    e = audit.append(
        actor=body.actor, role=role, action=body.action, target=conflict_id,
        reason=body.reason,
        before={"status": target.get("status", "open"),
                "class": target.get("class"),
                "confidence": target.get("confidence")},
        after={"status": body.action})
    return {"ok": True, "conflict": conflict_id, "action": body.action,
            "audit_seq": e.seq, "hash": e.hash, "chain_head": audit.head()}


# --------------------------------------------------------------------------
# audit
# --------------------------------------------------------------------------
@app.get("/api/audit")
def get_audit(limit: int = Query(default=500, ge=1, le=5000)):
    return {"count": len(audit), "chain_head": audit.head(),
            "entries": audit.to_dicts()[-limit:]}


@app.get("/api/audit/verify")
def verify_audit():
    return audit.verify()


@app.post("/api/audit/tamper-demo")
def tamper_demo(body: TamperRequest, role: str = Depends(get_role)):
    """Alter a historical entry in memory, show the break, then reload.

    Exists so the tamper-evidence claim can be demonstrated live instead of
    asserted. The on-disk log is untouched.
    """
    if role != "tehsildar":
        raise HTTPException(403, "tamper demonstration requires role 'tehsildar'")
    result = audit.simulate_tamper(body.seq, body.field_name, body.new_value)
    audit.load()
    result["restored"] = audit.verify()["intact"]
    return result


# --------------------------------------------------------------------------
# exports
# --------------------------------------------------------------------------
EXPORTS = {
    "geojson": "kshetra_harmonized.geojson",
    "csv": "kshetra_harmonized.csv",
    "shp": "kshetra_harmonized.shp",
    "dbf": "kshetra_harmonized.dbf",
    "pdf": "kshetra_audit_report.pdf",
    "manifest": "MANIFEST.json",
}


@app.get("/api/export")
def list_exports():
    return {"formats": [
        {"id": k, "file": v, "available": (EXPORT / v).exists(),
         "bytes": (EXPORT / v).stat().st_size if (EXPORT / v).exists() else 0}
        for k, v in EXPORTS.items()]}


@app.get("/api/export/{fmt}")
def download(fmt: str, role: str = Depends(get_role)):
    if role == "public":
        raise HTTPException(403, "exports contain personal data; "
                                 "role 'public' may not download them")
    if fmt not in EXPORTS:
        raise HTTPException(404, f"unknown format '{fmt}'")
    p = EXPORT / EXPORTS[fmt]
    if not p.exists():
        raise HTTPException(503, "exports not built — run scripts/check_export.py")
    audit.append(actor="api", role=role, action="export", target=fmt,
                 reason=f"{EXPORTS[fmt]} downloaded")
    return FileResponse(str(p), filename=p.name)


# --------------------------------------------------------------------------
# OGC API - Features (subset)
# --------------------------------------------------------------------------
@app.get("/ogc")
def ogc_landing():
    return {
        "title": "KSHETRA harmonized cadastre",
        "description": "OGC API - Features endpoint for the harmonized layer",
        "links": [
            {"rel": "self", "href": "/ogc", "type": "application/json"},
            {"rel": "conformance", "href": "/ogc/conformance"},
            {"rel": "data", "href": "/ogc/collections"},
        ],
    }


@app.get("/ogc/conformance")
def ogc_conformance():
    return {"conformsTo": [
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
        "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson",
    ]}


@app.get("/ogc/collections")
def ogc_collections():
    return {"collections": [
        {"id": k, "title": k, "itemType": "feature",
         "crs": ["http://www.opengis.net/def/crs/OGC/1.3/CRS84"],
         "links": [{"rel": "items", "href": f"/ogc/collections/{k}/items",
                    "type": "application/geo+json"}]}
        for k in LAYERS if (DEMO / LAYERS[k]).exists()]}


@app.get("/ogc/collections/{cid}/items")
def ogc_items(cid: str, role: str = Depends(get_role),
              limit: int = Query(default=1000, ge=1, le=10000),
              offset: int = Query(default=0, ge=0)):
    if cid not in LAYERS:
        raise HTTPException(404, f"unknown collection '{cid}'")
    fc = _load(LAYERS[cid])
    feats = fc["features"][offset:offset + limit]
    return JSONResponse(
        media_type="application/geo+json",
        content={
            "type": "FeatureCollection",
            "numberMatched": len(fc["features"]),
            "numberReturned": len(feats),
            "timeStamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "features": [{**f, "properties": redact_props(f["properties"], role)}
                         for f in feats],
            "links": [{"rel": "self",
                       "href": f"/ogc/collections/{cid}/items"
                               f"?limit={limit}&offset={offset}"}],
        })


# --------------------------------------------------------------------------
# the built UI
# --------------------------------------------------------------------------
# Mounted last, so every route above still wins: "/" falls through to the SPA
# only after the API and OGC paths have had their chance. Absent in local
# development, where Vite serves the UI on its own port -- so the mount is
# conditional rather than assumed.
DIST = ROOT / "dist"
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(DIST), html=True), name="ui")
