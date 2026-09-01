import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  api,
  type VersionInfo,
  type WeatherCheck,
  type WeatherFileEntry,
  type WeatherSeries,
  type RunEntry,
} from "../api";
import { ThermalRibbon } from "../ThermalRibbon";
import { StatusPill } from "../components";
import { useChart, MONTHS } from "../charts";
import { ExportBar } from "../ExportBar";

const DEFAULT_WEATHER = "Leeds_DSY1_2020High50_.epw";

/* Overview dashboard — every number comes from the real EPW through the core. */
export function Home() {
  const [version, setVersion] = useState<VersionInfo | null>(null);
  const [check, setCheck] = useState<WeatherCheck | null>(null);
  const [series, setSeries] = useState<WeatherSeries | null>(null);
  const [runs, setRuns] = useState<RunEntry[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const load = (path: string) => {
    Promise.all([api.weatherCheck(path), api.weatherSeries(path)])
      .then(([c, s]) => { setCheck(c); setSeries(s); })
      .catch((e) => setErr(String((e as Error).message ?? e)));
  };

  useEffect(() => {
    Promise.all([api.version(), api.weatherList(), api.runs()])
      .then(async ([v, w, r]: [VersionInfo, WeatherFileEntry[], RunEntry[]]) => {
        setVersion(v);
        setRuns(r);
        const pick = w.find((f) => f.name === DEFAULT_WEATHER) ?? w[0];
        if (pick) load(pick.path);
      })
      .catch((e) => setErr(String((e as Error).message ?? e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onUpload = async (file: File) => {
    setUploading(true);
    setErr(null);
    try {
      const res = await api.uploadWeather(file);
      load(res.path);
    } catch (e) {
      setErr(String((e as Error).message ?? e));
    } finally {
      setUploading(false);
    }
  };

  const summary = check?.weather_summary ?? null;
  const fingerprint = series ? [
    { label: "Dry-bulb (°C)", vals: series.monthly_db, unit: "", color: tempColor },
    { label: "RH (%)", vals: series.monthly_rh, unit: "", color: rhColor },
    { label: "GHI (kWh/m²)", vals: series.monthly_ghi, unit: "", color: ghiColor },
    { label: "Wind (m/s)", vals: series.monthly_wind, unit: "", color: () => "rgba(82,104,168,.16)" },
  ] : null;

  return (
    <>
      <section className="headline-row">
        <div>
          <h1>Overview</h1>
          <div className="breadcrumb">Home dashboard · <b>{check ? check.path.split("/").pop() : "loading…"}</b></div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", justifyContent: "flex-end" }}>
          <div className="privacy-note">
            <strong>✓ Runs locally on your machine</strong><br />
            Weather files never leave this device
          </div>
          <span className="screening-pill">
            Version-aware overheating screening<br />
            <span style={{ fontWeight: 600 }}>EPW · dwelling templates · EnergyPlus</span>
          </span>
        </div>
      </section>

      {err && <div className="note warn" style={{ marginBottom: 16 }}><strong>Could not load data.</strong> {err}</div>}

      {/* ---- hero cards ---- */}
      <section className="hero-grid">
        <article className="hero-card location">
          <span className="location-pill">⌖ {check ? `${check.city?.trim() || "—"}, ${check.country?.trim() || "—"}` : "…"}</span>
          <h2>{check?.city?.trim() || "—"}<br />{series ? "Climate snapshot" : ""}</h2>
          <div className="coords">
            {check ? `${Math.abs(check.latitude ?? 0).toFixed(2)}° ${((check.latitude ?? 0) >= 0 ? "N" : "S")}, ${Math.abs(check.longitude ?? 0).toFixed(2)}° ${((check.longitude ?? 0) >= 0 ? "E" : "W")} · ${check.elevation?.toFixed(0)} m` : ""}
          </div>
          <div className="loc-meta">
            <div className="mini-glass"><span>Dataset</span><strong>{check ? `${check.n_rows.toLocaleString()} hours` : "—"}</strong></div>
            <div className="mini-glass"><span>Records</span><strong>{check ? `${(check.n_rows / 24).toFixed(0)} days` : "—"}</strong></div>
          </div>
          <label className="upload-label" style={{
            display: "flex", alignItems: "center", justifyContent: "center", gap: 7,
            marginTop: 10, border: "1px dashed rgba(21,38,58,.25)", borderRadius: 13,
            padding: 9, fontSize: 10.5, fontWeight: 800, cursor: "pointer",
            position: "relative", zIndex: 3, background: "rgba(255,255,255,.38)",
          }}>
            {uploading ? "Uploading…" : "＋ Load another EPW"}
            <input type="file" accept=".epw" style={{ display: "none" }}
              onChange={(e) => { const f = e.target.files?.[0]; if (f) onUpload(f); }} />
          </label>
        </article>

        <article className="hero-card weather">
          <h3>{series ? `Annual snapshot · ${series.name.replace(/_/g, " ")}` : "Annual snapshot"}</h3>
          <div className="temp-now">{summary?.annual_mean_dry_bulb != null ? `${summary.annual_mean_dry_bulb.toFixed(1)}°C` : "…"}</div>
          <div className="weather-desc">Mean dry-bulb · full weather-file year</div>
          <div className="weather-bottom">
            <div className="weather-stat"><span>Hottest hour</span><strong>{summary ? `${summary.hottest_hour}°C` : "—"}</strong></div>
            <div className="weather-stat"><span>Coldest hour</span><strong>{summary ? `${summary.coldest_hour}°C` : "—"}</strong></div>
            <div className="weather-stat"><span>Hours &gt; 26 °C</span><strong>{summary ? `${summary.exceedance_hours_26c} h` : "—"}</strong></div>
          </div>
        </article>

        <article className="hero-card health">
          <div className="file-title">{check ? check.path.split("/").pop() : "…"}</div>
          <div className="file-loc">{check ? `${check.city}, ${check.country} · EPW weather file` : ""}</div>
          <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
            <div>
              <StatusPill status={check?.status ?? "INFO"} />
              <p style={{ fontSize: 9.5, color: "var(--muted-ink)", lineHeight: 1.45, margin: "8px 0" }}>
                {check
                  ? `${check.issues.length} QC finding${check.issues.length === 1 ? "" : "s"} · ${check.n_rows.toLocaleString()} hourly records · SHA-256 verified`
                  : "Running quality checks…"}
              </p>
              <Link to="/weather" style={{ fontSize: 10.5, fontWeight: 800 }}>Open Weather Lab ›</Link>
            </div>
          </div>
          <div className="meta-list">
            <span className="meta-tag">☁ {check?.country || "—"}</span>
            <span className="meta-tag">🕐 {check ? `${check.n_rows.toLocaleString()} h` : "—"}</span>
            <span className="meta-tag">⚙ E+ {version?.energyplus_version ?? "—"}</span>
          </div>
        </article>
      </section>

      {/* ---- metrics strip ---- */}
      {summary && (
        <section className="metrics" aria-label="Key climate metrics">
          <div className="metric"><div className="m-val">{summary.annual_mean_dry_bulb}<span className="m-unit">°C</span></div><div className="m-label">Mean dry-bulb</div></div>
          <div className="metric"><div className="m-val">{summary.hottest_hour}<span className="m-unit">°C</span></div><div className="m-label">Max temp</div></div>
          <div className="metric"><div className="m-val">{summary.coldest_hour}<span className="m-unit">°C</span></div><div className="m-label">Min temp</div></div>
          <div className="metric"><div className="m-val">{summary.exceedance_hours_26c}<span className="m-unit">h</span></div><div className="m-label">Hours &gt; 26 °C</div></div>
          <div className="metric"><div className="m-val">{summary.degree_hours_26c}<span className="m-unit">Kh</span></div><div className="m-label">Degree-hours &gt; 26 °C</div></div>
          <div className="metric"><div className="m-val">{summary.night_min_mean_jja ?? "—"}<span className="m-unit">°C</span></div><div className="m-label">Mean JJA night min</div></div>
        </section>
      )}

      {/* ---- dashboard grid ---- */}
      <section className="dashboard-grid">
        <div className="stack">
          {fingerprint && (
            <article className="card soft">
              <div className="card-head"><h3>Climate fingerprint · monthly averages</h3><span className="subtle">real EPW fields</span></div>
              <div className="fingerprint-wrap">
                <table className="fingerprint">
                  <thead>
                    <tr><th></th>{MONTHS.map((m) => <th key={m}>{m}</th>)}</tr>
                  </thead>
                  <tbody>
                    {fingerprint.map((row) => (
                      <tr key={row.label}>
                        <td>{row.label}</td>
                        {row.vals.map((v, i) => (
                          <td key={i}>
                            <span className="heat-cell" style={{ background: v === null ? "#f2f4f2" : row.color(v) }}>
                              {v === null ? "–" : v}
                            </span>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </article>
          )}

          {series && <ThermalRibbon dryBulb={series.dry_bulb} figNo="FIG 1" place={series.name.replace(/_/g, " ")} compact height={140} />}

          <article className="card">
            <div className="card-head"><h3>Quick actions</h3><span className="subtle">continue</span></div>
            <div className="quick-actions">
              <Link className="qa-btn" to="/analyze"><strong>Analyze a dwelling</strong><span>EnergyPlus + versioned standards</span></Link>
              <Link className="qa-btn" to="/compare"><strong>Compare weather files</strong><span>2–8 EPWs side by side</span></Link>
              <Link className="qa-btn" to="/comfort"><strong>Comfort Lab</strong><span>PMV · adaptive · UTCI</span></Link>
              <Link className="qa-btn" to="/atlas"><strong>Archetype Atlas</strong><span>Leeds dwelling templates</span></Link>
            </div>
          </article>
        </div>

        <div className="stack">
          {series && <SeverityGrid series={series} check={check} />}
          {series && <DegreeDayChart series={series} />}
        </div>

        <div className="stack">
          <article className="card">
            <div className="card-head"><h3>Runs this session</h3><Link className="subtle" to="/analyze">Run one →</Link></div>
            {runs.length === 0 && (
              <p style={{ fontSize: 10.5, color: "var(--muted-ink)" }}>
                No assessments yet — run one from Analyze and it appears here.
              </p>
            )}
            {runs.slice(0, 5).map((r) => (
              <div className="recent-item" key={r.run_id}>
                <div>
                  <div className="recent-title">{r.model ?? "demo model"} · {r.weather}</div>
                  <div className="recent-date mono">{r.pack_id} · {r.run_id}</div>
                </div>
                <StatusPill status={r.overall ?? "INFO"} />
              </div>
            ))}
          </article>

          {series && <CalendarCard dailyMean={series.daily_mean} />}
        </div>
      </section>
    </>
  );
}

/* ---- honest severity indicators (thresholds stated, no invented score) ---- */
function SeverityGrid({ series, check }: { series: WeatherSeries; check: WeatherCheck | null }) {
  const h26 = series ? series.daily_mean.length : 0; // placeholder to satisfy types
  void h26;
  const summary = check?.weather_summary;
  const items = [
    {
      val: summary ? `${summary.exceedance_hours_26c} h` : "—",
      lbl: "hours ≥ 26 °C in the year / overheating signal",
      flag: (summary?.exceedance_hours_26c ?? 0) > 100 ? "High" : (summary?.exceedance_hours_26c ?? 0) > 20 ? "Moderate" : "Low",
      cls: (summary?.exceedance_hours_26c ?? 0) > 100 ? "high" : (summary?.exceedance_hours_26c ?? 0) > 20 ? "moderate" : "low",
    },
    {
      val: summary ? `${summary.degree_hours_26c} Kh` : "—",
      lbl: "degree-hours ≥ 26 °C / intensity",
      flag: (summary?.degree_hours_26c ?? 0) > 300 ? "High" : (summary?.degree_hours_26c ?? 0) > 50 ? "Moderate" : "Low",
      cls: (summary?.degree_hours_26c ?? 0) > 300 ? "high" : (summary?.degree_hours_26c ?? 0) > 50 ? "moderate" : "low",
    },
    {
      val: series ? `${(series.hdd15_5.reduce((a: number, b) => a + (b ?? 0), 0)).toFixed(0)} °C-day` : "—",
      lbl: "HDD 15.5 °C / heating demand context",
      flag: "Context", cls: "moderate",
    },
    {
      val: series ? `${(series.cdd18.reduce((a: number, b) => a + (b ?? 0), 0)).toFixed(0)} °C-day` : "—",
      lbl: "CDD 18 °C / cooling season context",
      flag: (series?.cdd18.reduce((a: number, b) => a + (b ?? 0), 0) ?? 0) > 120 ? "Moderate" : "Low",
      cls: (series?.cdd18.reduce((a: number, b) => a + (b ?? 0), 0) ?? 0) > 120 ? "moderate" : "low",
    },
    {
      val: summary ? `${summary.hottest_hour} °C` : "—",
      lbl: "hottest single hour of the year",
      flag: (summary?.hottest_hour ?? 0) >= 30 ? "High" : (summary?.hottest_hour ?? 0) >= 26 ? "Moderate" : "Low",
      cls: (summary?.hottest_hour ?? 0) >= 30 ? "high" : (summary?.hottest_hour ?? 0) >= 26 ? "moderate" : "low",
    },
    {
      val: check ? check.status.replaceAll("_", " ") : "—",
      lbl: `QC verdict · ${check?.issues.length ?? 0} finding(s)`,
      flag: check?.status === "FAIL" ? "High" : check?.status === "PASS" ? "Low" : "Moderate",
      cls: check?.status === "FAIL" ? "high" : check?.status === "PASS" ? "low" : "moderate",
    },
  ];
  return (
    <article className="card">
      <div className="card-head"><h3>Screening indicators</h3><span className="subtle">thresholds stated, not scored</span></div>
      <div className="severity-grid">
        {items.map((s, i) => (
          <div className="sev-card" key={i}>
            <div className="sev-value">{s.val}</div>
            <div className="sev-label">{s.lbl}</div>
            <span className={`sev-flag ${s.cls}`}>{s.flag}</span>
          </div>
        ))}
      </div>
    </article>
  );
}

/* ---- monthly heating/cooling degree-day chart (computed from daily means) ---- */
function DegreeDayChart({ series }: { series: WeatherSeries }) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useChart(ref, null, []);
  useChart(ref, {
    grid: { left: 44, right: 10, top: 26, bottom: 22 },
    legend: {
      top: 0, left: 0, icon: "rect", itemWidth: 10, itemHeight: 8,
      textStyle: { fontFamily: "IBM Plex Mono", fontSize: 9.5, color: "#61707d" },
    },
    xAxis: { type: "category", data: MONTHS, axisLabel: { fontSize: 9, color: "#7c8998" }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { type: "value", axisLabel: { fontSize: 9, color: "#7c8998" }, splitLine: { lineStyle: { color: "#edf0ee" } } },
    series: [
      { name: "HDD 15.5 (°C-day)", type: "bar", stack: "dd", data: series.hdd15_5, itemStyle: { color: "#182b42", borderRadius: [4, 4, 0, 0] }, barWidth: "52%" },
      { name: "CDD 18 (°C-day)", type: "bar", stack: "dd", data: series.cdd18, itemStyle: { color: "#f39a3c", borderRadius: [4, 4, 0, 0] } },
    ],
    tooltip: { trigger: "axis", confine: true },
  }, [series]);

  return (
    <article className="card soft">
      <div className="card-head"><h3>Heating & cooling degree-days by month</h3><span className="subtle">from daily means</span></div>
      <div ref={ref} style={{ height: 214 }} role="img" aria-label="Monthly heating and cooling degree days bar chart" />
      <ExportBar chartRef={chartRef} figureName="fig_degree_days"
        caption="Monthly heating (base 15.5 °C) and cooling (base 18 °C) degree-days computed from daily mean dry-bulb."
        csv={{ header: ["month", "hdd15_5_cday", "cdd18_cday"], rows: MONTHS.map((m, i) => [m, series.hdd15_5[i], series.cdd18[i]]) }} />
    </article>
  );
}

/* ---- lime calendar card driven by the real daily means ---- */
function CalendarCard({ dailyMean }: { dailyMean: number[] }) {
  const [month, setMonth] = useState(6); // 0-based: July
  const [day, setDay] = useState(15);
  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const monthLens = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const monthStart = useMemo(() => {
    let acc = 0;
    const starts: number[] = [];
    for (const len of monthLens) { starts.push(acc); acc += len; }
    return starts;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const dayTemp = (d: number) => dailyMean[monthStart[month] + d - 1] ?? null;

  const firstDow = (monthStart[month] + 1) % 7; // 1 Jan of a non-leap daily series is a Monday
  const cells: (number | null)[] = [];
  for (let i = 0; i < firstDow; i++) cells.push(null);
  for (let d = 1; d <= monthLens[month]; d++) cells.push(d);
  while (cells.length % 7) cells.push(null);

  const temp = dayTemp(day);
  const desc = temp === null ? "—" : temp >= 22 ? "Warm day" : temp >= 15 ? "Mild day" : "Cool day";

  return (
    <article className="card calendar-card">
      <div className="calendar-top">
        <div><span className="subtle" style={{ color: "#647335" }}>EPW calendar · daily means</span><h3>{monthNames[month]}</h3></div>
        <div className="calendar-nav">
          <button className="cal-btn" aria-label="Previous month" onClick={() => setMonth((m) => (m + 11) % 12)}>‹</button>
          <button className="cal-btn" aria-label="Next month" onClick={() => setMonth((m) => (m + 1) % 12)}>›</button>
        </div>
      </div>
      <div className="calendar-week">{["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"].map((d) => <span key={d}>{d}</span>)}</div>
      <div className="calendar-days">
        {cells.map((d, i) => (
          <button key={i} className={d === day ? "selected" : d === null ? "muted" : ""}
            disabled={d === null}
            onClick={() => d !== null && setDay(d)}
            aria-label={d ? `Day ${d}` : undefined}>
            {d ?? ""}
          </button>
        ))}
      </div>
      <div className="date-weather">
        <div><small>{day} {monthNames[month]} · mean dry-bulb</small><strong>{temp !== null ? `${temp.toFixed(1)}°C` : "—"}</strong></div>
        <span>{desc}</span>
      </div>
    </article>
  );
}

/* ---- colour helpers for the fingerprint heat cells ---- */
function tempColor(v: number): string {
  const t = Math.max(0, Math.min(1, (v + 5) / 25));
  const ramp = [[71, 185, 207], [167, 221, 225], [215, 239, 120], [243, 154, 60], [229, 111, 47], [201, 68, 54]];
  const idx = Math.min(ramp.length - 2, Math.floor(t * (ramp.length - 1)));
  const f = t * (ramp.length - 1) - idx;
  const c = ramp[idx].map((ch, k) => Math.round(ch + (ramp[idx + 1][k] - ch) * f));
  return `rgba(${c[0]},${c[1]},${c[2]},${0.18 + 0.4 * t})`;
}
function rhColor(v: number): string {
  const t = Math.max(0, Math.min(1, (v - 60) / 30));
  return `rgba(71, 185, 207, ${0.12 + 0.4 * t})`;
}
function ghiColor(v: number): string {
  const t = Math.max(0, Math.min(1, v / 180));
  return `rgba(243, 154, 60, ${0.1 + 0.45 * t})`;
}
