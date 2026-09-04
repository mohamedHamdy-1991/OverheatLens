import { Link } from "react-router-dom";

/* Content pages — everything here describes the shipped tool truthfully. */

function Page({ title, intro, cover, children }: { title: string; intro: string; cover?: string; children: React.ReactNode }) {
  return (
    <>
      {cover && (
        <img className="page-cover" src={`img/${cover}`} alt="" loading="lazy"
          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
      )}
      <h1 className="page-title">{title}</h1>
      <p className="page-intro">{intro}</p>
      {children}
    </>
  );
}

const sect: React.CSSProperties = { marginTop: 26, maxWidth: "82ch" };
const h: React.CSSProperties = { fontFamily: "var(--nb-font-display)", fontSize: 19, marginBottom: 8 };
const p: React.CSSProperties = { marginBottom: 10 };
const code: React.CSSProperties = {
  fontFamily: "var(--nb-font-mono)", fontSize: 12.5, background: "var(--nb-ink)",
  color: "var(--nb-surface)", border: "var(--nb-border-2)", boxShadow: "var(--nb-shadow-sm)",
  borderRadius: 4, padding: "12px 16px", display: "block", whiteSpace: "pre-wrap",
  margin: "8px 0 14px",
};

export function Methods() {
  return (
    <Page cover="cover-methods.png" title="Methods" intro="How the science is implemented — thresholds are versioned data, provenance is part of every result.">
      <section style={sect}>
        <h2 style={h}>Versioned rule packs</h2>
        <p style={p}>
          No threshold lives in code. Each assessment method is a YAML rule pack validated
          against a JSON Schema; every criterion carries its clause reference, source
          register ID and verification status. Packs verified against the official
          documents are marked SOURCE VERIFIED and may run in compliance mode.
        </p>
        <p style={p}>
          The four bundled packs — TM59:2026, TM59:2017, Part O dynamic route (TM59:2017
          plus ADO §2.6 overrides) and TM52 — were each transcribed from the official
          publication and boundary-locked by tests. TM59:2026 assessments carry a
          research tag wherever the required 2025 weather release is substituted by the
          closest available file. See <span className="mono">docs/standards/</span> and{" "}
          <span className="mono">SOURCE_REGISTER.md</span> for the SHA-256-anchored evidence.
        </p>
      </section>
      <section style={sect}>
        <h2 style={h}>Simulation and operative temperature</h2>
        <p style={p}>
          Indoor conditions come from an official EnergyPlus binary (25.1.0 working pin;
          version recorded in every run manifest with both input hashes). Only{" "}
          <strong>Hourly</strong> reporting columns are harvested, keyed by their full
          zone path — Monthly/RunPeriod siblings are never stacked and distinct thermal
          zones are never merged (regression VAL-XSIM-05). Operative temperature is
          derived as Top = 0.5·(MAT + MRT), the standard low-air-speed approximation,
          and is labelled as a derived metric everywhere it appears.
        </p>
      </section>
      <section style={sect}>
        <h2 style={h}>Comfort models</h2>
        <p style={p}>
          Fanger PMV/PPD (ISO 7730:2025), EN 16798-1 adaptive comfort and UTCI are computed
          by the pinned pythermalcomfort library behind explicit applicability gates;
          out-of-range inputs return an explicit “outside applicability” verdict, never a
          misleading number. Simulation mode labels every input SIMULATED, DERIVED or ASSUMED.
        </p>
      </section>
      <section style={sect}>
        <h2 style={h}>Batches and reproducibility</h2>
        <p style={p}>
          Batch matrices run the same pipeline per cell — no separate mathematics. Every
          run persists to <span className="mono">data/runs/</span> with its manifest; the
          ZIP bundle carries inputs, manifest, results JSON, criteria CSV, report HTML
          and provenance so another researcher can reproduce the analysis.
        </p>
      </section>
      <section style={sect}>
        <h2 style={h}>Running the science without the interface</h2>
        <code style={code}>{`from overheatlens.standards import StandardsEngine

engine = StandardsEngine.load("uk_tm59_2017")
result = engine.evaluate_dwelling(rooms, category="II",
                                  daily_mean_outdoor=daily_means,
                                  mode="compliance")`}</code>
      </section>
      <section style={sect}>
        <p style={{ ...p, fontSize: 13 }}>
          OverheatLens is research and decision-support software — not a compliance
          certificate. See DISCLAIMER.md.
        </p>
      </section>
    </Page>
  );
}

