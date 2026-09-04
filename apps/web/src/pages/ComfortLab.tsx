import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { MethodNote, StatusPill, PageCover } from "../components";

/* Comfort Lab MANUAL mode — standard indices with explicit applicability gates.
   SIMULATION mode lives on Analyze (comfort-from-run). Mathematics:
   pythermalcomfort (ISO 7730:2025 default), never reimplemented. */

type ComfortPayload = {
  model: string;
  standard_edition: string;
  values: Record<string, number | boolean>;
  status: string;
  reason: string | null;
  provenance: Record<string, unknown>;
};

function Num({ id, value, set, step, min, max }: {
  id: string; value: number; set: (n: number) => void; step: number; min: number; max: number;
}) {
  return (
    <input id={id} className="nb-input" type="number" value={value} step={step} min={min} max={max}
      onChange={(e) => set(Number(e.target.value))} />
  );
}

const L = ({ children, htmlFor }: { children: React.ReactNode; htmlFor: string }) => (
  <label htmlFor={htmlFor} style={{
    fontFamily: "var(--nb-font-mono)", fontSize: 10.5, fontWeight: 700,
    textTransform: "uppercase", letterSpacing: "0.05em",
    display: "block", marginTop: 10,
  }}>{children}</label>
);

export function ComfortLab() {
  const [tdb, setTdb] = useState(26);
  const [tr, setTr] = useState(27);
  const [vr, setVr] = useState(0.15);
  const [rh, setRh] = useState(50);
  const [met, setMet] = useState(1.2);
  const [clo, setClo] = useState(0.5);
  const [pmv, setPmv] = useState<ComfortPayload | null>(null);

  const [aTdb, setATdb] = useState(27.5);
  const [aTrm, setATrm] = useState(19);
  const [adaptive, setAdaptive] = useState<ComfortPayload | null>(null);

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
      <PageCover img="cover-comfort.png" alt="" />
      <section className="headline-row">
        <div>
          <h1 className="page-title">Comfort Lab</h1>
          <p className="page-intro">
            <strong>Manual mode</strong> — enter conditions, get standard indices behind
            explicit applicability gates. <strong>Simulation mode</strong> — comfort computed
            from a real EnergyPlus run — lives on <Link to="/analyze">Analyze</Link>,
            where every input is labelled SIMULATED, DERIVED or ASSUMED.
          </p>
        </div>
        <span className="nb-chip">pythermalcomfort · ISO 7730:2025 default</span>
      </section>

      <section style={{ display: "grid", gap: 18, gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", maxWidth: 980 }}>
        <fieldset className="nb-card" style={{ margin: 0, padding: 18 }}>
          <legend className="nb-chip">INDOOR — FANGER PMV / PPD</legend>
          <L htmlFor="c-tdb">Air temperature tdb (°C)</L>
          <Num id="c-tdb" value={tdb} set={setTdb} step={0.5} min={-20} max={60} />
          <L htmlFor="c-tr">Mean radiant tr (°C)</L>
          <Num id="c-tr" value={tr} set={setTr} step={0.5} min={-20} max={60} />
          <L htmlFor="c-vr">Air speed vr (m/s)</L>
          <Num id="c-vr" value={vr} set={setVr} step={0.05} min={0} max={3} />
          <L htmlFor="c-rh">Relative humidity (%)</L>
          <Num id="c-rh" value={rh} set={setRh} step={5} min={0} max={100} />
          <L htmlFor="c-met">Metabolic rate (met)</L>
          <Num id="c-met" value={met} set={setMet} step={0.1} min={0.7} max={5} />
          <L htmlFor="c-clo">Clothing (clo)</L>
          <Num id="c-clo" value={clo} set={setClo} step={0.05} min={0} max={3} />
        </fieldset>

        <fieldset className="nb-card" style={{ margin: 0, padding: 18 }}>
          <legend className="nb-chip">ADAPTIVE — EN 16798-1</legend>
          <L htmlFor="c-atdb">Operative temperature (°C)</L>
          <Num id="c-atdb" value={aTdb} set={setATdb} step={0.5} min={-10} max={50} />
          <L htmlFor="c-trm">Outdoor running mean Trm (°C)</L>
          <Num id="c-trm" value={aTrm} set={setATrm} step={1} min={-10} max={40} />
          <p className="subtle" style={{ marginTop: 10 }}>
            Naturally-ventilated, occupant-controlled spaces only — the gate refuses
            air-conditioned application.
          </p>
        </fieldset>

        <fieldset className="nb-card" style={{ margin: 0, padding: 18 }}>
          <legend className="nb-chip">OUTDOOR — UTCI</legend>
          <L htmlFor="c-utdb">Air temperature (°C)</L>
          <Num id="c-utdb" value={uTdb} set={setUTdb} step={1} min={-40} max={55} />
          <L htmlFor="c-utr">Mean radiant (°C)</L>
          <Num id="c-utr" value={uTr} set={setUTr} step={1} min={-40} max={70} />
          <L htmlFor="c-uv">Wind at 10 m (m/s)</L>
          <Num id="c-uv" value={uV} set={setUV} step={0.5} min={0} max={20} />
          <L htmlFor="c-urh">Relative humidity (%)</L>
          <Num id="c-urh" value={uRh} set={setURh} step={5} min={0} max={100} />
        </fieldset>
      </section>

      <div style={{ marginTop: 18 }}>
        <button className="nb-btn" onClick={run} disabled={busy}>
          {busy ? "COMPUTING…" : "▶ COMPUTE COMFORT INDICES"}
        </button>
      </div>

      {err && <div className="note warn" style={{ marginTop: 16 }}><strong>Could not compute.</strong> {err}</div>}

      {(pmv || adaptive || utci) && (
        <section className="more-above" style={{ display: "grid", gap: 18, gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", maxWidth: 980 }}>
          {pmv && <ComfortCard title="Fanger PMV / PPD" r={pmv}
            rows={pmv.values.pmv !== undefined ? [
              ["PMV", Number(pmv.values.pmv).toFixed(2)],
              ["PPD", `${Number(pmv.values.ppd).toFixed(1)} %`],
            ] : []}
            scale={pmv.values.pmv !== undefined ? <PmvScale pmv={Number(pmv.values.pmv)} /> : null}
            note="ISO 7730:2025 · applicability tdb/tr 10–30 °C, vr 0–1 m/s, met 0.8–4, clo 0–2" />}
          {adaptive && <ComfortCard title="Adaptive comfort (EN 16798-1)" r={adaptive}
            rows={adaptive.values.tmp_cmf !== undefined ? [
              ["comfort temperature", `${Number(adaptive.values.tmp_cmf).toFixed(1)} °C`],
              ["Cat II upper limit", `${Number(adaptive.values.tmp_cmf_cat_ii_up).toFixed(1)} °C`],
              ["Cat II acceptable", adaptive.values.acceptability_cat_ii ? "✓ yes" : "✕ no"],
            ] : []}
            note="Trm 10–30 °C, v < 1.2 m/s; Category II is the CIBSE-recommended default" />}
          {utci && <ComfortCard title="Universal Thermal Climate Index" r={utci}
            rows={utci.values.utci !== undefined ? [
              ["UTCI", `${Number(utci.values.utci).toFixed(1)} °C`],
              ["stress band", utciBand(Number(utci.values.utci))],
            ] : []}
            note="v assessed at 10 m reference; 0.5–17 m/s applicability" />}
        </section>
      )}
      <MethodNote title="WHEN IS EACH METRIC APPLICABLE?">
        PMV/PPD needs steady indoor conditions with known clothing and activity — outdoor
        heatwaves and draughty rooms break its assumptions, and the gate says so. Adaptive
        EN 16798-1 applies to occupant-controlled, naturally-ventilated spaces. UTCI
        describes outdoor heat stress, never indoor comfort. NOT APPLICABLE is a result,
        not a failure.
      </MethodNote>
    </>
  );
}

/* 7-point PMV sensation strip with the computed value marked. */
function PmvScale({ pmv }: { pmv: number }) {
  const points = [-3, -2, -1, 0, 1, 2, 3];
  const labels = ["cold", "cool", "slightly cool", "neutral", "slightly warm", "warm", "hot"];
  const pos = Math.max(0, Math.min(6, Math.round(pmv + 3)));
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 2, marginTop: 10 }} role="img"
      aria-label={`PMV ${pmv.toFixed(2)}, sensation ${labels[pos]}`}>
      {points.map((p, i) => (
        <div key={p} title={labels[i]}
          style={{
            border: "2px solid var(--nb-ink)", textAlign: "center",
            fontFamily: "var(--nb-font-mono)", fontSize: 10, fontWeight: 800,
            padding: "5px 0",
            background: i === pos ? "var(--nb-ink)" : Math.abs(p) <= 1 ? "var(--nb-green)" : "var(--nb-surface)",
            color: i === pos ? "var(--nb-surface)" : "var(--nb-ink)",
          }}>
          {p > 0 ? `+${p}` : p}
        </div>
      ))}
    </div>
  );
}

