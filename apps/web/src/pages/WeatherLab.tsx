import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, type WeatherCheck, type WeatherFileEntry, type WeatherSeries } from "../api";
import { EmptyState, Figure, MethodNote, ProvenanceDrawer, StatusPill, PageCover } from "../components";
import { ThermalRibbon } from "../ThermalRibbon";
import { useChart, MONTHS, NB_HEAT_BINS, NB_INK, nbBase, nbThresholdLine } from "../charts";
import { ExportBar } from "../ExportBar";

export function WeatherLab() {
  const [files, setFiles] = useState<WeatherFileEntry[] | null>(null);
  const [selected, setSelected] = useState<WeatherFileEntry | null>(null);
  const [check, setCheck] = useState<WeatherCheck | null>(null);
  const [series, setSeries] = useState<WeatherSeries | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const loadList = () =>
    api.weatherList().then((fs) => {
      setFiles(fs);
      return fs;
    });

  useEffect(() => {
    loadList()
      .then((fs) => {
        const pick = fs.find((f) => f.name === "Leeds_DSY1_2020High50_.epw") ?? fs[0];
        if (pick) setSelected(pick);
      })
      .catch((e) => setError(String(e.message ?? e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selected) return;
    setCheck(null);
    setSeries(null);
    setError(null);
    Promise.all([api.weatherCheck(selected.path), api.weatherSeries(selected.path)])
      .then(([c, s]) => { setCheck(c); setSeries(s); })
      .catch((e) => setError(String(e.message ?? e)));
  }, [selected]);

  const uploadEpw = (file: File) => {
    setUploading(true);
    setError(null);
    api.uploadWeather(file)
      .then((saved) =>
        loadList().then((fs) => {
          const pick = fs.find((f) => f.path === saved.path) ?? null;
          setSelected(pick);
          if (!pick) setError("Upload saved, but the refreshed list does not show it yet.");
        }))
      .catch((e) => setError(String(e.message ?? e)))
      .finally(() => setUploading(false));
  };

  return (
    <>
      <PageCover img="cover-weather.png" alt="" />
      <section className="headline-row">
        <div>
          <h1 className="page-title">Weather Lab</h1>
          <p className="page-intro">
            Pick a weather file from the local library, or upload your own EPW. Every file
            passes structure + physics QC and a standards-compatibility review before any
            simulation trusts it.
          </p>
        </div>
      </section>

      <section className="nb-card" style={{ maxWidth: 760 }}>
        <div className="field">
          <label htmlFor="epw">Weather file · local library + uploads</label>
          <select
            id="epw" className="nb-input"
            value={selected?.path ?? ""}
            onChange={(e) => {
              const f = files?.find((x) => x.path === e.target.value);
              if (f) setSelected(f);
            }}
          >
            {files?.map((f) => (
              <option key={f.path} value={f.path}>{f.name} · {f.size_kb} kB</option>
            ))}
          </select>
        </div>
        {selected && (
          <p style={{ marginTop: 10, display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <span className="mono subtle">TM59:2017</span> <StatusPill status={selected.compat_2017} />
            <span className="mono subtle">TM59:2026</span> <StatusPill status={selected.compat_2026} />
          </p>
        )}
        <div style={{ marginTop: 12, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <button className="nb-btn secondary" onClick={() => fileInput.current?.click()} disabled={uploading}>
            {uploading ? "UPLOADING…" : "+ UPLOAD EPW"}
          </button>
          <input ref={fileInput} type="file" accept=".epw" style={{ display: "none" }}
            aria-label="Upload an EPW weather file"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadEpw(f); e.target.value = ""; }} />
          <span className="subtle">≤ 20 MB · saved to the local uploads library · checked on arrival</span>
        </div>
      </section>

      {error && <div className="note warn" style={{ marginTop: 16 }}><strong>Could not load this file.</strong> {error}</div>}

      {!check && !error && (
        <div style={{ marginTop: 16 }}>
          <EmptyState img="empty-weather.png" alt="Empty weather shelf illustration"
            title="READING THE SKY FILE…"
            body="Parsing headers, checking 8 760 hourly records against physics, and reviewing standards compatibility." />
        </div>
      )}

      {check && (
        <section className="more-above">
          <h2 className="section-h">Weather dossier</h2>
          <div className="metrics" style={{ marginTop: 12 }}>
            <div className="metric">
              <span className="m-val"><StatusPill status={check.status} /></span>
              <div className="m-label">QC verdict</div>
            </div>
            <div className="metric">
              <span className="m-val">{(check.n_rows / 1000).toFixed(2)}<span className="m-unit">k rows</span></span>
              <div className="m-label">records</div>
            </div>
            {check.weather_summary && (
              <>
                <div className="metric">
                  <span className="m-val">{check.weather_summary.annual_mean_dry_bulb}<span className="m-unit">°C</span></span>
                  <div className="m-label">annual mean</div>
                </div>
                <div className="metric">
                  <span className="m-val">{check.weather_summary.hottest_hour}<span className="m-unit">°C</span></span>
                  <div className="m-label">hottest hour</div>
                </div>
                <div className="metric">
                  <span className="m-val">{check.weather_summary.exceedance_hours_26c}<span className="m-unit">h</span></span>
                  <div className="m-label">hours &gt; 26 °C</div>
                </div>
                <div className="metric">
                  <span className="m-val">{check.weather_summary.degree_hours_26c}<span className="m-unit">Kh</span></span>
                  <div className="m-label">degree-hours &gt; 26 °C</div>
                </div>
              </>
            )}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16, marginTop: 4 }}>
            <div className="card">
              <div className="card-head"><h3>File dossier</h3><span className="subtle">EPW header</span></div>
              <dl className="mono" style={{ margin: 0, display: "grid", gridTemplateColumns: "auto 1fr", gap: "6px 14px", fontSize: 12 }}>
                <dt className="subtle">LOCATION</dt><dd style={{ margin: 0 }}>{check.city}, {check.country}</dd>
                <dt className="subtle">COORDS</dt><dd style={{ margin: 0 }}>{check.latitude?.toFixed(2)}, {check.longitude?.toFixed(2)} · {check.elevation?.toFixed(0)} m</dd>
                <dt className="subtle">SHA-256</dt><dd style={{ margin: 0, wordBreak: "break-all" }}>{check.sha256}</dd>
              </dl>
              <div style={{ marginTop: 10 }}>
                {selected && <Link className="nb-btn" style={{ minHeight: 40 }} to={`/analyze`}>USE IN ANALYSIS ›</Link>}
              </div>
            </div>
            <div className="card">
              <div className="card-head"><h3>EnergyPlus compatibility</h3><span className="subtle">structure</span></div>
              <p style={{ fontSize: 13 }}>
                {check.n_rows === 8760 || check.n_rows === 8784
                  ? `✓ ${check.n_rows.toLocaleString()} hourly records — calendar-complete, EnergyPlus-ready.`
                  : `⚠ ${check.n_rows.toLocaleString()} records — not a full year; check findings before simulating.`}
              </p>
              <MethodNote title="WHAT DOES QC CHECK?">
                File structure, header metadata, row count, timestamp continuity, missing
                fields, sentinel values (999.x), dew-point physics, spikes, stuck sensors,
                radiation/wind/pressure plausibility. Errors block simulation; warnings
                travel with the file into every report.
              </MethodNote>
            </div>
          </div>

          {check.issues.length > 0 && (
            <div className="table-wrap" style={{ marginTop: 16 }}>
              <table className="data">
                <thead>
                  <tr><th>Check</th><th>Severity</th><th>Finding</th></tr>
                </thead>
                <tbody>
                  {check.issues.map((i, idx) => (
                    <tr key={idx}>
                      <td className="mono">{i.code}</td>
                      <td><StatusPill status={i.severity} /></td>
                      <td>{i.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {check.issues.length === 0 && (
            <p style={{ marginTop: 14, fontSize: 13.5 }}>
              <StatusPill status="PASS" /> All checks passed — no structural or physical-plausibility findings.
            </p>
          )}
          <div style={{ marginTop: 12 }}>
            <ProvenanceDrawer rows={[
              { k: "file", v: check.path },
              { k: "sha-256", v: check.sha256 },
              { k: "records", v: String(check.n_rows) },
              { k: "verdict", v: check.status },
            ]} summary="WEATHER PROVENANCE" />
          </div>
        </section>
      )}

      {series && (
        <>
          <section style={{ marginTop: 24 }}>
            <ThermalRibbon dryBulb={series.dry_bulb} figNo="FIG 2" place={series.name.replace(/_/g, " ")} />
          </section>
          <section style={{ marginTop: 18, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(420px, 100%), 1fr))", gap: 18 }}>
            <MonthHourFigure matrix={series.month_hour_matrix} name={series.name} />
            <DurationFigure dryBulb={series.dry_bulb} name={series.name} />
          </section>
        </>
      )}
    </>
  );
}

function MonthHourFigure({ matrix, name }: { matrix: (number | null)[][]; name: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useChart(ref, null, []);
  useChart(ref, {
    ...nbBase(),
    grid: { left: 44, right: 10, top: 10, bottom: 28 },
    xAxis: {
      type: "category", data: MONTHS,
      axisLine: { show: true, lineStyle: { color: NB_INK, width: 2 } },
      axisTick: { show: false },
      axisLabel: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 10 },
    },
    yAxis: {
      type: "category", data: ["0", "6", "12", "18", "24"],
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 10 },
    },
    visualMap: { show: false, min: 0, max: 30, inRange: { color: NB_HEAT_BINS } },
    series: [{
      type: "heatmap",
      data: matrix.flatMap((row) => row.map((v, h) => [h, 4 - h / 6, v])),
      label: { show: false },
      itemStyle: { borderWidth: 0 },
    }],
    tooltip: {
      confine: true, backgroundColor: "#FCDD28", borderColor: NB_INK, borderWidth: 2,
      textStyle: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 12 },
      extraCssText: "box-shadow: 4px 4px 0 #161616; border-radius: 4px;",
      formatter: (p: unknown) => {
        const q = p as { value: [number, number, number] };
        return `${MONTHS[q.value[0]]}, ${q.value[1] * 6}:00 — mean ${q.value[2]?.toFixed(1) ?? "–"} °C`;
      },
    },
  }, [matrix]);

  return (
    <Figure figNo="FIG 3" caption="month × hour mean dry-bulb temperature (°C)">
      <div ref={ref} style={{ height: 280 }} role="img" aria-label="Month by hour mean temperature heat map" />
      <ExportBar chartRef={chartRef} figureName={`fig_month_hour_${name}`}
        caption={`Month by hour mean dry-bulb temperature for ${name}.`}
        csv={{ header: ["month", ...Array.from({ length: 24 }, (_, h) => `h${h + 1}`)], rows: matrix.map((row, m) => [MONTHS[m], ...row]) }} />
    </Figure>
  );
}

function DurationFigure({ dryBulb, name }: { dryBulb: (number | null)[]; name: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useChart(ref, null, []);
  const sorted = useMemo(
    () => dryBulb.filter((v): v is number => v !== null).sort((a, b) => a - b),
    [dryBulb],
  );
  useChart(ref, {
    ...nbBase(),
    grid: { left: 48, right: 12, top: 10, bottom: 30 },
    xAxis: {
      type: "value", min: 0, max: 100,
      axisLabel: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 10, formatter: "{value}%" },
      splitLine: { lineStyle: { color: "#D8CCB9", type: [4, 4] } },
      axisLine: { show: false }, axisTick: { show: false },
    },
    yAxis: {
      type: "value", name: "°C",
      nameTextStyle: { fontFamily: "IBM Plex Mono, monospace", fontSize: 10, color: NB_INK },
      axisLine: { show: true, lineStyle: { color: NB_INK, width: 2 } },
      axisLabel: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 10 },
      splitLine: { lineStyle: { color: "#D8CCB9", type: [4, 4] } },
    },
    series: [{
      type: "line", data: sorted, symbol: "none",
      lineStyle: { color: NB_INK, width: 3 },
      areaStyle: { color: "rgba(252, 221, 40, 0.35)" },
      ...(nbThresholdLine(26, "26 °C") as object),
    }],
    tooltip: {
      confine: true, backgroundColor: "#FCDD28", borderColor: NB_INK, borderWidth: 2,
      textStyle: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 12 },
      extraCssText: "box-shadow: 4px 4px 0 #161616; border-radius: 4px;",
      valueFormatter: (v: unknown) => `${Number(v).toFixed(1)} °C`,
    },
  }, [sorted]);

  const over26 = sorted.filter((v) => v >= 26).length;
  return (
    <Figure figNo="FIG 4" caption="dry-bulb duration curve — % of annual hours at or above temperature"
      meta={<span>{over26} h ≥ 26 °C</span>}>
      <div ref={ref} style={{ height: 280 }} role="img"
        aria-label={`Duration curve; ${over26} hours at or above 26 degrees Celsius.`} />
      <ExportBar chartRef={chartRef} figureName={`fig_duration_${name}`}
        caption={`Dry-bulb duration curve for ${name}: ${over26} hours at or above 26 °C.`}
        csv={{ header: ["rank_pct", "dry_bulb_c"], rows: sorted.map((v, i) => [Math.round((i / Math.max(1, sorted.length - 1)) * 1000) / 10, v]) }} />
    </Figure>
  );
}
