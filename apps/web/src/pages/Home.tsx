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
import { EmptyState, StatusPill } from "../components";
import { useChart, MONTHS, NB_INK, NB_PAPER } from "../charts";
import { ExportBar } from "../ExportBar";

const BASE = import.meta.env.BASE_URL || "./";
const DEFAULT_WEATHER = "Leeds_DSY1_2020High50_.epw";

/* Laboratory desktop: entry actions, case-file modules, live climate
   evidence from the real EPW through the core. */
export function Home() {
  const [version, setVersion] = useState<VersionInfo | null>(null);
  const [check, setCheck] = useState<WeatherCheck | null>(null);
  const [series, setSeries] = useState<WeatherSeries | null>(null);
  const [runs, setRuns] = useState<RunEntry[]>([]);
  const [packs, setPacks] = useState<{ rule_pack: string }[]>([]);
  const [err, setErr] = useState<string | null>(null);

  const load = (path: string) => {
    Promise.all([api.weatherCheck(path), api.weatherSeries(path)])
      .then(([c, s]) => { setCheck(c); setSeries(s); })
      .catch((e) => setErr(String((e as Error).message ?? e)));
  };

  useEffect(() => {
    Promise.all([api.version(), api.weatherList(), api.runs(), api.rulePacks()])
      .then(async ([v, w, r, p]: [VersionInfo, WeatherFileEntry[], RunEntry[], { rule_pack: string }[]]) => {
        setVersion(v);
        setRuns(r);
        setPacks(p);
        const pick = w.find((f) => f.name === DEFAULT_WEATHER) ?? w[0];
        if (pick) load(pick.path);
      })
      .catch((e) => setErr(String((e as Error).message ?? e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const summary = check?.weather_summary ?? null;
  const fingerprint = series ? [
    { label: "Dry-bulb (°C)", vals: series.monthly_db, unit: "", color: tempColor },
    { label: "RH (%)", vals: series.monthly_rh, unit: "", color: rhColor },
    { label: "GHI (kWh/m²)", vals: series.monthly_ghi, unit: "", color: ghiColor },
    { label: "Wind (m/s)", vals: series.monthly_wind, unit: "", color: () => "#FBFAF6" },
  ] : null;

  return (
    <>
      {/* ---- laboratory hero ---- */}
      <section className="lab-hero">
        <img className="hero-art" src={`${BASE}img/cover-home.png`}
          alt="Neo-Brutalist collage of terraced houses, a tower block, sun path and heat plume"
          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
        <div className="hero-copy">
          <h1>OVERHEATLENS</h1>
          <span className="tagline">BUILDING × WEATHER × HEAT × EVIDENCE</span>
          <p style={{ marginTop: 14, maxWidth: "70ch", fontSize: 14 }}>
            A digital overheating laboratory: weather quality → model readiness →
            EnergyPlus simulation → versioned standards → comfort → mitigation →
            reproducible evidence. Local-first — your files never leave this machine.
          </p>
          <div className="hero-actions">
            <Link className="nb-btn" to="/analyze">RUN A MODEL</Link>
            <Link className="nb-btn secondary" to="/atlas">EXPLORE ARCHETYPE ATLAS</Link>
            <Link className="nb-btn dark" to="/weather">OPEN WEATHER LAB</Link>
          </div>
        </div>
      </section>

      {err && <div className="note warn" style={{ marginBottom: 16 }}><strong>Could not load data.</strong> {err}</div>}

      {/* ---- research status strip ---- */}
      <section className="metrics" aria-label="Research status" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        <div className="metric">
          <div className="m-val">{packs.length}<span className="m-unit">packs</span></div>
          <div className="m-label">Versioned standards · source-verified</div>
        </div>
        <div className="metric">
          <div className="m-val">{version?.energyplus_version ?? "—"}</div>
          <div className="m-label">EnergyPlus engine (local)</div>
        </div>
        <div className="metric">
          <div className="m-val">{runs.length}<span className="m-unit">runs</span></div>
          <div className="m-label">Experiments in archive</div>
        </div>
        <div className="metric">
          <div className="m-val">{check ? check.n_rows.toLocaleString() : "—"}<span className="m-unit">h</span></div>
          <div className="m-label">{check ? check.path.split("/").pop() : "Reference weather"}</div>
        </div>
      </section>

      {/* ---- case-file modules ---- */}
      <section aria-label="Laboratory modules">
        <h2 className="section-h" style={{ marginBottom: 12 }}>Laboratory desktop</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 16, marginBottom: 20 }}>
          <ModuleFolder to="/analyze" tab="01" title="ANALYZE" desc="Model × weather × standard → EnergyPlus run" accent="var(--nb-yellow)" />
          <ModuleFolder to="/weather" tab="02" title="WEATHER LAB" desc="EPW quality, dossier & compatibility" accent="var(--nb-cyan)" />
          <ModuleFolder to="/atlas" tab="03" title="ARCHETYPE ATLAS" desc="15 research models + templates" accent="var(--nb-orange)" />
          <ModuleFolder to="/comfort" tab="04" title="COMFORT LAB" desc="PMV · adaptive · UTCI, gated" accent="var(--nb-green)" />
          <ModuleFolder to="/compare" tab="05" title="COMPARE" desc="Weather · runs · scenarios" accent="var(--nb-pink)" />
          <ModuleFolder to="/mitigation" tab="06" title="MITIGATION LAB" desc="Harehills parametric evidence" accent="var(--nb-violet)" />
          <ModuleFolder to="/runs" tab="07" title="RUN ARCHIVE" desc="Every experiment, reproducible" accent="var(--nb-bg)" />
          <ModuleFolder to="/validation" tab="08" title="VALIDATION" desc="Live evidence register" accent="var(--nb-bg)" />
        </div>
      </section>

      {/* ---- live climate evidence ---- */}
      <section className="headline-row" style={{ marginBottom: 12 }}>
        <h2 className="section-h">Reference climate · {check ? check.path.split("/").pop() : "loading…"}</h2>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <StatusPill status={check?.status ?? "INFO"} />
          <Link className="nb-btn secondary" style={{ minHeight: 38 }} to="/weather">Open Weather Lab ›</Link>
        </div>
      </section>

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
                            <span className="heat-cell" style={{ background: v === null ? "#F1E8D6" : row.color(v) }}>
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
        </div>

        <div className="stack">
          {series && <SeverityGrid series={series} check={check} />}
          {series && <DegreeDayChart series={series} />}
        </div>

        <div className="stack">
          <article className="card">
            <div className="card-head"><h3>Recent experiments</h3><Link className="subtle" to="/runs">Archive →</Link></div>
            {runs.length === 0 && (
              <EmptyState img="empty-runs.png" alt="Empty experiment shelf illustration"
                title="NO EXPERIMENTS YET"
                body="Run your first model × weather × standard analysis and it lands here with a run ID, hashes and provenance."
                action={<Link className="nb-btn" to="/analyze">Run EnergyPlus</Link>} />
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

function ModuleFolder({ to, tab, title, desc, accent }: {
  to: string; tab: string; title: string; desc: string; accent: string;
}) {
  return (
    <Link to={to} className="case-folder" style={{ textDecoration: "none", color: "inherit" }}>
      <span className="case-tab">{tab}</span>
      <span className="case-body" style={{ display: "block", background: accent }}>
        <span className="case-title" style={{ fontSize: 17 }}>{title}</span>
        <span style={{ display: "block", fontSize: 11.5, marginTop: 4 }}>{desc}</span>
        <span className="nb-chip" style={{ marginTop: 10 }}>OPEN ›</span>
      </span>
    </Link>
  );
}

/* ---- honest severity indicators (thresholds stated, no invented score) ---- */
function SeverityGrid({ series, check }: { series: WeatherSeries; check: WeatherCheck | null }) {
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
    backgroundColor: NB_PAPER,
    grid: { left: 44, right: 10, top: 30, bottom: 24 },
    legend: {
      top: 0, left: 0, icon: "rect", itemWidth: 14, itemHeight: 10,
      textStyle: { fontFamily: "IBM Plex Mono, monospace", fontSize: 10, color: NB_INK },
    },
    xAxis: {
      type: "category", data: MONTHS,
      axisLine: { show: true, lineStyle: { color: NB_INK, width: 2 } },
      axisTick: { show: false },
      axisLabel: { fontSize: 10, color: NB_INK, fontFamily: "IBM Plex Mono, monospace" },
    },
    yAxis: {
      type: "value",
      axisLine: { show: true, lineStyle: { color: NB_INK, width: 2 } },
      axisLabel: { fontSize: 10, color: NB_INK, fontFamily: "IBM Plex Mono, monospace" },
      splitLine: { lineStyle: { color: "#D8CCB9", type: [4, 4] } },
    },
    series: [
      {
        name: "HDD 15.5 (°C-day)", type: "bar", stack: "dd", data: series.hdd15_5,
        itemStyle: { color: "#161616", borderColor: "#161616", borderWidth: 1 }, barWidth: "54%",
      },
      {
        name: "CDD 18 (°C-day)", type: "bar", stack: "dd", data: series.cdd18,
        itemStyle: { color: "#F36D30", borderColor: "#161616", borderWidth: 1 },
      },
    ],
    tooltip: {
      trigger: "axis", confine: true, backgroundColor: "#FCDD28",
      borderColor: NB_INK, borderWidth: 2,
      textStyle: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 12 },
      extraCssText: "box-shadow: 4px 4px 0 #161616; border-radius: 4px;",
    },
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

/* ---- calendar card driven by the real daily means ---- */
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
        <div><span className="subtle">EPW calendar · daily means</span><h3>{monthNames[month]}</h3></div>
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

/* ---- stepped heat fills for the fingerprint cells ---- */
function tempColor(v: number): string {
  if (v < 0) return "#12C8B0";
  if (v < 5) return "#8FE3D4";
  if (v < 10) return "#FCDD28";
  if (v < 15) return "#F36D30";
  if (v < 20) return "#FF4F85";
  return "#D63A2F";
}
function rhColor(v: number): string {
  if (v < 70) return "#FBFAF6";
  if (v < 78) return "#8FE3D4";
  return "#12C8B0";
}
function ghiColor(v: number): string {
  if (v < 40) return "#FBFAF6";
  if (v < 90) return "#FCDD28";
  if (v < 150) return "#F36D30";
  return "#FF4F85";
}
