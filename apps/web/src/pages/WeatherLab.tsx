import { useEffect, useMemo, useRef, useState } from "react";
import { api, type WeatherCheck, type WeatherFileEntry, type WeatherSeries } from "../api";
import { Figure, StatusPill } from "../components";
import { ThermalRibbon } from "../ThermalRibbon";
import { useChart, TEMP_SCALE, MONTHS } from "../charts";

export function WeatherLab() {
  const [files, setFiles] = useState<WeatherFileEntry[] | null>(null);
  const [selected, setSelected] = useState<WeatherFileEntry | null>(null);
  const [check, setCheck] = useState<WeatherCheck | null>(null);
  const [series, setSeries] = useState<WeatherSeries | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.weatherList().then((fs) => {
      setFiles(fs);
      const pick = fs.find((f) => f.name === "Leeds_DSY1_2020High50_.epw") ?? fs[0];
      if (pick) setSelected(pick);
    }).catch((e) => setError(String(e.message ?? e)));
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

  return (
    <>
      <h1 className="page-title">Weather Lab</h1>
      <p className="page-intro">
        Pick a weather file from the local library. OverheatLens checks its structure and
        physics, then draws the climate — the same data every assessment starts from.
      </p>

      <section style={{ marginTop: 22, maxWidth: 720 }}>
        <label htmlFor="epw" style={{ fontFamily: "var(--font-mono)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.07em", color: "var(--muted-ink)" }}>
          Weather file
        </label>
        <select
          id="epw"
          value={selected?.path ?? ""}
          onChange={(e) => {
            const f = files?.find((x) => x.path === e.target.value);
            if (f) setSelected(f);
          }}
          style={{
            display: "block", width: "100%", marginTop: 6, padding: "9px 12px",
            border: "1px solid var(--line-strong)", borderRadius: 6,
            background: "var(--surface)", font: "inherit", color: "var(--ink)",
          }}
        >
          {files?.map((f) => (
            <option key={f.path} value={f.path}>{f.name}</option>
          ))}
        </select>
        {selected && (
          <p style={{ marginTop: 8, fontFamily: "var(--font-mono)", fontSize: 11.5, color: "var(--muted-ink)" }}>
            TM59:2017 <StatusPill status={selected.compat_2017} /> ·&nbsp;
            TM59:2026 <StatusPill status={selected.compat_2026} />
          </p>
        )}
      </section>

      {error && <div className="note warn" style={{ marginTop: 20 }}><strong>Could not load this file.</strong> {error}</div>}

      {check && (
        <section className="more-above" style={{ marginTop: 34 }}>
          <div className="metrics" aria-label="Quality summary">
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
              </>
            )}
          </div>
          {check.weather_summary && (
            <p style={{ marginTop: 8, fontFamily: "var(--font-mono)", fontSize: 11.5, color: "var(--muted-ink)" }}>
              sha256 {check.sha256.slice(0, 16)}… · {check.city}, {check.country}
            </p>
          )}
          {check.issues.length > 0 && (
            <div className="table-wrap" style={{ marginTop: 14 }}>
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
            <p style={{ marginTop: 14, color: "var(--muted-ink)", fontSize: 13.5 }}>
              All checks passed — no structural or physical-plausibility findings.
            </p>
          )}
        </section>
      )}

      {series && (
        <>
          <section style={{ marginTop: 34 }}>
            <ThermalRibbon dryBulb={series.dry_bulb} figNo="FIG 2" place={series.name.replace(/_/g, " ")} />
          </section>
          <section style={{ marginTop: 22, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))", gap: 18 }}>
            <MonthHourFigure matrix={series.month_hour_matrix} />
            <DurationFigure dryBulb={series.dry_bulb} />
          </section>
        </>
      )}
    </>
  );
}

function MonthHourFigure({ matrix }: { matrix: (number | null)[][] }) {
  const ref = useRef<HTMLDivElement>(null);
  useChart(ref, {
    grid: { left: 44, right: 10, top: 10, bottom: 24 },
    xAxis: { type: "category", data: MONTHS, axisLabel: { color: "#5e686e", fontFamily: "IBM Plex Mono", fontSize: 10 }, axisLine: { lineStyle: { color: "#b7b8b3" } }, axisTick: { show: false } },
    yAxis: { type: "category", data: ["0", "6", "12", "18", "24"], axisLabel: { color: "#5e686e", fontFamily: "IBM Plex Mono", fontSize: 10 }, axisLine: { show: false }, axisTick: { show: false } },
    visualMap: { show: false, min: 0, max: 30, inRange: { color: TEMP_SCALE.map((s) => s[1]) } },
    series: [{
      type: "heatmap",
      data: matrix.flatMap((row) => row.map((v, h) => [h, 4 - h / 6, v])),
      label: { show: false },
    }],
    tooltip: { confine: true, formatter: (p: unknown) => {
      const q = p as { value: [number, number, number] };
      return `${MONTHS[q.value[0]]}, ${q.value[1] * 6}:00 — mean ${q.value[2]?.toFixed(1) ?? "–"} °C`;
    } },
  }, [matrix]);

  return (
    <Figure figNo="FIG 3" caption="month × hour mean dry-bulb temperature (°C)">
      <div ref={ref} style={{ height: 260 }} role="img" aria-label="Month by hour mean temperature heat map" />
    </Figure>
  );
}

function DurationFigure({ dryBulb }: { dryBulb: (number | null)[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const sorted = useMemo(
    () => dryBulb.filter((v): v is number => v !== null).sort((a, b) => a - b),
    [dryBulb],
  );
  useChart(ref, {
    grid: { left: 44, right: 12, top: 10, bottom: 26 },
    xAxis: {
      type: "value", min: 0, max: 100,
      axisLabel: { color: "#5e686e", fontFamily: "IBM Plex Mono", fontSize: 10, formatter: "{value}%" },
      splitLine: { lineStyle: { color: "#eae8e2" } },
      axisLine: { show: false }, axisTick: { show: false },
    },
    yAxis: {
      type: "value", name: "°C", nameTextStyle: { fontFamily: "IBM Plex Mono", fontSize: 10, color: "#5e686e" },
      axisLabel: { color: "#5e686e", fontFamily: "IBM Plex Mono", fontSize: 10 },
      splitLine: { lineStyle: { color: "#eae8e2" } },
    },
    series: [{
      type: "line", data: sorted, symbol: "none",
      lineStyle: { color: "#1f5f70", width: 1.8 },
      areaStyle: { color: "rgba(31, 95, 112, 0.06)" },
      markLine: {
        symbol: "none", silent: true,
        lineStyle: { color: "#d4553d", type: "dashed", width: 1 },
        label: { fontFamily: "IBM Plex Mono", fontSize: 10, color: "#d4553d", formatter: "26 °C" },
        data: [{ yAxis: 26 }],
      },
    }],
    tooltip: { confine: true, valueFormatter: (v: unknown) => `${Number(v).toFixed(1)} °C` },
  }, [sorted]);

  const over26 = sorted.filter((v) => v >= 26).length;
  return (
    <Figure figNo="FIG 4" caption="dry-bulb duration curve — % of annual hours at or above temperature"
      meta={<span>{over26} h ≥ 26 °C</span>}>
      <div ref={ref} style={{ height: 260 }} role="img"
        aria-label={`Duration curve; ${over26} hours at or above 26 degrees Celsius.`} />
    </Figure>
  );
}
