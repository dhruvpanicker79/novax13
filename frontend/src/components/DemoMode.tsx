import { useEffect, useState } from "react";
import { useStore, type LayerId } from "../lib/store";
import * as I from "../lib/icons";

/**
 * Guided run-through of the presentation.
 *
 * Eight beats, each of which sets the layers, the dock tab and the camera it
 * needs, so the operator never hunts for a toggle mid-sentence. The script is
 * the deliverable as much as the software is: a demo that depends on
 * remembering which of twelve layers to switch on will fail under pressure.
 *
 * Every figure quoted below is read from the loaded artifacts rather than
 * typed in, so the script cannot drift away from what the pipeline actually
 * produced.
 */
interface Beat {
  title: string;
  say: string;
  layers?: Partial<Record<LayerId, boolean>>;
  tab?: ReturnType<typeof useStore.getState>["dockTab"];
  action?: () => void;
  figure?: (m: any, p: any, c: any) => string;
}

const BEATS: Beat[] = [
  {
    title: "The problem",
    say: "Ten datasets describe the same ground and no two agree. This is one " +
         "ward of Chandausi — the NAKSHA pilot town.",
    layers: { harmonized: true, legacy: false, conflicts: false, encroach: false,
              residuals: false, survey: false, uncertainty: false, change: false },
    tab: "metrics",
    figure: (m) => `${m.counts.legacy.toLocaleString()} legacy parcels vs ` +
                   `${m.counts.reference.toLocaleString()} reference parcels`,
  },
  {
    title: "It does not line up",
    say: "Here is the 1987 cadastral sheet over the same ground. Every arrow " +
         "is one parcel's displacement. You cannot match this by overlaying it.",
    layers: { legacy: true, residuals: true, harmonized: false },
    figure: (m) => `positional RMSE ${m.georef.rmse_raw} m — against NAKSHA's ` +
                   `10 cm orthoimagery spec`,
  },
  {
    title: "Georeference first",
    say: "Watch the sheet move. This has to happen before matching: plots are " +
         "11 m across and the error is 5 to 15 m, so an unaligned parcel " +
         "overlaps its neighbour more than its own counterpart.",
    layers: { legacy: true, residuals: false, harmonized: true },
    action: () => useStore.getState().playAlignment(),
    figure: (m) => `${m.georef.rmse_raw} m → ${m.georef.rmse_coarse} m, ` +
                   `${m.georef.inliers.toLocaleString()} inliers`,
  },
  {
    title: "It is doing spatial reasoning",
    say: "The matcher is 95 percent geometry. If it were joining on khasra " +
         "number this whole problem statement would be a database query.",
    layers: { legacy: false },
    tab: "validate",
    figure: (m) => `F1 ${m.matching.f1} · geometry ` +
                   `${(m.matching.geometry_share * 100).toFixed(1)}% · ` +
                   `blocking recall ${m.matching.blocking_recall}`,
  },
  {
    title: "The confidence is honest",
    say: "Calibration error is four decimal places from zero. That is what " +
         "turns a score into a decision: finalise the confident ones, review " +
         "the rest.",
    tab: "validate",
    layers: { confidence: true, harmonized: false },
    figure: (m) => `ECE ${m.matching.ece} · ${m.counts.conflicts} parcels ` +
                   `routed to review`,
  },
  {
    title: "No land was created or destroyed",
    say: "The summed parcel area falls, because land two people were both " +
         "recorded as owning is now counted once. The actual footprint goes up.",
    tab: "validate",
    layers: { confidence: false, harmonized: true },
    figure: (m) => `overlaps ${m.topology.overlaps_before.toLocaleString()} → ` +
                   `${m.topology.overlaps_after} · doubly-claimed ` +
                   `${m.topology.overlap_area_before.toLocaleString()} → ` +
                   `${m.topology.overlap_area_after} m²`,
  },
  {
    title: "It refuses to guess",
    say: "Holes the size of a whole parcel are flagged for survey, not filled. " +
         "Filling them would fabricate a boundary. And here is what is built " +
         "on public land.",
    tab: "change",
    layers: { encroach: true, govt: true, change: true },
    figure: (m) => `${m.topology.refused_to_fill} holes refused · ` +
                   `${m.change.encroachment} encroachments over ` +
                   `${m.change.encroached_sqm} m²`,
  },
  {
    title: "Where to send the surveyor",
    say: "NAKSHA's own progress review calls ground truthing its biggest " +
         "lagging component. So we close the loop: these are the points to " +
         "survey next, and we verified the prediction against what they " +
         "actually achieve.",
    tab: "survey",
    layers: { survey: true, uncertainty: true, encroach: false, change: false },
    figure: (m, p) =>
      `${p.points.length} GCPs · predicted ${m.targeting.rmse_predicted} m · ` +
      `achieved ${m.targeting.rmse_achieved} m · random ` +
      `${m.targeting.rmse_random} m`,
  },
];

