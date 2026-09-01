/* Typed client for the OverheatLens API. Types mirror what the core produces. */

export interface VersionInfo {
  core_version: string;
  energyplus_version: string | null;
}

export interface StandardsPassport {
  name: string;
  rule_pack: string;
  version: string;
  publisher: string;
  edition: string;
  source_status: string;
  source_refs: string[];
  weather_requirements: Record<string, unknown>;
  criteria_ids: string[];
  stages?: { id: string; description?: string }[];
  model_limits?: { id: string; clause: string; requirement: string }[];
}

export interface WeatherFileEntry {
  name: string;
  path: string;
  size_kb: number;
  compat_2017: string;
  compat_2026: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  path: string;
  city: string | null;
  description: string;
  n_zones: number | null;
  zone_names: string[];
  floor_area_m2: number | null;
  source: "template" | "upload";
}

export interface ModelUploadResult {
  model: ModelInfo;
  readiness: {
    status: string;
    rows: {
      check_id: string;
      title: string;
      severity: string;
      detected: string;
      required: string;
      why_it_matters: string;
      how_to_fix: string;
      source: string;
    }[];
  };
}

export interface WeatherIssue {
  code: string;
  severity: "error" | "warning" | "info";
  message: string;
}

export interface WeatherCheck {
  path: string;
  sha256: string;
  n_rows: number;
  status: "PASS" | "PASS_WITH_WARNINGS" | "FAIL";
  issues: WeatherIssue[];
  city?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
  elevation?: number;
  weather_summary?: Record<string, number | null> | null;
  summary_note?: string;
}

export interface RunEntry {
  run_id: string | null;
  weather: string;
  model: string | null;
  pack_id: string;
  overall: string | null;
}

export interface WeatherSeries {
  name: string;
  dry_bulb: (number | null)[];
  daily_mean: number[];
  month_hour_matrix: (number | null)[][];
  monthly: { month: number; mean: number | null; max: number | null; min: number | null }[];
  monthly_db: (number | null)[];
  monthly_rh: (number | null)[];
  monthly_ghi: (number | null)[];
  monthly_wind: (number | null)[];
  hdd15_5: (number | null)[];
  cdd18: (number | null)[];
}

export interface CriterionResult {
  criterion_id: string;
  rule_ref: string;
  metric_value: number | null;
  threshold: number;
  operator: string;
  units: string;
  passed: boolean | null;
  margin: number | null;
  status: "PASS" | "FAIL" | "NOT_EVALUATED" | "NOT_APPLICABLE" | "FLAG" | "NO_FLAG";
  verification_status: string;
  basis: Record<string, unknown>;
  notes: string[];
}

export interface RoomResult {
  room_id: string;
  room_type: string;
  passed: boolean;
  criteria: CriterionResult[];
}

export interface AnalyzeResult {
  model: { name: string; path: string };
  weather: { name: string; path: string };
  rule_pack: StandardsPassport;
  readiness: {
    status: string;
    rows: {
      check_id: string;
      title: string;
      severity: string;
      detected: string;
      required: string;
      why_it_matters: string;
      how_to_fix: string;
      source: string;
    }[];
  };
  run: {
    run_id: string;
    status: string;
    energyplus_version: string;
    err: { fatal: string[]; severe: string[]; warning_count: number };
  };
  result: {
    overall: "PASS" | "FAIL" | "INCOMPLETE";
    dwelling_category: string;
    rooms: RoomResult[];
  };
  series: Record<string, number[]>;
  rh: Record<string, number[] | null>;
  daily_mean_outdoor: number[];
  cached: boolean;
}

export interface ValidationRow {
  section: string;
  cells: string[];
}

export interface ComfortPayload {
  model: string;
  standard_edition: string;
  values: Record<string, number | boolean>;
  status: string;
  reason: string | null;
  provenance: Record<string, unknown>;
}

export interface ComfortRunZone {
  zone: string;
  adaptive_acceptable_pct: number | null;
  adaptive_hours_evaluated: number;
  adaptive_hours_excluded: number;
  mean_ppd: number | null;
  ppd_hours_evaluated: number;
  ppd_hours_excluded: number;
  max_top: number | null;
  reason: string | null;
}

