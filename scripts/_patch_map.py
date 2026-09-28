"""Add encroachment, change-event and epoch-t1 building layers to the map."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "frontend", "src", "components", "MapView.tsx")
s = open(P, encoding="utf-8").read()

if "l-encroach" in s:
    print("map already wired")
    raise SystemExit(0)

# --- sources -------------------------------------------------------------
s = s.replace(
    '''      add("conflicts", {''',
    '''      add("buildings", s.buildings ?? { type: "FeatureCollection", features: [] });
      add("encroach", {
        type: "FeatureCollection",
        features: (s.change?.encroachments ?? []).map((e) => ({
          type: "Feature",
          properties: { fid: e.building_fid, sqm: e.sqm, sev: e.severity,
                        cat: e.category, frac: e.fraction },
          geometry: { type: "Point", coordinates: e.at },
        })),
      });
      add("change", {
        type: "FeatureCollection",
        features: (s.change?.events ?? []).map((e) => ({
          type: "Feature",
          properties: { kind: e.kind, fid: e.fid, delta: e.delta_sqm,
                        dh: e.height_delta_m ?? 0 },
          geometry: { type: "Point", coordinates: e.at },
        })),
      });
      add("conflicts", {''')

# --- layers --------------------------------------------------------------
s = s.replace(
    '''      // ---- conflicts ----''',
    '''      // ---- epoch t1 footprints ----
      m.addLayer({
        id: "l-bldg", type: "fill", source: "buildings",
        layout: { visibility: "none" },
        paint: { "fill-color": "#c9d3dd", "fill-opacity": 0.3,
                 "fill-outline-color": "#e6e9ec" },
      });

      // ---- change events ----
      m.addLayer({
        id: "l-change", type: "circle", source: "change",
        layout: { visibility: "none" },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 14, 2.4, 18, 7],
          "circle-color": ["match", ["get", "kind"],
            "new", "#4d9fe8",
            "demolished", "#e05c54",
            "extended", "#e8a33d",
            "reduced", "#c07830",
            "heightened", "#3fbf5f",
            "#8c949c"],
          "circle-stroke-color": "#0d1114", "circle-stroke-width": 1,
          "circle-opacity": 0.92,
        },
      });

      // ---- encroachment: the layer an urban local body acts on ----
      m.addLayer({
        id: "l-encroach-halo", type: "circle", source: "encroach",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["get", "sqm"], 0, 12, 120, 34],
          "circle-color": "#e05c54", "circle-opacity": 0.16, "circle-blur": 0.4,
        },
      });
      m.addLayer({
        id: "l-encroach", type: "circle", source: "encroach",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 14, 4, 18, 10],
          "circle-color": ["match", ["get", "sev"],
            "severe", "#e05c54", "significant", "#e8a33d", "#8c949c"],
          "circle-stroke-color": "#0d1114", "circle-stroke-width": 1.6,
        },
      });
      m.addLayer({
        id: "l-encroach-lbl", type: "symbol", source: "encroach",
        layout: {
          "text-field": ["concat", ["to-string", ["round", ["get", "sqm"]]], " m2"],
          "text-size": 10, "text-offset": [0, -1.5], "text-allow-overlap": false,
        },
        paint: { "text-color": "#f2b5b1", "text-halo-color": "#0d1114",
                 "text-halo-width": 1.4 },
      });

      // ---- conflicts ----''')

# --- visibility sync -----------------------------------------------------
s = s.replace(
    '    vis("l-conf-pt", get("conflicts").on);\n  }, [s.layers, ready]);',
    '    vis("l-conf-pt", get("conflicts").on);\n'
    '    vis("l-bldg", get("buildings").on);\n'
    '    vis("l-change", get("change").on);\n'
    '    for (const l of ["l-encroach", "l-encroach-halo", "l-encroach-lbl"])\n'
    '      vis(l, get("encroach").on);\n'
    '  }, [s.layers, ready]);')

open(P, "w", encoding="utf-8").write(s)
print("MapView.tsx wired")
