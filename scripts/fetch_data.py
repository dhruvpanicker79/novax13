"""Fetch real source data for an AOI. Pure stdlib + requests (no numpy).

Sources:
  * Microsoft GlobalMLBuildingFootprints  -- AI-extracted footprints
  * OpenStreetMap via Overpass            -- municipal buildings + roads

Both are clipped to the AOI bbox and written as GeoJSON to data/raw/.
"""
import csv, gzip, io, json, math, os, sys, time
import requests

HEADERS = {"User-Agent": "BhoomiSetu/0.1 (SIH2026 cadastral research)"}
# The main Overpass instance is frequently overloaded; rotate through mirrors.
OVERPASS_MIRRORS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
os.makedirs("data/raw", exist_ok=True)

AOIS = {
    "chandausi": dict(lon=78.7749, lat=28.4515, half=0.018,
                      label="Chandausi, Sambhal, UP (NAKSHA pilot)"),
    "pune":      dict(lon=73.8553, lat=18.5308, half=0.018,
                      label="Pune, Shivajinagar"),
}


def bbox(a):
    return (a["lon"] - a["half"], a["lat"] - a["half"],
            a["lon"] + a["half"], a["lat"] + a["half"])


def quadkey(lon, lat, zoom=9):
    sin = math.sin(lat * math.pi / 180)
    x, y = (lon + 180) / 360, 0.5 - math.log((1 + sin) / (1 - sin)) / (4 * math.pi)
    n = 1 << zoom
    tx, ty = int(x * n), int(y * n)
    qk = ""
    for i in range(zoom, 0, -1):
        d, mask = 0, 1 << (i - 1)
        if tx & mask: d += 1
        if ty & mask: d += 2
        qk += str(d)
    return qk


def ring_in_bbox(coords, bb):
    """True if any vertex of the outer ring falls inside the bbox."""
    w, s, e, n = bb
    for x, y in coords:
        if w <= x <= e and s <= y <= n:
            return True
    return False


def download_resumable(url, dest, tries=6):
    """Download with HTTP Range resume.

    A 77 MB file over a slow link takes minutes, and a single read timeout
    throws away all of it. Resuming from the byte already on disk turns a
    fatal error into a retry, and the cached file makes re-parsing free.
    """
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for attempt in range(1, tries + 1):
        have = os.path.getsize(dest) if os.path.exists(dest) else 0
        headers = dict(HEADERS)
        if have:
            headers["Range"] = f"bytes={have}-"
        try:
            with requests.get(url, headers=headers, stream=True,
                              timeout=(30, 120)) as r:
                if r.status_code == 416:      # already complete
                    return dest
                if have and r.status_code != 206:
                    have = 0                  # server ignored Range; restart
                    mode = "wb"
                else:
                    mode = "ab" if have else "wb"
                total = r.headers.get("Content-Length")
                total = (int(total) + have) if total else None
                r.raise_for_status()
                got = have
                t0 = time.time()
                with open(dest, mode) as fh:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        if not chunk:
                            continue
                        fh.write(chunk)
                        got += len(chunk)
                        if got % (16 << 20) < (1 << 20):
                            pct = f"{100*got/total:.0f}%" if total else "?"
                            print(f"       {got/1e6:.0f} MB ({pct}) "
                                  f"{got/1e6/max(time.time()-t0,1):.1f} MB/s")
            return dest
        except requests.RequestException as ex:
            print(f"       attempt {attempt}: {type(ex).__name__} — resuming")
            time.sleep(5 * attempt)
    raise RuntimeError(f"could not download {url}")


def fetch_ms(key, aoi):
    bb = bbox(aoi)
    qk = quadkey(aoi["lon"], aoi["lat"], 9)
    with open("data/raw/ms_india_tiles.csv", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["QuadKey"] == qk]
    if not rows:
        print(f"  [ms] no tile for quadkey {qk}")
        return
    url = rows[0]["Url"]
    cache = f"data/raw/_cache/ms_{qk}.gz"
    print(f"  [ms] quadkey {qk}  {rows[0].get('Size','?')}")
    download_resumable(url, cache)
    print(f"  [ms] cached {os.path.getsize(cache)/1e6:.1f} MB, parsing ...")

    feats, t0, scanned = [], time.time(), 0
    with gzip.open(cache, "rt", encoding="utf-8") as fh:
        for line in fh:
            scanned += 1
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            geom = obj.get("geometry")
            if not geom or geom.get("type") != "Polygon":
                continue
            if ring_in_bbox(geom["coordinates"][0], bb):
                props = obj.get("properties", {}) or {}
                props["_source"] = "microsoft_ml_footprints"
                feats.append({"type": "Feature", "geometry": geom,
                              "properties": props})
    out = f"data/raw/{key}_ms_buildings.geojson"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"type": "FeatureCollection", "features": feats}, fh)
    print(f"  [ms] scanned {scanned:,} lines, kept {len(feats):,} -> {out} "
          f"({time.time()-t0:.0f}s)")


def overpass(query, rounds=2):
    """Try each mirror in turn; a 504 means that instance is busy, not that
    the query is wrong, so moving on is better than backing off in place."""
    last = None
    for rnd in range(rounds):
        for url in OVERPASS_MIRRORS:
            host = url.split("/")[2]
            try:
                r = requests.post(url, data={"data": query},
                                  headers=HEADERS, timeout=300)
            except requests.RequestException as ex:
                print(f"       {host}: {type(ex).__name__}")
                continue
            if r.status_code == 200:
                try:
                    return r.json()
                except json.JSONDecodeError:
                    print(f"       {host}: bad JSON")
                    continue
            print(f"       {host}: HTTP {r.status_code}")
            last = r
        if rnd + 1 < rounds:
            print("       all mirrors busy, waiting 30s")
            time.sleep(30)
    raise RuntimeError("all Overpass mirrors failed")


def fetch_osm(key, aoi):
    w, s, e, n = bbox(aoi)
    for kind, sel in (("buildings", 'way["building"]'),
                      ("roads", 'way["highway"]')):
        q = f'[out:json][timeout:240];{sel}({s},{w},{n},{e});out geom;'
        js = overpass(q)
        feats = []
        for el in js.get("elements", []):
            g = el.get("geometry")
            min_pts = 3 if kind == "buildings" else 2
            if not g or len(g) < min_pts:
                continue
            coords = [[p["lon"], p["lat"]] for p in g]
            if kind == "buildings":
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                if len(coords) < 4:
                    continue
                geom = {"type": "Polygon", "coordinates": [coords]}
            else:
                geom = {"type": "LineString", "coordinates": coords}
            props = dict(el.get("tags", {}))
            props["_source"] = "openstreetmap"
            props["_osm_id"] = el.get("id")
            feats.append({"type": "Feature", "geometry": geom,
                          "properties": props})
        out = f"data/raw/{key}_osm_{kind}.geojson"
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({"type": "FeatureCollection", "features": feats}, fh)
        print(f"  [osm] {kind}: {len(feats):,} -> {out}")
        time.sleep(8)


if __name__ == "__main__":
    want = sys.argv[1:] or list(AOIS)
    for key in want:
        aoi = AOIS[key]
        print(f"\n=== {aoi['label']} ===")
        print(f"  bbox {bbox(aoi)}")
        try:
            fetch_osm(key, aoi)
        except Exception as ex:
            print(f"  [osm] FAILED: {type(ex).__name__}: {ex}")
        try:
            fetch_ms(key, aoi)
        except Exception as ex:
            print(f"  [ms] FAILED: {type(ex).__name__}: {ex}")
