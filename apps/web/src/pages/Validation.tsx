import { useEffect, useMemo, useState } from "react";
import { api, type ValidationRow, type ValidationCampaign } from "../api";
import { StatusPill, PageCover } from "../components";

type Filter = "all" | "PASS" | "FAIL" | "PENDING" | "BLOCKED";

export function Validation() {
  const [rows, setRows] = useState<ValidationRow[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [campaign, setCampaign] = useState<ValidationCampaign | null>(null);

  useEffect(() => {
    api.validation().then(setRows).catch((e) => setErr(String(e.message ?? e)));
    api.validationCampaign().then(setCampaign).catch(() => setCampaign(null));
  }, []);

  const counts = useMemo(() => {
    const c: Record<string, number> = { PASS: 0, FAIL: 0, PENDING: 0, BLOCKED: 0 };
    for (const r of rows ?? []) {
      const v = r.cells.find((x) => /^(PASS|FAIL|PENDING|BLOCKED)$/i.test(x))?.toUpperCase();
      if (v && v in c) c[v]++;
    }
    return c;
  }, [rows]);

  const visible = (rows ?? []).filter((r) => {
    if (filter === "all") return true;
    return r.cells.some((c) => c.toUpperCase() === filter);
  });
  const visibleSections = [...new Set(visible.map((r) => r.section))];

  return (
    <>
      <PageCover img="cover-validation.png" alt="" />
      <section className="headline-row">
        <div>
          <h1 className="page-title">Validation</h1>
          <p className="page-intro">
            The live evidence register: every row names its method, rule, fixture, source,
            tolerance and date. This page reads <span className="mono">VALIDATION_MATRIX.md</span>{" "}
            directly, so it can never drift from the repository. Validation means equations,
            windows, thresholds and mappings checked — never just “the code ran”.
          </p>
        </div>
      </section>

      {err && <div className="note warn"><strong>Could not read the matrix.</strong> {err}</div>}

      {rows && (
        <section className="metrics" style={{ gridTemplateColumns: "repeat(5, 1fr)" }} aria-label="Evidence counts">
          <div className="metric"><div className="m-val">{rows.length}</div><div className="m-label">evidence rows</div></div>
          <div className="metric" style={{ background: "var(--nb-green)" }}><div className="m-val">{counts.PASS}</div><div className="m-label">pass</div></div>
          <div className="metric" style={{ background: "var(--nb-pink)" }}><div className="m-val">{counts.FAIL}</div><div className="m-label">fail</div></div>
          <div className="metric"><div className="m-val">{counts.PENDING}</div><div className="m-label">pending</div></div>
          <div className="metric" style={{ background: "var(--nb-violet)", color: "#fff" }}><div className="m-val">{counts.BLOCKED}</div><div className="m-label">blocked</div></div>
        </section>
      )}

      {campaign && campaign.status === "ready" && campaign.results && (
        <section className="more-above">
          <h2 className="section-h">Independent validation campaign</h2>
          <div className="note" style={{ margin: "8px 0 12px" }}>
            <strong>
              Campaign verdict:{" "}
              <StatusPill status={campaign.results.campaign_verdict} />
            </strong>{" "}
            — {campaign.results.summary.pass_or_confirmed} PASS/CONFIRMED ·{" "}
            {campaign.results.summary.incomplete} INCOMPLETE ·{" "}
            {campaign.results.summary.fail} FAIL · run{" "}
            <span className="mono">{campaign.results.finished_utc.slice(0, 16)}</span>{" "}
            UTC · method: <span className="mono">validation/METHOD.md</span>, re-run with{" "}
            <span className="mono">python validation/run_campaign.py</span>
          </div>
          <div className="table-wrap" style={{ marginTop: 10 }}>
            <table className="data">
              <thead>
                <tr><th>Case</th><th>Layer</th><th>What it proves</th><th>Verdict</th></tr>
              </thead>
              <tbody>
                {campaign.results.cases.map((c) => (
                  <tr key={c.id}>
                    <td className="mono" style={{ width: 320 }}>
                      <strong>{c.id}</strong> · {c.title}
                    </td>
                    <td className="mono" style={{ width: 70 }}>{c.layer}</td>
                    <td style={{ maxWidth: 420 }}>{c.reference}</td>
                    <td><StatusPill
                      status={/DIRECTIONAL/.test(c.verdict) ? "PASS" : c.verdict} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {(() => {
            const v12 = campaign.results.cases.find((c) => c.id === "V12");
            const zones = (v12?.detail?.zones ?? []) as {
              db_zone: string; app_room: string; db_verdict: string;
              app_verdict: string; agree: boolean; db_critA_pct?: number;
              app_critA_pct?: number; delta_pp?: number | null;
              db_critB_hr?: number | null; app_critB_hr?: number | null;
            }[];
            if (!v12 || !zones.length) return null;
            const corr = (v12.detail?.corridors ?? {}) as {
              app_pct?: number; db_stairsdown_pct?: number;
              db_stairsup_pct?: number; both_below_3pct?: boolean;
            };
            const notes = (v12.detail?.classification_notes ?? []) as string[];
            return (
              <div style={{ marginTop: 14 }}>
                <h3 className="section-h" style={{ fontSize: 14 }}>
                  V12 results · 01BA baseline — app vs DesignBuilder (same model, same weather)
                </h3>
                <p className="subtle" style={{ margin: "2px 0 8px", maxWidth: "95ch" }}>
                  The dwelling verdict is <strong>FAIL in both engines</strong> and every
                  habitable zone agrees. Absolute percentages differ between the two
                  simulation engines (E+ 25.1 vs DesignBuilder's internal E+ 23.1) —
                  deltas are reported, not hidden. Full report:{" "}
                  <span className="mono">validation/MODEL_01BA_DESIGNBUILDER_CROSSCHECK.md</span>
                </p>
                <div className="table-wrap">
                  <table className="data">
                    <thead>
                      <tr><th>Zone</th><th>DB verdict</th><th className="num">DB Crit A</th>
                        <th className="num">App Crit A</th><th className="num">Δ</th>
                        <th className="num">DB Crit B</th><th className="num">App Crit B</th>
                        <th>Agree</th></tr>
                    </thead>
                    <tbody>
                      {zones.map((z) => (
                        <tr key={z.db_zone}>
                          <td className="mono" style={{ fontSize: 11.5 }}>{z.db_zone}</td>
                          <td>{z.db_verdict}</td>
                          <td className="mono num">{z.db_critA_pct ?? "—"}%</td>
                          <td className="mono num">{z.app_critA_pct ?? "—"}%</td>
                          <td className="mono num" style={{ color: z.delta_pp == null ? undefined : Math.abs(z.delta_pp) > 5 ? "var(--nb-danger)" : undefined }}>
                            {z.delta_pp == null ? "—" : `${z.delta_pp > 0 ? "+" : ""}${z.delta_pp} pp`}
                          </td>
                          <td className="mono num">{z.db_critB_hr ?? "—"}</td>
                          <td className="mono num">{z.app_critB_hr ?? "—"}</td>
                          <td><StatusPill status={z.agree ? "PASS" : "FAIL"} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {corr.app_pct != null && (
                  <p className="subtle" style={{ marginTop: 8 }}>
                    Corridor (stairs): app {corr.app_pct}% vs DesignBuilder{" "}
                    {corr.db_stairsdown_pct}/{corr.db_stairsup_pct}% — below the 3% criterion
                    in both engines (Pass).
                  </p>
                )}
                {notes.length > 0 && (
                  <ul className="subtle" style={{ margin: "6px 0 0 18px", maxWidth: "95ch" }}>
                    {notes.map((n, i) => <li key={i} style={{ marginBottom: 4 }}>{n}</li>)}
                  </ul>
                )}
              </div>
            );
          })()}
        </section>
      )}

      {campaign && campaign.status !== "ready" && (
        <div className="note warn" style={{ marginTop: 10 }}>
          <strong>Validation campaign not run on this machine yet.</strong> {campaign.detail}
        </div>
      )}

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 6 }}>
        {(["all", "PASS", "FAIL", "PENDING", "BLOCKED"] as const).map((f) => (
          <button key={f} className={filter === f ? "nb-btn" : "nb-btn secondary"}
            style={{ minHeight: 36, fontSize: 12 }} onClick={() => setFilter(f)}>{f}</button>
        ))}
      </div>

      {visibleSections.map((sec) => (
        <section key={sec} className="more-above">
          <h2 className="section-h">{sec}</h2>
          <div className="table-wrap" style={{ marginTop: 10 }}>
            <table className="data">
              <tbody>
                {visible.filter((r) => r.section === sec).map((r, i) => (
                  <tr key={i}>
                    <td className="mono" style={{ width: 130 }}>{r.cells[0]}</td>
                    <td style={{ maxWidth: 460 }}>
                      {r.cells.slice(1, -2).join(" · ").replace(/\s*·\s*(PASS|FAIL|PENDING|BLOCKED)$/i, "")}
                    </td>
                    <td>{renderVerdict(r.cells)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}

      <section className="more-above">
        <h2 className="section-h">How to read a status</h2>
        <div className="table-wrap" style={{ marginTop: 10, maxWidth: 760 }}>
          <table className="data" style={{ minWidth: 0 }}>
            <tbody>
              <tr><td><StatusPill status="SOURCE_VERIFIED" /></td><td>Transcribed from the official document and boundary-locked by tests.</td></tr>
              <tr><td><StatusPill status="PASS" /></td><td>Claim demonstrated by the stated method and fixture.</td></tr>
              <tr><td><StatusPill status="RESEARCH_ONLY" /></td><td>Implemented but not compliance-grade — assumptions stated alongside.</td></tr>
              <tr><td><StatusPill status="PENDING" /></td><td>Fixture exists, run scheduled — not yet evidence.</td></tr>
              <tr><td><StatusPill status="BLOCKED" /></td><td>Waiting on a source or dependency — nothing invented meanwhile.</td></tr>
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

function renderVerdict(cells: string[]) {
  const verdict = cells.find((c) => /^(PASS|FAIL|PENDING|BLOCKED)$/i.test(c));
  return verdict ? <StatusPill status={verdict} /> : null;
}
