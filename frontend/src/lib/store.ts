import { create } from "zustand";
import type {
  AuditEntry, ChangeResult, Conflict, FC, Metrics, Residual,
  ExportManifest, ResolutionCase, SchemaResult, StageId, SurveyPlan,
  UncertaintyGrid,
} from "./types";
import { STAGES } from "./types";

const B = "/data";

async function j<T>(name: string): Promise<T> {
  const r = await fetch(`${B}/${name}`);
  if (!r.ok) throw new Error(`${name}: HTTP ${r.status}`);
  return r.json();
}


/** Authorisation model. Mirrors VISIBLE / MAY_ACT in api/main.py — the UI must
 *  not offer an action the server would refuse, and must not display a field
 *  the server would withhold. */
export type Role = "public" | "surveyor" | "clerk" | "tehsildar";

export interface RoleSpec {
  id: Role; label: string; blurb: string;
  seesOwner: boolean; seesTenure: boolean; canExport: boolean;
  may: string[];
}

export const ROLES: RoleSpec[] = [
  { id: "public", label: "Public", may: [],
    blurb: "Open access. Parcel geometry and khasra numbers only.",
    seesOwner: false, seesTenure: false, canExport: false },
  { id: "surveyor", label: "Surveyor", may: ["survey"],
    blurb: "Field staff. May raise a parcel for ground survey.",
    seesOwner: false, seesTenure: true, canExport: true },
  { id: "clerk", label: "Revenue clerk", may: ["escalate", "survey"],
    blurb: "Office staff. Full record, may escalate but not decide.",
    seesOwner: true, seesTenure: true, canExport: true },
  { id: "tehsildar", label: "Tehsildar", may: ["accept", "reject", "escalate", "survey"],
    blurb: "Revenue officer. Authorised to resolve a contested parcel.",
    seesOwner: true, seesTenure: true, canExport: true },
];

/** Withhold what this role may not see. Applied wherever an attribute is
 *  rendered, so a redacted field cannot leak through a panel nobody checked. */
export function redact(props: Record<string, any>, role: Role) {
  const r = ROLES.find((x) => x.id === role)!;
  const out = { ...props };
  const withheld: string[] = [];
  if (!r.seesOwner && "KHATEDAR_NM" in out) { delete out.KHATEDAR_NM; withheld.push("owner"); }
  if (!r.seesTenure) {
    for (const k of ["TENURE_TYP", "AREA_BIGHA"]) {
      if (k in out) { delete out[k]; withheld.push(k); }
    }
  }
  if (withheld.length) out._redacted = withheld;
  return out;
}


/** Fixture accounts. The role is a property of the account, not a choice the
 *  operator makes at sign-in. Deployment replaces this with the department
 *  directory; nothing here is a credential store. */
export interface Account {
  user: string; pw: string; name: string; role: Role;
}

export const ACCOUNTS: Account[] = [
  { user: "r.sharma", pw: "kshetra", name: "R. Sharma", role: "tehsildar" },
  { user: "a.verma", pw: "kshetra", name: "A. Verma", role: "clerk" },
  { user: "s.yadav", pw: "kshetra", name: "S. Yadav", role: "surveyor" },
  { user: "guest", pw: "guest", name: "Public access", role: "public" },
];

export type LayerId =
  | "reference" | "legacy" | "aligned" | "harmonized" | "govt"
  | "residuals" | "confidence" | "conflicts" | "survey" | "uncertainty"
  | "buildings" | "change" | "encroach";

export interface LayerState {
  id: LayerId; label: string; sub: string;
  on: boolean; opacity: number;
}

const DEFAULT_LAYERS: LayerState[] = [
  { id: "harmonized", label: "Harmonized cadastre", sub: "output · 3,047 parcels", on: true, opacity: 1 },
  { id: "confidence", label: "Confidence surface", sub: "calibrated p(match)", on: false, opacity: 0.85 },
  { id: "reference", label: "Reference parcels", sub: "AI-extracted · ground truth", on: false, opacity: 0.9 },
  { id: "legacy", label: "Legacy cadastral sheet", sub: "1987 · SYNTHETIC", on: false, opacity: 0.85 },
  { id: "residuals", label: "Residual vectors", sub: "pre-georeference error", on: false, opacity: 1 },
  { id: "uncertainty", label: "Uncertainty field", sub: "GP posterior σ", on: false, opacity: 0.7 },
  { id: "survey", label: "Survey plan", sub: "recommended GCPs", on: false, opacity: 1 },
  { id: "govt", label: "Government land", sub: "encroachment basis", on: true, opacity: 0.8 },
  { id: "encroach", label: "Encroachment", sub: "built on public land", on: true, opacity: 1 },
  { id: "change", label: "Change events", sub: "2023 -> 2025", on: false, opacity: 1 },
  { id: "buildings", label: "Building footprints", sub: "epoch t1", on: false, opacity: 0.9 },
  { id: "conflicts", label: "Conflict markers", sub: "review queue", on: true, opacity: 1 },
];

