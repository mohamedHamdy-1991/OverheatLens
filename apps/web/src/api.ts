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
  weather_summary?: Record<string, number | null> | null;
  summary_note?: string;
}

export interface WeatherSeries {
  name: string;
  dry_bulb: (number | null)[];
  daily_mean: number[];
  month_hour_matrix: (number | null)[][];
  monthly: { month: number; mean: number | null; max: number | null; min: number | null }[];
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
  daily_mean_outdoor: number[];
  cached: boolean;
}

export interface ValidationRow {
  section: string;
  cells: string[];
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
  analyze: (path: string, packId: string) =>
    fetch(
      `/api/analyze?weather_path=${encodeURIComponent(path)}&pack_id=${packId}`,
      { method: "POST" },
    ).then(async (r) => {
      const body = await r.json().catch(() => ({}));
      if (!r.ok) {
        throw new Error(
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail ?? r.status),
        );
      }
      return body as AnalyzeResult;
    }),
  validation: () => get<{ rows: ValidationRow[] }>("/api/validation").then((d) => d.rows),
};
