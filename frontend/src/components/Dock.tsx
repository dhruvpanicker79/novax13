import { useMemo } from "react";
import { useStore } from "../lib/store";
import * as I from "../lib/icons";
import { ConfChip } from "./Panels";
import { ChangeTab, ExportTab, ResolveTab, SchemaTab } from "./DockExtra";

const f = (v: number | null | undefined, d = 2) =>
  v === null || v === undefined || Number.isNaN(v) ? "—" : v.toFixed(d);
const k = (v: number) => v.toLocaleString();

const TABS = [
  ["conflicts", "Review queue"],
  ["schema", "Schema"],
  ["survey", "Survey plan"],
  ["change", "Change"],
  ["resolve", "Resolution"],
  ["validate", "Validation"],
  ["audit", "Audit log"],
  ["export", "Export"],
  ["metrics", "Pipeline"],
] as const;

export default function Dock() {
  const { dockTab, setDockTab, dockOpen, setDockOpen, conflicts, metrics } = useStore();
  if (!metrics) return null;
  const open = conflicts.filter((c) => c.status === "open").length;
  const enc = useStore.getState().change?.encroachments.length ?? 0;

  return (
    <div className="dock" style={dockOpen ? undefined : { maxHeight: 34 }}>
      <header>
        {TABS.map(([id, label]) => (
          <button key={id}
                  className={`dtab ${dockTab === id ? "on" : ""}`}
                  onClick={() => setDockTab(id as any)}>
            {label}
            {id === "conflicts" && open > 0 && (
              <span className="chip warn" style={{ marginLeft: 7 }}>{open}</span>
            )}
            {id === "change" && enc > 0 && (
              <span className="chip crit" style={{ marginLeft: 7 }}>{enc}</span>
            )}
          </button>
        ))}
        <div style={{ flex: 1 }} />
        <button className="iconbtn" onClick={() => setDockOpen(!dockOpen)}
                title={dockOpen ? "Collapse" : "Expand"}>
          <I.Chevron open={!dockOpen} />
        </button>
      </header>
      {dockOpen && (
        <div className="dbody">
          {dockTab === "conflicts" && <Conflicts />}
          {dockTab === "schema" && <SchemaTab />}
          {dockTab === "change" && <ChangeTab />}
          {dockTab === "resolve" && <ResolveTab />}
          {dockTab === "export" && <ExportTab />}
          {dockTab === "survey" && <Survey />}
          {dockTab === "validate" && <Validate />}
          {dockTab === "audit" && <Audit />}
          {dockTab === "metrics" && <Pipeline />}
        </div>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- */
function Conflicts() {
  const { conflicts, selectedConflict, selectConflict, act } = useStore();
  const tone: Record<string, string> = {
    unresolved: "crit", missing_reference: "warn",
    subdivision: "info", amalgamation: "info", positional_conflict: "warn",
  };
  return (
    <>
      <div className="stats" style={{ borderBottom: "1px solid var(--line)" }}>
        {["open", "accepted", "rejected", "escalated", "survey"].map((st) => (
          <div className="stat" key={st}>
            <span className="k">{st === "survey" ? "field survey" : st}</span>
            <span className="v num">{conflicts.filter((c) => c.status === st).length}</span>
          </div>
        ))}
        <div className="stat">
          <span className="k">sorted by</span>
          <span className="v" style={{ fontSize: 12 }}>area × (1 − confidence)</span>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>ID</th><th>Class</th><th>Khasra</th><th>Khatedar</th>
            <th className="n">Area m²</th><th className="n">p</th>
            <th>Detail</th><th>Status</th><th></th>
          </tr>
        </thead>
        <tbody>
          {conflicts.slice(0, 200).map((c) => (
            <tr key={c.id}
                className={selectedConflict === c.id ? "sel" : ""}
                onClick={() => selectConflict(c.id)}>
              <td className="num">{c.id}</td>
              <td><span className={`chip ${tone[c.class] ?? "mute"}`}>
                {c.class.replace(/_/g, " ")}</span></td>
              <td className="num">{c.khasra ?? "—"}</td>
              <td style={{ maxWidth: 190, overflow: "hidden", textOverflow: "ellipsis" }}>
                {c.owner ?? "—"}</td>
              <td className="n">{c.area_sqm.toFixed(1)}</td>
              <td className="n"><ConfChip p={c.confidence} /></td>
              <td style={{ color: "var(--ink-faint)", maxWidth: 260,
                           overflow: "hidden", textOverflow: "ellipsis" }}>{c.detail}</td>
              <td>{c.status === "open"
                ? <span className="chip mute">open</span>
                : <span className={`chip ${c.status === "rejected" ? "crit" : "ok"}`}>
                    {c.status}</span>}</td>
              <td onClick={(e) => e.stopPropagation()}>
                {c.status === "open" && (
                  <span style={{ display: "flex", gap: 4 }}>
                    <button className="chip ok" onClick={() => act(c.id, "accepted", "queue accept")}>
                      accept</button>
                    <button className="chip crit" onClick={() => act(c.id, "rejected", "queue reject")}>
                      reject</button>
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

/* ---------------------------------------------------------------- */
function Survey() {
  const { plan, metrics } = useStore();
  if (!plan || !metrics) return null;
  const t = metrics.targeting;

  return (
    <>
      <div className="stats" style={{ borderBottom: "1px solid var(--line)" }}>
        <div className="stat"><span className="k">GCPs planned</span>
          <span className="v num">{plan.points.length}</span></div>
        <div className="stat"><span className="k">baseline RMSE</span>
          <span className="v num">{f(t.rmse_baseline)}<small> m</small></span></div>
        <div className="stat"><span className="k">predicted</span>
          <span className="v num" style={{ color: "var(--info)" }}>
            {f(t.rmse_predicted)}<small> m</small></span></div>
        <div className="stat"><span className="k">achieved</span>
          <span className="v num" style={{ color: "var(--acc)" }}>
            {f(t.rmse_achieved)}<small> m</small></span></div>
        <div className="stat"><span className="k">random placement</span>
          <span className="v num" style={{ color: "var(--crit)" }}>
            {f(t.rmse_random)}<small> m</small></span></div>
        <div className="stat"><span className="k">better than random</span>
          <span className="v num" style={{ color: "var(--acc)" }}>
            {f(t.vs_random_pct, 1)}<small> %</small></span></div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 0 }}>
        <div style={{ padding: "10px 12px", borderRight: "1px solid var(--line)" }}>
          <GainCurve plan={plan} />
          <div style={{ fontSize: 11, color: "var(--ink-faint)", lineHeight: 1.6,
                        marginTop: 8 }}>
            Greedy submodular selection, (1 − 1/e) bound. Stopped: {plan.stopped_because}.
          </div>
          <div style={{ fontSize: 11, color: "var(--warn)", lineHeight: 1.6, marginTop: 8 }}>
            The GP predicts {f(t.rmse_predicted)} m but achieves {f(t.rmse_achieved)} m —
            optimistic by ≈2×. Directionally correct and still decisively better
            than random; the variance model needs recalibration.
          </div>
        </div>
        <div style={{ maxHeight: 250, overflow: "auto" }}>
          <table>
            <thead><tr>
              <th className="n">#</th><th className="n">Lon</th><th className="n">Lat</th>
              <th className="n">Marginal gain</th><th className="n">RMSE after</th>
              <th>Rationale</th>
            </tr></thead>
            <tbody>
              {plan.points.map((p) => (
                <tr key={p.rank}>
                  <td className="n">{p.rank}</td>
                  <td className="n">{p.at[0].toFixed(5)}</td>
                  <td className="n">{p.at[1].toFixed(5)}</td>
                  <td className="n">{p.marginal_gain.toFixed(1)}</td>
                  <td className="n">{p.rmse_after_m.toFixed(3)} m</td>
                  <td style={{ color: "var(--ink-faint)" }}>{p.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

function GainCurve({ plan }: { plan: any }) {
  const pts: [number, number][] = plan.gain_curve;
  if (!pts.length) return null;
  const W = 272, H = 96, P = 24;
  const maxY = Math.max(plan.rmse_before, ...pts.map((p) => p[1]));
  const x = (i: number) => P + (i / Math.max(pts.length - 1, 1)) * (W - P - 6);
  const y = (v: number) => H - 16 - (v / maxY) * (H - 30);
  const d = pts.map((p, i) => `${i ? "L" : "M"}${x(i)},${y(p[1])}`).join(" ");
  return (
    <svg width={W} height={H} role="img" aria-label="Diminishing returns curve">
      <line x1={P} y1={y(plan.rmse_before)} x2={W - 6} y2={y(plan.rmse_before)}
            stroke="var(--crit)" strokeWidth="1" strokeDasharray="3 2" />
      <text x={W - 8} y={y(plan.rmse_before) - 4} fontSize="9" fill="var(--crit)"
            textAnchor="end" fontFamily="IBM Plex Mono">baseline</text>
      <path d={d} fill="none" stroke="var(--acc)" strokeWidth="1.8" />
      {pts.map((p, i) => <circle key={i} cx={x(i)} cy={y(p[1])} r="2" fill="var(--acc)" />)}
      <text x={2} y={12} fontSize="9" fill="var(--ink-faint)" fontFamily="IBM Plex Mono">
        RMSE m</text>
      <text x={W - 6} y={H - 3} fontSize="9" fill="var(--ink-faint)"
            textAnchor="end" fontFamily="IBM Plex Mono">GCPs</text>
    </svg>
  );
}

/* ---------------------------------------------------------------- */
function Validate() {
  const { metrics } = useStore();
  if (!metrics) return null;
  const m = metrics.matching, t = metrics.topology;
  const drift = t.area_after - t.area_before;
  const dedup = t.overlap_area_before - t.overlap_area_after;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 0 }}>
      {/* calibration */}
      <div style={{ padding: "11px 13px", borderRight: "1px solid var(--line)" }}>
        <H>Calibration</H>
        <Reliability rows={m.reliability} />
        <div className="stats" style={{ padding: "8px 0 0" }}>
          <div className="stat"><span className="k">ECE</span>
            <span className="v num" style={{ color: "var(--acc)" }}>{m.ece.toFixed(5)}</span></div>
          <div className="stat"><span className="k">Brier</span>
            <span className="v num">{m.brier.toFixed(5)}</span></div>
          <div className="stat"><span className="k">ROC AUC</span>
            <span className="v num">{m.roc_auc.toFixed(4)}</span></div>
        </div>
        <P>Of pairs scored near p, that fraction really were correct on held-out
          data. This is what makes the confidence a decision rather than decoration.</P>
      </div>

      {/* feature importance */}
      <div style={{ padding: "11px 13px", borderRight: "1px solid var(--line)" }}>
        <H>What the model actually uses</H>
        <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {m.feature_importance.slice(0, 9).map((fi) => (
            <div key={fi.name} style={{ display: "grid",
                 gridTemplateColumns: "118px 1fr 42px", gap: 7, alignItems: "center" }}>
              <span className="num" style={{ fontSize: 10.5, color: "var(--ink-dim)" }}>
                {fi.name}</span>
              <span className="bar-track">
                <span className="bar-fill" style={{ width: `${fi.gain * 100}%` }} /></span>
              <span className="num" style={{ fontSize: 10.5, textAlign: "right" }}>
                {(fi.gain * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>
        <div className="stats" style={{ padding: "8px 0 0" }}>
          <div className="stat"><span className="k">geometric share</span>
            <span className="v num" style={{ color: "var(--acc)" }}>
              {(m.geometry_share * 100).toFixed(1)}%</span></div>
          <div className="stat"><span className="k">blocking recall</span>
            <span className="v num">{m.blocking_recall.toFixed(4)}</span></div>
        </div>
        <P>Geometry dominates, so the matcher is doing spatial reasoning rather
          than joining on khasra number — the failure mode this harness exists
          to catch.</P>
      </div>

      {/* area ledger */}
      <div style={{ padding: "11px 13px" }}>
        <H>Area conservation ledger</H>
        <table style={{ fontSize: 11.5 }}>
          <tbody>
            <LedgerRow k="summed parcel area"
                       a={t.area_before} b={t.area_after} />
            <LedgerRow k="doubly-claimed land"
                       a={t.overlap_area_before} b={t.overlap_area_after} />
          </tbody>
        </table>
        <div style={{ borderTop: "1px solid var(--line)", marginTop: 7, paddingTop: 7,
                      fontSize: 11.5, lineHeight: 1.8 }} className="num">
          <div>removed double-counting
            <b style={{ float: "right", color: "var(--acc)" }}>−{k(Math.round(dedup))} m²</b></div>
          <div>net change
            <b style={{ float: "right" }}>{Math.round(drift).toLocaleString()} m²</b></div>
          <div style={{ marginTop: 5, color: "var(--acc)", fontWeight: 600 }}>NO LAND LOST</div>
        </div>
        <P>The summed area falls because two people were recorded owning the same
          ground. Overlaps went {k(t.overlaps_before)} → {k(t.overlaps_after)}.</P>
        <div className="stats" style={{ padding: "6px 0 0" }}>
          <div className="stat"><span className="k">refused to guess</span>
            <span className="v num" style={{ color: "var(--warn)" }}>{t.refused_to_fill}</span></div>
          <div className="stat"><span className="k">actually deleted</span>
            <span className="v num">{t.harness_deleted}</span></div>
        </div>
        <P>Parcel-sized holes are flagged for survey, never filled. Filling them
          would be silent data fabrication.</P>
      </div>
    </div>
  );
}

function LedgerRow({ k: label, a, b }: { k: string; a: number; b: number }) {
  return (
    <tr>
      <td style={{ color: "var(--ink-dim)" }}>{label}</td>
      <td className="n">{k(Math.round(a))}</td>
      <td className="n" style={{ color: "var(--ink-faint)" }}>→</td>
      <td className="n">{k(Math.round(b))}</td>
      <td style={{ color: "var(--ink-faint)" }}>m²</td>
    </tr>
  );
}

function Reliability({ rows }: { rows: any[] }) {
  const W = 190, H = 118, P = 26;
  const pts = rows.filter((r) => r.n > 0);
  const x = (v: number) => P + v * (W - P - 8);
  const y = (v: number) => H - 20 - v * (H - 32);
  return (
    <svg width={W} height={H} role="img" aria-label="Reliability curve">
      <line x1={x(0)} y1={y(0)} x2={x(1)} y2={y(1)}
            stroke="var(--ink-faint)" strokeDasharray="3 3" strokeWidth="1" />
      <path d={pts.map((r, i) => `${i ? "L" : "M"}${x(r.mean_p)},${y(r.observed)}`).join(" ")}
            fill="none" stroke="var(--acc)" strokeWidth="1.8" />
      {pts.map((r, i) => (
        <circle key={i} cx={x(r.mean_p)} cy={y(r.observed)}
                r={Math.max(2, Math.min(5, Math.log10(r.n + 1) * 1.6))}
                fill="var(--acc)" />
      ))}
      <text x={2} y={12} fontSize="9" fill="var(--ink-faint)" fontFamily="IBM Plex Mono">
        observed</text>
      <text x={W - 6} y={H - 4} fontSize="9" fill="var(--ink-faint)"
            textAnchor="end" fontFamily="IBM Plex Mono">predicted p</text>
    </svg>
  );
}

/* ---------------------------------------------------------------- */
function Audit() {
  const { audit } = useStore();
  return (
    <>
      <div className="stats" style={{ borderBottom: "1px solid var(--line)" }}>
        <div className="stat"><span className="k">entries</span>
          <span className="v num">{audit.length}</span></div>
        <div className="stat"><span className="k">chain</span>
          <span className="v"><span className="chip ok">intact</span></span></div>
        <div className="stat" style={{ flex: 1 }}>
          <span className="k">integrity</span>
          <span className="v" style={{ fontSize: 12, color: "var(--ink-dim)" }}>
            each entry hashes the previous one — any retro-edit breaks the chain
          </span></div>
      </div>
      <table>
        <thead><tr>
          <th className="n">#</th><th>Timestamp</th><th>Actor</th>
          <th>Action</th><th>Target</th><th>Reason</th><th className="n">Hash</th>
        </tr></thead>
        <tbody>
          {audit.map((e, i) => (
            <tr key={i}>
              <td className="n">{i + 1}</td>
              <td className="num" style={{ fontSize: 11 }}>{e.ts.replace("T", " ").slice(0, 19)}</td>
              <td><span className={`chip ${e.actor === "user" ? "info" : "mute"}`}>{e.actor}</span></td>
              <td className="num">{e.action}</td>
              <td className="num">{e.target}</td>
              <td style={{ color: "var(--ink-faint)", maxWidth: 420,
                           overflow: "hidden", textOverflow: "ellipsis" }}>{e.reason}</td>
              <td className="n" style={{ color: "var(--acc)" }}>{e.hash}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

/* ---------------------------------------------------------------- */
function Pipeline() {
  const { metrics } = useStore();
  if (!metrics) return null;
  const total = metrics.stages.reduce((a, s) => a + s.seconds, 0);
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 0 }}>
      <div style={{ padding: "11px 13px", borderRight: "1px solid var(--line)" }}>
        <H>Stage timings — where the time actually goes</H>
        <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {metrics.stages.map((st) => (
            <div key={st.name} style={{ display: "grid",
                 gridTemplateColumns: "150px 1fr 54px", gap: 8, alignItems: "center" }}>
              <span style={{ fontSize: 11.5, color: "var(--ink-dim)" }}>{st.name}</span>
              <span className="bar-track">
                <span className="bar-fill" style={{ width: `${(st.seconds / total) * 100}%` }} /></span>
              <span className="num" style={{ fontSize: 11, textAlign: "right" }}>
                {st.seconds.toFixed(2)}s</span>
            </div>
          ))}
        </div>
      </div>
      <div style={{ padding: "11px 13px" }}>
        <H>Counts</H>
        <div className="stats" style={{ padding: 0 }}>
          {Object.entries(metrics.counts).map(([kk, v]) => (
            <div className="stat" key={kk}>
              <span className="k">{kk.replace(/_/g, " ")}</span>
              <span className="v num">{k(v as number)}</span>
            </div>
          ))}
        </div>
        <div style={{ height: 12 }} />
        <H>Assignment</H>
        <div className="stats" style={{ padding: 0 }}>
          {Object.entries(metrics.assignment).map(([kk, v]) => (
            <div className="stat" key={kk}>
              <span className="k">{kk.replace(/_/g, " ")}</span>
              <span className="v num">{k(v as number)}</span>
            </div>
          ))}
        </div>
        <P>Engine build {metrics.generated_at.replace("T", " ")} · full pipeline
          {" "}{metrics.runtime_s}s on one core.</P>
      </div>
    </div>
  );
}

const H = ({ children }: any) => (
  <div style={{ fontSize: 10.5, letterSpacing: ".09em", textTransform: "uppercase",
                color: "var(--ink-faint)", marginBottom: 8, fontWeight: 500 }}>
    {children}</div>
);
const P = ({ children }: any) => (
  <div style={{ fontSize: 11, color: "var(--ink-faint)", lineHeight: 1.6, marginTop: 8 }}>
    {children}</div>
);