interface S {
  loaded: boolean;
  error: string | null;

  reference?: FC; legacy?: FC; aligned?: FC; harmonized?: FC; govt?: FC;
  metrics?: Metrics;
  conflicts: Conflict[];
  plan?: SurveyPlan;
  residuals: Residual[];
  uncertainty?: UncertaintyGrid;
  schema?: SchemaResult;
  change?: ChangeResult;
  resolutions: ResolutionCase[];
  buildings?: FC;
  manifest?: ExportManifest;

  layers: LayerState[];
  toggleLayer: (id: LayerId) => void;
  setOpacity: (id: LayerId, v: number) => void;

  /** Which pipeline stages have completed. Drives the stage tracker. */
  done: StageId[];
  running: StageId | null;
  runPipeline: () => Promise<void>;

  /** true = show pre-georeference geometry, so the alignment can be replayed */
  showRaw: boolean;
  setShowRaw: (v: boolean) => void;
  aligning: boolean;
  playAlignment: () => void;

  selected: string | null;
  select: (fid: string | null) => void;
  selectedConflict: string | null;
  selectConflict: (id: string | null) => void;

  dockTab: "conflicts" | "schema" | "survey" | "change" | "resolve"
         | "validate" | "audit" | "export" | "metrics";
  setDockTab: (t: S["dockTab"]) => void;
  dockOpen: boolean;
  setDockOpen: (v: boolean) => void;

  panel: "project" | "layers" | "inspect";
  setPanel: (p: S["panel"]) => void;

  audit: AuditEntry[];
  act: (id: string, action: Conflict["status"], reason: string) => void;

  role: Role;
  signedIn: boolean;
  operator: string;
  signIn: (r: Role, name?: string) => void;
  signOut: () => void;
  basemap: "imagery" | "light" | "dark";
  setBasemap: (b: S["basemap"]) => void;
  pitched: boolean;
  setPitched: (v: boolean) => void;
  basemapOffline: boolean;
  setBasemapOffline: (v: boolean) => void;
  cursor: { lon: number; lat: number; zoom: number };
  setCursor: (c: S["cursor"]) => void;

  load: () => Promise<void>;
}

/** Tamper-evident audit chain: each entry hashes the previous one, so any
 *  retro-edit breaks the chain and is detectable. */
function chainHash(prev: string, e: Omit<AuditEntry, "hash">): string {
  const s = prev + e.ts + e.actor + e.action + e.target + e.reason;
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h.toString(16).padStart(8, "0");
}

