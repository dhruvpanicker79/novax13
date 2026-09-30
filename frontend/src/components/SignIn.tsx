import { useEffect, useRef, useState } from "react";
import { LogoLockup } from "./Logo";
import { ACCOUNTS, ROLES, useStore } from "../lib/store";
import * as I from "../lib/icons";

/**
 * Sign-in.
 *
 * The role is a property of the account, not something the operator picks —
 * an officer does not choose to be a tehsildar at the door. Credentials are
 * checked against a fixture table here; in deployment the department
 * directory authenticates and the role comes back from it. The screen says so
 * once, quietly, rather than implying a control that is not there.
 */
export default function SignIn() {
  const { signIn } = useStore();
  const [user, setUser] = useState("");
  const [pw, setPw] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const userRef = useRef<HTMLInputElement>(null);

  useEffect(() => { userRef.current?.focus(); }, []);

  const submit = (e?: React.FormEvent) => {
    e?.preventDefault();
    const u = user.trim().toLowerCase();
    const acct = ACCOUNTS.find((a) => a.user === u);
    if (!acct || acct.pw !== pw) {
      // One message for both failure modes: saying which half was wrong tells
      // an attacker which usernames exist.
      setErr("Those credentials were not recognised.");
      setPw("");
      return;
    }
    setErr(null);
    setBusy(true);
    window.setTimeout(() => signIn(acct.role, acct.name), 260);
  };

  const fill = (u: string, p: string) => {
    setUser(u); setPw(p); setErr(null);
  };

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 200, overflow: "auto",
      background:
        "radial-gradient(1100px 620px at 78% 16%, #dfe9f2 0%, rgba(223,233,242,0) 62%), " +
        "radial-gradient(900px 560px at 12% 88%, #e2efe6 0%, rgba(226,239,230,0) 58%), " +
        "#eef0f3",
      display: "grid", placeItems: "center", padding: 22,
    }}>
      <div style={{ width: "min(880px, 100%)", display: "grid",
                    gridTemplateColumns: "1fr 352px", gap: 34,
                    alignItems: "center" }}>

        {/* ---- identity + what this is ---- */}
        <div>
          <LogoLockup size={50} />
          <div style={{ marginTop: 20, fontSize: 21, lineHeight: 1.4,
                        fontWeight: 600, maxWidth: 430 }}>
            One cadastral layer from a dozen sources that disagree — with an
            honest confidence on every parcel.
          </div>
          <div style={{ marginTop: 13, fontSize: 13.5, color: "var(--ink-dim)",
                        lineHeight: 1.6, maxWidth: 430 }}>
            Legacy sheets carry metres of error against orthoimagery specified
            to centimetres. KSHETRA georeferences, matches on geometry, repairs
            topology without losing land, and sends only the genuinely doubtful
            cases to a human.
          </div>

          <div style={{ display: "flex", gap: 24, marginTop: 26 }}>
            {[["3,047", "parcels harmonized"],
              ["0.00009", "calibration error"],
              ["5,038 → 0", "overlapping pairs"]].map(([v, k]) => (
              <div key={k}>
                <div className="num" style={{ fontSize: 19, fontWeight: 600,
                                              color: "var(--acc)" }}>{v}</div>
                <div style={{ fontSize: 10.5, color: "var(--ink-faint)",
                              letterSpacing: ".04em", marginTop: 2 }}>{k}</div>
              </div>
            ))}
          </div>
        </div>

        {/* ---- credentials ---- */}
        <form onSubmit={submit} className="card"
              style={{ boxShadow: "0 2px 6px rgba(23,27,32,.08), " +
                                  "0 18px 46px rgba(23,27,32,.12)" }}>
          <header><span className="grow">Sign in</span>
            <span className="chip mute">Sambhal · UP</span></header>

          <div style={{ padding: "16px 17px 18px" }}>
            <label style={{ fontSize: 11.5, color: "var(--ink-dim)",
                            display: "block", marginBottom: 5 }}>
              Username
            </label>
            <input ref={userRef} value={user} autoComplete="username"
                   onChange={(e) => { setUser(e.target.value); setErr(null); }}
                   placeholder="e.g. r.sharma" />

            <label style={{ fontSize: 11.5, color: "var(--ink-dim)",
                            display: "block", margin: "12px 0 5px" }}>
              Password
            </label>
            <input type="password" value={pw} autoComplete="current-password"
                   onChange={(e) => { setPw(e.target.value); setErr(null); }}
                   placeholder="••••••••" />

            {err && (
              <div style={{ marginTop: 11, padding: "7px 10px", borderRadius: 3,
                            background: "var(--crit-ghost)", color: "var(--crit)",
                            fontSize: 12 }}>
                {err}
              </div>
            )}

            <button type="submit" disabled={busy}
                    style={{ width: "100%", marginTop: 15, padding: "10px 0",
                             borderRadius: 3, fontSize: 13.5, fontWeight: 600,
                             border: "1px solid var(--acc)",
                             background: busy ? "var(--acc-dim)" : "var(--acc)",
                             color: "var(--on-acc)" }}>
              {busy ? "Signing in…" : "Sign in"}
            </button>

            <button type="button" onClick={() => setShowHelp((v) => !v)}
                    style={{ marginTop: 12, fontSize: 11.5,
                             color: "var(--ink-faint)", display: "flex",
                             alignItems: "center", gap: 6 }}>
              <I.Chevron open={showHelp} /> Evaluation accounts
            </button>

            {showHelp && (
              <div style={{ marginTop: 8, borderTop: "1px solid var(--line)",
                            paddingTop: 9 }}>
                {ACCOUNTS.map((a) => (
                  <button key={a.user} type="button"
                          onClick={() => fill(a.user, a.pw)}
                          style={{ display: "block", width: "100%",
                                   textAlign: "left", padding: "5px 7px",
                                   borderRadius: 3, marginBottom: 2 }}
                          onMouseEnter={(e) => (e.currentTarget.style.background = "var(--panel-hi)")}
                          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
                    <span className="num" style={{ fontSize: 11.5 }}>{a.user}</span>
                    <span style={{ fontSize: 10.5, color: "var(--ink-faint)",
                                   float: "right" }}>
                      {ROLES.find((r) => r.id === a.role)!.label}
                    </span>
                  </button>
                ))}
                <div style={{ fontSize: 10.5, color: "var(--ink-faint)",
                              lineHeight: 1.55, marginTop: 7 }}>
                  Fixture credentials for evaluation. Deployment authenticates
                  against the department directory and takes the role from it;
                  no password is stored here.
                </div>
              </div>
            )}
          </div>
        </form>
      </div>

      <div style={{ position: "absolute", bottom: 16, left: 0, right: 0,
                    textAlign: "center", fontSize: 11,
                    color: "var(--ink-faint)" }}>
        Cadastral geometry in this build is <b>SYNTHETIC</b>, derived from
        OpenStreetMap block structure and labelled throughout. Building
        footprints and the road network are real.
      </div>
    </div>
  );
}
