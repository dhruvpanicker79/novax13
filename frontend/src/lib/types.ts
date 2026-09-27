export type FC = GeoJSON.FeatureCollection<GeoJSON.Polygon, any>;

export interface Metrics {
  generated_at: string;
  runtime_s: number;
  stages: { name: string; seconds: number }[];
  counts: {
    reference: number; legacy: number; buildings: number; govt: number;
    candidate_pairs: number; conflicts: number;
  };
  georef: {
    rmse_raw: number; rmse_coarse: number; displacement_m: number;
    rotation_deg: number; scale: number; inliers: number;
  };
  matching: {
    blocking_recall: number; f1: number; precision: number; recall: number;
    roc_auc: number; ece: number; brier: number;
    tp: number; fp: number; fn: number; tn: number;
    geometry_share: number;
    feature_importance: { name: string; gain: number }[];
    reliability: { lo: number; hi: number; n: number; mean_p: number | null; observed: number | null }[];
    coverage_at_99: number;
  };
  assignment: Record<string, number>;
  topology: {
    invalid_before: number; invalid_after: number;
    overlaps_before: number; overlaps_after: number;
    overlap_area_before: number; overlap_area_after: number;
    gaps_before: number; gaps_after: number;
    total_before: number; total_after: number;
    vertices_snapped: number; residual_slivers: number;
    refused_to_fill: number; harness_deleted: number;
    area_before: number; area_after: number; area_drift_pct: number;
  };
  targeting: {
    n_points: number; rmse_baseline: number; rmse_predicted: number;
    rmse_achieved: number | null; rmse_random: number | null;
    vs_random_pct: number | null; lengthscale_m: number;
  };
}

export interface Conflict {
  id: string; fid: string; ref: string[];
  class: string; confidence: number; detail: string;
  area_sqm: number; khasra: string | null; owner: string | null;
  at: [number, number]; status: "open" | "accepted" | "rejected" | "escalated" | "survey";
}

export interface SurveyPoint {
  rank: number; at: [number, number];
  marginal_gain: number; rmse_after_m: number; rmse_delta_m: number;
  parcel_fid: string | null; reason: string;
  utm_x: number; utm_y: number;
}

export interface SurveyPlan {
  points: SurveyPoint[];
  rmse_before: number; rmse_after: number;
  achieved: number | null; achieved_random: number | null;
  baseline: number;
  gain_curve: [number, number][];
  hyper: string; n_parcels: number; stopped_because: string;
}

export interface Residual {
  from: [number, number]; to: [number, number]; m: number; fid: string;
}

export interface UncertaintyGrid {
  grid: [number, number, number, number][]; // lon, lat, sd_before, sd_after
  n: number;
  bounds: [number, number, number, number];
}

export interface AuditEntry {
  ts: string; actor: "system" | "user"; action: string;
  target: string; reason: string; hash: string;
}

export type StageId =
  | "ingest" | "schema" | "validate" | "georef" | "blocking"
  | "match" | "assign" | "topology" | "conflicts" | "uncertainty" | "targeting";

export const STAGES: { id: StageId; label: string }[] = [
  { id: "ingest", label: "Ingest" },
  { id: "schema", label: "Schema" },
  { id: "validate", label: "Validate" },
  { id: "georef", label: "Georeference" },
  { id: "blocking", label: "Blocking" },
  { id: "match", label: "Match" },
  { id: "assign", label: "Assign" },
  { id: "topology", label: "Topology" },
  { id: "conflicts", label: "Conflicts" },
  { id: "uncertainty", label: "Uncertainty" },
  { id: "targeting", label: "Targeting" },
];
