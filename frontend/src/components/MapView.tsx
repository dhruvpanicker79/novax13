import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useStore } from "../lib/store";
import type { FC } from "../lib/types";

/** Esri basemaps: free, no key, and three registers for three jobs --
 *  imagery to prove the parcels sit on real buildings, a light canvas when the
 *  data itself should carry all the colour, and a dark one for a projector in
 *  a bright room. */
const BASEMAPS: Record<string, {
  url: string; bright: [number, number]; sat: number; maxzoom: number;
}> = {
  imagery: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    bright: [0.34, 1.0], sat: -0.5, maxzoom: 19,
  },
  light: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    // Esri's canvas basemaps stop at z16. Declaring that lets MapLibre
    // overzoom the last real level; leaving it at 19 asks for tiles that do
    // not exist and the map simply goes blank in 3D.
    bright: [0.0, 1.0], sat: 0, maxzoom: 16,
  },
  dark: {
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    bright: [0.0, 1.0], sat: 0, maxzoom: 16,
  },
};

/** Sequential single-hue ramp for confidence. Never a rainbow: a rainbow
 *  implies category boundaries that do not exist in a continuous measure. */
const CONF_RAMP: (string | number)[] = [
  0.0, "#7d1d16", 0.5, "#b3541e", 0.75, "#cf8f22", 0.9, "#b8bf2e", 0.97, "#4faa4a", 1.0, "#14884a",
];

function lerpFC(a: FC, b: FC, t: number): FC {
  // Both layers carry the same fids in the same order, so vertices pair up
  // positionally. The legacy sheet may have been decimated, so guard on length.
  const feats = a.features.map((fa, i) => {
    const fb = b.features[i];
    const ra = fa.geometry.coordinates[0];
    const rb = fb?.geometry.coordinates[0];
    if (!rb || rb.length !== ra.length) return fa;
    const ring = ra.map((p, k) => [
      p[0] + (rb[k][0] - p[0]) * t,
      p[1] + (rb[k][1] - p[1]) * t,
    ]);
    return { ...fa, geometry: { type: "Polygon", coordinates: [ring] } } as any;
  });
  return { type: "FeatureCollection", features: feats };
}

