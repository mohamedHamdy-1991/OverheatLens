import { useEffect, useState } from "react";
import { api, type ValidationRow } from "../api";
import { StatusPill } from "../components";

export function Validation() {
  const [rows, setRows] = useState<ValidationRow[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.validation().then(setRows).catch((e) => setErr(String(e.message ?? e)));
  }, []);

  const sections = [...new Set((rows ?? []).map((r) => r.section))];
  const nPass = (rows ?? []).filter((r) =>
    r.cells.some((c) => /^PASS$/i.test(c))).length;

  return (
    <>
      <h1 className="page-title">Validation</h1>
      <p className="page-intro">
        The live validation matrix behind this tool — every row names its fixture, source,
        tolerance and date. This page reads <code className="mono">VALIDATION_MATRIX.md</code>{" "}
        directly, so it can never drift from the repository.
      </p>
      {err && <div className="note warn" style={{ marginTop: 18 }}><strong>Could not read the matrix.</strong> {err}</div>}
      {rows && (
        <p style={{ marginTop: 16, fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--muted-ink)" }}>
          {rows.length} rows · {nPass} recorded PASS · source: VALIDATION_MATRIX.md
        </p>
      )}
      {sections.map((sec) => (
        <section key={sec} className="more-above">
          <h2 className="section-h">{sec}</h2>
          <div className="table-wrap">
            <table className="data">
              <tbody>
                {rows!.filter((r) => r.section === sec).map((r, i) => (
                  <tr key={i}>
                    <td className="mono" style={{ width: 130 }}>{r.cells[0]}</td>
                    <td style={{ maxWidth: 420 }}>
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
    </>
  );
}

function renderVerdict(cells: string[]) {
  const verdict = cells.find((c) => /^(PASS|FAIL|PENDING|BLOCKED)$/i.test(c));
  return verdict ? <StatusPill status={verdict} /> : null;
}
