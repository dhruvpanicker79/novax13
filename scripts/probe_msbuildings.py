"""Check Microsoft GlobalMLBuildingFootprints coverage for our AOIs."""
import csv, io, math, sys
import requests

LINKS = "https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv"
HEADERS = {"User-Agent": "BhoomiSetu/0.1 (SIH2026 cadastral research)"}

AOIS = {
    "Chandausi (NAKSHA pilot)": (78.7749, 28.4515),
    "Bhopal":                   (77.4126, 23.2599),
    "Indore":                   (75.8577, 22.7196),
    "Pune":                     (73.8553, 18.5308),
    "Jaipur":                   (75.8267, 26.9239),
}


def quadkey(lon, lat, zoom=9):
    """Bing tile quadkey — the indexing MS uses for these files."""
    sin = math.sin(lat * math.pi / 180)
    x = (lon + 180) / 360
    y = 0.5 - math.log((1 + sin) / (1 - sin)) / (4 * math.pi)
    n = 1 << zoom
    tx, ty = int(x * n), int(y * n)
    qk = ""
    for i in range(zoom, 0, -1):
        d, mask = 0, 1 << (i - 1)
        if tx & mask:
            d += 1
        if ty & mask:
            d += 2
        qk += str(d)
    return qk


print("fetching MS dataset index ...")
r = requests.get(LINKS, headers=HEADERS, timeout=300)
r.raise_for_status()
rows = list(csv.DictReader(io.StringIO(r.text)))
print(f"index has {len(rows):,} tiles globally")

india = [x for x in rows if x.get("Location") == "India"]
print(f"India tiles: {len(india):,}")
by_qk = {}
for x in india:
    by_qk.setdefault(x["QuadKey"], []).append(x)

print(f"\n{'AOI':<28} {'quadkey':<12} {'MS tile?':<10} size")
print("-" * 68)
for name, (lon, lat) in AOIS.items():
    qk = quadkey(lon, lat, 9)
    hit = by_qk.get(qk)
    if hit:
        sz = hit[0].get("Size", "?")
        print(f"{name:<28} {qk:<12} {'YES':<10} {sz}")
    else:
        print(f"{name:<28} {qk:<12} {'no':<10} -")

with open("data/raw/ms_india_tiles.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(india)
print(f"\nwrote data/raw/ms_india_tiles.csv ({len(india):,} rows)")
