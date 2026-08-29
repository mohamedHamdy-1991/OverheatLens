import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type VersionInfo, type StandardsPassport, type WeatherFileEntry, type WeatherSeries } from "../api";
import { ThermalRibbon } from "../ThermalRibbon";
import { StatusPill } from "../components";

const DEFAULT_WEATHER = "Leeds_DSY1_2020High50_.epw";

export function Home() {
  const [version, setVersion] = useState<VersionInfo | null>(null);
  const [packs, setPacks] = useState<StandardsPassport[]>([]);
  const [files, setFiles] = useState<WeatherFileEntry[]>([]);
  const [series, setSeries] = useState<WeatherSeries | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.version(),
      api.rulePacks(),
      api.weatherList(),
    ]).then(async ([v, p, w]: [VersionInfo, StandardsPassport[], WeatherFileEntry[]]) => {
      setVersion(v);
      setPacks(p);
      setFiles(w);
      const pick = w.find((f) => f.name === DEFAULT_WEATHER) ?? w[0];
      if (pick) setSeries(await api.weatherSeries(pick.path));
    }).catch((e) => setErr(String(e.message ?? e)));
  }, []);

  const verified = packs.filter((p) => p.source_status === "source_verified").length;

  return (
    <>
      <header style={{ maxWidth: 900 }}>
        <h1 className="page-title" style={{ fontSize: 40, maxWidth: "18ch" }}>
          See where overheating begins.
        </h1>
        <p className="page-intro" style={{ fontSize: 16.5, marginTop: 12 }}>
          Open, reproducible building-overheating assessment, weather intelligence and
          thermal-comfort analysis — from weather-file quality through EnergyPlus
          simulation to versioned standards evidence.
        </p>
        <div style={{ display: "flex", gap: 12, marginTop: 22, flexWrap: "wrap" }}>
          <Link to="/analyze" className="btn">Analyze a building</Link>
          <Link to="/atlas" className="btn secondary">Explore an archetype</Link>
        </div>
        <p style={{ marginTop: 14, fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--muted-ink)" }}>
          EnergyPlus {version?.energyplus_version ?? "—"}-powered · version-aware TM59 / Part O workflows · open methodology
        </p>
      </header>

      {err && (
        <div className="note warn" style={{ marginTop: 24 }}>
          <strong>API unavailable.</strong> {err} — start the app with
          “Start&nbsp;OverheatLens”, then reload this page.
        </div>
      )}

      {series && (
        <section style={{ marginTop: 36 }} aria-label="Live thermal year of the default weather file">
          <ThermalRibbon dryBulb={series.dry_bulb} figNo="FIG 1" place={series.name.replace(/_/g, " ")} height={210} />
        </section>
      )}

      <section className="more-above" aria-label="Start a task">
        <h2 className="section-h">Start here</h2>
        <div className="table-wrap">
          <table className="data" style={{ minWidth: 0 }}>
            <tbody>
              {[
                { to: "/analyze", t: "Analyze a building", d: "Run the demo dwelling through EnergyPlus and evaluate it against a versioned overheating standard." },
                { to: "/weather", t: "Check a weather file", d: `Quality-check any EPW in the local library — ${files.filter((f) => !f.name.startsWith("[fixture]")).length} files found.` },
                { to: "/validation", t: "See the evidence", d: "The live validation matrix behind every number this tool prints." },
              ].map((r) => (
                <tr key={r.to}>
                  <td style={{ width: 240 }}>
                    <Link to={r.to} style={{ fontWeight: 600 }}>{r.t} →</Link>
                  </td>
                  <td style={{ color: "var(--muted-ink)" }}>{r.d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="more-above" aria-label="Standards and evidence status">
        <h2 className="section-h">What this tool implements — and what it doesn’t yet</h2>
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Rule pack</th>
                <th>Edition</th>
                <th>Criteria</th>
                <th>Source status</th>
              </tr>
            </thead>
            <tbody>
              {packs.map((p) => (
                <tr key={p.rule_pack}>
                  <td className="mono">{p.rule_pack}</td>
                  <td>{p.edition}</td>
                  <td className="mono">{p.criteria_ids.join(", ") || "—"}</td>
                  <td><StatusPill status={p.source_status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p style={{ marginTop: 10, fontFamily: "var(--font-mono)", fontSize: 11.5, color: "var(--muted-ink)" }}>
          {verified}/{packs.length} rule packs source-verified against the official documents ·
          core {version?.core_version ?? "—"} · EnergyPlus {version?.energyplus_version ?? "not found"}
        </p>
      </section>
    </>
  );
}
