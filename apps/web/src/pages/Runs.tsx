import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type RunEntry } from "../api";
import { EmptyState, StatusPill, PageCover } from "../components";

export function Runs() {
  const [runs, setRuns] = useState<RunEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  const refresh = () => {
    api.runs().then(setRuns).catch((e) => setError(String(e.message ?? e)));
  };

  useEffect(() => { refresh(); }, []);

  const remove = async (id: string) => {
    if (!window.confirm(`Delete local run ${id}? The archived files are removed from this machine.`)) return;
    setDeleting(id);
    try {
      await api.runDelete(id);
      refresh();
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setDeleting(null);
    }
  };

  return (
    <>
      <PageCover img="cover-runs.png" alt="" />
      <section className="headline-row">
        <div>
          <h1 className="page-title">Run Archive</h1>
          <p className="page-intro">
            Every experiment, persistent across restarts: run ID, model × weather ×
            standard, verdict, hashes. Open any run to replay its evidence — or export
            its reproducibility bundle.
          </p>
        </div>
        <Link className="nb-btn" to="/scenarios">+ NEW BATCH</Link>
      </section>

      {error && <div className="note warn"><strong>Archive unavailable.</strong> {error}</div>}

      {!runs && !error && <p className="mono subtle" role="status">Reading the archive…</p>}

      {runs && runs.length === 0 && (
        <EmptyState img="empty-runs.png" alt="Empty experiment shelf illustration"
          title="THE SHELF IS EMPTY"
          body="No experiments yet. Run a model × weather × standard analysis and it is filed here automatically with full provenance."
          action={<Link className="nb-btn" to="/analyze">Run EnergyPlus</Link>} />
      )}

      {runs && runs.length > 0 && (
        <section className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Run ID</th><th>Model</th><th>Weather</th><th>Standard</th>
                <th>Verdict</th><th>Archived</th><th></th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.run_id ?? `${r.weather}-${r.pack_id}`}>
                  <td className="mono" style={{ fontSize: 11.5 }}>{r.run_id ?? "—"}</td>
                  <td style={{ fontSize: 12.5 }}>{r.model ?? "—"}</td>
                  <td className="mono" style={{ fontSize: 11.5 }}>{r.weather}</td>
                  <td className="mono" style={{ fontSize: 11.5 }}>{r.pack_id}</td>
                  <td><StatusPill status={r.overall ?? "INFO"} /></td>
                  <td className="mono subtle" style={{ fontSize: 11 }}>{r.created_utc ?? r.source ?? "—"}</td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    {r.run_id && (
                      <>
                        <Link className="nb-btn secondary" style={{ minHeight: 34, fontSize: 12 }}
                          to={`/analyze?run=${encodeURIComponent(r.run_id)}`}>OPEN</Link>{" "}
                        <a className="nb-btn secondary" style={{ minHeight: 34, fontSize: 12 }}
                          href={api.bundleUrl(r.run_id)}>ZIP ↓</a>{" "}
                        <button className="nb-btn secondary" style={{ minHeight: 34, fontSize: 12 }}
                          disabled={deleting === r.run_id} onClick={() => remove(r.run_id!)}>
                          {deleting === r.run_id ? "…" : "DELETE"}
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
      <p className="subtle" style={{ marginTop: 10 }}>
        Archive lives in <span className="mono">data/runs/</span> on this machine only —
        delete a run to remove its files. The ZIP bundle carries inputs, manifest,
        results, criteria CSV, report and provenance for publication.
      </p>
    </>
  );
}
