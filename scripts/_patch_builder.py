"""One-shot patch: wire schema matching, change detection, encroachment and
conflict resolution into scripts/build_demo.py."""
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_demo.py")
s = open(P, encoding="utf-8").read()

if "match_schema" in s:
    print("already wired")
    raise SystemExit(0)

s = s.replace(
    "from kshetra.crs import utm_to_geodetic",
    "from shapely.affinity import scale as shp_scale, translate as shp_translate\n"
    "\n"
    "from kshetra.attributes.schema_match import match_schema\n"
    "from kshetra.change.detect import (\n"
    "    build_dossier, detect_change, detect_encroachment)\n"
    "from kshetra.conflict.resolve import Claim, SourceProfile, resolve_parcel\n"
    "from kshetra.crs import utm_to_geodetic")

NEW = '''    # ---- 6b. schema auto-matching -------------------------------------
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
            gc = gf.geometry.centroid
            bx, by, mx, my = gf.geometry.bounds
            for e in range(2):
                src = b0[int(rng2.integers(0, len(b0)))]
                sc = src.geometry.centroid
                # Straddle the boundary: unauthorised construction creeps over
                # an edge rather than landing in the middle of a park.
                edge = rng2.uniform(0.45, 0.95)
                off_x = gc.x - sc.x + (mx - gc.x) * edge + rng2.uniform(-4, 4)
                off_y = gc.y - sc.y + rng2.uniform(-9, 9)
                g = shp_translate(src.geometry, off_x, off_y)
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

    # ---- 7. write ------------------------------------------------------'''

s = s.replace("    # ---- 7. write ------------------------------------------------------", NEW)

s = s.replace(
    '    write("metrics.json", metrics)',
    '    write("schema.json", schema_out)\n'
    '    write("change.json", change_out)\n'
    '    write("buildings_t1.geojson", t1_fc)\n'
    '    write("resolutions.json", conflict_cases)\n'
    '\n'
    '    metrics["schema"] = {\n'
    '        "mapped": sum(1 for f in schema_out["fields"] if f["column"]),\n'
    '        "total": len(schema_out["fields"]),\n'
    '        "area_unit": sm.area_unit,\n'
    '        "area_unit_confidence": round(sm.area_unit_confidence, 4),\n'
    '    }\n'
    '    metrics["change"] = dict(chg.counts())\n'
    '    metrics["change"]["encroached_sqm"] = round(chg.encroached_area(), 1)\n'
    '    metrics["change"]["dsm_available"] = chg.dsm_available\n'
    '    write("metrics.json", metrics)')

TAIL_OLD = '    print(f"  conflicts   {len(conflicts)}")'
TAIL_NEW = """    print(f"  conflicts   {len(conflicts)}")
    print(f"  schema      {metrics['schema']['mapped']}/{metrics['schema']['total']}"
          f" columns, area unit {sm.area_unit}"
          f" ({sm.area_unit_confidence:.2f})")
    print(f"  change      {chg.summary()}")"""
s = s.replace(TAIL_OLD, TAIL_NEW)

open(P, "w", encoding="utf-8").write(s)
print("build_demo.py wired")
