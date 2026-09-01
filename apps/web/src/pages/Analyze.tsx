import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  api,
  type AnalyzeResult,
  type ComfortRunResult,
  type CriterionResult,
  type ModelInfo,
  type WeatherFileEntry,
  type StandardsPassport,
} from "../api";
import { Figure, StatusPill } from "../components";
import { useChart } from "../charts";

const PACKS = [
  { id: "uk_tm59_2017", label: "TM59:2017 — legacy / comparison" },
  { id: "uk_tm59_2026", label: "TM59:2026 — current design guidance" },
  { id: "uk_part_o_dynamic", label: "Part O — statutory dynamic route" },
  { id: "uk_tm52", label: "TM52 — adaptive (non-domestic criteria)" },
];

const DEMO_OPTION = { path: "", label: "Synthetic two-zone dwelling (bundled demo)" };

export function Analyze() {
  const [files, setFiles] = useState<WeatherFileEntry[] | null>(null);
  const [weather, setWeather] = useState<string>("");
  const [models, setModels] = useState<ModelInfo[] | null>(null);
  const [modelPath, setModelPath] = useState<string>(DEMO_OPTION.path);
  const [params] = useSearchParams();
  const [pack, setPack] = useState("uk_tm59_2017");
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [comfort, setComfort] = useState<ComfortRunResult | null>(null);
  const [comfortError, setComfortError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [uploadingModel, setUploadingModel] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [packsInfo, setPacksInfo] = useState<StandardsPassport[]>([]);
  const idfInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.weatherList().then((fs) => {
      setFiles(fs);
      const pick = fs.find((f) => f.name === "Leeds_DSY1_2020High50_.epw") ?? fs[0];
      if (pick) setWeather(pick.path);
    });
    api.rulePacks().then(setPacksInfo);
    api.models().then((ms) => {
      setModels(ms);
      const wanted = params.get("model");
      if (wanted && ms.some((m) => m.path === wanted)) setModelPath(wanted);
    }).catch(() => setModels([]));
  }, []);

  const run = () => {
    setRunning(true);
    setError(null);
    setComfort(null);
    setComfortError(null);
    api.analyze(weather, pack, modelPath || undefined)
      .then((r) => {
        setResult(r);
        return api
          .comfortRun(weather, pack, modelPath || undefined)
          .then(setComfort)
          .catch((e) => setComfortError(String(e.message ?? e)));
      })
      .catch((e) => setError(String(e.message ?? e)))
      .finally(() => setRunning(false));
  };

  const uploadIdf = (file: File) => {
    setUploadingModel(true);
    setError(null);
    api.uploadModel(file)
      .then((saved) =>
        api.models().then((ms) => {
          setModels(ms);
          setModelPath(saved.model.path);
        }))
      .catch((e) => setError(String(e.message ?? e)))
      .finally(() => setUploadingModel(false));
  };

  const download = (name: string, data: BlobPart, mime: string) => {
    const url = URL.createObjectURL(new Blob([data], { type: mime }));
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
  };

  const saveReport = () => {
    setSaving(true);
    setError(null);
    api.report(weather, pack, modelPath || undefined)
      .then((html) => {
        download(`overheatlens_report_${result?.run.run_id}.html`, html, "text/html");
      })
      .catch((e) => setError(String(e.message ?? e)))
      .finally(() => setSaving(false));
  };

  const exportJson = () => {
    if (!result) return;
    download(
      `overheatlens_results_${result.run.run_id}.json`,
      JSON.stringify(result, null, 2),
      "application/json",
    );
  };

  const selectedPack = packsInfo.find((p) => p.rule_pack === pack);

  return (
    <>
      <h1 className="page-title">Analyze</h1>
      <p className="page-intro">
        Run a dwelling model through the real pipeline: readiness checks, an official
        EnergyPlus simulation, and a versioned standards evaluation. Start with the
        bundled synthetic dwelling, pick a Leeds archetype template, or upload your own IDF.
      </p>

      <section style={{ marginTop: 24, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 18, maxWidth: 860 }}>
        <div>
          <label htmlFor="std" style={{ fontFamily: "var(--font-mono)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--muted-ink)" }}>
            Standard
          </label>
          <select id="std" value={pack} onChange={(e) => setPack(e.target.value)}
            style={{ display: "block", width: "100%", marginTop: 6, padding: "9px 12px", border: "1px solid var(--line-strong)", borderRadius: 6, background: "var(--surface)", font: "inherit", color: "var(--ink)" }}>
            {PACKS.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
          </select>
          {selectedPack && (
            <p style={{ marginTop: 8, fontSize: 12.5, color: "var(--muted-ink)" }}>
              {selectedPack.name} · edition {selectedPack.edition} ·{" "}
              <StatusPill status={selectedPack.source_status} />
            </p>
          )}
        </div>
        <div>
          <label htmlFor="wf" style={{ fontFamily: "var(--font-mono)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--muted-ink)" }}>
            Weather file
          </label>
          <select id="wf" value={weather} onChange={(e) => setWeather(e.target.value)}
            style={{ display: "block", width: "100%", marginTop: 6, padding: "9px 12px", border: "1px solid var(--line-strong)", borderRadius: 6, background: "var(--surface)", font: "inherit", color: "var(--ink)" }}>
            {files?.map((f) => <option key={f.path} value={f.path}>{f.name}</option>)}
          </select>
          <p style={{ marginTop: 8, fontSize: 12.5, color: "var(--muted-ink)" }}>
            Need to vet a file first? <Link to="/weather">Weather Lab →</Link>
          </p>
        </div>
        <div>
          <label htmlFor="mdl" style={{ fontFamily: "var(--font-mono)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--muted-ink)" }}>
            Model
          </label>
          <select id="mdl" value={modelPath} onChange={(e) => setModelPath(e.target.value)}
            style={{ display: "block", width: "100%", marginTop: 6, padding: "9px 12px", border: "1px solid var(--line-strong)", borderRadius: 6, background: "var(--surface)", font: "inherit", color: "var(--ink)" }}>
            <option value={DEMO_OPTION.path}>{DEMO_OPTION.label}</option>
            {models && models.some((m) => m.source === "template") && (
              <optgroup label="Leeds archetype templates">
                {models.filter((m) => m.source === "template").map((m) => (
                  <option key={m.id} value={m.path}>
                    {m.name} ({m.n_zones ?? "?"} zones)
                  </option>
                ))}
              </optgroup>
            )}
            {models && models.some((m) => m.source === "upload") && (
              <optgroup label="Uploaded models">
                {models.filter((m) => m.source === "upload").map((m) => (
                  <option key={m.id} value={m.path}>
                    {m.name} ({m.n_zones ?? "?"} zones)
                  </option>
                ))}
              </optgroup>
            )}
          </select>
          <div style={{ marginTop: 8, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            <button className="btn secondary" onClick={() => idfInput.current?.click()} disabled={uploadingModel}>
              {uploadingModel ? "Uploading…" : "Upload IDF"}
            </button>
            <input
              ref={idfInput}
              type="file"
              accept=".idf"
              style={{ display: "none" }}
              aria-label="Upload an IDF model file"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) uploadIdf(f);
                e.target.value = "";
              }}
            />
            <span style={{ fontSize: 12.5, color: "var(--muted-ink)" }}>
              Saved locally (max 20 MB) and checked on arrival.
            </span>
          </div>
        </div>
      </section>

      <div style={{ marginTop: 20, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <button className="btn" onClick={run} disabled={running || !weather}>
          {running ? "Simulating…" : result ? "Re-run assessment" : "Run assessment"}
        </button>
        {result && !running && (
          <>
            <button className="btn secondary" onClick={saveReport} disabled={saving}>
              {saving ? "Preparing…" : "Save report (HTML)"}
            </button>
            <button className="btn secondary" onClick={exportJson}>
              Export results (JSON)
            </button>
          </>
        )}
        {running && (
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--muted-ink)" }}>
            readiness → EnergyPlus {""}→ standards evaluation — usually a few seconds
          </span>
        )}
      </div>
      {result && !running && (
        <p style={{ marginTop: 8, fontFamily: "var(--font-mono)", fontSize: 11.5, color: "var(--muted-ink)" }}>
          Report is self-contained HTML — print to PDF from your browser.
        </p>
      )}

      {error && (
        <div className="note warn" style={{ marginTop: 18 }}>
          <strong>Run failed.</strong> {error}
        </div>
      )}

      {result && <Results r={result} comfort={comfort} comfortError={comfortError} running={running} />}
    </>
  );
}