export const useStore = create<S>((set, get) => ({
  loaded: false,
  error: null,
  conflicts: [],
  residuals: [],
  resolutions: [],
  layers: DEFAULT_LAYERS,
  done: [],
  running: null,
  showRaw: false,
  aligning: false,
  selected: null,
  selectedConflict: null,
  dockTab: "conflicts",
  dockOpen: true,
  panel: "project",
  audit: [],
  role: "tehsildar",
  signedIn: false,
  operator: "",
  signIn: (role, name = "") => set({ role, operator: name, signedIn: true }),
  signOut: () => set({ signedIn: false, operator: "", selected: null,
                       selectedConflict: null }),
  basemap: "imagery",
  setBasemap: (basemap) => set({ basemap }),
  pitched: false,
  // Turning the camera on also turns the buildings on; a pitched
  // map with flat footprints looks broken rather than three-dimensional.
  setPitched: (pitched) => set((st) => ({
    pitched,
    layers: st.layers.map((l) =>
      l.id === "buildings" ? { ...l, on: pitched } : l),
  })),
  basemapOffline: false,
  setBasemapOffline: (basemapOffline) => set({ basemapOffline }),
  cursor: { lon: 78.7749, lat: 28.4515, zoom: 15 },

  setCursor: (cursor) => set({ cursor }),
  setPanel: (panel) => set({ panel }),
  setDockTab: (dockTab) => set({ dockTab, dockOpen: true }),
  setDockOpen: (dockOpen) => set({ dockOpen }),
  setShowRaw: (showRaw) => set({ showRaw }),
  select: (selected) => set({ selected, panel: selected ? "inspect" : get().panel }),
  selectConflict: (selectedConflict) => {
    const c = get().conflicts.find((x) => x.id === selectedConflict);
    set({ selectedConflict, selected: c ? c.fid : get().selected, panel: c ? "inspect" : get().panel });
  },

  toggleLayer: (id) =>
    set((s) => ({ layers: s.layers.map((l) => (l.id === id ? { ...l, on: !l.on } : l)) })),
  setOpacity: (id, v) =>
    set((s) => ({ layers: s.layers.map((l) => (l.id === id ? { ...l, opacity: v } : l)) })),

  playAlignment: () => {
    if (get().aligning) return;
    // The animation is meaningless with the legacy sheet hidden, so turn it
    // on for the duration whatever the operator had toggled.
    set((st) => ({
      aligning: true,
      showRaw: true,
      layers: st.layers.map((l) => (l.id === "legacy" ? { ...l, on: true } : l)),
    }));
    // Hold the misregistered state briefly so the viewer registers the problem,
    // then hand control to the map layer, which interpolates the transform.
    window.setTimeout(() => set({ showRaw: false }), 700);
    window.setTimeout(() => set({ aligning: false }), 2500);
  },

  runPipeline: async () => {
    const order = STAGES.map((s) => s.id);
    set({ done: [], running: null });
    for (const id of order) {
      set({ running: id });
      if (id === "georef") get().playAlignment();
      // Per-stage dwell is proportional to the real measured cost, so the
      // tracker reflects where the time actually goes.
      const m = get().metrics;
      const real = m?.stages.find((s) => s.name.toLowerCase().includes(id.slice(0, 5)));
      const ms = Math.min(1400, Math.max(260, (real?.seconds ?? 0.4) * 90));
      await new Promise((r) => setTimeout(r, id === "georef" ? 2400 : ms));
      set((s) => ({ done: [...s.done, id] }));
    }
    set({ running: null });
  },

  act: (id, action, reason) =>
    set((s) => {
      const conflicts = s.conflicts.map((c) =>
        c.id === id ? { ...c, status: action } : c);
      const prev = s.audit.length ? s.audit[s.audit.length - 1].hash : "genesis";
      const base = {
        ts: new Date().toISOString(),
        actor: "user" as const,
        action,
        target: id,
        reason,
      };
      return {
        conflicts,
        audit: [...s.audit, { ...base, hash: chainHash(prev, base) }],
      };
    }),

  load: async () => {
    try {
      const [reference, legacy, aligned, harmonized, govt, metrics, conflicts,
        plan, residuals, uncertainty, schema, change, resolutions,
        buildings, manifest] = await Promise.all([
        j<FC>("reference.geojson"),
        j<FC>("legacy.geojson"),
        j<FC>("aligned.geojson"),
        j<FC>("harmonized.geojson"),
        j<FC>("govt_land.geojson"),
        j<Metrics>("metrics.json"),
        j<Conflict[]>("conflicts.json"),
        j<SurveyPlan>("survey_plan.json"),
        j<Residual[]>("residuals.json"),
        j<UncertaintyGrid>("uncertainty.json"),
        j<SchemaResult>("schema.json"),
        j<ChangeResult>("change.json"),
        j<ResolutionCase[]>("resolutions.json"),
        j<FC>("buildings_t1.geojson"),
        j<ExportManifest>("export_manifest.json"),
      ]);

      const seed: AuditEntry[] = [];
      let prev = "genesis";
      const sys = [
        ["pipeline.run", "all", `engine build ${metrics.generated_at}`],
        ["georeference", "legacy", `coarse align, ${metrics.georef.inliers} inliers, RMSE ${metrics.georef.rmse_raw}→${metrics.georef.rmse_coarse} m`],
        ["match", "all", `F1 ${metrics.matching.f1}, ECE ${metrics.matching.ece}`],
        ["topology", "aligned", `${metrics.topology.total_before}→${metrics.topology.total_after} errors, area drift ${metrics.topology.area_drift_pct}%`],
        ["refuse_fill", "gaps", `${metrics.topology.refused_to_fill} parcel-sized holes flagged for survey, not filled`],
        ["schema.match", "legacy", `${schema.fields.filter(f => f.column).length}/7 columns mapped, area unit ${schema.area_unit}`],
        ["change.detect", "epoch t1", `${change.counts.new ?? 0} new, ${change.counts.demolished ?? 0} demolished, ${change.counts.heightened ?? 0} heightened`],
        ["encroachment", "govt_land", `${change.encroachments.length} flagged over ${change.encroached_sqm} m2`],
        ["targeting", "aoi", `${metrics.targeting.n_points} GCPs planned`],
      ];
      for (const [action, target, reason] of sys) {
        const base = { ts: metrics.generated_at, actor: "system" as const, action, target, reason };
        const hash = chainHash(prev, base);
        seed.push({ ...base, hash });
        prev = hash;
      }

      set({
        reference, legacy, aligned, harmonized, govt, metrics,
        conflicts: conflicts.map((c) => ({ ...c, status: "open" as const })),
        plan, residuals, uncertainty, schema, change, resolutions, buildings,
        manifest, audit: seed,
        layers: DEFAULT_LAYERS.map((l) =>
          l.id === "harmonized"
            ? { ...l, sub: `output · ${metrics.counts.legacy.toLocaleString()} parcels` }
            : l),
        loaded: true,
      });
    } catch (e: any) {
      set({ error: e?.message ?? String(e) });
    }
  },
}));
