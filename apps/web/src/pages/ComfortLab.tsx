import { useState } from "react";
import { api } from "../api";
import { StatusPill } from "../components";

/* Comfort Lab — real Phase-4 wrappers exposed through the API.
 * Mathematics: pythermalcomfort 4.4.2 (ISO 7730:2025 default), never reimplemented. */

type ComfortPayload = {
  model: string;
  standard_edition: string;
  values: Record<string, number | boolean>;
  status: string;
  reason: string | null;
  provenance: Record<string, unknown>;
};

const field: React.CSSProperties = {
  width: "100%", marginTop: 4, padding: "8px 10px",
  border: "1px solid var(--line-strong)", borderRadius: 6,
  background: "var(--surface)", font: "inherit", color: "var(--ink)",
};
const label: React.CSSProperties = {
  fontFamily: "var(--font-mono)", fontSize: 11, textTransform: "uppercase",
  letterSpacing: "0.07em", color: "var(--muted-ink)",
};

function Num({ id, value, set, step, min, max }: {
  id: string; value: number; set: (n: number) => void; step: number; min: number; max: number;
}) {
  return (
    <input id={id} type="number" value={value} step={step} min={min} max={max}
      onChange={(e) => set(Number(e.target.value))} style={field} />
  );
}

export function ComfortLab() {
  // Fanger inputs
  const [tdb, setTdb] = useState(26);
  const [tr, setTr] = useState(27);
  const [vr, setVr] = useState(0.15);
  const [rh, setRh] = useState(50);
  const [met, setMet] = useState(1.2);
  const [clo, setClo] = useState(0.5);
  const [pmv, setPmv] = useState<ComfortPayload | null>(null);

  // adaptive inputs
  const [aTdb, setATdb] = useState(27.5);
  const [aTrm, setATrm] = useState(19);
  const [adaptive, setAdaptive] = useState<ComfortPayload | null>(null);

  // outdoor
  const [uTdb, setUTdb] = useState(32);
  const [uTr, setUTr] = useState(38);
  const [uV, setUV] = useState(1.0);
  const [uRh, setURh] = useState(45);
  const [utci, setUtci] = useState<ComfortPayload | null>(null);

  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = async () => {
    setBusy(true);
    setErr(null);
    try {
      const [p, a, u] = await Promise.all([
        api.comfortPmv({ tdb, tr, vr, rh, met, clo }),
        api.comfortAdaptive({ tdb: aTdb, tr: aTdb, trm: aTrm, v: 0.2 }),
        api.comfortUtci({ tdb: uTdb, tr: uTr, v: uV, rh: uRh }),
      ]);
      setPmv(p);
      setAdaptive(a);
      setUtci(u);
    } catch (e) {
      setErr(String((e as Error).message ?? e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <h1 className="page-title">Comfort Lab</h1>
      <p className="page-intro">
        Standard comfort indices computed by the pinned
        {" "}<a href="https://pythermalcomfort.readthedocs.io/" target="_blank" rel="noreferrer">pythermalcomfort</a>{" "}
        library behind explicit applicability gates — when an input sits outside a
        model’s range, OverheatLens says so instead of printing a number.
      </p>

      <section style={{ marginTop: 24, display: "grid", gap: 18, gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", maxWidth: 960 }}>
        <fieldset style={{ border: "1px solid var(--line)", borderRadius: 8, background: "var(--surface)", padding: "14px 16px 16px", margin: 0 }}>
          <legend style={label}>Indoor — Fanger PMV / PPD</legend>
          <label htmlFor="c-tdb" style={label}>Air temperature tdb (°C)</label>
          <Num id="c-tdb" value={tdb} set={setTdb} step={0.5} min={-20} max={60} />
          <label htmlFor="c-tr" style={label}>Mean radiant tr (°C)</label>
          <Num id="c-tr" value={tr} set={setTr} step={0.5} min={-20} max={60} />
          <label htmlFor="c-vr" style={label}>Air speed vr (m/s)</label>
          <Num id="c-vr" value={vr} set={setVr} step={0.05} min={0} max={3} />
          <label htmlFor="c-rh" style={label}>Relative humidity (%)</label>
          <Num id="c-rh" value={rh} set={setRh} step={5} min={0} max={100} />
          <label htmlFor="c-met" style={label}>Metabolic rate (met)</label>
          <Num id="c-met" value={met} set={setMet} step={0.1} min={0.7} max={5} />
          <label htmlFor="c-clo" style={label}>Clothing (clo)</label>
          <Num id="c-clo" value={clo} set={setClo} step={0.05} min={0} max={3} />
        </fieldset>

        <fieldset style={{ border: "1px solid var(--line)", borderRadius: 8, background: "var(--surface)", padding: "14px 16px 16px", margin: 0 }}>
          <legend style={label}>Adaptive (EN 16798-1)</legend>
          <label htmlFor="c-atdb" style={label}>Operative temperature (°C)</label>
          <Num id="c-atdb" value={aTdb} set={setATdb} step={0.5} min={-10} max={50} />
          <label htmlFor="c-trm" style={label}>Outdoor running mean Trm (°C)</label>
          <Num id="c-trm" value={aTrm} set={setATrm} step={1} min={-10} max={40} />

          <legend style={{ ...label, marginTop: 18 }}>Outdoor — UTCI</legend>
          <label htmlFor="c-utdb" style={label}>Air temperature (°C)</label>
          <Num id="c-utdb" value={uTdb} set={setUTdb} step={1} min={-40} max={55} />
          <label htmlFor="c-utr" style={label}>Mean radiant (°C)</label>
          <Num id="c-utr" value={uTr} set={setUTr} step={1} min={-40} max={70} />
          <label htmlFor="c-uv" style={label}>Wind at 10 m (m/s)</label>
          <Num id="c-uv" value={uV} set={setUV} step={0.5} min={0} max={20} />
          <label htmlFor="c-urh" style={label}>Relative humidity (%)</label>
          <Num id="c-urh" value={uRh} set={setURh} step={5} min={0} max={100} />
        </fieldset>
      </section>

      <div style={{ marginTop: 18 }}>
        <button className="btn" onClick={run} disabled={busy}>
          {busy ? "Computing…" : "Compute comfort indices"}
        </button>
      </div>

      {err && <div className="note warn" style={{ marginTop: 16 }}><strong>Could not compute.</strong> {err}</div>}

      {(pmv || adaptive || utci) && (
        <section className="more-above" style={{ display: "grid", gap: 18, gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", maxWidth: 960 }}>
          {pmv && <ComfortCard title="Fanger PMV / PPD" r={pmv}
            rows={pmv.values.pmv !== undefined ? [
              ["PMV", Number(pmv.values.pmv).toFixed(2)],
              ["PPD", `${Number(pmv.values.ppd).toFixed(1)} %`],
            ] : []}
            note="ISO 7730:2025 · applicability tdb/tr 10–30 °C, vr 0–1 m/s, met 0.8–4, clo 0–2" />}
          {adaptive && <ComfortCard title="Adaptive comfort (EN 16798-1)" r={adaptive}
            rows={adaptive.values.tmp_cmf !== undefined ? [
              ["comfort temperature", `${Number(adaptive.values.tmp_cmf).toFixed(1)} °C`],
              ["Cat II upper limit", `${Number(adaptive.values.tmp_cmf_cat_ii_up).toFixed(1)} °C`],
              ["Cat II acceptable", adaptive.values.acceptability_cat_ii ? "yes" : "no"],
            ] : []}
            note="Trm 10–30 °C, v < 1.2 m/s; Category II is the CIBSE-recommended default" />}
          {utci && <ComfortCard title="Universal Thermal Climate Index" r={utci}
            rows={utci.values.utci !== undefined ? [
              ["UTCI", `${Number(utci.values.utci).toFixed(1)} °C`],
            ] : []}
            note="v assessed at 10 m reference; 0.5–17 m/s applicability" />}
        </section>
      )}
    </>
  );
}

function ComfortCard({ title, r, rows, note }: {
  title: string; r: ComfortPayload; rows: [string, string][]; note: string;
}) {
  return (
    <div className="figure" style={{ padding: "14px 16px 12px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <h3 style={{ fontFamily: "var(--font-serif)", fontSize: 17 }}>{title}</h3>
        <StatusPill status={r.status} />
      </div>
      {r.status === "OK" ? (
        <table className="data" style={{ minWidth: 0, marginTop: 8 }}>
          <tbody>
            {rows.map(([k, v]) => (
              <tr key={k}>
                <td style={{ color: "var(--muted-ink)" }}>{k}</td>
                <td className="mono" style={{ textAlign: "right", fontSize: 15, fontWeight: 600 }}>{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p style={{ marginTop: 10, fontSize: 13.5, color: "var(--muted-ink)" }}>
          {r.reason}
        </p>
      )}
      <p className="figure-caption" style={{ borderTop: "1px solid var(--line)", marginTop: 10, paddingTop: 8 }}>
        <span>{note}</span>
        <span style={{ marginLeft: "auto" }}>
          {String((r.provenance as { library_version?: string }).library_version ?? "")}
        </span>
      </p>
    </div>
  );
}