export default function DemoMode() {
  const [on, setOn] = useState(false);
  const [i, setI] = useState(0);
  const { metrics, plan, change, layers, toggleLayer, setDockTab } = useStore();

  const apply = (n: number) => {
    const b = BEATS[n];
    if (!b) return;
    if (b.layers) {
      const cur = useStore.getState().layers;
      for (const [id, want] of Object.entries(b.layers)) {
        const l = cur.find((x) => x.id === (id as LayerId));
        if (l && l.on !== want) toggleLayer(id as LayerId);
      }
    }
    if (b.tab) setDockTab(b.tab);
    b.action?.();
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === "INPUT") return;
      if (e.key === "d") { setOn((v) => !v); return; }
      if (!on) return;
      if (e.key === "ArrowRight" || e.key === "PageDown") {
        setI((v) => { const n = Math.min(v + 1, BEATS.length - 1); apply(n); return n; });
      }
      if (e.key === "ArrowLeft" || e.key === "PageUp") {
        setI((v) => { const n = Math.max(v - 1, 0); apply(n); return n; });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [on, layers]);

  if (!metrics) return null;

  if (!on) {
    return (
      <button
        className="float"
        onClick={() => { setOn(true); setI(0); apply(0); }}
        title="Guided demo  (d)"
        style={{
          top: 10, right: 10, zIndex: 30,
          background: "var(--panel)", border: "1px solid var(--line)",
          borderRadius: 3, padding: "6px 12px", fontSize: 12, fontWeight: 600,
          display: "flex", alignItems: "center", gap: 7,
          boxShadow: "0 1px 3px rgba(23,27,32,.12)",
        }}>
        <I.Play /> Guided demo
      </button>
    );
  }

  const b = BEATS[i];
  const fig = b.figure?.(metrics, plan, change) ?? "";

  return (
    <div className="float" style={{
      top: 10, right: 10, width: 336, zIndex: 31,
      background: "var(--panel)", border: "1px solid var(--line)",
      borderRadius: 3, boxShadow: "0 2px 10px rgba(23,27,32,.16)",
    }}>
      <header style={{
        background: "var(--panel-hi)", borderBottom: "1px solid var(--line)",
        padding: "7px 11px", display: "flex", alignItems: "center", gap: 8,
        fontSize: 12, fontWeight: 600,
      }}>
        <span className="num" style={{ color: "var(--acc)" }}>
          {String(i + 1).padStart(2, "0")}/{BEATS.length}
        </span>
        <span style={{ flex: 1 }}>{b.title}</span>
        <button className="iconbtn" style={{ width: 20, height: 20 }}
                onClick={() => setOn(false)} title="Exit (d)">
          <I.Close />
        </button>
      </header>

      <div style={{ padding: "11px 13px" }}>
        <div style={{ fontSize: 13, lineHeight: 1.55 }}>{b.say}</div>
        {fig && (
          <div className="num" style={{
            marginTop: 9, paddingTop: 9, borderTop: "1px solid var(--line)",
            fontSize: 11.5, color: "var(--acc)", lineHeight: 1.6,
          }}>{fig}</div>
        )}

        <div style={{ display: "flex", gap: 6, marginTop: 11 }}>
          <button
            onClick={() => { const n = Math.max(i - 1, 0); setI(n); apply(n); }}
            disabled={i === 0}
            style={{
              flex: 1, padding: "6px 0", borderRadius: 3, fontSize: 12,
              border: "1px solid var(--line)", background: "var(--panel-hi)",
              color: "var(--ink-dim)", opacity: i === 0 ? 0.45 : 1,
            }}>Back</button>
          <button
            onClick={() => {
              const n = Math.min(i + 1, BEATS.length - 1); setI(n); apply(n);
            }}
            disabled={i === BEATS.length - 1}
            style={{
              flex: 2, padding: "6px 0", borderRadius: 3, fontSize: 12,
              fontWeight: 600, border: "1px solid var(--acc)",
              background: "var(--acc)", color: "var(--on-acc)",
              opacity: i === BEATS.length - 1 ? 0.45 : 1,
            }}>Next</button>
        </div>
        <div style={{ fontSize: 10.5, color: "var(--ink-faint)", marginTop: 7 }}>
          Arrow keys to move · d to exit
        </div>
      </div>
    </div>
  );
}