export interface ComfortRunResult {
  assumptions: Record<string, string | number>;
  zones: ComfortRunZone[];
  note?: string;
  model: { name: string; path: string };
  weather: { name: string; path: string };
  run_id: string;
  computed_from: string;
}

export interface CompareFile {
  name: string;
  path: string;
  annual_mean: number;
  hottest: number;
  hours_over_26: number;
  degree_hours_26: number;
  daily_mean: number[];
}

async function get<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error(
      typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? r.status),
    );
  }
  return r.json();
}

async function post<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, { method: "POST", ...init });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error(
      typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? r.status),
    );
  }
  return body as T;
}

function upload(file: File): RequestInit {
  return {
    headers: { "Content-Type": "application/octet-stream" },
    body: file,
  };
}

export const api = {
  version: () => get<VersionInfo>("/api/version"),
  rulePacks: () =>
    get<{ packs: StandardsPassport[] }>("/api/rule-packs").then((d) => d.packs),
  weatherList: () =>
    get<{ weather_dir: string; files: WeatherFileEntry[] }>("/api/weather").then(
      (d) => d.files,
    ),
  weatherCheck: (path: string) =>
    get<WeatherCheck>(`/api/weather/check?path=${encodeURIComponent(path)}`),
  weatherSeries: (path: string) =>
    get<WeatherSeries>(`/api/weather/series?path=${encodeURIComponent(path)}`),
  uploadWeather: (file: File) =>
    post<WeatherCheck & { path: string }>(
      `/api/weather/upload?name=${encodeURIComponent(file.name)}`,
      upload(file),
    ),
  models: () => get<{ models: ModelInfo[] }>("/api/models").then((d) => d.models),
  uploadModel: (file: File) =>
    post<ModelUploadResult>(
      `/api/models/upload?name=${encodeURIComponent(file.name)}`,
      upload(file),
    ),
  analyze: (path: string, packId: string, modelPath?: string) =>
    post<AnalyzeResult>(
      `/api/analyze?weather_path=${encodeURIComponent(path)}&pack_id=${packId}` +
      (modelPath ? `&model_path=${encodeURIComponent(modelPath)}` : ""),
    ),
  comfortRun: (path: string, packId: string, modelPath?: string) =>
    post<ComfortRunResult>(
      `/api/comfort/run?weather_path=${encodeURIComponent(path)}&pack_id=${packId}` +
      (modelPath ? `&model_path=${encodeURIComponent(modelPath)}` : ""),
    ),
  report: (path: string, packId: string, modelPath?: string) =>
    fetch(
      `/api/report?weather_path=${encodeURIComponent(path)}&pack_id=${packId}` +
      (modelPath ? `&model_path=${encodeURIComponent(modelPath)}` : ""),
    ).then(async (r) => {
      if (!r.ok) throw new Error(`report request failed (${r.status})`);
      return r.text();
    }),
  validation: () => get<{ rows: ValidationRow[] }>("/api/validation").then((d) => d.rows),
  runs: () => get<{ runs: RunEntry[] }>("/api/runs").then((d) => d.runs),
  comfortPmv: (q: { tdb: number; tr: number; vr: number; rh: number; met: number; clo: number }) =>
    get<ComfortPayload>(`/api/comfort/pmv?${new URLSearchParams(Object.entries(q).map(([k, v]) => [k, String(v)]))}`),
  comfortAdaptive: (q: { tdb: number; tr: number; trm: number; v: number }) =>
    get<ComfortPayload>(`/api/comfort/adaptive?${new URLSearchParams(Object.entries(q).map(([k, v]) => [k, String(v)]))}`),
  comfortUtci: (q: { tdb: number; tr: number; v: number; rh: number }) =>
    get<ComfortPayload>(`/api/comfort/utci?${new URLSearchParams(Object.entries(q).map(([k, v]) => [k, String(v)]))}`),
  compare: (paths: string[]) =>
    get<{ files: CompareFile[] }>(`/api/compare?paths=${paths.map(encodeURIComponent).join(",")}`)
      .then((d) => d.files),
};
