import { useState } from "react";
import { LogoLockup } from "./Logo";
import { ROLES, useStore, type Role } from "../lib/store";
import * as I from "../lib/icons";

/**
 * Role selection, and deliberately not a credential prompt.
 *
 * A demo login that accepts any password teaches the viewer nothing and
 * implies a control that is not there. What is real here is the
 * *authorisation* model: the role you choose genuinely changes what the
 * application will show you and what it will let you do, mirroring the
 * server-side rules in api/main.py. Owner names are personal data under the
 * DPDP Act 2023, so a public session simply never receives them.
 *
 * Production would put SSO in front of this and derive the role from the
 * directory. The screen says so rather than pretending otherwise.
 */
export default function SignIn() {
  const { signIn } = useStore();
  const [sel, setSel] = useState<Role>("tehsildar");

  return (
    <div style={{
      position: "absolute", inset: 0, zIndex: 100,
      background: "var(--sunk)",
      display: "grid", placeItems: "center", padding: 20,
      overflow: "auto",
    }}>
      <div style={{ width: "min(760px, 100%)" }}>
        <div style={{ marginBottom: 22 }}><LogoLockup /></div>

        <div className="card">
          <header>
            <span className="grow">Select an operating role</span>
            <span className="chip mute">Chandausi ward 04</span>
          </header>

          <div style={{ padding: "13px 15px" }}>
            <div style={{ fontSize: 12.5, color: "var(--ink-dim)",
                          lineHeight: 1.6, marginBottom: 13 }}>
              Land records contain personal data. What you see below changes
              with the role — this is the same rule the API enforces, not a
              display filter.
            </div>

            <div style={{ display: "grid", gap: 8,
                          gridTemplateColumns: "repeat(auto-fit,minmax(168px,1fr))" }}>
              {ROLES.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setSel(r.id)}
                  style={{
                    textAlign: "left", padding: "11px 12px", borderRadius: 3,
                    border: `1px solid ${sel === r.id ? "var(--acc)" : "var(--line)"}`,
                    background: sel === r.id ? "var(--acc-ghost)" : "var(--panel)",
                    outline: sel === r.id ? "1px solid var(--acc)" : "none",
                  }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 7,
                                marginBottom: 5 }}>
                    <span style={{ color: sel === r.id ? "var(--acc)" : "var(--ink-faint)" }}>
                      <I.Shield />
                    </span>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{r.label}</span>
                  </div>
                  <div style={{ fontSize: 11, color: "var(--ink-faint)",
                                lineHeight: 1.5 }}>{r.blurb}</div>
                </button>
              ))}
            </div>

            <Capabilities role={sel} />

            <div style={{ display: "flex", alignItems: "center", gap: 12,
                          marginTop: 15 }}>
              <button
                onClick={() => signIn(sel)}
                style={{
                  padding: "9px 22px", borderRadius: 3, fontSize: 13,
                  fontWeight: 600, border: "1px solid var(--acc)",
                  background: "var(--acc)", color: "var(--on-acc)",
                }}>
                Enter as {ROLES.find((r) => r.id === sel)!.label}
              </button>
              <div style={{ fontSize: 11, color: "var(--ink-faint)",
                            lineHeight: 1.5 }}>
                No credential check. Production authenticates through the
                department directory and derives the role from it; the
                authorisation rules below are what this prototype implements.
              </div>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 13, fontSize: 11, color: "var(--ink-faint)",
                      lineHeight: 1.65 }}>
          Cadastral geometry in this build is <b>SYNTHETIC</b>, derived from
          OpenStreetMap block structure and labelled as such throughout. The
          AI-extracted building footprints and road network are real.
        </div>
      </div>
    </div>
  );
}

function Capabilities({ role }: { role: Role }) {
  const r = ROLES.find((x) => x.id === role)!;
  const Row = ({ k, v, ok }: { k: string; v: string; ok: boolean }) => (
    <div style={{ display: "grid", gridTemplateColumns: "150px 1fr",
                  gap: 10, padding: "3px 0", fontSize: 12 }}>
      <span style={{ color: "var(--ink-dim)" }}>{k}</span>
      <span style={{ color: ok ? "var(--ink)" : "var(--ink-faint)" }}>
        <span className={`chip ${ok ? "ok" : "mute"}`}
              style={{ marginRight: 7 }}>{ok ? "yes" : "no"}</span>
        {v}
      </span>
    </div>
  );
  return (
    <div style={{ marginTop: 13, paddingTop: 12,
                  borderTop: "1px solid var(--line)" }}>
      <div style={{ fontSize: 10.5, letterSpacing: ".09em",
                    textTransform: "uppercase", color: "var(--ink-faint)",
                    marginBottom: 7, fontWeight: 500 }}>
        What this role can do
      </div>
      <Row k="Owner names" ok={r.seesOwner}
           v={r.seesOwner ? "visible" : "withheld — personal data (DPDP 2023)"} />
      <Row k="Tenure and area" ok={r.seesTenure} v={r.seesTenure ? "visible" : "withheld"} />
      <Row k="Resolve conflicts" ok={r.may.includes("accept")}
           v={r.may.includes("accept") ? "may accept or reject" :
              r.may.length ? `may ${r.may.join(", ")} only` : "read only"} />
      <Row k="Download exports" ok={r.canExport}
           v={r.canExport ? "GeoJSON, Shapefile, CSV, PDF" : "blocked — exports carry personal data"} />
    </div>
  );
}
