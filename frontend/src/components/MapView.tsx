import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useStore } from "../lib/store";
import type { FC } from "../lib/types";

const SAT =
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";

/** Sequential single-hue ramp for confidence. Never a rainbow: a rainbow
 *  implies category boundaries that do not exist in a continuous measure. */
const CONF_RAMP: (string | number)[] = [
  0.0, "#3b1f1c", 0.5, "#7a3b24", 0.75, "#b8722a", 0.9, "#d9b23c", 0.97, "#6fcf6a", 1.0, "#2fbf5a",
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
        sources: {
          sat: { type: "raster", tiles: [SAT], tileSize: 256, maxzoom: 19,
                 attribution: "Imagery © Esri" },
        },
        layers: [
          // Hold the imagery well back. A survey basemap exists to give
          // context, not to compete: desaturated and dimmed, the parcel
          // colours read cleanly on top of it.
          { id: "sat", type: "raster", source: "sat",
            paint: {
              "raster-brightness-max": 0.55,
              "raster-brightness-min": 0.02,
              "raster-saturation": -0.55,
              "raster-contrast": 0.12,
            } },
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

    m.on("error", (e: any) => console.error("[maplibre]", e?.error?.message ?? e));
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
            0, "#10233a", 1.5, "#1d5c8a", 2.5, "#3f9dc4", 3.5, "#f0d35a"],
          "circle-opacity": 0.5, "circle-blur": 1,
        },
      });

      // ---- government land ----
      m.addLayer({
        id: "l-govt", type: "fill", source: "govt",
        paint: { "fill-color": "#4d9fe8", "fill-opacity": 0.18 },
      });
      m.addLayer({
        id: "l-govt-line", type: "line", source: "govt",
        paint: { "line-color": "#4d9fe8", "line-width": 1.4, "line-dasharray": [3, 2] },
      });

      // ---- harmonized output ----
      // Widths interpolate with zoom: a fixed 1 px hairline disappears when
      // 3,000 parcels are on screen at once and looks crude when zoomed in.
      m.addLayer({
        id: "l-harm", type: "fill", source: "harmonized",
        paint: {
          "fill-color": "#3fbf5f",
          "fill-opacity": ["interpolate", ["linear"], ["zoom"], 13, 0.13, 16, 0.18, 18, 0.1],
        },
      });
      m.addLayer({
        id: "l-harm-line", type: "line", source: "harmonized",
        paint: {
          "line-color": "#6ee089",
          "line-width": ["interpolate", ["linear"], ["zoom"], 13, 0.7, 15, 1.3, 18, 2.4],
          "line-opacity": 0.95,
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
        paint: { "line-color": "#4d9fe8", "line-width": 1.1 },
      });

      // ---- legacy sheet: dashed, so it reads as the older, provisional
      // record even where it happens to sit on top of the output ----
      m.addLayer({
        id: "l-leg", type: "line", source: "legacy",
        paint: {
          "line-color": "#f0a94a",
          "line-width": ["interpolate", ["linear"], ["zoom"], 13, 0.8, 15, 1.4, 18, 2.6],
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
            0, "#3fbf5f", 5, "#e8a33d", 12, "#e05c54"],
          "line-width": 1.3, "line-opacity": 0.85,
        },
      });

      // ---- survey plan ----
      m.addLayer({
        id: "l-survey-halo", type: "circle", source: "survey",
        layout: { visibility: "none" },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["get", "rank"], 1, 22, 40, 9],
          "circle-color": "#3fbf5f", "circle-opacity": 0.14,
        },
      });
      m.addLayer({
        id: "l-survey", type: "circle", source: "survey",
        layout: { visibility: "none" },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["get", "rank"], 1, 8, 40, 4],
          "circle-color": "#3fbf5f",
          "circle-stroke-color": "#08130c", "circle-stroke-width": 1.5,
        },
      });
      m.addLayer({
        id: "l-survey-lbl", type: "symbol", source: "survey",
        layout: {
          visibility: "none",
          "text-field": ["to-string", ["get", "rank"]],
          "text-size": 10, "text-offset": [0, -1.4], "text-allow-overlap": false,
        },
        paint: { "text-color": "#e6e9ec", "text-halo-color": "#0d1114", "text-halo-width": 1.3 },
      });

      // ---- epoch t1 footprints ----
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

      // ---- conflicts ----
      m.addLayer({
        id: "l-conf-pt", type: "circle", source: "conflicts",
        paint: {
          // Small when the whole ward is in view so 257 markers read as a
          // distribution rather than a mass of dots; individually clickable
          // once the operator zooms in.
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 14, 1.8, 16, 3.4, 18, 6.5],
          "circle-color": ["match", ["get", "cls"],
            "unresolved", "#e05c54",
            "missing_reference", "#e8a33d",
            "subdivision", "#4d9fe8",
            "amalgamation", "#a06fd0",
            "#e8a33d"],
          "circle-stroke-color": "#0d1114", "circle-stroke-width": 1,
          "circle-opacity": 0.9,
        },
      });

      // ---- selection ----
      m.addLayer({
        id: "l-sel", type: "line", source: "harmonized",
        filter: ["==", ["get", "fid"], "___none___"],
        paint: { "line-color": "#ffffff", "line-width": 2.4 },
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
    vis("l-bldg", get("buildings").on);
    vis("l-change", get("change").on);
    for (const l of ["l-encroach", "l-encroach-halo", "l-encroach-lbl"])
      vis(l, get("encroach").on);
  }, [s.layers, ready]);

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
