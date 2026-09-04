import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  api,
  type EnergyExperiment,
  type EnergyExperimentRow,
  type ModelInfo,
  type WeatherFileEntry,
} from "../api";
import { EmptyState, MethodNote, StatusPill, PageCover } from "../components";

function verdictPill(v?: string | null) {
  if (!v) return <span className="subtle">—</span>;
  return <StatusPill status={v === "PASS" ? "PASS" : v === "FAIL" ? "FAIL" : "INCOMPLETE"} />;
}

function stdVerdict(row: EnergyExperimentRow, pack: string) {
  return row.standards_summary?.find((s) => s.pack_id === pack)?.overall ?? null;
}

function adaptiveMean(row: EnergyExperimentRow): number | null {
  const vals = (row.comfort?.zones ?? [])
    .map((z) => z.adaptive_acceptable_pct)
    .filter((v): v is number => v != null);
  if (!vals.length) return null;
  return Math.round((vals.reduce((a, b) => a + b, 0) / vals.length) * 10) / 10;
}

function ppdMean(row: EnergyExperimentRow): number | null {
  const vals = (row.comfort?.zones ?? [])
    .map((z) => z.mean_ppd)
    .filter((v): v is number => v != null);
  if (!vals.length) return null;
  return Math.round((vals.reduce((a, b) => a + b, 0) / vals.length) * 10) / 10;
}

const num = (v?: number | null) => (v != null ? v.toLocaleString() : "—");