export default function MapView() {
  const ref = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  const map = useRef<maplibregl.Map | null>(null);
  const raf = useRef<number | null>(null);

  const s = useStore();

  // ---- init ---------------------------------------------------------
  useEffect(() => {
    if (!ref.current || map.current) return;
    const m = new maplibregl.Map({
      container: ref.current,
      style: {
        version: 8,
        glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
        sources: Object.fromEntries(Object.entries(BASEMAPS).map(([k, v]) => [
          k, { type: "raster", tiles: [v.url], tileSize: 256, maxzoom: v.maxzoom,
               attribution: "© Esri" },
        ])) as any,
        layers: [
          // Drawn beneath the imagery so the map degrades to a neutral sheet
          // rather than to black if tiles never arrive. Demo venues lose wifi.
          { id: "bg", type: "background",
            paint: { "background-color": "#e9ecef" } },
          // One raster layer per basemap; only the visible one fetches tiles.
          ...Object.entries(BASEMAPS).map(([k, v]) => ({
            id: `bm-${k}`, type: "raster" as const, source: k,
            layout: { visibility: (k === "imagery" ? "visible" : "none") as any },
            paint: {
              "raster-brightness-min": v.bright[0],
              "raster-brightness-max": v.bright[1],
              "raster-saturation": v.sat,
              "raster-contrast": k === "imagery" ? -0.16 : 0,
              "raster-opacity": k === "imagery" ? 0.74 : 0.9,
            },
          })),
        ],
      },
      center: [78.7749, 28.4515],
      zoom: 15.4,
      attributionControl: false,
    });
    m.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
    m.addControl(new maplibregl.ScaleControl({ maxWidth: 110, unit: "metric" }), "bottom-right");
    map.current = m;
    (window as any).__map = m;   // diagnostics handle
    m.on("style.load", () => {
      // Only visible once pitched; without it a tilted map ends at a hard
      // horizon line.
      try {
        (m as any).setSky?.({
          "sky-color": "#b9d3e8", "horizon-color": "#e8eef4",
          "fog-color": "#eef1f4", "fog-ground-blend": 0.6,
          "sky-horizon-blend": 0.7, "horizon-fog-blend": 0.5,
        });
      } catch { /* older maplibre: no sky, no loss */ }
    });

    let tileFails = 0;
    m.on("error", (e: any) => {
      const msg = e?.error?.message ?? String(e);
      if (e?.sourceId === "sat") {
        // One failure is a flaky tile; a run of them means the basemap is
        // unreachable, which the operator should be told rather than left to
        // infer from a blank map.
        if (++tileFails === 6) useStore.getState().setBasemapOffline(true);
        return;
      }
      console.error("[maplibre]", msg);
    });
    m.on("sourcedata", (e: any) => {
      if (e.sourceId === "sat" && e.isSourceLoaded && tileFails < 6)
        useStore.getState().setBasemapOffline(false);
    });
    m.on("mousemove", (e) =>
      useStore.getState().setCursor({
        lon: e.lngLat.lng, lat: e.lngLat.lat, zoom: m.getZoom(),
      }));
    m.on("zoom", () => {
      const c = m.getCenter();
      useStore.getState().setCursor({ lon: c.lng, lat: c.lat, zoom: m.getZoom() });
    });
    return () => { m.remove(); map.current = null; };
  }, []);

  // ---- data + layers -------------------------------------------------
  useEffect(() => {
    const m = map.current;
    if (!m || !s.loaded || !s.harmonized) return;

    const boot = () => {
      if (m.getSource("harmonized")) return;

      const add = (id: string, data: any) =>
        m.addSource(id, { type: "geojson", data } as any);

      add("reference", s.reference);
      add("legacy", s.showRaw ? s.legacy : s.aligned);
      add("harmonized", s.harmonized);
      add("govt", s.govt);
      add("residuals", {
        type: "FeatureCollection",
        features: s.residuals.map((r) => ({
          type: "Feature", properties: { m: r.m },
          geometry: { type: "LineString", coordinates: [r.from, r.to] },
        })),
      });
      add("survey", {
        type: "FeatureCollection",
        features: (s.plan?.points ?? []).map((p) => ({
          type: "Feature",
          properties: { rank: p.rank, gain: p.marginal_gain, rmse: p.rmse_after_m },
          geometry: { type: "Point", coordinates: p.at },
        })),
      });
      add("uncert", {
        type: "FeatureCollection",
        features: (s.uncertainty?.grid ?? []).map((g) => ({
          type: "Feature", properties: { sd: g[2], sd2: g[3] },
          geometry: { type: "Point", coordinates: [g[0], g[1]] },
        })),
      });
      add("buildings", s.buildings ?? { type: "FeatureCollection", features: [] });
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
      add("conflicts", {
        type: "FeatureCollection",
        features: s.conflicts.map((c) => ({
          type: "Feature",
          properties: { id: c.id, cls: c.class, conf: c.confidence },
          geometry: { type: "Point", coordinates: c.at },
        })),
      });

      // ---- uncertainty heat (drawn first, under everything) ----
      m.addLayer({
        id: "l-uncert", type: "circle", source: "uncert",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 13, 9, 17, 34],
          "circle-color": ["interpolate", ["linear"], ["get", "sd"],
            0, "#dbe7f2", 1.5, "#8fbcd9", 2.5, "#3f9dc4", 3.5, "#e0a01f"],
          "circle-opacity": 0.55, "circle-blur": 1,
        },
      });

      // ---- government land ----
      m.addLayer({
        id: "l-govt", type: "fill", source: "govt",
        paint: { "fill-color": "#1667ad", "fill-opacity": 0.16 },
      });
      m.addLayer({
        id: "l-govt-line", type: "line", source: "govt",
        paint: { "line-color": "#0f5590", "line-width": 1.6, "line-dasharray": [3, 2] },
      });

      // ---- harmonized output ----
      // Widths interpolate with zoom: a fixed 1 px hairline disappears when
      // 3,000 parcels are on screen at once and looks crude when zoomed in.
      m.addLayer({
        id: "l-harm", type: "fill", source: "harmonized",
        paint: {
          "fill-color": "#14884a",
          "fill-opacity": ["interpolate", ["linear"], ["zoom"], 13, 0.34, 16, 0.3, 18, 0.18],
        },
      });
      m.addLayer({
        id: "l-harm-line", type: "line", source: "harmonized",
        paint: {
          "line-color": "#0f7a3f",
          "line-width": ["interpolate", ["linear"], ["zoom"], 13, 1.3, 15, 2.2, 18, 3.6],
          "line-opacity": 1,
        },
      });

      // ---- confidence choropleth ----
      m.addLayer({
        id: "l-conf", type: "fill", source: "harmonized",
        layout: { visibility: "none" },
        paint: {
          "fill-color": ["interpolate", ["linear"], ["coalesce", ["get", "confidence"], 0],
            ...CONF_RAMP],
          "fill-opacity": 0.72,
        },
      });

      // ---- reference ----
      m.addLayer({
        id: "l-ref", type: "line", source: "reference",
        layout: { visibility: "none" },
        paint: { "line-color": "#1667ad", "line-width": 1.2 },
      });

      // ---- legacy sheet: dashed, so it reads as the older, provisional
      // record even where it happens to sit on top of the output ----
      m.addLayer({
        id: "l-leg", type: "line", source: "legacy",
        paint: {
          "line-color": "#c2650a",
          "line-width": ["interpolate", ["linear"], ["zoom"], 13, 1.2, 15, 1.9, 18, 3.2],
          "line-opacity": 0.95,
          "line-dasharray": [2.5, 1.6],
        },
      });

      // ---- residual vectors ----
      m.addLayer({
        id: "l-resid", type: "line", source: "residuals",
        layout: { visibility: "none" },
        paint: {
          "line-color": ["interpolate", ["linear"], ["get", "m"],
            0, "#17914a", 5, "#9a6710", 12, "#b3261e"],
          "line-width": 1.3, "line-opacity": 0.85,
        },
      });

      // ---- survey plan ----
      m.addLayer({
        id: "l-survey-halo", type: "circle", source: "survey",
        layout: { visibility: "none" },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["get", "rank"], 1, 22, 40, 9],
          "circle-color": "#17914a", "circle-opacity": 0.18,
        },
      });
      m.addLayer({
        id: "l-survey", type: "circle", source: "survey",
        layout: { visibility: "none" },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["get", "rank"], 1, 8, 40, 4],
          "circle-color": "#17914a",
          "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.6,
        },
      });
      m.addLayer({
        id: "l-survey-lbl", type: "symbol", source: "survey",
        layout: {
          visibility: "none",
          "text-field": ["to-string", ["get", "rank"]],
          "text-size": 10, "text-offset": [0, -1.4], "text-allow-overlap": false,
        },
        paint: { "text-color": "#171b20", "text-halo-color": "#ffffff", "text-halo-width": 1.6 },
      });

      // ---- epoch t1 footprints, flat ----
      m.addLayer({
        id: "l-bldg", type: "fill", source: "buildings",
        layout: { visibility: "none" },
        paint: { "fill-color": "#5a646e", "fill-opacity": 0.28,
                 "fill-outline-color": "#2f363d" },
      });

      // ---- the same footprints extruded to their surveyed height ----
      // A building that gained storeys is identical in plan view. Extrusion is
      // the only way the viewer sees what the DSM sees, and it is also what
      // makes the scene read as a city rather than a diagram.
      m.addLayer({
        id: "l-bldg-3d", type: "fill-extrusion", source: "buildings",
        layout: { visibility: "none" },
        paint: {
          "fill-extrusion-height": ["coalesce", ["get", "height_m"], 6],
          "fill-extrusion-base": 0,
          "fill-extrusion-opacity": 0.92,
          "fill-extrusion-color": ["interpolate", ["linear"],
            ["coalesce", ["get", "height_m"], 6],
            3, "#cfd6dd", 8, "#9fb0c0", 14, "#6d8499", 20, "#42607a"],
          "fill-extrusion-vertical-gradient": true,
        },
      });

      // ---- change events ----
      m.addLayer({
        id: "l-change", type: "circle", source: "change",
        layout: { visibility: "none" },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 14, 2.4, 18, 7],
          "circle-color": ["match", ["get", "kind"],
            "new", "#1667ad",
            "demolished", "#b3261e",
            "extended", "#9a6710",
            "reduced", "#7d5410",
            "heightened", "#17914a",
            "#6b7480"],
          "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.2,
          "circle-opacity": 0.92,
        },
      });

      // ---- encroachment: the layer an urban local body acts on ----
      m.addLayer({
        id: "l-encroach-halo", type: "circle", source: "encroach",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["get", "sqm"], 0, 12, 120, 34],
          "circle-color": "#b3261e", "circle-opacity": 0.2, "circle-blur": 0.4,
        },
      });
      m.addLayer({
        id: "l-encroach", type: "circle", source: "encroach",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 14, 4, 18, 10],
          "circle-color": ["match", ["get", "sev"],
            "severe", "#b3261e", "significant", "#9a6710", "#6b7480"],
          "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.8,
        },
      });
      m.addLayer({
        id: "l-encroach-lbl", type: "symbol", source: "encroach",
        layout: {
          "text-field": ["concat", ["to-string", ["round", ["get", "sqm"]]], " m2"],
          "text-size": 10, "text-offset": [0, -1.5], "text-allow-overlap": false,
        },
        paint: { "text-color": "#8e1a14", "text-halo-color": "#ffffff",
                 "text-halo-width": 1.8 },
      });

      // ---- conflicts ----
      m.addLayer({
        id: "l-conf-pt", type: "circle", source: "conflicts",
        paint: {
          // Small when the whole ward is in view so 257 markers read as a
          // distribution rather than a mass of dots; individually clickable
          // once the operator zooms in.
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 14, 1.8, 16, 3.4, 18, 6.5],
          "circle-color": ["match", ["get", "cls"],
            "unresolved", "#b3261e",
            "missing_reference", "#9a6710",
            "subdivision", "#1667ad",
            "amalgamation", "#7a3fa8",
            "#9a6710"],
          "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.2,
          "circle-opacity": 0.9,
        },
      });

      // ---- selection ----
      m.addLayer({
        id: "l-sel", type: "line", source: "harmonized",
        filter: ["==", ["get", "fid"], "___none___"],
        paint: { "line-color": "#111417", "line-width": 2.6 },
      });

      m.on("click", "l-harm", (e) => {
        const f = e.features?.[0];
        if (f) useStore.getState().select(f.properties?.fid ?? null);
      });
      m.on("click", "l-conf-pt", (e) => {
        const f = e.features?.[0];
        if (f) useStore.getState().selectConflict(f.properties?.id ?? null);
      });
      for (const id of ["l-harm", "l-conf-pt"]) {
        m.on("mouseenter", id, () => (m.getCanvas().style.cursor = "pointer"));
        m.on("mouseleave", id, () => (m.getCanvas().style.cursor = ""));
      }

      // Fit over the WHOLE layer. Features are emitted block by block, so any
      // head slice is a narrow strip of the city and fitting to it zooms the
      // camera into a sliver.
      const b = new maplibregl.LngLatBounds();
      for (const f of s.harmonized!.features)
        for (const c of f.geometry.coordinates[0]) b.extend(c as any);
      // Asymmetric padding: the left panel stack and the bottom dock cover
      // real estate, so symmetric padding centres the ward under the chrome
      // and wastes the visible area.
      m.fitBounds(b, {
        padding: { top: 78, left: 336, right: 28, bottom: 300 },
        duration: 0,
      });
      // Layers exist only now. Until this flips, the visibility effect has
      // nothing to act on, so the store's initial on/off state is never
      // applied and every layer renders at its style default.
      setReady(true);
    };

    if (m.isStyleLoaded()) boot();
    else m.once("load", boot);
  }, [s.loaded]);

  // ---- layer visibility / opacity -------------------------------------
  useEffect(() => {
    const m = map.current;
    if (!m || !ready || !m.getLayer("l-harm")) return;
    const get = (id: string) => s.layers.find((l) => l.id === id)!;
    const vis = (layer: string, on: boolean) =>
      m.setLayoutProperty(layer, "visibility", on ? "visible" : "none");

    const conf = get("confidence");
    vis("l-conf", conf.on);
    vis("l-harm", get("harmonized").on && !conf.on);
    vis("l-harm-line", get("harmonized").on);
    m.setPaintProperty("l-harm-line", "line-opacity", get("harmonized").opacity * 0.85);
    vis("l-ref", get("reference").on);
    vis("l-leg", get("legacy").on);
    m.setPaintProperty("l-leg", "line-opacity", get("legacy").opacity);
    vis("l-resid", get("residuals").on);
    vis("l-uncert", get("uncertainty").on);
    for (const l of ["l-survey", "l-survey-halo", "l-survey-lbl"]) vis(l, get("survey").on);
    vis("l-govt", get("govt").on);
    vis("l-govt-line", get("govt").on);
    vis("l-conf-pt", get("conflicts").on);
    for (const k of Object.keys(BASEMAPS)) vis(`bm-${k}`, k === s.basemap);
    // Flat footprints when the map is level, extruded when it is pitched --
    // never both, or the fill z-fights the extrusion base.
    vis("l-bldg", get("buildings").on && !s.pitched);
    vis("l-bldg-3d", get("buildings").on && s.pitched);
    vis("l-change", get("change").on);
    for (const l of ["l-encroach", "l-encroach-halo", "l-encroach-lbl"])
      vis(l, get("encroach").on);
    // On the dark canvas the parcel fill has to lift instead of darken, or
    // the layer vanishes into the background it was drawn to stand out from.
    const dark = s.basemap === "dark";
    m.setPaintProperty("l-harm", "fill-color", dark ? "#3fbf5f" : "#14884a");
    m.setPaintProperty("l-harm-line", "line-color", dark ? "#6ee089" : "#0f7a3f");
    m.setPaintProperty("l-leg", "line-color", dark ? "#f0a94a" : "#c2650a");
  }, [s.layers, s.basemap, s.pitched, ready]);

  // ---- camera pitch ----------------------------------------------------
  useEffect(() => {
    const m = map.current;
    if (!m || !ready) return;
    // Extruded 6 m buildings are invisible at ward zoom, so tilting also
    // moves in far enough for the extrusion to read. Coming back out restores
    // the whole-ward view.
    m.easeTo({
      pitch: s.pitched ? 55 : 0,
      bearing: s.pitched ? -20 : 0,
      zoom: s.pitched ? Math.max(m.getZoom(), 16.8) : Math.min(m.getZoom(), 15.2),
      duration: 1100,
    });
  }, [s.pitched, ready]);

  // ---- selection highlight --------------------------------------------
  useEffect(() => {
    const m = map.current;
    if (!m || !m.getLayer("l-sel")) return;
    m.setFilter("l-sel", ["==", ["get", "fid"], s.selected ?? "___none___"]);
  }, [s.selected]);

  // ---- fly to the selected conflict ------------------------------------
  useEffect(() => {
    const m = map.current;
    if (!m || !s.selectedConflict) return;
    const c = s.conflicts.find((x) => x.id === s.selectedConflict);
    if (c) m.easeTo({ center: c.at, zoom: Math.max(m.getZoom(), 17), duration: 650 });
  }, [s.selectedConflict]);

  // ---- the alignment animation -----------------------------------------
  // The signature moment: the misregistered legacy sheet slides onto the
  // reference frame. 1600 ms with a decelerating curve, slow enough to read.
  useEffect(() => {
    const m = map.current;
    if (!m || !m.getSource("legacy") || !s.legacy || !s.aligned) return;
    const src = m.getSource("legacy") as maplibregl.GeoJSONSource;

    if (s.showRaw) {
      if (raf.current) cancelAnimationFrame(raf.current);
      src.setData(s.legacy as any);
      return;
    }

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced || !s.aligning) { src.setData(s.aligned as any); return; }

    const t0 = performance.now();
    const DUR = 1600;
    const ease = (t: number) => 1 - Math.pow(1 - t, 4);
    const step = (now: number) => {
      const t = Math.min(1, (now - t0) / DUR);
      src.setData(lerpFC(s.legacy!, s.aligned!, ease(t)) as any);
      if (t < 1) raf.current = requestAnimationFrame(step);
    };
    raf.current = requestAnimationFrame(step);
    return () => { if (raf.current) cancelAnimationFrame(raf.current); };
  }, [s.showRaw, s.aligning, s.loaded]);

  return <div id="map" ref={ref} />;
}
