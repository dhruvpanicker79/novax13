import { useState } from "react";
import { useStore } from "../lib/store";
import * as I from "../lib/icons";

const n2 = (v: number | null | undefined, d = 2) =>
  v === null || v === undefined || Number.isNaN(v) ? "—" : v.toFixed(d);

/* --------------------------------------------------------------- */
export function SourceCards() {
  const { layers, toggleLayer, metrics } = useStore();
  const [open, setOpen] = useState(true);
  const shown = open ? layers : layers.slice(0, 2);

  return (
    <div className="float tl" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ display: "flex", gap: 6, alignItems: "flex-start" }}>
        {layers.slice(0, 2).map((l) => (
          <div key={l.id} className={`routecard ${l.on ? "on" : ""}`}
               onClick={() => toggleLayer(l.id)}>
            <span className="glyph"><I.Drone /></span>
            <span className="meta">
              <span className="nm">{l.label}</span>
              <span className="sub">{l.sub}</span>
            </span>
            <span className="acts">
              {l.on && <span style={{ color: "var(--acc)" }}><I.Check /></span>}
              <button title="Visibility" onClick={(e) => { e.stopPropagation(); toggleLayer(l.id); }}>
                <I.Eye />
              </button>
              <button title="More" onClick={(e) => e.stopPropagation()}><I.Kebab /></button>
            </span>
          </div>
        ))}
        <button className="routecard" style={{ minWidth: 0, padding: "9px 8px" }}
                onClick={() => setOpen(!open)} title="All layers">
          <I.Chevron open={open} />
        </button>
      </div>

      {open && <PanelCard />}
      {open && metrics && <LayerList />}
    </div>
  );
}

