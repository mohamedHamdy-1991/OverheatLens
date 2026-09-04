import { useEffect, useMemo, useRef, useState } from "react";
import { api, type AnalyzeResult, type RunEntry, type WeatherFileEntry } from "../api";
import { ThermalRibbon } from "../ThermalRibbon";
import { EmptyState, MethodNote, StatusPill, PageCover } from "../components";
import { useChart, NB_INK, NB_PAPER, nbBase, nbCategoryAxis, nbValueAxis } from "../charts";
import { ExportBar } from "../ExportBar";

interface CompareFile {
  name: string;
  path: string;
  annual_mean: number;
  hottest: number;
  hours_over_26: number;
  degree_hours_26: number;
  daily_mean: number[];
}

type Mode = "weather" | "runs";

export function Compare() {
  const [mode, setMode] = useState<Mode>("weather");
  return (
    <>
      <PageCover img="cover-compare.png" alt="" />
      <section className="headline-row">
        <div>
          <h1 className="page-title">Compare</h1>
          <p className="page-intro">
            Controlled comparisons only: state what is held constant and what varies,
            or the numbers mislead. Weather-vs-weather uses EPW headline metrics;
            run-vs-run replays archived EnergyPlus experiments side by side.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className={mode === "weather" ? "nb-btn" : "nb-btn secondary"} style={{ minHeight: 40 }} onClick={() => setMode("weather")}>WEATHER × WEATHER</button>
          <button className={mode === "runs" ? "nb-btn" : "nb-btn secondary"} style={{ minHeight: 40 }} onClick={() => setMode("runs")}>RUN × RUN</button>
        </div>
      </section>
      {mode === "weather" ? <WeatherCompare /> : <RunCompare />}
    </>
  );
}

/* ---------------- weather vs weather ---------------- */

