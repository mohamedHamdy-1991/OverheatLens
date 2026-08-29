import { Link } from "react-router-dom";

/* Real content pages — the plan's docs set, scoped to what exists today.
 * Everything here describes the shipped tool truthfully (RULE 29). */

function Page({ title, intro, children }: { title: string; intro: string; children: React.ReactNode }) {
  return (
    <>
      <h1 className="page-title">{title}</h1>
      <p className="page-intro">{intro}</p>
      {children}
    </>
  );
}

const sect: React.CSSProperties = { marginTop: 34, maxWidth: "82ch" };
const h = { fontFamily: "var(--font-serif)", fontSize: 19, fontWeight: 600, marginBottom: 8 } as const;
const p = { marginBottom: 10, color: "var(--ink)" } as const;
const code: React.CSSProperties = {
  fontFamily: "var(--font-mono)", fontSize: 12.5, background: "var(--surface)",
  border: "1px solid var(--line)", borderRadius: 6, padding: "10px 14px",
  display: "block", whiteSpace: "pre-wrap", margin: "8px 0 14px",
};

export function Methods() {
  return (
    <Page title="Methods" intro="How the science is implemented — thresholds are versioned data, provenance is part of every result.">
      <section style={sect}>
        <h2 style={h}>Versioned rule packs</h2>
        <p style={p}>
          No threshold lives in code. Each assessment method is a YAML rule pack validated
          against a JSON Schema; every criterion carries its clause reference, source
          register ID and verification status. Packs whose sources were verified against
          the official documents are marked SOURCE VERIFIED and may run in compliance
          mode; others are refused.
        </p>
        <p style={p}>
          The four bundled packs — TM59:2026, TM59:2017, Part O dynamic route (TM59:2017
          plus ADO §2.6 overrides) and TM52 — were each transcribed from the official
          publication and boundary-locked by tests. See the verification notes in
          {" "}<code className="mono">docs/standards/</code> and SOURCE_REGISTER.md for
          the SHA-256-anchored evidence.
        </p>
      </section>
      <section style={sect}>
        <h2 style={h}>Simulation and operative temperature</h2>
        <p style={p}>
          Indoor conditions come from an official EnergyPlus binary (version recorded in
          every run manifest with both input hashes). Operative temperature is derived as
          Top = 0.5·(MAT + MRT), the standard low-air-speed approximation, and is labelled
          as a derived metric everywhere it appears.
        </p>
      </section>
      <section style={sect}>
        <h2 style={h}>Comfort models</h2>
        <p style={p}>
          Fanger PMV/PPD (ISO 7730:2025), EN 16798-1 adaptive comfort and UTCI are computed
          by the pinned pythermalcomfort library behind explicit applicability gates;
          out-of-range inputs return an explicit “outside applicability” verdict, never a
          misleading number.
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
        <p style={{ ...p, color: "var(--muted-ink)", fontSize: 13 }}>
          OverheatLens is research and decision-support software — not a compliance
          certificate. See DISCLAIMER.md.
        </p>
      </section>
    </Page>
  );
}

export function Docs() {
  return (
    <Page title="Docs" intro="Quick start for the local, zero-install tool. Full guides arrive with the documentation phase.">
      <section style={sect}>
        <h2 style={h}>Start</h2>
        <p style={p}>
          Double-click <strong>Start OverheatLens</strong> (macOS) or
          <strong> Start OverheatLens.bat</strong> (Windows). The first run sets up its
          own private environment and builds the interface; later runs start in seconds
          and open <code className="mono">http://127.0.0.1:8620</code>. Close with the
          matching Close script.
        </p>
      </section>
      <section style={sect}>
        <h2 style={h}>Typical paths</h2>
        <div className="table-wrap">
          <table className="data" style={{ minWidth: 0 }}>
            <tbody>
              <tr><td>Check a weather file</td><td><Link to="/weather">Weather Lab →</Link></td></tr>
              <tr><td>Run an overheating assessment</td><td><Link to="/analyze">Analyze →</Link></td></tr>
              <tr><td>Comfort indices</td><td><Link to="/comfort">Comfort Lab →</Link></td></tr>
              <tr><td>Evidence for every number</td><td><Link to="/validation">Validation →</Link></td></tr>
            </tbody>
          </table>
        </div>
      </section>
      <section style={sect}>
        <h2 style={h}>Command line & Python</h2>
        <code style={code}>{`./.venv/bin/python -m overheatlens check-epw my_file.epw
./.venv/bin/python -m pytest packages/overheatlens-core/tests -q`}</code>
        <p style={p}>
          The scientific core is importable without the web app — see{" "}
          <Link to="/methods">Methods</Link> for a two-line example.
        </p>
      </section>
      <section style={sect}>
        <h2 style={h}>Where things live</h2>
        <code style={code}>{`packages/overheatlens-core/   scientific package (authoritative)
apps/api                      FastAPI service
apps/web                      this interface
fixtures/                     synthetic test files
docs/standards/               source-verification notes
VALIDATION_MATRIX.md          live evidence register`}</code>
      </section>
    </Page>
  );
}

export function About() {
  return (
    <Page title="About" intro="OverheatLens — Open Building Overheating & Climate-Resilience Hub.">
      <section style={sect}>
        <p style={{ ...p, fontSize: 15.5 }}>
          <strong>See the heat. Trace the evidence. Test the response.</strong>{" "}
          OverheatLens links weather-file quality, model readiness, EnergyPlus simulation,
          versioned overheating standards and comfort analytics into one reproducible
          chain — open source, local-first, with provenance attached to every result.
        </p>
      </section>
      <section style={sect}>
        <h2 style={h}>Project</h2>
        <div className="table-wrap" style={{ maxWidth: 640 }}>
          <table className="data" style={{ minWidth: 0 }}>
            <tbody>
              <tr><td>Author</td><td>Mohamed Hamdy Ali — Leeds Beckett University</td></tr>
              <tr><td>Licence</td><td>MIT (LICENSE)</td></tr>
              <tr><td>Status</td><td>research software, early release (see IMPLEMENTATION_STATUS.md)</td></tr>
              <tr><td>Citation</td><td className="mono">CITATION.cff</td></tr>
            </tbody>
          </table>
        </div>
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