function Results({ r, comfort, comfortError, running }: {
  r: AnalyzeResult;
  comfort: ComfortRunResult | null;
  comfortError: string | null;
  running: boolean;
}) {
  const modelName = r.model.name.length > 26 ? `${r.model.name.slice(0, 26)}…` : r.model.name;
  return (
    <>
      <section style={{ marginTop: 30 }}>
        <div className="metrics" aria-label="Assessment summary">
          <div className="metric" style={{ flex: "0 0 170px" }}>
            <span className="m-val"><StatusPill status={r.result.overall} /></span>
            <div className="m-label">dwelling overall</div>
          </div>
          <div className="metric">
            <span className="m-val"><StatusPill status={r.readiness.status} /></span>
            <div className="m-label">model readiness</div>
          </div>
          <div className="metric">
            <span className="m-val mono" style={{ fontSize: 14 }}>{r.run.run_id}</span>
            <div className="m-label">run id</div>
          </div>
          <div className="metric">
            <span className="m-val" style={{ fontSize: 16 }}>E+ {r.run.energyplus_version}</span>
            <div className="m-label">engine</div>
          </div>
          <div className="metric">
            <span className="m-val" style={{ fontSize: 15 }} title={r.model.name}>{modelName}</span>
            <div className="m-label">model</div>
          </div>
          <div className="metric">
            <span className="m-val" style={{ fontSize: 16 }}>{r.weather.name.replace(/_/g, " ").slice(0, 18)}…</span>
            <div className="m-label">weather</div>
          </div>
        </div>
        <p style={{ marginTop: 8, fontFamily: "var(--font-mono)", fontSize: 11.5, color: "var(--muted-ink)" }}>
          rule pack {r.rule_pack.rule_pack} v{r.rule_pack.version} · category {r.result.dwelling_category} ·
          {" "}{r.cached ? "served from this session’s run cache" : "freshly simulated"} ·
          {" "}errors: {r.run.err.fatal.length} fatal, {r.run.err.severe.length} severe, {r.run.err.warning_count} warnings
        </p>
      </section>

      <section className="more-above">
        <h2 className="section-h">Criterion results</h2>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Room</th>
                <th>Type</th>
                <th>Criterion</th>
                <th>Rule reference</th>
                <th>Result</th>
                <th>Metric</th>
                <th>Threshold</th>
              </tr>
            </thead>
            <tbody>
              {r.result.rooms.flatMap((room) =>
                room.criteria.map((c: CriterionResult) => (
                  <tr key={room.room_id + c.criterion_id}>
                    <td>{room.room_id}</td>
                    <td>{room.room_type}</td>
                    <td className="mono">{c.criterion_id}</td>
                    <td style={{ color: "var(--muted-ink)", fontSize: 12.5 }}>{c.rule_ref}</td>
                    <td><StatusPill status={c.status} /></td>
                    <td className="mono">{c.metric_value ?? "—"} {c.units}</td>
                    <td className="mono">
                      {c.operator} {c.threshold} {c.units}
                    </td>
                  </tr>
                )),
              )}
            </tbody>
          </table>
        </div>
        <p style={{ marginTop: 8, fontSize: 12.5, color: "var(--muted-ink)", maxWidth: "90ch" }}>
          Every result above is computed by the core package from the EnergyPlus run; the
          rule reference names the clause each threshold was verified against. A dwelling
          passes only when every applicable criterion passes — unevaluated criteria make
          the result INCOMPLETE, never a pass.
        </p>
      </section>

      <section className="more-above">
        <h2 className="section-h">Comfort from this run</h2>
        {comfortError && (
          <div className="note warn">
            <strong>Comfort could not be computed for this run.</strong> {comfortError}
          </div>
        )}
        {!comfort && !comfortError && !running && (
          <p style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--muted-ink)" }}>
            computing comfort from this run…
          </p>
        )}
        {comfort && <ComfortTable c={comfort} />}
      </section>

      <section className="more-above">
        <h2 className="section-h">Simulated temperatures</h2>
        <RoomFigure r={r} />
      </section>

      <section className="more-above">
        <h2 className="section-h">Model readiness — every finding explained</h2>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Check</th>
                <th>Verdict</th>
                <th>Detected</th>
                <th>Why it matters</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {r.readiness.rows.map((row) => (
                <tr key={row.check_id}>
                  <td className="mono">{row.check_id}</td>
                  <td><StatusPill status={row.severity === "ok" ? "PASS" : row.severity} /></td>
                  <td style={{ maxWidth: 260 }}>{row.detected}</td>
                  <td style={{ color: "var(--muted-ink)", maxWidth: 320 }}>{row.why_it_matters}</td>
                  <td style={{ color: "var(--muted-ink)", fontSize: 12 }}>{row.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="more-above">
        <h2 className="section-h">Provenance</h2>
        <div className="table-wrap">
          <table className="data">
            <tbody>
              <tr><td className="mono">model</td><td>{r.model.name}</td></tr>
              <tr><td className="mono">weather</td><td>{r.weather.name}</td></tr>
              <tr><td className="mono">energyplus</td><td className="mono">{r.run.energyplus_version}</td></tr>
              <tr><td className="mono">rule pack</td><td className="mono">{r.rule_pack.rule_pack} v{r.rule_pack.version} — {r.rule_pack.name}</td></tr>
              <tr>
                <td className="mono">weather requirement</td>
                <td style={{ fontSize: 12.5 }}>
                  {String((r.rule_pack.weather_requirements as Record<string, unknown>)?.recommended_minimum ?? "—")}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function ComfortTable({ c }: { c: ComfortRunResult }) {
  const a = c.assumptions;
  const withReason = c.zones.filter((z) => z.reason);
  const fmt = (v: number | null, unit: string) =>
    v === null ? "—" : `${v.toFixed(1)}${unit}`;
  return (
    <Figure
      figNo="TAB 1"
      caption="comfort indices computed from this run’s simulated hourly temperatures"
      meta={<span>pythermalcomfort {String(a.library_version ?? "")}</span>}
    >
      {c.note && (
        <p style={{ margin: 0, fontSize: 13, color: "var(--muted-ink)" }}>{c.note}</p>
      )}
      {c.zones.length > 0 && (
        <table className="data">
          <thead>
            <tr>
              <th>Zone</th>
              <th>Adaptive acceptable · Cat II</th>
              <th>Mean PPD</th>
              <th>Max Top</th>
            </tr>
          </thead>
          <tbody>
            {c.zones.map((z) => (
              <tr key={z.zone}>
                <td>{z.zone}</td>
                <td className="mono">
                  {fmt(z.adaptive_acceptable_pct, "%")}
                  {z.adaptive_hours_excluded > 0 && (
                    <span style={{ color: "var(--muted-ink)", fontSize: 11 }}>
                      {" "}({z.adaptive_hours_excluded} h excluded)
                    </span>
                  )}
                </td>
                <td className="mono">
                  {fmt(z.mean_ppd, "%")}
                  {z.ppd_hours_excluded > 0 && (
                    <span style={{ color: "var(--muted-ink)", fontSize: 11 }}>
                      {" "}({z.ppd_hours_excluded} h excluded)
                    </span>
                  )}
                </td>
                <td className="mono">{fmt(z.max_top, " °C")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p style={{ margin: "10px 0 0", fontSize: 12.5, color: "var(--muted-ink)", maxWidth: "96ch" }}>
        Stated assumptions: met {a.met} · clo {a.clo} (summer ensemble) · air speed{" "}
        {a.air_speed_m_s} m/s · occupied hours 9 am–10 pm (hour-ending 10–22) · window{" "}
        {String(a.assessment_window ?? "May–September")} · adaptive: {a.adaptive_standard}{" "}
        (Trm from EPW daily means) · PPD: {a.ppd_standard}.
      </p>
      <p style={{ margin: "6px 0 0", fontSize: 12, color: "var(--muted-ink)", maxWidth: "96ch" }}>
        {c.computed_from}. Comfort mathematics come from the wrapped library only — nothing
        is recomputed here; hours it cannot evaluate are excluded and counted, never
        extrapolated. Relative humidity: {String(a.rh ?? "harvested from the same run")}.
      </p>
      {withReason.length > 0 && (
        <p style={{ margin: "6px 0 0", fontSize: 12, color: "var(--muted-ink)" }}>
          {withReason.map((z) => `${z.zone}: ${z.reason}`).join(" · ")}
        </p>
      )}
    </Figure>
  );
}

function RoomFigure({ r }: { r: AnalyzeResult }) {
  const ref = useRef<HTMLDivElement>(null);
  const zones = Object.keys(r.series);
  const outdoor = r.daily_mean_outdoor;

  const week = 24 * 7;
  // centre the window on the hottest outdoor week (real data, RULE 28)
  const start = (() => {
    let best = 0, bestMean = -Infinity;
    for (let i = 0; i + week <= outdoor.length; i += 24) {
      const mean = outdoor.slice(i, i + week).reduce((a, b) => a + b, 0) / week;
      if (mean > bestMean) { bestMean = mean; best = i; }
    }
    return Math.max(0, best - 24 * 3);
  })();

  useChart(ref, {
    grid: { left: 44, right: 12, top: 28, bottom: 26 },
    legend: {
      top: 0, left: 0, icon: "rect", itemWidth: 10, itemHeight: 3,
      textStyle: { fontFamily: "IBM Plex Mono", fontSize: 10.5, color: "#5e686e" },
    },
    xAxis: {
      type: "category",
      data: Array.from({ length: week }, (_, i) => {
        const h = (start + i) % 24;
        const d = Math.floor((start + i) / 24) + 1;
        return h === 0 && d % 2 === 1 ? `day ${d}` : "";
      }),
      axisLabel: { color: "#5e686e", fontFamily: "IBM Plex Mono", fontSize: 9.5 },
      axisLine: { lineStyle: { color: "#b7b8b3" } }, axisTick: { show: false },
    },
    yAxis: {
      type: "value", name: "°C", nameTextStyle: { fontFamily: "IBM Plex Mono", fontSize: 10, color: "#5e686e" },
      axisLabel: { color: "#5e686e", fontFamily: "IBM Plex Mono", fontSize: 10 },
      splitLine: { lineStyle: { color: "#eae8e2" } },
    },
    series: [
      {
        name: "outdoor (daily mean)", type: "line" as const, symbol: "none" as const,
        data: outdoor.slice(start, start + week),
        lineStyle: { color: "#86a9b3", width: 1.4 },
      },
      ...zones.map((z, i) => ({
        name: `${z} Top`,
        type: "line" as const, symbol: "none" as const, showSymbol: false,
        data: r.series[z].slice(start, start + week),
        lineStyle: { color: ["#d4553d", "#e58a3a"][i % 2], width: 1.6 },
      })),
    ],
    tooltip: { trigger: "axis", confine: true, valueFormatter: (v: unknown) => `${Number(v).toFixed(1)} °C` },
  }, [r]);

  return (
    <Figure figNo="FIG 5"
      caption="operative temperature during the hottest outdoor week (hourly, real run output)"
      meta={<span>{zones.join(" · ")}</span>}>
      <div ref={ref} style={{ height: 280 }} role="img"
        aria-label="Line chart of outdoor mean and room operative temperatures over the hottest week" />
    </Figure>
  );
}
