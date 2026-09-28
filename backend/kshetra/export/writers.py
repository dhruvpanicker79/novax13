"""Export the harmonized layer in the formats a municipality can actually use.

Four outputs, each for a different consumer:

``GeoJSON``   web clients and anything modern
``Shapefile`` still the lingua franca of Indian revenue departments, and the
              format Bhu-Naksha imports
``CSV``       the attribute table, for people who work in a spreadsheet
``PDF``       the audit report -- every change, its reason, its confidence and
              its source, which is what makes the output reviewable rather
              than merely available

Two constraints shape the code. Shapefile field names are capped at 10
characters by the DBF format, so long canonical names are truncated
deterministically and the mapping is written alongside as a sidecar -- silently
mangling ``recorded_area_sqm`` to ``recorded_a`` with no record of it is how
attribute meaning gets lost between departments. And every export carries a
manifest with the audit chain head, so a file can be tied back to the exact
pipeline state that produced it.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import time
from typing import Any, Sequence

__all__ = ["export_geojson", "export_shapefile", "export_csv",
           "export_audit_pdf", "write_manifest", "ExportBundle"]

#: DBF truncates field names to 10 characters.
DBF_NAME_LIMIT = 10


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _dbf_names(fields: Sequence[str]) -> dict[str, str]:
    """Map canonical names onto unique <=10 character DBF names."""
    out: dict[str, str] = {}
    used: set[str] = set()
    for f in fields:
        base = f[:DBF_NAME_LIMIT]
        name, n = base, 1
        while name.lower() in used:
            suffix = str(n)
            name = base[: DBF_NAME_LIMIT - len(suffix)] + suffix
            n += 1
        used.add(name.lower())
        out[f] = name
    return out


# --------------------------------------------------------------------------
def export_geojson(features: list[dict], path: str, crs: str = "EPSG:4326") -> str:
    fc = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": crs}},
        "features": features,
    }
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(fc, fh, separators=(",", ":"))
    return path


def export_csv(features: list[dict], path: str) -> str:
    """Attribute table only. Geometry is summarised as a representative point."""
    if not features:
        return path
    keys: list[str] = []
    for f in features:
        for k in f.get("properties", {}):
            if k not in keys:
                keys.append(k)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys + ["lon", "lat"],
                           extrasaction="ignore")
        w.writeheader()
        for f in features:
            row = dict(f.get("properties", {}))
            ring = f["geometry"]["coordinates"][0]
            row["lon"] = round(sum(p[0] for p in ring) / len(ring), 7)
            row["lat"] = round(sum(p[1] for p in ring) / len(ring), 7)
            w.writerow(row)
    return path


def export_shapefile(features: list[dict], path_base: str,
                     crs_wkt: str | None = None) -> dict:
    """Write an ESRI Shapefile plus a sidecar recording the field-name mapping."""
    import shapefile  # pyshp

    os.makedirs(os.path.dirname(os.path.abspath(path_base)), exist_ok=True)
    keys: list[str] = []
    for f in features:
        for k in f.get("properties", {}):
            if k not in keys:
                keys.append(k)
    names = _dbf_names(keys)

    w = shapefile.Writer(path_base, shapeType=shapefile.POLYGON)
    for k in keys:
        sample = next((f["properties"].get(k) for f in features
                       if f["properties"].get(k) is not None), None)
        if isinstance(sample, bool):
            w.field(names[k], "L")
        elif isinstance(sample, int):
            w.field(names[k], "N", 18, 0)
        elif isinstance(sample, float):
            w.field(names[k], "N", 18, 6)
        else:
            w.field(names[k], "C", 120)

    for f in features:
        w.poly([[list(p) for p in f["geometry"]["coordinates"][0]]])
        w.record(**{names[k]: f["properties"].get(k) for k in keys})
    w.close()

    # .prj so the file is not orphaned from its CRS
    if crs_wkt:
        with open(path_base + ".prj", "w", encoding="utf-8") as fh:
            fh.write(crs_wkt)

    # Record the truncation, so nobody has to guess what 'recorded_a' meant.
    sidecar = path_base + ".fields.json"
    with open(sidecar, "w", encoding="utf-8") as fh:
        json.dump({"note": "DBF truncates field names to 10 characters; "
                           "this maps the exported names back to canonical ones.",
                   "mapping": names}, fh, indent=1)
    return {"base": path_base, "fields": names, "sidecar": sidecar}


# --------------------------------------------------------------------------
#: fpdf2's built-in fonts are latin-1 only. Rather than ship a Unicode TTF just
#: for punctuation, fold the few non-latin-1 characters we use down to ASCII.
_PDF_FOLD = {
    "—": "-", "–": "-", "→": "->", "…": "...",
    "·": "-", "²": "2", "³": "3", "’": "'",
    "“": '"', "”": '"', "‘": "'", "₹": "Rs ",
    "σ": "sigma", "≥": ">=", "≤": "<=", "×": "x",
}


def _pdf_text(t: Any) -> str:
    s = str(t)
    for a, b in _PDF_FOLD.items():
        s = s.replace(a, b)
    # Anything still outside latin-1 is dropped rather than raising mid-report.
    return s.encode("latin-1", "replace").decode("latin-1")


def export_audit_pdf(path: str, audit: Sequence[dict], metrics: dict,
                     verification: dict, title: str = "KSHETRA") -> str:
    """Audit report: what changed, why, on whose evidence, and at what confidence."""
    from fpdf import FPDF

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    def h1(t):
        pdf.set_font("Helvetica", "B", 15); pdf.set_text_color(20, 24, 28)
        pdf.cell(0, 9, _pdf_text(t), new_x="LMARGIN", new_y="NEXT")

    def h2(t):
        pdf.ln(2); pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(70, 76, 84)
        pdf.cell(0, 6, _pdf_text(t).upper(), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(200, 204, 210)
        pdf.line(pdf.l_margin, pdf.get_y(), 210 - pdf.r_margin, pdf.get_y())
        pdf.ln(1.5)

    def kv(k, v, colour=(20, 24, 28)):
        pdf.set_font("Helvetica", "", 9); pdf.set_text_color(90, 96, 104)
        pdf.cell(66, 5.4, _pdf_text(k))
        pdf.set_font("Courier", "", 9); pdf.set_text_color(*colour)
        pdf.cell(0, 5.4, _pdf_text(v), new_x="LMARGIN", new_y="NEXT")

    def body(t):
        pdf.set_font("Helvetica", "", 8.6); pdf.set_text_color(90, 96, 104)
        pdf.multi_cell(0, 4.4, _pdf_text(t))
        pdf.ln(1)

    h1(f"{title} — Harmonization Audit Report")
    pdf.set_font("Helvetica", "", 9); pdf.set_text_color(110, 116, 124)
    pdf.cell(0, 5, _pdf_text(
        f"Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}"
        f"   |   Chandausi, Sambhal, Uttar Pradesh   |   EPSG:32644"),
        new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    h2("Chain integrity")
    ok = verification.get("intact")
    kv("Status", "INTACT" if ok else f"BROKEN at entry {verification.get('broken_at')}",
       (30, 120, 60) if ok else (170, 40, 36))
    kv("Entries verified", f"{verification.get('verified')} / {verification.get('total')}")
    if verification.get("head"):
        kv("Chain head", verification["head"][:48] + "…")
    body("Each entry carries a SHA-256 over its own contents and the hash of the "
         "entry before it. Altering any historical field breaks every link after "
         "it, so silent selective edits are detectable.")

    g, m, t = metrics.get("georef", {}), metrics.get("matching", {}), metrics.get("topology", {})
    h2("Harmonization result")
    kv("Positional RMSE", f"{g.get('rmse_raw')} m  ->  {g.get('rmse_coarse')} m")
    kv("Match F1 / ROC AUC", f"{m.get('f1')} / {m.get('roc_auc')}")
    kv("Calibration error (ECE)", m.get("ece"))
    kv("Blocking recall", m.get("blocking_recall"))
    kv("Geometric share of model", f"{round((m.get('geometry_share') or 0) * 100, 1)} %")

    h2("Topology and area conservation")
    kv("Topology errors", f"{t.get('total_before')}  ->  {t.get('total_after')}")
    kv("Overlapping parcel pairs", f"{t.get('overlaps_before')}  ->  {t.get('overlaps_after')}")
    kv("Doubly-claimed land", f"{t.get('overlap_area_before')} m2  ->  {t.get('overlap_area_after')} m2")
    kv("Summed parcel area", f"{t.get('area_before')} m2  ->  {t.get('area_after')} m2")
    kv("Parcel-sized holes refused", t.get("refused_to_fill"))
    body("The summed parcel area falls because land recorded as owned by two "
         "parties simultaneously is counted once after harmonization. No land "
         "was created or destroyed. Holes the size of a whole parcel are flagged "
         "for ground survey and deliberately not filled; filling them would "
         "fabricate a boundary.")

    ch = metrics.get("change") or {}
    if ch:
        h2("Change and encroachment")
        for k2 in ("new", "demolished", "extended", "heightened"):
            if ch.get(k2):
                kv(k2.capitalize(), ch[k2])
        kv("Encroachment on public land",
           f"{ch.get('encroachment', 0)} sites, {ch.get('encroached_sqm', 0)} m2",
           (170, 40, 36))
        body("Encroachment findings are advisory. This report is not a mutation "
             "record and carries no statutory effect; each finding requires "
             "verification on site by the competent revenue officer.")

    # --- the log itself ---
    pdf.add_page()
    h2(f"Audit trail — {len(audit)} entries")
    pdf.set_font("Courier", "B", 7.2); pdf.set_text_color(70, 76, 84)
    cols = [(11, "#"), (30, "Timestamp"), (24, "Actor"), (28, "Action"),
            (24, "Target"), (61, "Reason")]
    for wdt, lbl in cols:
        pdf.cell(wdt, 5, _pdf_text(lbl))
    pdf.ln(5)
    pdf.set_font("Courier", "", 6.8)
    for e in audit[:220]:
        if pdf.get_y() > 272:
            pdf.add_page()
        pdf.set_text_color(20, 24, 28)
        pdf.cell(11, 4.4, _pdf_text(e.get("seq", "")))
        pdf.cell(30, 4.4, _pdf_text(e.get("ts", ""))[:19])
        pdf.cell(24, 4.4, _pdf_text(e.get("actor", ""))[:13])
        pdf.cell(28, 4.4, _pdf_text(e.get("action", ""))[:16])
        pdf.cell(24, 4.4, _pdf_text(e.get("target", ""))[:13])
        pdf.set_text_color(110, 116, 124)
        pdf.cell(61, 4.4, _pdf_text(e.get("reason", ""))[:46])
        pdf.ln(4.4)

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    pdf.output(path)
    return path


# --------------------------------------------------------------------------
class ExportBundle:
    """A set of exported files plus a manifest tying them to the pipeline state."""

    def __init__(self, out_dir: str):
        self.out_dir = out_dir
        self.files: list[str] = []
        os.makedirs(out_dir, exist_ok=True)

    def add(self, path: str) -> None:
        if os.path.exists(path):
            self.files.append(path)

    def manifest(self, chain_head: str, metrics: dict, extra: dict | None = None
                 ) -> dict:
        entries = []
        for p in sorted(set(self.files)):
            entries.append({
                "file": os.path.basename(p),
                "bytes": os.path.getsize(p),
                "sha256": _sha256_file(p),
            })
        return {
            "product": "KSHETRA harmonized cadastre",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "crs": "EPSG:4326 (geographic) / EPSG:32644 (projected)",
            "audit_chain_head": chain_head,
            "pipeline": {
                "rmse_before_m": metrics.get("georef", {}).get("rmse_raw"),
                "rmse_after_m": metrics.get("georef", {}).get("rmse_coarse"),
                "match_f1": metrics.get("matching", {}).get("f1"),
                "calibration_ece": metrics.get("matching", {}).get("ece"),
            },
            "disclaimer": (
                "Contains SYNTHETIC cadastral geometry derived from OpenStreetMap "
                "block structure. Not a record of title. Advisory only."),
            "files": entries,
            **(extra or {}),
        }

    def write_manifest(self, chain_head: str, metrics: dict,
                       extra: dict | None = None) -> str:
        p = os.path.join(self.out_dir, "MANIFEST.json")
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(self.manifest(chain_head, metrics, extra), fh, indent=1)
        return p


def write_manifest(out_dir: str, files: Sequence[str], chain_head: str,
                   metrics: dict) -> str:
    b = ExportBundle(out_dir)
    for f in files:
        b.add(f)
    return b.write_manifest(chain_head, metrics)
