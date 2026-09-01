import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

/* Mirrors GET /api/models (agreed contract). Typed here rather than in src/api.ts
   so the Atlas keeps working while the client module evolves. */
interface ArchetypeModel {
  id: string;
  name: string;
  path: string;
  city: string;
  description: string;
  n_zones: number;
  zone_names: string[];
  floor_area_m2: number;
  source?: string;
}

const labelStyle = {
  fontFamily: "var(--font-mono)",
  fontSize: 10.5,
  textTransform: "uppercase",
  letterSpacing: "0.07em",
  color: "var(--muted-ink)",
} as const;

export function Atlas() {
  const [models, setModels] = useState<ArchetypeModel[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/models")
      .then(async (r) => {
        if (!r.ok) {
          const body = await r.json().catch(() => ({}));
          throw new Error(
            typeof body.detail === "string" ? body.detail : `request failed (${r.status})`,
          );
        }
        return r.json() as Promise<{ models: ArchetypeModel[] }>;
      })
      .then((d) => {
        if (!cancelled) setModels(d.models);
      })
      .catch((e) => {
        if (!cancelled) setError(String(e.message ?? e));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <h1 className="page-title">Archetype Atlas</h1>
      <p className="page-intro">
        Illustrative Leeds dwelling templates shipped with the tool — representative
        forms and fabric, not surveyed buildings. Open any template in the pipeline,
        or bring your own IDF on the{" "}
        <Link to="/analyze">Analyze page</Link>.
      </p>

      {models === null && !error && (
        <p role="status" style={{ marginTop: 24, color: "var(--muted-ink)" }}>
          Loading archetype templates…
        </p>
      )}

      {error && (
        <div className="note warn" style={{ marginTop: 24 }}>
          <strong>Could not load the archetype catalogue.</strong> {error} — start the
          app with “Start&nbsp;OverheatLens”, then reload this page.
        </div>
      )}

      {models !== null && !error && models.length === 0 && (
        <div className="note" style={{ marginTop: 24 }}>
          No archetype templates are registered yet. You can still analyze the demo
          dwelling on the <Link to="/analyze">Analyze page</Link>.
        </div>
      )}

      {models !== null && !error && models.length > 0 && (
        <section className="more-above" style={{ marginTop: 28 }} aria-label="Archetype templates">
          <h2 className="section-h">
            Dwelling templates <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 400, color: "var(--muted-ink)" }}>({models.length})</span>
          </h2>
          <div
            style={{
              marginTop: 14,
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
              gap: 18,
            }}
          >
            {models.map((m) => (
              <ArchetypeCard key={m.id} m={m} />
            ))}
          </div>
        </section>
      )}
    </>
  );
}

function ArchetypeCard({ m }: { m: ArchetypeModel }) {
  return (
    <article
      className="figure"
      style={{ display: "flex", flexDirection: "column", gap: 12, margin: 0 }}
      aria-label={`Archetype template: ${m.name}`}
    >
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 8 }}>
        <h3
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: 18,
            fontWeight: 600,
            letterSpacing: "-0.01em",
            margin: 0,
          }}
        >
          {m.name}
        </h3>
        <span className="pill pill-neutral">{m.city}</span>
      </div>

      <p style={{ margin: 0, fontSize: 13.5, lineHeight: 1.5 }}>{m.description}</p>

      <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
        <div>
          <div style={labelStyle}>Zones</div>
          <ul
            className="mono"
            style={{ listStyle: "none", margin: "4px 0 0", padding: 0, fontSize: 12.5, lineHeight: 1.6 }}
          >
            {(m.zone_names ?? []).map((z) => (
              <li key={z}>{z}</li>
            ))}
          </ul>
        </div>
        <div>
          <div style={labelStyle}>Floor area</div>
          <div className="mono" style={{ marginTop: 4, fontSize: 15, fontWeight: 600 }}>
            {m.floor_area_m2} <span style={{ fontWeight: 400, fontSize: 12 }}>m2</span>
          </div>
        </div>
      </div>

      <div style={{ marginTop: "auto", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
        <Link to={`/analyze?model=${encodeURIComponent(m.path)}`}>Analyze this archetype →</Link>
        <span className="mono" style={{ fontSize: 11, color: "var(--muted-ink)" }}>
          {m.id} · {m.n_zones} zones
        </span>
      </div>

      {m.source ? (
        <figcaption className="figure-caption" style={{ marginTop: 0 }}>
          <span>source: {m.source}</span>
        </figcaption>
      ) : null}
    </article>
  );
}
