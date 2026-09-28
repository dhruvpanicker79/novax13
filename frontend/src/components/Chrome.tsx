import { useStore } from "../lib/store";
import { STAGES } from "../lib/types";
import * as I from "../lib/icons";

/* ------------------------------------------------------------------ */
export function TopBar() {
  const { metrics, running, done, runPipeline, playAlignment, panel, setPanel } =
    useStore();
  const busy = running !== null;

  return (
    <div className="topbar">
      <button className="iconbtn" title="Menu"><I.Menu /></button>
      <span className="title">KSHETRA</span>
      <span style={{ color: "var(--ink-faint)", fontSize: 12 }}>
        Chandausi, Sambhal · UP
      </span>
      <button className="iconbtn" title="Rename"><I.Edit /></button>

      <div style={{ width: 14 }} />
      <button
        className="iconbtn on"
        title="Run pipeline"
        onClick={() => !busy && runPipeline()}
        disabled={busy}
        style={busy ? { opacity: 0.6 } : undefined}
      >
        <I.Play />
      </button>
      <button className="iconbtn" title="Replay alignment" onClick={playAlignment}>
        <I.Mountain />
      </button>

      <div className="spacer" />

      <div className="search">
        <I.Search />
        <input placeholder="Search khasra, owner, conflict ID…" />
      </div>

      <div className="spacer" />

      <div className="pipeline" title="Pipeline stages">
        {STAGES.slice(3, 8).map((st) => {
          const cls = done.includes(st.id) ? "done" : running === st.id ? "run" : "";
          return (
            <div className={`pstage ${cls}`} key={st.id}>
              <span className="dot" />{st.label}
            </div>
          );
        })}
      </div>

      <button className={`iconbtn ${panel === "layers" ? "on" : ""}`}
              title="Layers" onClick={() => setPanel(panel === "layers" ? "project" : "layers")}>
        <I.Layers />
      </button>
      <button className="iconbtn" title="Report"><I.Report /></button>

      <div className="modepill">
        <I.Shield />
        <span>{metrics ? "Reviewer" : "—"}</span>
        <I.Chevron />
      </div>
      <button className="iconbtn" title="More"><I.Kebab /></button>
    </div>
  );
}

/* ------------------------------------------------------------------ */
const TOOLS = [
  { id: "inspect", icon: <I.Pin />, label: "Inspect parcel" },
  { id: "poly", icon: <I.Poly />, label: "Area of interest" },
  { id: "measure", icon: <I.Ruler />, label: "Measure" },
  { id: "grid", icon: <I.Grid />, label: "Blocking grid" },
  { id: "target", icon: <I.Target />, label: "Survey targeting" },
  { id: "warn", icon: <I.Warn />, label: "Conflicts" },
  { id: "chart", icon: <I.Chart />, label: "Validation" },
  { id: "export", icon: <I.Export />, label: "Export" },
];

export function Rail() {
  const { dockTab, setDockTab, layers, toggleLayer } = useStore();
  const jump: Record<string, any> = {
    target: () => { setDockTab("survey"); if (!layers.find(l => l.id === "survey")!.on) toggleLayer("survey"); },
    warn: () => setDockTab("conflicts"),
    chart: () => setDockTab("validate"),
    export: () => setDockTab("metrics"),
    grid: () => { const l = layers.find(l => l.id === "residuals")!; if (!l.on) toggleLayer("residuals"); },
  };
  const active: Record<string, boolean> = {
    target: dockTab === "survey", warn: dockTab === "conflicts",
    chart: dockTab === "validate", export: dockTab === "metrics",
  };

  return (
    <div className="rail">
      {TOOLS.map((t, i) => (
        <div key={t.id}>
          <button
            className={`tool ${active[t.id] ? "on" : ""}`}
            title={t.label}
            onClick={() => jump[t.id]?.()}
          >
            {t.icon}
          </button>
          {(i === 2 || i === 4) && <div className="sep" />}
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
export function Readout() {
  const { cursor, metrics } = useStore();
  const dms = (v: number, pos: string, neg: string) => {
    const h = v >= 0 ? pos : neg;
    const a = Math.abs(v);
    const d = Math.floor(a);
    const m = Math.floor((a - d) * 60);
    const sec = ((a - d) * 60 - m) * 60;
    return `${d}° ${String(m).padStart(2, "0")}' ${sec.toFixed(2)}" ${h}`;
  };
  return (
    <div className="float bl" style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
      <Compass />
      <div className="readout">
        <div><b>{dms(cursor.lat, "N", "S")}</b></div>
        <div><b>{dms(cursor.lon, "E", "W")}</b></div>
        <div style={{ marginTop: 5 }}>
          CRS <b>EPSG:32644</b> · UTM 44N / WGS 84
        </div>
        <div>
          Zoom <b>{cursor.zoom.toFixed(1)}</b>
          {metrics && <> · Parcels <b>{metrics.counts.legacy.toLocaleString()}</b></>}
        </div>
      </div>
    </div>
  );
}

function Compass() {
  return (
    <div className="readout" style={{ padding: 7 }}>
      <svg width="52" height="52" viewBox="0 0 52 52" aria-hidden="true">
        <circle cx="26" cy="26" r="22" fill="none" stroke="var(--line)" strokeWidth="1" />
        <circle cx="26" cy="26" r="16" fill="none" stroke="var(--line-soft)" strokeWidth="1" />
        <path d="M26 7 L30 26 L26 22 L22 26 Z" fill="var(--acc)" />
        <path d="M26 45 L22 26 L26 30 L30 26 Z" fill="#aab2ba" />
        {["N", "E", "S", "W"].map((t, i) => {
          const a = (i * 90 - 90) * (Math.PI / 180);
          return (
            <text key={t} x={26 + Math.cos(a) * 19} y={26 + Math.sin(a) * 19 + 3}
                  fontSize="8" fill="var(--ink-faint)" textAnchor="middle"
                  fontFamily="IBM Plex Mono">{t}</text>
          );
        })}
      </svg>
    </div>
  );
}
