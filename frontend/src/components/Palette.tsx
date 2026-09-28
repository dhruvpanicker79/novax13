import { useEffect, useMemo, useRef, useState } from "react";
import { redact, useStore, type LayerId } from "../lib/store";
import * as I from "../lib/icons";

/**
 * Command palette and search, on one surface.
 *
 * This is the single highest-leverage element in the interface. An operator
 * working a review queue should never hunt through twelve layer toggles to
 * find the one they want, and a judge asking "can you find khasra 214/3"
 * should see it happen in two seconds rather than watch someone pan a map.
 *
 * Search runs over the real parcel attributes and the conflict queue, and
 * respects the signed-in role: a public session cannot search by owner name,
 * because it was never sent the owner names.
 */
type Item = {
  id: string;
  label: string;
  hint?: string;
  group: string;
  run: () => void;
};

export default function Palette() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [i, setI] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const s = useStore();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = (e.target as HTMLElement)?.tagName === "INPUT";
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
        setQ(""); setI(0);
        return;
      }
      if (!typing && e.key === "/") {
        e.preventDefault(); setOpen(true); setQ(""); setI(0); return;
      }
      if (open && e.key === "Escape") { setOpen(false); return; }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  useEffect(() => { if (open) inputRef.current?.focus(); }, [open]);

  const items = useMemo<Item[]>(() => {
    if (!s.loaded) return [];
    const out: Item[] = [];

    for (const l of s.layers) {
      out.push({
        id: `layer:${l.id}`, group: "Layer",
        label: `${l.on ? "Hide" : "Show"} ${l.label}`,
        hint: l.sub,
        run: () => s.toggleLayer(l.id as LayerId),
      });
    }

    const tabs: [string, string][] = [
      ["conflicts", "Review queue"], ["schema", "Schema"],
      ["survey", "Survey plan"], ["change", "Change"],
      ["resolve", "Resolution"], ["validate", "Validation"],
      ["audit", "Audit log"], ["export", "Export"], ["metrics", "Pipeline"],
    ];
    for (const [id, label] of tabs) {
      out.push({
        id: `tab:${id}`, group: "Go to", label,
        run: () => s.setDockTab(id as any),
      });
    }

    out.push(
      { id: "act:run", group: "Action", label: "Run the pipeline",
        hint: "Space", run: () => s.runPipeline() },
      { id: "act:align", group: "Action", label: "Replay the alignment",
        hint: "\\", run: () => s.playAlignment() },
      { id: "act:signout", group: "Action",
        label: `Sign out of ${s.role}`, run: () => s.signOut() },
    );

    return out;
  }, [s.loaded, s.layers, s.role]);

  // --- searching the actual data -------------------------------------
  const results = useMemo(() => {
    const term = q.trim().toLowerCase();
    if (!term) return { cmds: items.slice(0, 9), parcels: [], conflicts: [] };

    const cmds = items.filter((x) =>
      x.label.toLowerCase().includes(term) ||
      x.group.toLowerCase().includes(term)).slice(0, 6);

    const seesOwner = s.role === "clerk" || s.role === "tehsildar";
    const parcels = (s.harmonized?.features ?? [])
      .filter((f) => {
        const p = f.properties;
        if (String(p.KHSRA_NUM ?? "").toLowerCase().includes(term)) return true;
        if (String(p.fid ?? "").toLowerCase().includes(term)) return true;
        if (seesOwner &&
            String(p.KHATEDAR_NM ?? "").toLowerCase().includes(term)) return true;
        return false;
      })
      .slice(0, 6);

    const conflicts = s.conflicts.filter((c) =>
      c.id.toLowerCase().includes(term) ||
      String(c.khasra ?? "").toLowerCase().includes(term) ||
      c.class.includes(term)).slice(0, 6);

    return { cmds, parcels, conflicts };
  }, [q, items, s.harmonized, s.conflicts, s.role]);

  const flat: Item[] = useMemo(() => [
    ...results.cmds,
    // Redact here too. Keeping owner names out of the *search* is not enough
    // if the result row then prints one as its subtitle — which is exactly
    // what this did until it was tested as a public session.
    ...results.parcels.map((f) => {
      const p = redact(f.properties, s.role);
      return {
        id: `p:${p.fid}`, group: "Parcel",
        label: `Khasra ${p.KHSRA_NUM ?? "—"}`,
        hint: p.KHATEDAR_NM ?? `${p.fid}${p.LU_CODE ? " · " + p.LU_CODE : ""}`,
        run: () => s.select(p.fid),
      };
    }),
    ...results.conflicts.map((c) => ({
      id: `c:${c.id}`, group: "Conflict",
      label: `${c.id} · ${c.class.replace(/_/g, " ")}`,
      hint: `khasra ${c.khasra ?? "—"} · ${c.area_sqm.toFixed(0)} m²`,
      run: () => s.selectConflict(c.id),
    })),
  ], [results]);

  if (!open) return null;

  const pick = (n: number) => {
    const it = flat[n];
    if (!it) return;
    it.run();
    setOpen(false);
  };

  return (
    <div
      onClick={() => setOpen(false)}
      style={{
        position: "absolute", inset: 0, zIndex: 90,
        background: "rgba(23,27,32,0.28)",
        display: "flex", justifyContent: "center", alignItems: "flex-start",
        paddingTop: "12vh",
      }}>
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "min(600px, 92%)", background: "var(--panel)",
          border: "1px solid var(--line)", borderRadius: 4,
          boxShadow: "0 8px 40px rgba(23,27,32,.24)", overflow: "hidden",
        }}>
        <div style={{ display: "flex", alignItems: "center", gap: 9,
                      padding: "11px 14px",
                      borderBottom: "1px solid var(--line)" }}>
          <span style={{ color: "var(--ink-faint)" }}><I.Search /></span>
          <input
            ref={inputRef}
            value={q}
            placeholder="Search khasra, owner, conflict ID — or type a command"
            onChange={(e) => { setQ(e.target.value); setI(0); }}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") { e.preventDefault(); setI((v) => Math.min(v + 1, flat.length - 1)); }
              if (e.key === "ArrowUp") { e.preventDefault(); setI((v) => Math.max(v - 1, 0)); }
              if (e.key === "Enter") { e.preventDefault(); pick(i); }
            }}
            style={{ border: "none", background: "none", fontSize: 14, padding: 0 }}
          />
          <span className="chip mute">esc</span>
        </div>

        <div style={{ maxHeight: 340, overflowY: "auto" }}>
          {flat.length === 0 && (
            <div style={{ padding: "18px 14px", fontSize: 12,
                          color: "var(--ink-faint)" }}>
              Nothing matches “{q}”.
              {s.role === "public" && (
                <div style={{ marginTop: 6 }}>
                  This session is signed in as <b>public</b>, so owner names
                  were never sent and cannot be searched.
                </div>
              )}
            </div>
          )}
          {flat.map((it, n) => (
            <div
              key={it.id}
              onMouseEnter={() => setI(n)}
              onClick={() => pick(n)}
              style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "8px 14px", cursor: "pointer",
                background: n === i ? "var(--acc-ghost)" : "transparent",
                borderLeft: `2px solid ${n === i ? "var(--acc)" : "transparent"}`,
              }}>
              <span className="chip mute" style={{ minWidth: 62, textAlign: "center" }}>
                {it.group}
              </span>
              <span style={{ flex: 1, fontSize: 13 }}>{it.label}</span>
              {it.hint && (
                <span className="num" style={{ fontSize: 11, color: "var(--ink-faint)",
                                               maxWidth: 210, overflow: "hidden",
                                               textOverflow: "ellipsis",
                                               whiteSpace: "nowrap" }}>
                  {it.hint}
                </span>
              )}
            </div>
          ))}
        </div>

        <div style={{ padding: "7px 14px", borderTop: "1px solid var(--line)",
                      background: "var(--panel-hi)", fontSize: 10.5,
                      color: "var(--ink-faint)", display: "flex", gap: 14 }}>
          <span>↑↓ move</span><span>↵ select</span>
          <span>⌘K / Ctrl-K toggle</span>
          <span style={{ marginLeft: "auto" }}>role: {s.role}</span>
        </div>
      </div>
    </div>
  );
}