function utciBand(u: number): string {
  if (u < 9) return "slight cold stress or cooler";
  if (u < 26) return "no thermal stress";
  if (u < 32) return "moderate heat stress";
  if (u < 38) return "strong heat stress";
  if (u < 46) return "very strong heat stress";
  return "extreme heat stress";
}

function ComfortCard({ title, r, rows, note, scale }: {
  title: string; r: ComfortPayload; rows: [string, string][]; note: string; scale?: React.ReactNode;
}) {
  return (
    <div className="nb-card" style={{ padding: 18 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <h3 style={{ fontFamily: "var(--nb-font-display)", fontSize: 16 }}>{title}</h3>
        <StatusPill status={r.status} />
      </div>
      <p className="mono subtle" style={{ marginTop: 4 }}>{r.model} · {r.standard_edition}</p>
      {r.status === "OK" ? (
        <table className="data" style={{ minWidth: 0, marginTop: 8 }}>
          <tbody>
            {rows.map(([k, v]) => (
              <tr key={k}>
                <td>{k}</td>
                <td className="mono num" style={{ fontSize: 15, fontWeight: 800 }}>{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="note warn" style={{ marginTop: 10 }}>
          <strong>NOT APPLICABLE.</strong> {r.reason}
        </div>
      )}
      {scale}
      <p className="mono subtle" style={{ marginTop: 10 }}>
        {note} · lib {String((r.provenance as { library_version?: string }).library_version ?? "")}
      </p>
    </div>
  );
}