export function Docs() {
  return (
    <Page cover="cover-docs.png" title="Docs" intro="Quick start for the local, zero-install tool.">
      <section style={sect}>
        <h2 style={h}>Start</h2>
        <p style={p}>
          Double-click <strong>Start OverheatLens</strong> (macOS) or
          <strong> Start OverheatLens.bat</strong> (Windows). The first run sets up its
          own private environment and builds the interface; later runs start in seconds
          and open <span className="mono">http://127.0.0.1:8620</span>. Close with the
          matching Close script. Developers: <strong>Debug OverheatLens</strong> runs the
          same app on <span className="mono">http://127.0.0.1:8621</span> with auto-reload,
          debug logging and a startup self-check (log at{" "}
          <span className="mono">logs/overheatlens-debug.log</span>).
        </p>
      </section>
      <section style={sect}>
        <h2 style={h}>Typical paths</h2>
        <div className="table-wrap">
          <table className="data" style={{ minWidth: 0 }}>
            <tbody>
              <tr><td>Check a weather file</td><td><Link to="/weather">Weather Lab →</Link></td></tr>
              <tr><td>Run an overheating assessment</td><td><Link to="/analyze">Analyze →</Link></td></tr>
              <tr><td>Browse the model library</td><td><Link to="/atlas">Archetype Atlas →</Link></td></tr>
              <tr><td>Batch matrices</td><td><Link to="/scenarios">Scenario & Batch →</Link></td></tr>
              <tr><td>Comfort indices</td><td><Link to="/comfort">Comfort Lab →</Link></td></tr>
              <tr><td>Mitigation evidence</td><td><Link to="/mitigation">Mitigation Lab →</Link></td></tr>
              <tr><td>Evidence for every number</td><td><Link to="/validation">Validation →</Link></td></tr>
            </tbody>
          </table>
        </div>
      </section>
      <section style={sect}>
        <h2 style={h}>Command line & Python</h2>
        <code style={code}>{`./.venv/bin/python -m overheatlens check-epw my_file.epw
PYTHONPATH=packages/overheatlens-core ./.venv/bin/python -m pytest packages/overheatlens-core/tests -q
./.venv/bin/python scripts/audit_archetypes.py   # 15-model EnergyPlus regression`}</code>
        <p style={p}>
          The scientific core is importable without the web app — see{" "}
          <Link to="/methods">Methods</Link> for a two-line example.
        </p>
      </section>
      <section style={sect}>
        <h2 style={h}>Where things live</h2>
        <code style={code}>{`packages/overheatlens-core/   scientific package (authoritative)
apps/api                      FastAPI service (+ run archive, batch, bundles)
apps/web                      this interface
data/archetypes/idf/          15 research IDFs (audited, see audit_report.json)
data/mitigation/              Harehills catalogue (generated locally, git-ignored)
data/runs/                    persistent run archive (local only, git-ignored)
fixtures/                     synthetic test files
docs/standards/               source-verification notes
VALIDATION_MATRIX.md          live evidence register`}</code>
      </section>
    </Page>
  );
}

export function About() {
  return (
    <Page cover="cover-about.png" title="About" intro="OverheatLens — an open research platform for reproducible domestic overheating analysis.">
      <section style={sect}>
        <p style={{ ...p, fontSize: 15.5 }}>
          <strong>See the heat. Trace the evidence. Test the response.</strong>{" "}
          OverheatLens links weather-file quality, model readiness, EnergyPlus simulation,
          versioned overheating standards, comfort analytics, mitigation testing and
          reproducible evidence export into one chain — open source, local-first, with
          provenance attached to every result.
        </p>
      </section>
      <section style={sect}>
        <h2 style={h}>Project</h2>
        <div className="table-wrap" style={{ maxWidth: 640 }}>
          <table className="data" style={{ minWidth: 0 }}>
            <tbody>
              <tr><td>Author</td><td>Mohamed Hamdy Ali — Leeds Sustainability Institute, Leeds Beckett University</td></tr>
              <tr><td>Licence</td><td>MIT (LICENSE)</td></tr>
              <tr><td>Engine</td><td>EnergyPlus 25.1.0 (local official binary, version pinned per run)</td></tr>
              <tr><td>Status</td><td>research software — see IMPLEMENTATION_STATUS.md and Validation</td></tr>
              <tr><td>Citation</td><td className="mono">CITATION.cff</td></tr>
            </tbody>
          </table>
        </div>
      </section>
      <section style={sect}>
        <h2 style={h}>Local-first privacy</h2>
        <p style={p}>
          IDF files, EPW files and research models stay on this machine. Nothing is
          uploaded anywhere; the run archive, uploads and derived catalogues live under{" "}
          <span className="mono">data/</span> and are excluded from version control.
        </p>
      </section>
      <section style={sect}>
        <h2 style={h}>The one-sentence caution</h2>
        <p style={p}>
          OverheatLens implements published methods and orchestrates real simulations, but
          it is <strong>not a certified compliance certificate</strong>: formal submissions
          must use the applicable current requirements and be reviewed by a suitably
          qualified professional.
        </p>
      </section>
    </Page>
  );
}
