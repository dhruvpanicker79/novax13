"""Sanity-check fetched layers without the numeric stack.

Uses the shoelace formula on a locally-projected plane, which is accurate
enough over a 4 km AOI to tell a real building from a parsing accident.
"""
import json, math, sys, os

def local_scale(lat):
    """Metres per degree at this latitude (WGS84 series approximation)."""
    p = math.radians(lat)
    m_lat = 111132.92 - 559.82*math.cos(2*p) + 1.175*math.cos(4*p)
    m_lon = 111412.84*math.cos(p) - 93.5*math.cos(3*p)
    return m_lon, m_lat

def ring_area_m2(ring, lon0, lat0):
    mx, my = local_scale(lat0)
    pts = [((x-lon0)*mx, (y-lat0)*my) for x, y in ring]
    s = 0.0
    for i in range(len(pts)-1):
        s += pts[i][0]*pts[i+1][1] - pts[i+1][0]*pts[i][1]
    return abs(s)/2.0

def inspect(path):
    if not os.path.exists(path):
        print(f"  MISSING {path}")
        return
    gj = json.load(open(path, encoding="utf-8"))
    feats = gj["features"]
    if not feats:
        print(f"  {os.path.basename(path):<38} 0 features")
        return
    xs, ys = [], []
    for f in feats:
        g = f["geometry"]
        cs = g["coordinates"][0] if g["type"] == "Polygon" else g["coordinates"]
        for x, y in cs:
            xs.append(x); ys.append(y)
    lon0, lat0 = sum(xs)/len(xs), sum(ys)/len(ys)

    name = os.path.basename(path)
    if feats[0]["geometry"]["type"] == "Polygon":
        areas = sorted(ring_area_m2(f["geometry"]["coordinates"][0], lon0, lat0)
                       for f in feats)
        med = areas[len(areas)//2]
        tiny = sum(1 for a in areas if a < 5)
        huge = sum(1 for a in areas if a > 20000)
        print(f"  {name:<38} {len(feats):>6,} polys   "
              f"median {med:7.1f} m²   p05 {areas[len(areas)//20]:6.1f}   "
              f"p95 {areas[int(len(areas)*.95)]:7.1f}")
        print(f"  {'':<38} degenerate(<5m²) {tiny}   implausible(>2ha) {huge}")
    else:
        tot = 0.0
        mx, my = local_scale(lat0)
        for f in feats:
            cs = f["geometry"]["coordinates"]
            for i in range(len(cs)-1):
                dx = (cs[i+1][0]-cs[i][0])*mx
                dy = (cs[i+1][1]-cs[i][1])*my
                tot += math.hypot(dx, dy)
        print(f"  {name:<38} {len(feats):>6,} lines   total {tot/1000:.1f} km")
    print(f"  {'':<38} bbox {min(xs):.4f},{min(ys):.4f} -> {max(xs):.4f},{max(ys):.4f}")

print("CHANDAUSI — real fetched layers\n")
for p in ["data/raw/chandausi_ms_buildings.geojson",
          "data/raw/chandausi_osm_buildings.geojson",
          "data/raw/chandausi_osm_roads.geojson"]:
    inspect(p); print()

ms = json.load(open("data/raw/chandausi_ms_buildings.geojson", encoding="utf-8"))
osm = json.load(open("data/raw/chandausi_osm_buildings.geojson", encoding="utf-8"))
print(f"THE GAP:  {len(ms['features']):,} AI-extracted footprints  vs  "
      f"{len(osm['features'])} in the municipal/OSM layer")
if osm['features']:
    print(f"          ratio {len(ms['features'])/len(osm['features']):.0f} : 1")
print("\nsample MS properties:", json.dumps(ms["features"][0]["properties"]))