export function Mitigation() {
  const [models, setModels] = useState<ModelInfo[] | null>(null);
  const [weatherFiles, setWeatherFiles] = useState<WeatherFileEntry[] | null>(null);
  const [modelId, setModelId] = useState<string>("");
  const [weather, setWeather] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EnergyExperiment | null>(null);

  useEffect(() => {
    api.models()
      .then((ms) => {
        setModels(ms);
        const first = ms.find((m) => m.source === "research");
        if (first) setModelId((cur) => cur || first.id);
      })
      .catch((e) => setError(String(e.message ?? e)));
    api.weatherList()
      .then((fs) => {
        setWeatherFiles(fs);
        const dsy = fs.find((f) => f.name.includes("DSY1_2020High50"));
        if (dsy) setWeather((cur) => cur || dsy.path);
      })
      .catch(() => setWeatherFiles(null));
  }, []);

  const run = () => {
    if (!modelId || !weather) return;
    setBusy(true);
    setError(null);
    api.energyExperiment(modelId, weather)
      .then(setResult)
      .catch((e) => setError(String(e.message ?? e)))
      .finally(() => setBusy(false));
  };

  const cases: EnergyExperimentRow[] = result
    ? [result.baseline, ...result.strategies]
    : [];

  return (
    <>
      <PageCover img="cover-mitigation.png" alt="" />
      <section className="headline-row">
        <div>
          <h1 className="page-title">Mitigation Lab</h1>
          <p className="page-intro">
            Controlled experiments on the model and weather you choose: the lab runs the
            dwelling baseline against the author's stored strategy variants — S2 restricted
            window opening and S3 night-purge ventilation — as real EnergyPlus simulations.
            Every run is judged by the versioned standards (TM59:2017, TM59:2026, Part O
            dynamic, TM52) and the comfort suite, and annual facility energy is read from
            the model's own meters. Anything that cannot be computed says INCOMPLETE —
            nothing is estimated.
          </p>
        </div>
      </section>

      {error && <div className="note warn"><strong>Experiment failed.</strong> {error}</div>}

      <section className="more-above">
        <h2 className="section-h">Set up the experiment</h2>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center", margin: "10px 0" }}>
          <label className="subtle" htmlFor="mit-model">MODEL</label>
          <select id="mit-model" className="nb-btn secondary" style={{ minHeight: 40, maxWidth: 380 }}
            value={modelId} onChange={(e) => setModelId(e.target.value)}>
            {(models ?? []).filter((m) => m.source !== "upload").map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
          <label className="subtle" htmlFor="mit-weather">WEATHER FILE</label>
          <select id="mit-weather" className="nb-btn secondary" style={{ minHeight: 40, maxWidth: 380 }}
            value={weather} onChange={(e) => setWeather(e.target.value)}>
            <option value="">— choose an EPW —</option>
            {(weatherFiles ?? []).map((f) => (
              <option key={f.path} value={f.path}>{f.name}</option>
            ))}
          </select>
          <button className="nb-btn" style={{ minHeight: 40 }}
            disabled={!modelId || !weather || busy} onClick={run}>
            {busy ? "RUNNING 3 SIMULATIONS…" : "RUN MITIGATION EXPERIMENT"}
          </button>
        </div>
        <MethodNote>
          Three real EnergyPlus runs (baseline + S2 + S3) through the validated pipeline.
          Results are archived in the <Link to="/runs">Run Archive</Link> with full
          provenance; the campaign that validates this pipeline lives on the{" "}
          <Link to="/validation">Validation</Link> page.
        </MethodNote>
      </section>

      {!result && !error && (
        <EmptyState img="empty-mitigation.png" alt="Mitigation workbench illustration"
          title="NO EXPERIMENT RUN YET"
          body="Choose a model and a weather file, then run the experiment. The baseline and each strategy are simulated separately and compared honestly — including the cases where a saving cannot be computed." />
      )}

      {result && (
        <>
          <section className="context-bar">
            <div className="context-cell"><small>MODEL</small>
              <strong>{result.model.name}</strong></div>
            <div className="context-cell"><small>WEATHER</small>
              <strong>{result.weather.name.slice(0, 34)}</strong></div>
            <div className="context-cell"><small>SIMULATIONS</small>
              <strong>{cases.filter((c) => c.status === "complete").length} completed</strong></div>
          </section>

          <section className="more-above">
            <h2 className="section-h">Standards &amp; comfort · every run, every standard</h2>
            <div className="table-wrap" style={{ marginTop: 10 }}>
              <table className="data">
                <thead>
                  <tr>
                    <th>Case</th><th>TM59:2017</th><th>TM59:2026</th><th>Part O dyn.</th><th>TM52</th>
                    <th className="num">Adaptive OK (May–Sep)</th><th className="num">Mean PPD</th>
                  </tr>
                </thead>
                <tbody>
                  {cases.map((r) => (
                    <tr key={r.strategy}>
                      <td><strong>{r.strategy}</strong>{r.note && <><br /><span className="subtle" style={{ fontSize: 11.5 }}>{r.note}</span></>}</td>
                      <td>{verdictPill(stdVerdict(r, "uk_tm59_2017"))}</td>
                      <td>{verdictPill(stdVerdict(r, "uk_tm59_2026"))}</td>
                      <td>{verdictPill(stdVerdict(r, "uk_part_o_dynamic"))}</td>
                      <td>{verdictPill(stdVerdict(r, "uk_tm52"))}</td>
                      <td className="mono num">{adaptiveMean(r) != null ? `${adaptiveMean(r)}%` : "—"}</td>
                      <td className="mono num">{ppdMean(r) != null ? `${ppdMean(r)}%` : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="subtle" style={{ marginTop: 8 }}>
              Adaptive OK = share of May–September occupied hours inside EN 16798-1
              Category II, computed by the comfort suite on the simulated operative
              temperature (mean across zones). TM52 is a room-level standard — the
              dwelling column shows its overall roll-up, which can be INCOMPLETE by design.
            </p>
          </section>

          <section className="more-above">
            <h2 className="section-h">Annual energy saved</h2>
            <div className="table-wrap" style={{ marginTop: 10 }}>
              <table className="data">
                <thead>
                  <tr>
                    <th>Case</th><th className="num">Electricity (kWh/yr)</th>
                    <th className="num">District heating (kWh/yr)</th>
                    <th className="num">Total (kWh/yr)</th>
                    <th className="num">Saved vs baseline</th>
                  </tr>
                </thead>
                <tbody>
                  {cases.map((r) => (
                    <tr key={r.strategy}>
                      <td><strong>{r.strategy}</strong></td>
                      <td className="mono num">{num(r.electricity_kwh)}</td>
                      <td className="mono num">
                        {[r.district_heating_kwh, r.district_cooling_kwh].some((v) => v != null)
                          ? [r.district_heating_kwh, r.district_cooling_kwh].map((v) => v?.toLocaleString() ?? "—").join(" / ")
                          : "—"}
                      </td>
                      <td className="mono num">{num(r.total_kwh)}</td>
                      <td className="mono num" style={{ color: r.total_saved_kwh == null ? undefined : r.total_saved_kwh >= 0 ? "#1e7a3c" : "var(--nb-danger)" }}>
                        {r.total_saved_kwh == null ? "—"
                          : `${r.total_saved_kwh.toLocaleString()} kWh (${r.total_saved_pct ?? "—"}%)`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="subtle" style={{ marginTop: 8 }}>
              Energy comes from the facility meters inside the author's own models
              (J-meters only, converted to kWh). Cases marked INCOMPLETE carry no meters
              or no active strategy physics — savings are never estimated.
            </p>
          </section>
        </>
      )}
    </>
  );
}
