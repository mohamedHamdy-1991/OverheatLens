import { useEffect, useMemo, useState } from "react";
import { api, type WeatherFileEntry } from "../api";
import { ThermalRibbon } from "../ThermalRibbon";
import { StatusPill } from "../components";

interface CompareFile {
  name: string;
  path: string;
  annual_mean: number;
  hottest: number;
  hours_over_26: number;
  degree_hours_26: number;
  daily_mean: number[];
}

export function Compare() {
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
      <h1 className="page-title">Compare</h1>
      <p className="page-intro">
        Put 2–8 weather files side by side: aligned thermal years, headline metrics, and
        deltas against the first file — the same series the assessments use.
      </p>

      <section style={{ marginTop: 20 }}>
        <div style={labelStyle}>Weather library — pick 2 to 8</div>
        <div className="table-wrap" style={{ maxHeight: 260, overflowY: "auto" }}>
          <table className="data" style={{ minWidth: 0 }}>
            <tbody>
              {files?.filter((f) => !f.name.startsWith("[fixture]")).map((f) => (
                <tr key={f.path} onClick={() => toggle(f.path)}
                  style={{ cursor: "pointer" }}>
                  <td style={{ width: 34 }}>
                    <input type="checkbox" checked={picked.includes(f.path)}
                      onChange={() => toggle(f.path)}
                      aria-label={`Select ${f.name}`} />
                  </td>
                  <td className="mono" style={{ fontSize: 12 }}>{f.name}</td>
                  <td style={{ width: 150 }}>
                    <StatusPill status={f.compat_2017} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ marginTop: 14, display: "flex", gap: 12, alignItems: "center" }}>
          <button className="btn" onClick={run} disabled={!canRun || busy}>
            {busy ? "Loading…" : `Compare ${picked.length} files`}
          </button>
          {!canRun && (
            <span style={{ fontSize: 13, color: "var(--muted-ink)" }}>
              select at least two files
            </span>
          )}
        </div>
      </section>

      {err && <div className="note warn" style={{ marginTop: 16 }}><strong>Compare failed.</strong> {err}</div>}

      {data && (
        <>
          <section className="more-above" style={{ display: "grid", gap: 18, gridTemplateColumns: "repeat(auto-fit, minmax(460px, 1fr))" }}>
            {data.map((f, i) => (
              <ThermalRibbon key={f.path} dryBulb={f.daily_mean}
                figNo={`FIG ${i + 1}`} place={f.name.replace(/_/g, " ")} compact height={120} hoursPerDay={1} />
            ))}
          </section>

          <section className="more-above">
            <h2 className="section-h">Headline metrics</h2>
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th>File</th>
                    <th>Annual mean</th>
                    <th>Hottest hour</th>
                    <th>Hours &gt; 26 °C</th>
                    <th>Degree-hours &gt; 26 °C</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((f) => (
                    <tr key={f.path}>
                      <td className="mono" style={{ fontSize: 12 }}>{f.name}</td>
                      <td className="mono">{f.annual_mean} °C</td>
                      <td className="mono">{f.hottest} °C</td>
                      <td className="mono">{f.hours_over_26} h</td>
                      <td className="mono">{f.degree_hours_26} Kh</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {deltas && (
            <section className="more-above">
              <h2 className="section-h">Change against {data[0].name.replace(/_/g, " ")}</h2>
              <div className="table-wrap" style={{ maxWidth: 720 }}>
                <table className="data">
                  <thead>
                    <tr><th>File</th><th>Δ annual mean</th><th>Δ hottest hour</th><th>Δ hours &gt; 26 °C</th></tr>
                  </thead>
                  <tbody>
                    {deltas.map((d) => (
                      <tr key={d.name}>
                        <td className="mono" style={{ fontSize: 12 }}>{d.name}</td>
                        <td className="mono" style={{ color: d.dMean > 0 ? "var(--fail)" : "var(--pass)" }}>
                          {d.dMean >= 0 ? "+" : ""}{d.dMean.toFixed(2)} K
                        </td>
                        <td className="mono">{d.dHot >= 0 ? "+" : ""}{d.dHot.toFixed(1)} K</td>
                        <td className="mono">{d.dH26 >= 0 ? "+" : ""}{d.dH26} h</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </>
      )}
    </>
  );
}

const labelStyle: React.CSSProperties = {
  fontFamily: "var(--font-mono)", fontSize: 11, textTransform: "uppercase",
  letterSpacing: "0.07em", color: "var(--muted-ink)", marginBottom: 8, display: "block",
};

