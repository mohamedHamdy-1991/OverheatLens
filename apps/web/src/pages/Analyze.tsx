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
import { Figure, StatusPill, StandardBadge, ResultVerdict, MarginBar, ProvenanceDrawer, MethodNote, PageCover } from "../components";
import { useChart, NB_INK, NB_SERIES, nbBase, nbCategoryAxis, nbValueAxis, nbThresholdLine } from "../charts";
import { ExportBar } from "../ExportBar";

const PACKS = [
  { id: "uk_tm59_2017", label: "TM59:2017 — CIBSE domestic overheating" },
  { id: "uk_tm59_2026", label: "TM59:2026 — current (research-tagged weather)" },
  { id: "uk_part_o_dynamic", label: "Part O — statutory dynamic route" },
  { id: "uk_tm52", label: "TM52 — adaptive criteria" },
];

const DEMO_OPTION = { path: "", label: "Synthetic two-zone dwelling (bundled demo)" };

type Stage = "idle" | "validating" | "simulating" | "harvesting" | "evaluating" | "done";

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
  const [stage, setStage] = useState<Stage>("idle");
  const [saving, setSaving] = useState(false);
  const [uploadingModel, setUploadingModel] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [packsInfo, setPacksInfo] = useState<StandardsPassport[]>([]);
  const idfInput = useRef<HTMLInputElement>(null);
  const running = stage !== "idle" && stage !== "done";

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
    const runId = params.get("run");
    if (runId) {
      setStage("evaluating");
      api.runDetail(runId)
        .then((d) => {
          setResult(d.payload);
          setWeather(d.payload.weather.path);
          setPack(d.payload.rule_pack.rule_pack);
          setModelPath(d.payload.model.path);
          setStage("done");
          return api.comfortRun(d.payload.weather.path, d.payload.rule_pack.rule_pack, d.payload.model.path)
            .then(setComfort)
            .catch((e) => setComfortError(String(e.message ?? e)));
        })
        .catch((e) => { setError(String(e.message ?? e)); setStage("idle"); });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const run = () => {
    setStage("validating");
    setError(null);
    setComfort(null);
    setComfortError(null);
    // Stages are honest UI states around one awaited pipeline call — the
    // sequence is real (readiness → E+ → harvest → evaluate) but the timing
    // shown is indicative, never a fabricated percentage.
    setStage("simulating");
    api.analyze(weather, pack, modelPath || undefined)
      .then((r) => {
        setStage("evaluating");
        setResult(r);
        setStage("done");
        return api
          .comfortRun(weather, pack, modelPath || undefined)
          .then(setComfort)
          .catch((e) => setComfortError(String(e.message ?? e)));
      })
      .catch((e) => { setError(String(e.message ?? e)); setStage("idle"); });
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
  const modelName = (p: string) =>
    p ? (models?.find((m) => m.path === p)?.name ?? p.split("/").pop() ?? p) : "Synthetic two-zone dwelling";

  return (
    <>
      <PageCover img="cover-analyze.png" alt="" />
      <section className="headline-row">
        <div>
          <h1 className="page-title">Analyze</h1>
          <p className="page-intro">
            One experiment: <strong>building + weather + standard → EnergyPlus →
            evidence</strong>. Configure the four stages, check readiness, run.
          </p>
        </div>
        {result && (
          <div className="context-bar" style={{ margin: 0 }}>
            <div className="context-cell"><small>MODEL</small><strong>{modelName(modelPath).slice(0, 22)}</strong></div>
            <div className="context-cell"><small>WEATHER</small><strong>{result.weather.name.slice(0, 22)}</strong></div>
            <div className="context-cell"><small>STANDARD</small><strong>{pack}</strong></div>
            <div className="context-cell"><small>RUN</small><strong>{result.run.run_id}</strong></div>
          </div>
        )}
      </section>

      {/* ---- 4-stage configuration ---- */}
      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16, marginBottom: 16 }}>
        <div className="nb-card" style={{ padding: 18 }}>
          <span className="nb-chip">STAGE 1 · BUILDING</span>
          <div className="field" style={{ marginTop: 12, marginBottom: 0 }}>
            <label htmlFor="mdl">Research archetype · template · upload</label>
            <select id="mdl" className="nb-input" value={modelPath} onChange={(e) => setModelPath(e.target.value)}>
              <option value={DEMO_OPTION.path}>{DEMO_OPTION.label}</option>
              {models && models.some((m) => m.source === "research") && (
                <optgroup label="Research archetypes (DEEP / measured)">
                  {models.filter((m) => m.source === "research").map((m) => (
                    <option key={m.id} value={m.path}>{m.name} ({m.n_zones ?? "?"} zones)</option>
                  ))}
                </optgroup>
              )}
              {models && models.some((m) => m.source === "template") && (
                <optgroup label="Generic templates">
                  {models.filter((m) => m.source === "template").map((m) => (
                    <option key={m.id} value={m.path}>{m.name} ({m.n_zones ?? "?"} zones)</option>
                  ))}
                </optgroup>
              )}
              {models && models.some((m) => m.source === "upload") && (
                <optgroup label="Your uploaded models">
                  {models.filter((m) => m.source === "upload").map((m) => (
                    <option key={m.id} value={m.path}>{m.name} ({m.n_zones ?? "?"} zones)</option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>
          <div style={{ marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button className="nb-btn secondary" style={{ minHeight: 40 }} onClick={() => idfInput.current?.click()} disabled={uploadingModel}>
              {uploadingModel ? "UPLOADING…" : "+ UPLOAD IDF"}
            </button>
            <input ref={idfInput} type="file" accept=".idf" style={{ display: "none" }}
              aria-label="Upload an IDF model file"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadIdf(f); e.target.value = ""; }} />
            {modelPath && <Link className="nb-btn secondary" style={{ minHeight: 40 }} to={`/atlas?model=${encodeURIComponent(modelPath)}`}>MODEL DOSSIER ›</Link>}
          </div>
        </div>

        <div className="nb-card" style={{ padding: 18 }}>
          <span className="nb-chip">STAGE 2 · WEATHER</span>
          <div className="field" style={{ marginTop: 12, marginBottom: 0 }}>
            <label htmlFor="wf">Library EPW · uploaded EPW</label>
            <select id="wf" className="nb-input" value={weather} onChange={(e) => setWeather(e.target.value)}>
              {files?.map((f) => <option key={f.path} value={f.path}>{f.name}</option>)}
            </select>
          </div>
          <p className="hint" style={{ fontSize: 12, marginTop: 10 }}>
            Every file passes QC before simulation. <Link to="/weather">Vet it in Weather Lab →</Link>
          </p>
        </div>

        <div className="nb-card" style={{ padding: 18 }}>
          <span className="nb-chip">STAGE 3 · STANDARD</span>
          <div className="field" style={{ marginTop: 12, marginBottom: 0 }}>
            <label htmlFor="std">Versioned rule pack</label>
            <select id="std" className="nb-input" value={pack} onChange={(e) => setPack(e.target.value)}>
              {PACKS.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
            </select>
          </div>
          {selectedPack && (
            <p style={{ marginTop: 10, fontSize: 12 }}>
              <StandardBadge packId={selectedPack.rule_pack} version={selectedPack.version} />{" "}
              {selectedPack.edition}
            </p>
          )}
        </div>

        <div className="nb-card" style={{ padding: 18, background: "var(--nb-ink)", color: "var(--nb-surface)" }}>
          <span className="nb-chip">STAGE 4 · RUN</span>
          <RunStages stage={stage} />
          <button className="nb-btn" style={{ width: "100%", justifyContent: "center", marginTop: 12 }}
            onClick={run} disabled={running || !weather}>
            {running ? "ENERGYPLUS RUNNING…" : result ? "↻ RE-RUN ENERGYPLUS" : "▶ RUN ENERGYPLUS"}
          </button>
          {result && !running && (
            <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
              <button className="nb-btn secondary" style={{ minHeight: 40 }} onClick={saveReport} disabled={saving}>
                {saving ? "…" : "REPORT"}
              </button>
              <button className="nb-btn secondary" style={{ minHeight: 40 }} onClick={exportJson}>JSON</button>
              <a className="nb-btn secondary" style={{ minHeight: 40 }} href={api.bundleUrl(result.run.run_id)}>BUNDLE ↓</a>
            </div>
          )}
        </div>
      </section>

      {error && (
        <div className="note warn" style={{ marginBottom: 16 }}>
          <strong>ENERGYPLUS SIMULATION FAILED.</strong> {error}
          <div style={{ marginTop: 8, display: "flex", gap: 8 }}>
            {modelPath && <Link className="nb-btn secondary" style={{ minHeight: 36 }} to={`/atlas?model=${encodeURIComponent(modelPath)}`}>OPEN READINESS CHECK</Link>}
          </div>
        </div>
      )}

      {result && <Results r={result} comfort={comfort} comfortError={comfortError} running={running} packId={pack} />}
    </>
  );
}

function RunStages({ stage }: { stage: Stage }) {
  const steps: { id: Stage; label: string }[] = [
    { id: "validating", label: "MODEL VALIDATION" },
    { id: "simulating", label: "ENERGYPLUS" },
    { id: "harvesting", label: "OUTPUT PARSING" },
    { id: "evaluating", label: "STANDARD EVALUATION" },
  ];
  const order: Stage[] = ["idle", "validating", "simulating", "harvesting", "evaluating", "done"];
  const idx = order.indexOf(stage);
  return (
    <ul style={{ listStyle: "none", margin: "12px 0 0", padding: 0, fontFamily: "var(--nb-font-mono)", fontSize: 11.5 }}>
      {steps.map((s) => {
        const si = order.indexOf(s.id);
        const state = stage === "done" || idx > si ? "✓" : idx === si ? "●" : "○";
        return <li key={s.id} style={{ padding: "3px 0", opacity: state === "○" ? 0.55 : 1 }}>{state} {s.label}</li>;
      })}
    </ul>
  );
}

function Results({ r, comfort, comfortError, running, packId }: {
  r: AnalyzeResult;
  comfort: ComfortRunResult | null;
  comfortError: string | null;
  running: boolean;
  packId: string;
}) {
  const verdict = r.result.overall === "PASS" ? "PASS" : r.result.overall === "FAIL" ? "FAIL" : "INCOMPLETE";
  const margins = r.result.rooms.flatMap((room) =>
    room.criteria
      .filter((c) => c.metric_value !== null && c.passed !== null)
      .map((c) => ({ room: room.room_id, c })));
  return (
    <>
      <section style={{ marginTop: 8 }}>
        <ResultVerdict verdict={verdict}
          detail={<>
            <strong>{r.model.name}</strong> × <strong>{r.weather.name}</strong> · {packId} ·
            dwelling category {r.result.dwelling_category}.{" "}
            {r.cached ? "Served from this session's run cache." : "Freshly simulated with EnergyPlus " + r.run.energyplus_version + "."}{" "}
            Errors: {r.run.err.fatal.length} fatal · {r.run.err.severe.length} severe · {r.run.err.warning_count} warnings.
          </>} />
      </section>

      {(r.standards_summary?.length ?? 0) > 0 && (
        <section className="more-above">
          <h2 className="section-h">Same run, every standard</h2>
          <p className="subtle" style={{ margin: "2px 0 8px" }}>
            One EnergyPlus simulation, judged by every compliance-allowed rule pack.
          </p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {r.standards_summary!.map((s) => (
              <span key={s.pack_id} className="nb-chip"
                style={{ background: s.chosen ? "var(--nb-yellow)" : "var(--nb-bg)", border: "var(--nb-border-2)", padding: "6px 10px" }}>
                <span className="mono">{s.pack_id}</span> ·{" "}
                <StatusPill status={s.overall === "PASS" ? "PASS" : s.overall === "FAIL" ? "FAIL" : "INCOMPLETE"} />
              </span>
            ))}
          </div>
        </section>
      )}

      {r.energy && Object.keys(r.energy).length > 0 && (
        <section className="more-above">
          <h2 className="section-h">Annual energy (from the model's own meters)</h2>
          <div className="table-wrap" style={{ marginTop: 10, maxWidth: 560 }}>
            <table className="data">
              <tbody>
                {Object.entries(r.energy).map(([meter, v]) => (
                  <tr key={meter}>
                    <td className="mono">{meter}</td>
                    <td className="mono num">{v.annual_kwh != null ? `${v.annual_kwh.toLocaleString()} kWh` : "INCOMPLETE — no runperiod total"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {margins.length > 0 && (
        <section className="more-above">
          <h2 className="section-h">Why — distance to each threshold</h2>
          <div className="card" style={{ marginTop: 10 }}>
            {margins.slice(0, 12).map(({ room, c }) => (
              <MarginBar key={room + c.criterion_id} label={`${room} · ${c.criterion_id}`}
                value={Number(c.metric_value)} limit={Number(c.threshold)}
                unit={c.units || ""} higherIsWorse={c.operator === ">" || c.operator === ">="} />
            ))}
            {margins.length > 12 && <p className="subtle">+ {margins.length - 12} further criteria in the table below.</p>}
          </div>
        </section>
      )}

      <section className="more-above">
        <h2 className="section-h">Criterion results</h2>
        <div className="table-wrap" style={{ marginTop: 10 }}>
          <table className="data">
            <thead>
              <tr>
                <th>Room</th>
                <th>Type</th>
                <th>Criterion</th>
                <th>Rule reference</th>
                <th>Result</th>
                <th className="num">Metric</th>
                <th className="num">Threshold</th>
              </tr>
            </thead>
            <tbody>
              {r.result.rooms.flatMap((room) =>
                room.criteria.map((c: CriterionResult) => (
                  <tr key={room.room_id + c.criterion_id}>
                    <td>{room.room_id}</td>
                    <td>{room.room_type}</td>
                    <td className="mono">{c.criterion_id}</td>
                    <td style={{ fontSize: 12.5 }}>{c.rule_ref}</td>
                    <td><StatusPill status={c.status} /></td>
                    <td className="mono num">{c.metric_value ?? "—"} {c.units}</td>
                    <td className="mono num">{c.operator} {c.threshold} {c.units}</td>
                  </tr>
                )),
              )}
            </tbody>
          </table>
        </div>
        <MethodNote>
          A dwelling passes only when every applicable criterion passes. Unevaluated
          criteria (missing outputs, unmapped rooms) make the result INCOMPLETE —
          never a pass, never a fail. Each rule reference names the verified clause.
        </MethodNote>
      </section>

      <section className="more-above">
        <h2 className="section-h">Operative temperature + threshold</h2>
        <div style={{ marginTop: 10 }}><RoomFigure r={r} /></div>
      </section>

      <section className="more-above">
        <h2 className="section-h">Zone × time heatmap · hottest week</h2>
        <div style={{ marginTop: 10 }}><ZoneHeatmap r={r} /></div>
      </section>

      <section className="more-above">
        <h2 className="section-h">Comfort from this run</h2>
        <div style={{ marginTop: 10 }}>
          {comfortError && (
            <div className="note warn">
              <strong>Comfort could not be computed for this run.</strong> {comfortError}
            </div>
          )}
          {!comfort && !comfortError && running && (
            <p className="mono subtle">computing comfort from this run…</p>
          )}
          {comfort && <ComfortTable c={comfort} />}
        </div>
      </section>

      <section className="more-above">
        <h2 className="section-h">Model readiness — every finding explained</h2>
        <div className="table-wrap" style={{ marginTop: 10 }}>
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
                  <td style={{ maxWidth: 320 }}>{row.why_it_matters}</td>
                  <td style={{ fontSize: 12 }}>{row.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="more-above">
        <h2 className="section-h">Provenance</h2>
        <div style={{ marginTop: 10 }}>
          <ProvenanceDrawer rows={[
            { k: "model", v: `${r.model.name} (${r.model.path})` },
            { k: "weather", v: `${r.weather.name} (${r.weather.path})` },
            { k: "engine", v: `EnergyPlus ${r.run.energyplus_version}` },
            { k: "rule pack", v: `${r.rule_pack.rule_pack} v${r.rule_pack.version} — ${r.rule_pack.name}` },
            { k: "run id", v: r.run.run_id },
            { k: "operative temp", v: "Top = 0.5 × (MAT + MRT), derived low-air-speed approximation" },
          ]} />
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
      caption="comfort indices computed from this run's simulated hourly temperatures"
      meta={<span>pythermalcomfort {String(a.library_version ?? "")}</span>}
    >
      {c.note && <p style={{ margin: 0, fontSize: 13 }}>{c.note}</p>}
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
                    <span className="subtle"> ({z.adaptive_hours_excluded} h excluded)</span>
                  )}
                </td>
                <td className="mono">
                  {fmt(z.mean_ppd, "%")}
                  {z.ppd_hours_excluded > 0 && (
                    <span className="subtle"> ({z.ppd_hours_excluded} h excluded)</span>
                  )}
                </td>
                <td className="mono">{fmt(z.max_top, " °C")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p style={{ margin: "10px 0 0", fontSize: 12.5, maxWidth: "96ch" }}>
        Stated assumptions: met {a.met} · clo {a.clo} (summer ensemble) · air speed{" "}
        {a.air_speed_m_s} m/s · occupied hours 9 am–10 pm (hour-ending 10–22) · window{" "}
        {String(a.assessment_window ?? "May–September")} · adaptive: {a.adaptive_standard}{" "}
        (Trm from EPW daily means) · PPD: {a.ppd_standard}.
      </p>
      {withReason.length > 0 && (
        <p style={{ margin: "6px 0 0", fontSize: 12 }}>
          {withReason.map((z) => `${z.zone}: ${z.reason}`).join(" · ")}
        </p>
      )}
    </Figure>
  );
}

/* Operative temperature lines — switch between the hottest outdoor week and
   the whole simulated year; the 26 °C reference runs through both views. */
const MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
const MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function TimeViewButtons({ view, setView }: {
  view: "week" | "year"; setView: (v: "week" | "year") => void;
}) {
  return (
    <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
      {(["year", "week"] as const).map((v) => (
        <button key={v} className={view === v ? "nb-btn" : "nb-btn secondary"}
          style={{ minHeight: 32, fontSize: 11.5 }} onClick={() => setView(v)}>
          {v === "year" ? "WHOLE YEAR" : "HOTTEST WEEK"}
        </button>
      ))}
    </div>
  );
}

function hottestWeekStart(outdoor: number[], week: number): number {
  let best = 0, bestMean = -Infinity;
  for (let i = 0; i + week <= outdoor.length; i += 24) {
    const mean = outdoor.slice(i, i + week).reduce((a, b) => a + b, 0) / week;
    if (mean > bestMean) { bestMean = mean; best = i; }
  }
  return Math.max(0, best - 24 * 3);
}

function RoomFigure({ r }: { r: AnalyzeResult }) {
  const [view, setView] = useState<"week" | "year">("week");
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useChart(ref, null, []);
  const zones = Object.keys(r.series);
  const outdoor = r.daily_mean_outdoor;

  const week = 24 * 7;
  const total = r.series[zones[0]].length;
  const hottestStart = hottestWeekStart(outdoor, week);
  const start = view === "week" ? hottestStart : 0;
  const hours = view === "week" ? week : total;

  const xLabels = view === "year"
    ? Array.from({ length: total }, (_, i) => {
        const d = Math.floor(i / 24);
        let m = 0, acc = 0;
        while (m < 12 && acc + MONTH_DAYS[m] <= d) acc += MONTH_DAYS[m++];
        return i % 24 === 0 && acc === d ? MONTH_ABBR[m] : "";
      })
    : Array.from({ length: week }, (_, i) => {
        const h = (start + i) % 24;
        const d = Math.floor((start + i) / 24) + 1;
        return h === 0 && d % 2 === 1 ? `day ${d}` : "";
      });

  const outdoorLine = view === "year"
    ? outdoor.flatMap((v) => Array(24).fill(v)).slice(0, total)
    : outdoor.slice(start, start + week);

  useChart(ref, {
    ...nbBase(),
    xAxis: nbCategoryAxis(view === "week" ? "hour" : "month",
      xLabels.slice(0, hours)),
    yAxis: nbValueAxis("°C"),
    legend: {
      top: 0, left: 0, icon: "rect", itemWidth: 14, itemHeight: 10,
      textStyle: { fontFamily: "IBM Plex Mono, monospace", fontSize: 10, color: NB_INK },
    },
    ...(view === "year" ? {
      dataZoom: [{ type: "inside" }, { type: "slider", height: 18, bottom: 4 }],
      grid: { left: 50, right: 16, top: 30, bottom: 52 },
    } : {}),
    series: [
      {
        name: "outdoor (daily mean)", type: "line", symbol: "none",
        data: outdoorLine,
        lineStyle: { color: "#0a7a6e", width: 2, type: [6, 3] },
      },
      ...zones.slice(0, 8).map((z, i) => ({
        name: `${z} Top`,
        type: "line" as const, symbol: "none" as const, showSymbol: false,
        data: r.series[z].slice(start, start + hours),
        lineStyle: { color: NB_SERIES[i % NB_SERIES.length], width: view === "year" ? 2 : 3 },
        ...(nbThresholdLine(26, "26 °C ref") as object),
      })),
    ],
    tooltip: {
      trigger: "axis", confine: true, backgroundColor: "#FCDD28",
      borderColor: NB_INK, borderWidth: 2,
      textStyle: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 12 },
      extraCssText: "box-shadow: 4px 4px 0 #161616; border-radius: 4px;",
      valueFormatter: (v: unknown) => `${Number(v).toFixed(1)} °C`,
    },
  }, [r, view]);

  const csvRows: (string | number | null)[][] = [];
  for (let i = 0; i < hours; i++) {
    const row: (string | number | null)[] = [start + i + 1];
    for (const z of zones) row.push(r.series[z][start + i] ?? null);
    csvRows.push(row);
  }

  const viewNote = view === "year"
    ? "whole simulated year (hourly — scroll/zoom inside the chart)"
    : "hottest outdoor week (hourly)";

  return (
    <Figure figNo="FIG 5"
      caption={`operative temperature — ${viewNote}${zones.length > 8 ? ` — first 8 of ${zones.length} zones plotted` : ""}`}
      meta={<span>{zones.slice(0, 8).join(" · ")}</span>}>
      <TimeViewButtons view={view} setView={setView} />
      <div ref={ref} style={{ height: view === "year" ? 330 : 300 }} role="img"
        aria-label={`Line chart of outdoor mean and room operative temperatures, ${viewNote}`} />
      <ExportBar chartRef={chartRef} figureName={`fig_room_temps_${view}_${r.run.run_id}`}
        caption={`Hourly operative temperature per zone, ${viewNote}. Model ${r.model.name}, weather ${r.weather.name}, run ${r.run.run_id}.`}
        csv={{ header: ["hour_index_1", ...zones], rows: csvRows }} />
    </Figure>
  );
}


/* Zone × time heatmap of operative temperature — hottest week hour by hour,
   or the whole year condensed to one daily-max cell per zone and day. */
function ZoneHeatmap({ r }: { r: AnalyzeResult }) {
  const [view, setView] = useState<"week" | "year">("week");
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useChart(ref, null, []);
  const zones = Object.keys(r.series).slice(0, 12);
  const outdoor = r.daily_mean_outdoor;
  const week = 24 * 7;
  const start = hottestWeekStart(outdoor, week);
  const days = Math.floor(r.series[zones[0]].length / 24);

  const xLabels: string[] = [];
  const data: [number, number, number][] = [];
  if (view === "week") {
    for (let i = 0; i < week; i++) {
      const h = (start + i) % 24;
      const d = Math.floor((start + i) / 24) + 1;
      xLabels.push(h === 12 ? `d${d}` : "");
    }
    zones.forEach((z, zi) => {
      for (let i = 0; i < week; i++) {
        const v = r.series[z][start + i];
        if (v !== null && v !== undefined) data.push([i, zi, Math.round(v * 10) / 10]);
      }
    });
  } else {
    for (let d = 0; d < days; d++) {
      let m = 0, acc = 0;
      while (m < 12 && acc + MONTH_DAYS[m] <= d) acc += MONTH_DAYS[m++];
      xLabels.push(acc === d ? MONTH_ABBR[m] : "");
    }
    zones.forEach((z, zi) => {
      for (let d = 0; d < days; d++) {
        const dayVals = r.series[z].slice(d * 24, d * 24 + 24)
          .filter((v) => v !== null && v !== undefined) as number[];
        if (dayVals.length) data.push([d, zi, Math.round(Math.max(...dayVals) * 10) / 10]);
      }
    });
  }
  const all = data.map((d) => d[2]);
  const lo = Math.min(...all), hi = Math.max(...all);

  useChart(ref, {
    ...nbBase(),
    grid: { left: 150, right: 16, top: 12, bottom: 40 },
    xAxis: nbCategoryAxis(view === "week" ? "hour of hottest week" : "day of year (daily max)",
      xLabels),
    yAxis: {
      type: "category", data: zones,
      axisLine: { show: true, lineStyle: { color: NB_INK, width: 2 } },
      axisTick: { show: false },
      axisLabel: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 10 },
    },
    visualMap: {
      show: false, min: lo, max: hi,
      inRange: { color: ["#12C8B0", "#8FE3D4", "#FCDD28", "#F36D30", "#FF4F85", "#D63A2F"] },
    },
    series: [{ type: "heatmap", data, itemStyle: { borderWidth: 0 } }],
    tooltip: {
      confine: true, backgroundColor: "#FCDD28", borderColor: NB_INK, borderWidth: 2,
      textStyle: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 12 },
      extraCssText: "box-shadow: 4px 4px 0 #161616; border-radius: 4px;",
      formatter: (p: unknown) => {
        const v = (p as { value: [number, number, number] }).value;
        const where = view === "week" ? `hour ${start + v[0] + 1}` : `day ${v[0] + 1} (daily max)`;
        return `${zones[v[1]]} · ${where} — ${v[2].toFixed(1)} °C`;
      },
    },
  }, [r, view]);

  const range = `${lo.toFixed(1)}–${hi.toFixed(1)} °C`;
  const viewNote = view === "week"
    ? `hottest week, hour by hour (${range})`
    : `whole year as daily maxima (${range})`;

  return (
    <Figure figNo="FIG 6"
      caption={`zone × time operative temperature, ${viewNote}`}
      meta={<span>{zones.length} zones · {view === "week" ? "hottest outdoor week" : `${days} days`}</span>}>
      <TimeViewButtons view={view} setView={setView} />
      <div ref={ref} style={{ height: Math.max(220, zones.length * 30 + 80) }} role="img"
        aria-label={`Heatmap of operative temperature per zone, ${view === "week" ? "hottest week" : "whole year as daily maxima"}, ${lo.toFixed(1)} to ${hi.toFixed(1)} degrees.`} />
      <ExportBar chartRef={chartRef} figureName={`fig_zone_heatmap_${view}_${r.run.run_id}`}
        caption={`Zone by ${view === "week" ? "hour (hottest week)" : "day (daily maximum, whole year)"} operative temperature heatmap. Model ${r.model.name}, weather ${r.weather.name}, run ${r.run.run_id}.`}
        csv={{ header: ["zone", view === "week" ? "hour_index_1" : "day_index_1", "top_c"], rows: zones.flatMap((z, zi) => data.filter((d) => d[1] === zi).map((d) => [z, start + d[0] + 1, d[2]] as (string | number | null)[])) }} />
    </Figure>
  );
}