function WeatherCompare() {
  const [files, setFiles] = useState<WeatherFileEntry[] | null>(null);
  const [picked, setPicked] = useState<string[]>([]);
  const [data, setData] = useState<CompareFile[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.weatherList().then((fs) => {
      setFiles(fs);
      const d = fs.find((f) => f.name === "Leeds_DSY1_2020High50_.epw");
      const alt = fs.find((f) => f.name === "Leeds_DSY1_2050High50_.epw");
      setPicked([d?.path, alt?.path].filter((p): p is string => Boolean(p)));
    });
  }, []);

  const canRun = picked.length >= 2 && picked.length <= 8;

  const run = () => {
    setBusy(true);
    setErr(null);
    api.compare(picked)
      .then(setData)
      .catch((e) => setErr(String((e as Error).message ?? e)))
      .finally(() => setBusy(false));
  };

  const toggle = (path: string) => {
    setPicked((cur) =>
      cur.includes(path) ? cur.filter((p) => p !== path)
        : cur.length >= 8 ? cur : [...cur, path]);
  };

  const deltas = useMemo(() => {
    if (!data || data.length < 2) return null;
    const base = data[0];
    return data.slice(1).map((f) => ({
      name: f.name,
      dMean: f.annual_mean - base.annual_mean,
      dHot: f.hottest - base.hottest,
      dH26: f.hours_over_26 - base.hours_over_26,
    }));
  }, [data]);

  return (
    <>
      <section className="nb-card" style={{ maxWidth: 780 }}>
        <span className="nb-chip">CONTROLLED · MODEL: — · STANDARD: — · VARIABLE: WEATHER</span>
        <div className="table-wrap" style={{ maxHeight: 260, overflowY: "auto", marginTop: 12 }}>
          <table className="data" style={{ minWidth: 0 }}>
            <tbody>
              {files?.filter((f) => !f.name.startsWith("[fixture]")).map((f) => (
                <tr key={f.path} onClick={() => toggle(f.path)} style={{ cursor: "pointer" }}
                  className={picked.includes(f.path) ? "selected-row" : undefined}>
                  <td style={{ width: 34 }}>
                    <input type="checkbox" checked={picked.includes(f.path)}
                      onChange={() => toggle(f.path)} aria-label={`Select ${f.name}`} />
                  </td>
                  <td className="mono" style={{ fontSize: 12 }}>{f.name}</td>
                  <td style={{ width: 170 }}><StatusPill status={f.compat_2017} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ marginTop: 14, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <button className="nb-btn" onClick={run} disabled={!canRun || busy}>
            {busy ? "LOADING…" : `COMPARE ${picked.length} FILES`}
          </button>
          {!canRun && <span className="subtle">Select at least two files (max 8).</span>}
        </div>
      </section>

      {err && <div className="note warn" style={{ marginTop: 16 }}><strong>Compare failed.</strong> {err}</div>}

      {!data && !err && (
        <div style={{ marginTop: 16 }}>
          <EmptyState img="empty-compare.png" alt="Two overlapping climate charts illustration"
            title="SELECT AT LEAST TWO FILES"
            body="Pick weather files above — aligned thermal years, headline metrics and deltas against the first file appear here." />
        </div>
      )}

      {data && (
        <>
          <section className="more-above" style={{ display: "grid", gap: 18, gridTemplateColumns: "repeat(auto-fit, minmax(460px, 1fr))" }}>
            {data.map((f, i) => (
              <ThermalRibbon key={f.path} dryBulb={f.daily_mean}
                figNo={`FIG C${i + 1}`} place={f.name.replace(/_/g, " ")} compact height={120} hoursPerDay={1} />
            ))}
          </section>

          <section className="more-above">
            <h2 className="section-h">Headline metrics</h2>
            <div className="table-wrap" style={{ marginTop: 10 }}>
              <table className="data">
                <thead>
                  <tr>
                    <th>File</th>
                    <th className="num">Annual mean</th>
                    <th className="num">Hottest hour</th>
                    <th className="num">Hours &gt; 26 °C</th>
                    <th className="num">Degree-hours &gt; 26 °C</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((f) => (
                    <tr key={f.path}>
                      <td className="mono" style={{ fontSize: 12 }}>{f.name}</td>
                      <td className="mono num">{f.annual_mean} °C</td>
                      <td className="mono num">{f.hottest} °C</td>
                      <td className="mono num">{f.hours_over_26} h</td>
                      <td className="mono num">{f.degree_hours_26} Kh</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {deltas && (
            <section className="more-above">
              <h2 className="section-h">Change against {data[0].name.replace(/_/g, " ")}</h2>
              <div className="table-wrap" style={{ maxWidth: 720, marginTop: 10 }}>
                <table className="data">
                  <thead>
                    <tr><th>File</th><th className="num">Δ annual mean</th><th className="num">Δ hottest hour</th><th className="num">Δ hours &gt; 26 °C</th></tr>
                  </thead>
                  <tbody>
                    {deltas.map((d) => (
                      <tr key={d.name}>
                        <td className="mono" style={{ fontSize: 12 }}>{d.name}</td>
                        <td className="mono num" style={{ color: d.dMean > 0 ? "var(--nb-danger)" : "#1e7a3c" }}>
                          {d.dMean >= 0 ? "+" : ""}{d.dMean.toFixed(2)} K
                        </td>
                        <td className="mono num">{d.dHot >= 0 ? "+" : ""}{d.dHot.toFixed(1)} K</td>
                        <td className="mono num">{d.dH26 >= 0 ? "+" : ""}{d.dH26} h</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
          <DeltaChart data={data} />
        </>
      )}
    </>
  );
}

function DeltaChart({ data }: { data: CompareFile[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useChart(ref, null, []);
  useChart(ref, {
    ...nbBase("Annual mean vs hours > 26 °C"),
    xAxis: nbValueAxis("annual mean dry-bulb (°C)"),
    yAxis: nbValueAxis("hours > 26 °C"),
    series: [{
      type: "scatter", symbolSize: 16,
      data: data.map((f) => ({ value: [f.annual_mean, f.hours_over_26], name: f.name })),
      itemStyle: { color: "#F36D30", borderColor: NB_INK, borderWidth: 2 },
      label: {
        show: true, formatter: (p: unknown) => String((p as { name: string }).name).replace(/_/g, " ").slice(0, 18),
        fontFamily: "IBM Plex Mono, monospace", fontSize: 9, color: NB_INK, position: "top",
      },
    }],
    tooltip: {
      confine: true, backgroundColor: "#FCDD28", borderColor: NB_INK, borderWidth: 2,
      textStyle: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 12 },
      extraCssText: "box-shadow: 4px 4px 0 #161616; border-radius: 4px;",
      formatter: (p: unknown) => {
        const q = p as { name: string; value: [number, number] };
        return `${q.name}<br/>${q.value[0].toFixed(2)} °C · ${q.value[1]} h > 26 °C`;
      },
    },
  }, [data]);
  return (
    <section className="more-above">
      <div className="figure" style={{ margin: 0 }}>
        <div ref={ref} style={{ height: 300 }} role="img" aria-label="Scatter of annual mean against hours above 26 degrees" />
        <div className="figure-caption"><span className="fig-no">FIG C-S</span><span>each file positioned by mean vs heat exposure</span>
          <ExportBar chartRef={chartRef} figureName="fig_compare_scatter"
            caption="Weather-file comparison scatter: annual mean dry-bulb against hours above 26 °C."
            csv={{ header: ["file", "annual_mean_c", "hours_over_26"], rows: data.map((f) => [f.name, f.annual_mean, f.hours_over_26]) }} />
        </div>
      </div>
    </section>
  );
}

/* ---------------- run vs run ---------------- */

function RunCompare() {
  const [runs, setRuns] = useState<RunEntry[] | null>(null);
  const [picked, setPicked] = useState<string[]>([]);
  const [details, setDetails] = useState<AnalyzeResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.runs().then(setRuns).catch((e) => setErr(String(e.message ?? e)));
  }, []);

  const toggle = (id: string) => {
    setPicked((cur) =>
      cur.includes(id) ? cur.filter((x) => x !== id)
        : cur.length >= 4 ? cur : [...cur, id]);
  };

  const run = async () => {
    setBusy(true);
    setErr(null);
    try {
      const ds = await Promise.all(picked.map((id) => api.runDetail(id).then((d) => d.payload)));
      setDetails(ds);
    } catch (e) {
      setErr(String((e as Error).message ?? e));
    } finally {
      setBusy(false);
    }
  };

  const models = new Set(details.map((d) => d.model.path));
  const weathers = new Set(details.map((d) => d.weather.path));
  const packs = new Set(details.map((d) => d.rule_pack.rule_pack));

  return (
    <>
      <section className="nb-card" style={{ maxWidth: 780 }}>
        <span className="nb-chip">PICK 2–4 ARCHIVED RUNS · MAX 4 SERIES PER CHART</span>
        <div className="table-wrap" style={{ maxHeight: 260, overflowY: "auto", marginTop: 12 }}>
          <table className="data" style={{ minWidth: 0 }}>
            <tbody>
              {(runs ?? []).filter((r) => r.run_id).map((r) => (
                <tr key={r.run_id!} onClick={() => toggle(r.run_id!)} style={{ cursor: "pointer" }}
                  className={picked.includes(r.run_id!) ? "selected-row" : undefined}>
                  <td style={{ width: 34 }}>
                    <input type="checkbox" checked={picked.includes(r.run_id!)}
                      onChange={() => toggle(r.run_id!)} aria-label={`Select ${r.run_id}`} />
                  </td>
                  <td className="mono" style={{ fontSize: 11.5 }}>{r.run_id}</td>
                  <td style={{ fontSize: 12 }}>{r.model ?? "—"} × {r.weather}</td>
                  <td><StatusPill status={r.overall ?? "INFO"} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {(runs ?? []).length === 0 && (
          <p className="subtle" style={{ marginTop: 10 }}>Archive is empty — run an analysis first.</p>
        )}
        <div style={{ marginTop: 14 }}>
          <button className="nb-btn" onClick={run} disabled={picked.length < 2 || busy}>
            {busy ? "LOADING RUNS…" : `COMPARE ${picked.length} RUNS`}
          </button>
        </div>
      </section>

      {err && <div className="note warn" style={{ marginTop: 16 }}><strong>Compare failed.</strong> {err}</div>}

      {details.length >= 2 && (
        <>
          <section className="context-bar" style={{ marginTop: 18 }}>
            <div className="context-cell"><small>CONTROLLED · MODEL</small><strong>{models.size === 1 ? [...models][0].split("/").pop() : `VARIES ×${models.size}`}</strong></div>
            <div className="context-cell"><small>CONTROLLED · WEATHER</small><strong>{weathers.size === 1 ? [...weathers][0].split("/").pop() : `VARIES ×${weathers.size}`}</strong></div>
            <div className="context-cell"><small>CONTROLLED · STANDARD</small><strong>{packs.size === 1 ? [...packs][0] : `VARIES ×${packs.size}`}</strong></div>
          </section>
          {(models.size > 1 || weathers.size > 1) && (
            <p className="note warn" style={{ marginTop: 12 }}>
              <strong>Uncontrolled comparison.</strong> More than one variable differs — treat
              deltas as exploratory, not causal.
            </p>
          )}
          <section className="more-above">
            <h2 className="section-h">Verdicts</h2>
            <div className="table-wrap" style={{ marginTop: 10 }}>
              <table className="data">
                <thead><tr><th>Run</th><th>Model × weather</th><th>Standard</th><th>Verdict</th></tr></thead>
                <tbody>
                  {details.map((d) => (
                    <tr key={d.run.run_id}>
                      <td className="mono">{d.run.run_id}</td>
                      <td style={{ fontSize: 12 }}>{d.model.name} × {d.weather.name}</td>
                      <td className="mono" style={{ fontSize: 11.5 }}>{d.rule_pack.rule_pack} v{d.rule_pack.version}</td>
                      <td><StatusPill status={d.result.overall} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <RunOverlay details={details} />
        </>
      )}
      <MethodNote title="WHAT MAKES A COMPARISON CONTROLLED?">
        Same model + same standard + same EnergyPlus version, varying only weather (or
        vice versa). The header above names what is held constant. Batch matrices in
        Scenario & Batch are built to guarantee this by construction.
      </MethodNote>
    </>
  );
}

/* Overlay hottest-week Top of the first zone of each run. */
function RunOverlay({ details }: { details: AnalyzeResult[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useChart(ref, null, []);
  const outdoor = details[0].daily_mean_outdoor;
  const week = 24 * 7;
  const start = (() => {
    let best = 0, bestMean = -Infinity;
    for (let i = 0; i + week <= outdoor.length; i += 24) {
      const mean = outdoor.slice(i, i + week).reduce((a, b) => a + b, 0) / week;
      if (mean > bestMean) { bestMean = mean; best = i; }
    }
    return Math.max(0, best - 24 * 3);
  })();
  const shown = details.slice(0, 4);
  const COLORS = ["#161616", "#F36D30", "#12C8B0", "#8167F5"];
  const overlayRows: (string | number | null)[][] = [];
  for (let i = 0; i < week; i++) {
    const row: (string | number | null)[] = [start + i + 1];
    for (const d of shown) {
      const z = Object.keys(d.series)[0];
      row.push(d.series[z]?.[start + i] ?? null);
    }
    overlayRows.push(row);
  }

  useChart(ref, {
    ...nbBase(),
    backgroundColor: NB_PAPER,
    xAxis: nbCategoryAxis("hour", Array.from({ length: week }, (_, i) => {
      const h = (start + i) % 24;
      return h === 12 ? `d${Math.floor((start + i) / 24) + 1}` : "";
    })),
    yAxis: nbValueAxis("Top (°C)"),
    legend: {
      top: 0, left: 0, icon: "rect", itemWidth: 14, itemHeight: 10,
      textStyle: { fontFamily: "IBM Plex Mono, monospace", fontSize: 10, color: NB_INK },
    },
    series: shown.map((d, i) => {
      const z = Object.keys(d.series)[0];
      return {
        name: `${d.run.run_id} · ${z}`,
        type: "line" as const, symbol: "none" as const,
        data: (d.series[z] ?? []).slice(start, start + week),
        lineStyle: { color: COLORS[i % COLORS.length], width: 3 },
      };
    }),
    tooltip: {
      trigger: "axis", confine: true, backgroundColor: "#FCDD28",
      borderColor: NB_INK, borderWidth: 2,
      textStyle: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 12 },
      extraCssText: "box-shadow: 4px 4px 0 #161616; border-radius: 4px;",
      valueFormatter: (v: unknown) => `${Number(v).toFixed(1)} °C`,
    },
  }, [details]);

  return (
    <section className="more-above">
      <div className="figure" style={{ margin: 0 }}>
        <div ref={ref} style={{ height: 300 }} role="img" aria-label="Overlay of operative temperature across compared runs" />
        <div className="figure-caption"><span className="fig-no">FIG C-R</span>
          <span>first-zone operative temperature overlay · hottest week of run 1</span>
          <ExportBar chartRef={chartRef} figureName="fig_run_overlay"
            caption={`First-zone operative temperature overlay for runs ${details.map((d) => d.run.run_id).join(", ")}.`}
            csv={{ header: ["hour_index_1", ...shown.map((d) => d.run.run_id)], rows: overlayRows }} />
        </div>
      </div>
    </section>
  );
}
