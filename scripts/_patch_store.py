"""Wire the new artifacts (schema, change, resolutions, epoch t1) into the
frontend store, layer list and dock tab set."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "frontend", "src", "lib", "store.ts")
s = open(P, encoding="utf-8").read()

if "ChangeResult" in s:
    print("store already wired")
    raise SystemExit(0)

s = s.replace(
    'import type {\n  AuditEntry, Conflict, FC, Metrics, Residual, StageId, SurveyPlan,\n  UncertaintyGrid,\n} from "./types";',
    'import type {\n  AuditEntry, ChangeResult, Conflict, FC, Metrics, Residual,\n  ResolutionCase, SchemaResult, StageId, SurveyPlan, UncertaintyGrid,\n} from "./types";')

s = s.replace(
    '  | "residuals" | "confidence" | "conflicts" | "survey" | "uncertainty";',
    '  | "residuals" | "confidence" | "conflicts" | "survey" | "uncertainty"\n'
    '  | "buildings" | "change" | "encroach";')

s = s.replace(
    '  { id: "govt", label: "Government land", sub: "encroachment basis", on: true, opacity: 0.8 },',
    '  { id: "govt", label: "Government land", sub: "encroachment basis", on: true, opacity: 0.8 },\n'
    '  { id: "encroach", label: "Encroachment", sub: "built on public land", on: true, opacity: 1 },\n'
    '  { id: "change", label: "Change events", sub: "2023 -> 2025", on: false, opacity: 1 },\n'
    '  { id: "buildings", label: "Building footprints", sub: "epoch t1", on: false, opacity: 0.9 },')

s = s.replace(
    "  residuals: Residual[];\n  uncertainty?: UncertaintyGrid;",
    "  residuals: Residual[];\n  uncertainty?: UncertaintyGrid;\n"
    "  schema?: SchemaResult;\n  change?: ChangeResult;\n"
    "  resolutions: ResolutionCase[];\n  buildings?: FC;")

s = s.replace(
    '  dockTab: "conflicts" | "survey" | "validate" | "audit" | "metrics";',
    '  dockTab: "conflicts" | "schema" | "survey" | "change" | "resolve"\n'
    '         | "validate" | "audit" | "metrics";')

s = s.replace(
    "  conflicts: [],\n  residuals: [],",
    "  conflicts: [],\n  residuals: [],\n  resolutions: [],")

s = s.replace(
    """      const [reference, legacy, aligned, harmonized, govt, metrics, conflicts,
        plan, residuals, uncertainty] = await Promise.all([""",
    """      const [reference, legacy, aligned, harmonized, govt, metrics, conflicts,
        plan, residuals, uncertainty, schema, change, resolutions,
        buildings] = await Promise.all([""")

s = s.replace(
    '        j<UncertaintyGrid>("uncertainty.json"),\n      ]);',
    '        j<UncertaintyGrid>("uncertainty.json"),\n'
    '        j<SchemaResult>("schema.json"),\n'
    '        j<ChangeResult>("change.json"),\n'
    '        j<ResolutionCase[]>("resolutions.json"),\n'
    '        j<FC>("buildings_t1.geojson"),\n      ]);')

s = s.replace(
    '        ["targeting", "aoi", `${metrics.targeting.n_points} GCPs planned`],',
    '        ["schema.match", "legacy", `${schema.fields.filter(f => f.column).length}/7 columns mapped, area unit ${schema.area_unit}`],\n'
    '        ["change.detect", "epoch t1", `${change.counts.new ?? 0} new, ${change.counts.demolished ?? 0} demolished, ${change.counts.heightened ?? 0} heightened`],\n'
    '        ["encroachment", "govt_land", `${change.encroachments.length} flagged over ${change.encroached_sqm} m2`],\n'
    '        ["targeting", "aoi", `${metrics.targeting.n_points} GCPs planned`],')

s = s.replace(
    "        plan, residuals, uncertainty, audit: seed,",
    "        plan, residuals, uncertainty, schema, change, resolutions, buildings,\n"
    "        audit: seed,")

open(P, "w", encoding="utf-8").write(s)
print("store.ts wired")
