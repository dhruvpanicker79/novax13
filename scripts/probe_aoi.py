"""Probe candidate AOIs for OSM building density via Overpass.

Runs on stdlib + requests only, so it works even with the numeric stack blocked.
Answers the question the build prompt flags as must-verify-first: is the NAKSHA
pilot site actually mapped well enough to demo on?
"""
import json, sys, time
import requests

OVERPASS = "https://overpass-api.de/api/interpreter"
# Overpass returns 406 without an identifying User-Agent.
HEADERS = {"User-Agent": "BhoomiSetu/0.1 (SIH2026 cadastral research; contact via github)"}

AOIS = {
    "Chandausi, Sambhal, UP (NAKSHA pilot)": (78.7749, 28.4515),
    "Bhopal (old city)":                     (77.4126, 23.2599),
    "Indore (core)":                         (75.8577, 22.7196),
    "Pune (Shivajinagar)":                   (73.8553, 18.5308),
    "Jaipur (walled city)":                  (75.8267, 26.9239),
}
HALF = 0.018          # ~2 km half-span -> ~4 x 4 km AOI


def probe(lon, lat):
    s, w, n, e = lat - HALF, lon - HALF, lat + HALF, lon + HALF
    q = f"""
    [out:json][timeout:90];
    (
      way["building"]({s},{w},{n},{e});
      relation["building"]({s},{w},{n},{e});
    );
    out count;
    """
    q2 = f"""
    [out:json][timeout:90];
    way["highway"]({s},{w},{n},{e});
    out count;
    """
    out = {}
    for label, query in (("buildings", q), ("highways", q2)):
        r = requests.post(OVERPASS, data={"data": query},
                          headers=HEADERS, timeout=180)
        r.raise_for_status()
        js = r.json()
        tags = js.get("elements", [{}])[0].get("tags", {})
        out[label] = int(tags.get("total", 0))
        time.sleep(2)
    return out, (w, s, e, n)


print(f"OSM density probe  (~{HALF*2*111:.1f} x {HALF*2*111:.1f} km AOIs)\n")
print(f"{'AOI':<42} {'buildings':>10} {'roads':>8}   verdict")
print("-" * 82)
results = {}
for name, (lon, lat) in AOIS.items():
    try:
        counts, bbox = probe(lon, lat)
        b, h = counts["buildings"], counts["highways"]
        if b >= 3000:
            verdict = "EXCELLENT"
        elif b >= 1200:
            verdict = "workable"
        elif b >= 300:
            verdict = "thin"
        else:
            verdict = "TOO SPARSE"
        print(f"{name:<42} {b:>10,} {h:>8,}   {verdict}")
        results[name] = {"lon": lon, "lat": lat, "bbox": bbox,
                         "buildings": b, "highways": h, "verdict": verdict}
    except Exception as ex:
        print(f"{name:<42} {'ERROR':>10}   {type(ex).__name__}: {ex}")

with open("data/raw/aoi_probe.json", "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=1)
print("\nwrote data/raw/aoi_probe.json")