/* --------------------------------------------------------------- */
function PanelCard() {
  const { metrics, panel, setPanel, selected, harmonized, conflicts,
          selectedConflict } = useStore();
  const [tab, setTab] = useState<"basic" | "advanced" | "actions">("basic");
  if (!metrics) return null;

  const feat = selected
    ? harmonized?.features.find((f) => f.properties.fid === selected)
    : undefined;
  const conf = conflicts.find((c) => c.id === selectedConflict);

  return (
    <div className="card" style={{ width: 300 }}>
      <header>
        <span className="grow">
          {panel === "inspect" && selected ? "Parcel inspector" : "Project"}
        </span>
        {panel === "inspect" && (
          <button className="iconbtn" style={{ width: 20, height: 20 }}
                  onClick={() => { useStore.getState().select(null); setPanel("project"); }}>
            <I.Close />
          </button>
        )}
      </header>

      <div className="tabs">
        {(["basic", "advanced", "actions"] as const).map((t) => (
          <button key={t} className={tab === t ? "on" : ""} onClick={() => setTab(t)}>
            {t[0].toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {panel === "inspect" && feat ? (
        <div className="rows">
          {tab === "basic" && (
            <>
              <Row k="Khasra no." v={feat.properties.KHSRA_NUM ?? "—"} mono />
              <Row k="Khatedar" v={feat.properties.KHATEDAR_NM ?? "—"} />
              <Row k="Area, m²" v={n2(feat.properties.area_sqm ?? 0, 1)} mono />
              <Row k="Land use" v={feat.properties.LU_CODE ?? "—"} />
              <Row k="Tenure" v={feat.properties.TENURE_TYP ?? "—"} />
              <Row k="Ward" v={feat.properties.WARD ?? "—"} mono />
              <Row k="ULPIN" v={feat.properties.PARCEL_UID ?? "—"} mono />
              <div style={{ height: 8 }} />
              <Row
                k="Confidence"
                v={<ConfChip p={feat.properties.confidence ?? 0} />}
              />
              <Row k="Relation" v={feat.properties.relation ?? "—"} />
            </>
          )}
          {tab === "advanced" && (
            <>
              <Row k="Source" v="legacy_cadastre" mono />
              <Row k="Vintage" v="1987" mono />
              <Row k="σ stated, m" v="6.00" mono />
              <Row k="Authority" v="ownership" />
              <div style={{ height: 8 }} />
              <div style={{ fontSize: 11, color: "var(--ink-faint)", lineHeight: 1.6 }}>
                Provenance weight is inverse-variance (1/σ²), so GNSS control
                dominates geometry while the revenue record retains authority
                over ownership.
              </div>
            </>
          )}
          {tab === "actions" && <ActionBlock conflictId={conf?.id} />}
        </div>
      ) : (
        <div className="rows">
          {tab === "basic" && (
            <>
              <Row k="Area of interest" v="Chandausi ward 04" />
              <Row k="Reference CRS" v="EPSG:32644" mono />
              <Row k="Reference parcels" v={metrics.counts.reference.toLocaleString()} mono />
              <Row k="Legacy parcels" v={metrics.counts.legacy.toLocaleString()} mono />
              <Row k="Candidate pairs" v={metrics.counts.candidate_pairs.toLocaleString()} mono />
              <Row k="Open conflicts" v={metrics.counts.conflicts.toLocaleString()} mono />
              <div style={{ height: 8 }} />
              <Row k="Positional RMSE" v={
                <span className="num">
                  <span style={{ color: "var(--crit)" }}>{n2(metrics.georef.rmse_raw)}</span>
                  {" → "}
                  <span style={{ color: "var(--acc)" }}>{n2(metrics.georef.rmse_coarse)}</span>
                  <small style={{ color: "var(--ink-faint)" }}> m</small>
                </span>} />
            </>
          )}
          {tab === "advanced" && (
            <>
              <Row k="Blocking radius, m" v="18.00" mono />
              <Row k="Auto-accept p ≥" v="0.95" mono />
              <Row k="Split containment" v="0.50" mono />
              <Row k="Snap tolerance, m" v="0.60" mono />
              <Row k="GP lengthscale, m" v={n2(metrics.targeting.lengthscale_m, 1)} mono />
              <div style={{ height: 8 }} />
              <div style={{ fontSize: 11, color: "var(--ink-faint)", lineHeight: 1.6 }}>
                Thresholds are tuned on a held-out city, never on this one.
              </div>
            </>
          )}
          {tab === "actions" && (
            <div style={{ fontSize: 12, color: "var(--ink-dim)", lineHeight: 1.7 }}>
              Select a parcel or conflict on the map to act on it.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ActionBlock({ conflictId }: { conflictId?: string }) {
  const act = useStore((s) => s.act);
  if (!conflictId)
    return <div style={{ fontSize: 12, color: "var(--ink-dim)" }}>
      No open conflict on this parcel.
    </div>;
  const B = ({ a, label, tone }: any) => (
    <button
      onClick={() => act(conflictId, a, `reviewer ${a}`)}
      style={{
        flex: 1, padding: "7px 0", borderRadius: 3, fontSize: 12, fontWeight: 600,
        background: tone === "ok" ? "var(--ok-ghost)" : tone === "crit"
          ? "var(--crit-ghost)" : "var(--panel-hi)",
        color: tone === "ok" ? "var(--ok)" : tone === "crit" ? "var(--crit)" : "var(--ink-dim)",
        border: "1px solid var(--line)",
      }}>
      {label}
    </button>
  );
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ display: "flex", gap: 5 }}>
        <B a="accepted" label="Accept" tone="ok" />
        <B a="rejected" label="Reject" tone="crit" />
      </div>
      <div style={{ display: "flex", gap: 5 }}>
        <B a="escalated" label="Escalate" />
        <B a="survey" label="Field survey" />
      </div>
      <div style={{ fontSize: 10.5, color: "var(--ink-faint)", lineHeight: 1.55, marginTop: 3 }}>
        Every action is appended to the hash-chained audit log.
      </div>
    </div>
  );
}

function Row({ k, v, mono }: { k: string; v: any; mono?: boolean }) {
  return (
    <div className="row">
      <label>{k}</label>
      <div className={`val ${mono ? "num" : ""}`}>{v}</div>
    </div>
  );
}

export function ConfChip({ p }: { p: number }) {
  const tone = p >= 0.95 ? "ok" : p >= 0.7 ? "warn" : "crit";
  return <span className={`chip ${tone}`}>{p.toFixed(3)}</span>;
}

/* --------------------------------------------------------------- */
function LayerList() {
  const { layers, toggleLayer, setOpacity } = useStore();
  return (
    <div className="card" style={{ width: 300 }}>
      <header><span className="grow">Layers</span></header>
      {/* Bounded and scrollable: the stack grew past the viewport once the
          change and encroachment layers were added, and pushed itself under
          the dock. */}
      <div style={{ padding: "4px 0 6px", maxHeight: 190, overflowY: "auto" }}>
        {layers.map((l) => (
          <div key={l.id}
               style={{ padding: "5px 11px", display: "flex", alignItems: "center", gap: 8 }}>
            <button
              onClick={() => toggleLayer(l.id)}
              title={l.on ? "Hide" : "Show"}
              style={{
                width: 15, height: 15, borderRadius: 2, flex: "0 0 15px",
                border: `1px solid ${l.on ? "var(--acc)" : "var(--line)"}`,
                background: l.on ? "var(--acc)" : "transparent",
                display: "grid", placeItems: "center", color: "#08130c",
              }}>
              {l.on && <I.Check />}
            </button>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12, whiteSpace: "nowrap", overflow: "hidden",
                            textOverflow: "ellipsis" }}>{l.label}</div>
              <div style={{ fontSize: 10, color: "var(--ink-faint)" }}>{l.sub}</div>
            </div>
            <input type="range" min={0} max={1} step={0.05} value={l.opacity}
                   onChange={(e) => setOpacity(l.id, +e.target.value)}
                   style={{ width: 54, padding: 0, background: "none", border: "none" }} />
          </div>
        ))}
      </div>
    </div>
  );
}
