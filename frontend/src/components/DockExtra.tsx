import { useStore } from "../lib/store";

const k = (v: number) => v.toLocaleString();

const H = ({ children }: any) => (
  <div style={{ fontSize: 10.5, letterSpacing: ".09em", textTransform: "uppercase",
                color: "var(--ink-faint)", marginBottom: 8, fontWeight: 500 }}>
    {children}</div>
);
const P = ({ children }: any) => (
  <div style={{ fontSize: 11, color: "var(--ink-faint)", lineHeight: 1.6, marginTop: 8 }}>
    {children}</div>
);

/* ================================================================== */
export function SchemaTab() {
  const { schema } = useStore();
  if (!schema) return null;
  const mapped = schema.fields.filter((f) => f.column).length;

  return (
    <>
      <div className="stats" style={{ borderBottom: "1px solid var(--line)" }}>
        <div className="stat"><span className="k">columns mapped</span>
          <span className="v num" style={{ color: mapped === 7 ? "var(--acc)" : "var(--warn)" }}>
            {mapped}/{schema.fields.length}</span></div>
        <div className="stat"><span className="k">area unit inferred</span>
          <span className="v num" style={{ color: "var(--acc)" }}>{schema.area_unit ?? "—"}</span></div>
        <div className="stat"><span className="k">unit confidence</span>
          <span className="v num">{(schema.area_unit_confidence * 100).toFixed(1)}<small> %</small></span></div>
        <div className="stat"><span className="k">scale to m²</span>
          <span className="v num">×{schema.area_scale.toFixed(3)}</span></div>
        <div className="stat"><span className="k">unmapped</span>
          <span className="v num">{schema.unmapped.length}</span></div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 330px" }}>
        <table>
          <thead><tr>
            <th>Canonical field</th><th>Source column</th>
            <th className="n">Confidence</th><th>Evidence</th><th>Runner-up</th>
          </tr></thead>
          <tbody>
            {schema.fields.map((f) => (
              <tr key={f.canonical}>
                <td className="num" style={{ color: "var(--ink-dim)" }}>{f.canonical}</td>
                <td className="num" style={{ color: f.column ? "var(--acc)" : "var(--crit)" }}>
                  {f.column ?? "unmapped"}</td>
                <td className="n">
                  <span className={`chip ${f.confidence >= 0.8 ? "ok" : f.confidence >= 0.5 ? "warn" : "crit"}`}>
                    {f.confidence.toFixed(3)}</span></td>
                <td style={{ color: "var(--ink-faint)", maxWidth: 400,
                             overflow: "hidden", textOverflow: "ellipsis" }}>{f.evidence}</td>
                <td className="num" style={{ color: "var(--ink-faint)" }}>
                  {f.alternatives[0] ? `${f.alternatives[0][0]} ${f.alternatives[0][1].toFixed(2)}` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div style={{ padding: "11px 13px", borderLeft: "1px solid var(--line)" }}>
          <H>Area unit, inferred from geometry</H>
          <div className="num" style={{ fontSize: 12, lineHeight: 1.8 }}>
            <div>recorded column <b style={{ float: "right", color: "var(--acc)" }}>
              {schema.fields.find((f) => f.canonical === "area")?.column ?? "—"}</b></div>
            <div>inferred unit <b style={{ float: "right", color: "var(--acc)" }}>
              {schema.area_unit}</b></div>
            <div>m² per unit <b style={{ float: "right" }}>{schema.area_scale.toFixed(4)}</b></div>
          </div>
          <div style={{ fontSize: 11, color: "var(--ink-dim)", lineHeight: 1.65,
                        marginTop: 9, paddingTop: 9, borderTop: "1px solid var(--line)" }}>
            {schema.area_unit_evidence}
          </div>
          <P>
            The unit is not read from the column name. Recorded values are divided
            by the surveyed area of the same parcels and the modal ratio is matched
            against known units. NIC&rsquo;s own Bhu-Naksha manual documents a
            hand-entered per-state scale factor on import — UP ×4000, Himachal ×22.
            Inferring it removes that magic number from the critical path.
          </P>
        </div>
      </div>
    </>
  );
}

/* ================================================================== */
export function ChangeTab() {
  const { change, selectConflict } = useStore();
  if (!change) return null;
  const c = change.counts;
  const tone: Record<string, string> = {
    new: "info", demolished: "crit", extended: "warn",
    reduced: "warn", heightened: "ok",
  };
  const sev: Record<string, string> = {
    severe: "crit", significant: "warn", minor: "mute",
  };

  return (
    <>
      <div className="stats" style={{ borderBottom: "1px solid var(--line)" }}>
        <div className="stat"><span className="k">epoch</span>
          <span className="v" style={{ fontSize: 12 }}>{change.epoch_from} → {change.epoch_to}</span></div>
        {["new", "demolished", "extended", "heightened"].map((kk) => (
          <div className="stat" key={kk}>
            <span className="k">{kk}</span>
            <span className="v num">{c[kk] ?? 0}</span></div>
        ))}
        <div className="stat"><span className="k">encroachments</span>
          <span className="v num" style={{ color: "var(--crit)" }}>
            {change.encroachments.length}</span></div>
        <div className="stat"><span className="k">public land taken</span>
          <span className="v num" style={{ color: "var(--crit)" }}>
            {k(Math.round(change.encroached_sqm))}<small> m²</small></span></div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr" }}>
        <div>
          <div style={{ padding: "9px 13px 4px" }}><H>Encroachment on government land</H></div>
          <table>
            <thead><tr>
              <th>Building</th><th>On</th><th className="n">Area m²</th>
              <th className="n">% of bldg</th><th>Severity</th><th className="n">p</th>
            </tr></thead>
            <tbody>
              {change.encroachments.map((e) => (
                <tr key={e.building_fid}>
                  <td className="num">{e.building_fid}</td>
                  <td>{e.category}</td>
                  <td className="n">{e.sqm.toFixed(1)}</td>
                  <td className="n">{(e.fraction * 100).toFixed(1)}</td>
                  <td><span className={`chip ${sev[e.severity]}`}>{e.severity}</span></td>
                  <td className="n">{e.confidence.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {change.sample_dossier && (
            <div style={{ padding: "11px 13px", borderTop: "1px solid var(--line)" }}>
              <H>Change dossier — not a mutation record</H>
              <div className="num" style={{ fontSize: 11, lineHeight: 1.75 }}>
                {["type", "status", "building_fid", "government_parcel",
                  "encroached_sqm", "severity", "decision_required"].map((f) => (
                  <div key={f}>
                    <span style={{ color: "var(--ink-faint)" }}>{f}</span>
                    <b style={{ float: "right" }}>{String(change.sample_dossier![f])}</b>
                  </div>
                ))}
              </div>
              <P>{change.sample_dossier.note}</P>
            </div>
          )}
        </div>

        <div style={{ borderLeft: "1px solid var(--line)" }}>
          <div style={{ padding: "9px 13px 4px" }}>
            <H>Change events {!change.dsm_available && "(no DSM — vertical change not assessed)"}</H>
          </div>
          <div style={{ maxHeight: 250, overflow: "auto" }}>
            <table>
              <thead><tr>
                <th>Kind</th><th>Feature</th><th className="n">Area m²</th>
                <th className="n">Δ m²</th><th className="n">Δh m</th><th>Note</th>
              </tr></thead>
              <tbody>
                {change.events.slice(0, 160).map((e, i) => (
                  <tr key={i}>
                    <td><span className={`chip ${tone[e.kind] ?? "mute"}`}>{e.kind}</span></td>
                    <td className="num">{e.fid}</td>
                    <td className="n">{e.area_sqm.toFixed(1)}</td>
                    <td className="n" style={{ color: e.delta_sqm > 0 ? "var(--warn)" : e.delta_sqm < 0 ? "var(--crit)" : "var(--ink-faint)" }}>
                      {e.delta_sqm > 0 ? "+" : ""}{e.delta_sqm.toFixed(1)}</td>
                    <td className="n" style={{ color: e.height_delta_m ? "var(--ok)" : "var(--ink-faint)" }}>
                      {e.height_delta_m != null ? `+${e.height_delta_m.toFixed(1)}` : "—"}</td>
                    <td style={{ color: "var(--ink-faint)", maxWidth: 260,
                                 overflow: "hidden", textOverflow: "ellipsis" }}>{e.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ padding: "0 13px 11px" }}>
            <P>
              <b style={{ color: "var(--ok)" }}>{c.heightened ?? 0} heightened</b> events have an
              unchanged footprint and are invisible to plan-view differencing. Only
              the DSM height delta sees a building that gained storeys.
            </P>
          </div>
        </div>
      </div>
    </>
  );
}

/* ================================================================== */
export function ResolveTab() {
  const { resolutions } = useStore();
  if (!resolutions.length) return null;

  return (
    <div style={{ padding: "11px 13px" }}>
      <H>Provenance-weighted conflict resolution — worked cases</H>
      <div style={{ display: "grid", gap: 9,
                    gridTemplateColumns: "repeat(auto-fit, minmax(330px, 1fr))" }}>
        {resolutions.map((rc) => (
          <div key={rc.fid} className="card" style={{ background: "var(--sunk)" }}>
            <header>
              <span className="grow">{rc.title}</span>
              {rc.needs_human
                ? <span className="chip warn">human</span>
                : <span className="chip ok">auto</span>}
            </header>
            <div style={{ padding: "8px 11px" }}>
              <table style={{ fontSize: 11 }}>
                <tbody>
                  {rc.claims.map((cl, i) => (
                    <tr key={i}>
                      <td style={{ color: "var(--ink-dim)", padding: "2px 0" }}>
                        {cl.label}
                        {cl.authority.includes(cl.field) &&
                          <span className="chip info" style={{ marginLeft: 6 }}>authoritative</span>}
                      </td>
                      <td className="n" style={{ padding: "2px 0" }}>σ {cl.sigma_m}m</td>
                      <td className="n" style={{ padding: "2px 0 2px 10px", maxWidth: 150,
                                                 overflow: "hidden", textOverflow: "ellipsis" }}>
                        {String(cl.value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {rc.resolutions.map((r, i) => (
                <div key={i} style={{ marginTop: 8, paddingTop: 8,
                                      borderTop: "1px solid var(--line)" }}>
                  <div style={{ fontSize: 12 }}>
                    <b className="num" style={{ color: "var(--acc)" }}>
                      {typeof r.value === "number" ? r.value.toFixed(2) : String(r.value)}
                    </b>
                    <span className="chip mute" style={{ float: "right" }}>{r.rule}</span>
                  </div>
                  {r.note && <div style={{ fontSize: 10.5, color: "var(--ink-faint)",
                                           marginTop: 4, lineHeight: 1.55 }}>{r.note}</div>}
                </div>
              ))}

              {rc.transitive.map((t, i) => (
                <div key={i} style={{ fontSize: 10.5, color: "var(--warn)",
                                      marginTop: 6, lineHeight: 1.5 }}>
                  transitive: {t}
                </div>
              ))}
              {rc.reason && (
                <div style={{ fontSize: 10.5, color: "var(--ink-faint)",
                              marginTop: 6, lineHeight: 1.5 }}>{rc.reason}</div>
              )}
            </div>
          </div>
        ))}
      </div>
      <P>
        Authority is per attribute, not per source. Measured quantities combine by
        inverse variance; recorded ones follow legal authority. Conflating the two
        produces a system that will overwrite a title with a photograph.
      </P>
    </div>
  );
}
