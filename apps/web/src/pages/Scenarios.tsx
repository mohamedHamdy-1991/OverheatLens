import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type BatchEntry, type BatchResultItem, type ModelInfo, type WeatherFileEntry } from "../api";
import { EmptyState, StatusPill, PageCover } from "../components";

type Mode = "multi-weather" | "multi-model" | "matrix";

export function Scenarios() {
  const [mode, setMode] = useState<Mode>("multi-weather");
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [files, setFiles] = useState<WeatherFileEntry[]>([]);
  const [selModels, setSelModels] = useState<string[]>([]);
  const [selWeather, setSelWeather] = useState<string[]>([]);
  const [pack, setPack] = useState("uk_tm59_2017");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<BatchResultItem[] | null>(null);

  useEffect(() => {
    api.models().then(setModels).catch(() => setModels([]));
    api.weatherList().then((fs) => {
      const real = fs.filter((f) => !f.name.startsWith("[fixture]"));
      setFiles(real);
      const d = real.find((f) => f.name === "Leeds_DSY1_2020High50_.epw");
      const alt = real.find((f) => f.name === "Leeds_DSY1_2050High50_.epw");
      setSelWeather([d?.path, alt?.path].filter((p): p is string => Boolean(p)));
    }).catch(() => setFiles([]));
  }, []);

  const toggle = (list: string[], v: string, max: number, set: (s: string[]) => void) => {
    set(list.includes(v) ? list.filter((x) => x !== v) : list.length >= max ? list : [...list, v]);
  };

  const plan: BatchEntry[] = (() => {
    if (mode === "multi-weather") {
      const m = selModels[0] || "";
      return selWeather.map((w) => ({ weather_path: w, model_path: m || undefined, pack_id: pack }));
    }
    if (mode === "multi-model") {
      const w = selWeather[0] || "";
      return selModels.map((m) => ({ weather_path: w, model_path: m || undefined, pack_id: pack }));
    }
    const m = selModels.length ? selModels : [""];
    const w = selWeather.length ? selWeather : [];
    return w.flatMap((ww) => m.map((mm) => ({ weather_path: ww, model_path: mm || undefined, pack_id: pack })));
  })();

  const valid = mode === "multi-weather"
    ? selWeather.length >= 1 && selWeather.length <= 12 && !!selModels[0]
    : mode === "multi-model"
      ? selModels.length >= 1 && selModels.length <= 12 && !!selWeather[0]
      : selModels.length >= 1 && selWeather.length >= 1 && plan.length <= 96;

  const launch = async () => {
    setBusy(true);
    setError(null);
    setResults(null);
    try {
      const out = await api.batch(plan, pack);
      setResults(out.runs);
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageCover img="cover-scenarios.png" alt="" />
      <section className="headline-row">
        <div>
          <h1 className="page-title">Scenario & Batch</h1>
          <p className="page-intro">
            Controlled batch experiments with real EnergyPlus runs: one building across
            many weather files, one weather across many archetypes, or a full matrix.
            Every run lands in the archive with its own ID and provenance.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button className={mode === "multi-weather" ? "nb-btn" : "nb-btn secondary"} style={{ minHeight: 40 }} onClick={() => setMode("multi-weather")}>1 × N WEATHER</button>
          <button className={mode === "multi-model" ? "nb-btn" : "nb-btn secondary"} style={{ minHeight: 40 }} onClick={() => setMode("multi-model")}>N MODELS × 1</button>
          <button className={mode === "matrix" ? "nb-btn" : "nb-btn secondary"} style={{ minHeight: 40 }} onClick={() => setMode("matrix")}>MATRIX</button>
        </div>
      </section>

      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16 }}>
        <div className="nb-card" style={{ padding: 18 }}>
          <span className="nb-chip">
            {mode === "multi-weather" ? "PICK 1 MODEL" : `PICK MODELS · ${selModels.length}`} (research first)
          </span>
          <div style={{ maxHeight: 260, overflowY: "auto", marginTop: 10, border: "var(--nb-border-1)" }}>
            {models.map((m) => {
              const on = selModels.includes(m.path);
              const click = () => mode === "multi-weather" ? setSelModels([m.path]) : toggle(selModels, m.path, 12, setSelModels);
              return (
                <label key={m.id} style={{ display: "flex", gap: 8, padding: "7px 10px", fontSize: 12.5, cursor: "pointer", background: on ? "var(--nb-yellow)" : undefined, borderBottom: "1px solid var(--nb-line-soft)" }}>
                  <input type="checkbox" checked={on} onChange={click} />
                  <span><strong>{m.name}</strong> <span className="mono subtle">· {m.n_zones ?? "?"} zones · {m.source}</span></span>
                </label>
              );
            })}
          </div>
        </div>
        <div className="nb-card" style={{ padding: 18 }}>
          <span className="nb-chip">
            {mode === "multi-model" ? "PICK 1 WEATHER" : `PICK WEATHER · ${selWeather.length}`}
          </span>
          <div style={{ maxHeight: 260, overflowY: "auto", marginTop: 10, border: "var(--nb-border-1)" }}>
            {files.map((f) => {
              const on = selWeather.includes(f.path);
              const click = () => mode === "multi-model" ? setSelWeather([f.path]) : toggle(selWeather, f.path, 12, setSelWeather);
              return (
                <label key={f.path} style={{ display: "flex", gap: 8, padding: "7px 10px", fontSize: 12.5, cursor: "pointer", background: on ? "var(--nb-cyan)" : undefined, borderBottom: "1px solid var(--nb-line-soft)" }}>
                  <input type="checkbox" checked={on} onChange={click} />
                  <span className="mono">{f.name}</span>
                </label>
              );
            })}
          </div>
        </div>
        <div className="nb-card" style={{ padding: 18, background: "var(--nb-ink)", color: "var(--nb-surface)" }}>
          <span className="nb-chip">LAUNCH</span>
          <div className="field" style={{ marginTop: 12 }}>
            <label htmlFor="b-pack" style={{ color: "var(--nb-surface)" }}>Standard for every run</label>
            <select id="b-pack" className="nb-input" value={pack} onChange={(e) => setPack(e.target.value)}>
              <option value="uk_tm59_2017">TM59:2017</option>
              <option value="uk_tm59_2026">TM59:2026 (research-tagged)</option>
              <option value="uk_part_o_dynamic">Part O dynamic</option>
              <option value="uk_tm52">TM52</option>
            </select>
          </div>
          <p className="mono" style={{ fontSize: 13 }}>
            {plan.length} model{plan.length === 1 ? "" : "s"} × {mode === "multi-model" ? 1 : selWeather.length} weather = <strong>{plan.length} simulations</strong>
          </p>
          <p style={{ fontSize: 12, opacity: 0.8 }}>Sequential on this machine — a full 15 × 12 matrix takes a while. Repeats reuse the cache.</p>
          <button className="nb-btn" style={{ width: "100%", justifyContent: "center", marginTop: 8 }}
            disabled={!valid || busy} onClick={launch}>
            {busy ? "RUNNING BATCH…" : `▶ RUN ${plan.length} SIMULATIONS`}
          </button>
          {!valid && <p className="mono" style={{ fontSize: 11, marginTop: 8 }}>Select the required models and weather first (matrix ≤ 96).</p>}
        </div>
      </section>

      {error && <div className="note warn" style={{ marginTop: 16 }}><strong>Batch failed.</strong> {error}</div>}

      {!results && !error && (
        <div style={{ marginTop: 16 }}>
          <EmptyState img="empty-scenarios.png" alt="Batch matrix grid illustration"
            title="DESIGN THE MATRIX"
            body="Pick models and weather files above. The batch uses real simulations — workload is shown before anything runs, and every run is filed in the archive." />
        </div>
      )}

      {results && (
        <section className="more-above">
          <h2 className="section-h">Batch results · {results.length} runs</h2>
          <div className="table-wrap" style={{ marginTop: 10 }}>
            <table className="data">
              <thead><tr><th>Run</th><th>Model</th><th>Weather</th><th>Verdict</th><th></th></tr></thead>
              <tbody>
                {results.map((r, i) => (
                  <tr key={r.run_id ?? i}>
                    <td className="mono" style={{ fontSize: 11.5 }}>{r.run_id ?? "—"}</td>
                    <td style={{ fontSize: 12.5 }}>{r.model ?? "—"}{r.cached ? <span className="subtle"> (cached)</span> : ""}</td>
                    <td className="mono" style={{ fontSize: 11.5 }}>{r.weather}</td>
                    <td>{r.error ? <span className="note warn" style={{ fontSize: 12 }}>{r.error.slice(0, 120)}</span> : <StatusPill status={r.overall ?? "INFO"} />}</td>
                    <td>{r.run_id && !r.error && <Link className="nb-btn secondary" style={{ minHeight: 32, fontSize: 12 }} to={`/analyze?run=${encodeURIComponent(r.run_id)}`}>OPEN</Link>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p style={{ marginTop: 10 }}><Link className="nb-btn" to="/runs">OPEN RUN ARCHIVE ›</Link></p>
        </section>
      )}
    </>
  );
}
