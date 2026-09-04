import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, type ModelDetail, type ModelInfo } from "../api";
import { EmptyState, MethodNote, ProvenanceDrawer, StatusPill, PageCover } from "../components";

type View = "cards" | "matrix";

const SOURCE_LABEL: Record<string, { label: string; note: string }> = {
  research: { label: "RESEARCH MODEL", note: "Measured/DEEP research dwelling — evidence-grade." },
  template: { label: "GENERIC TEMPLATE", note: "Controlled analytical template — assumptions stated, not calibrated." },
  upload: { label: "USER MODEL", note: "Your uploaded IDF — original never modified." },
};

export function Atlas() {
  const [models, setModels] = useState<ModelInfo[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<View>("cards");
  const [filter, setFilter] = useState<string>("all");
  const [params, setParams] = useSearchParams();
  const focusPath = params.get("model");

  useEffect(() => {
    api.models()
      .then(setModels)
      .catch((e) => setError(String(e.message ?? e)));
  }, []);

  const shown = useMemo(() => {
    if (!models) return null;
    return filter === "all" ? models : models.filter((m) => m.source === filter);
  }, [models, filter]);

  return (
    <>
      <PageCover img="cover-atlas.png" alt="" />
      <section className="headline-row">
        <div>
          <h1 className="page-title">Archetype Atlas</h1>
          <p className="page-intro">
            The architectural model library. <strong>Research models</strong> are measured
            DEEP dwellings — evidence-grade. <strong>Generic templates</strong> are controlled
            analytical forms with stated assumptions. <strong>User models</strong> are your
            uploads. Never confuse the three.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className={view === "cards" ? "nb-btn" : "nb-btn secondary"} style={{ minHeight: 40 }} onClick={() => setView("cards")}>CARDS</button>
          <button className={view === "matrix" ? "nb-btn" : "nb-btn secondary"} style={{ minHeight: 40 }} onClick={() => setView("matrix")}>MATRIX</button>
        </div>
      </section>

      {error && (
        <div className="note warn"><strong>Could not load the model library.</strong> {error}</div>
      )}

      {focusPath && (
        <ModelDossier path={focusPath} onClose={() => setParams({})} />
      )}

      {models && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 14 }}>
          {(["all", "research", "template", "upload"] as const).map((f) => (
            <button key={f} className={filter === f ? "nb-btn" : "nb-btn secondary"}
              style={{ minHeight: 36, fontSize: 12 }} onClick={() => setFilter(f)}>
              {f.toUpperCase()} ({f === "all" ? models.length : models.filter((m) => m.source === f).length})
            </button>
          ))}
        </div>
      )}

      {!models && !error && <p role="status" className="mono subtle">Loading model library…</p>}

      {shown && shown.length === 0 && (
        <EmptyState img="empty-model.png" alt="Empty drawing-archive shelf illustration"
          title="NO MODELS IN THIS DRAWER"
          body="No models match this filter. Upload an IDF on the Analyze page and it appears here under User models."
          action={<Link className="nb-btn" to="/analyze">Upload IDF</Link>} />
      )}

      {shown && shown.length > 0 && view === "cards" && (
        <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 18 }} aria-label="Model cards">
          {shown.map((m) => <ArchetypeCard key={m.id} m={m} onOpen={() => setParams({ model: m.path })} />)}
        </section>
      )}

      {shown && shown.length > 0 && view === "matrix" && (
        <section className="table-wrap" aria-label="Model matrix">
          <table className="data">
            <thead>
              <tr>
                <th>Code</th><th>Model</th><th>Kind</th>
                <th className="num">Zones</th><th className="num">Floor area</th>
                <th>Bedrooms*</th><th></th>
              </tr>
            </thead>
            <tbody>
              {shown.map((m) => {
                const beds = (m.zone_names ?? []).filter((z) => /bed/i.test(z)).length;
                return (
                  <tr key={m.id} className={focusPath === m.path ? "selected-row" : undefined}>
                    <td className="mono">{m.id}</td>
                    <td style={{ fontWeight: 700 }}>{m.name}</td>
                    <td><StatusPill status={m.source === "research" ? "SOURCE_VERIFIED" : m.source === "upload" ? "INFO" : "RESEARCH_ONLY"} /></td>
                    <td className="mono num">{m.n_zones ?? "?"}</td>
                    <td className="mono num">{m.floor_area_m2 != null ? `${m.floor_area_m2} m²` : "—"}</td>
                    <td className="mono num">{beds || "—"}</td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      <button className="nb-btn secondary" style={{ minHeight: 34, fontSize: 12 }} onClick={() => setParams({ model: m.path })}>DOSSIER</button>{" "}
                      <Link className="nb-btn" style={{ minHeight: 34, fontSize: 12 }} to={`/analyze?model=${encodeURIComponent(m.path)}`}>RUN ›</Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="subtle" style={{ padding: "8px 14px" }}>*Bedrooms counted by zone-name match — verify in the dossier before publishing.</p>
        </section>
      )}

      <MethodNote title="RESEARCH MODEL vs TEMPLATE — WHAT IS THE DIFFERENCE?">
        Research models carry measured provenance (source dwelling, construction era,
        modification history, file hash). Generic templates are simplified analytical
        forms for users without their own IDF — their assumptions are stated in the
        dossier and they must never be presented as calibrated stock. Your uploads are
        never modified: scenario copies are made explicitly, never silently.
      </MethodNote>
    </>
  );
}

/* Public typology portraits (public/img) — keyed by model stem. Codes never
   appear on the artwork; the mapping lives only in the data layer. */
const PORTRAIT: Record<string, string> = {
  "00CS_detached": "portrait-detached-stone-cottage.png",
  "01BA_end_terrace": "portrait-end-terrace-1930s.png",
  "17BG_back_to_back_end": "portrait-back-to-back-end.png",
  "27BG_back_to_back_mid": "portrait-back-to-back-mid.png",
  "52NP_mid_terrace_EWI": "portrait-mid-terrace-ewi.png",
  "55AD_semi_detached": "portrait-semi-detached.png",
  "56TR_end_terrace": "portrait-end-terrace.png",
  "04KG_semi_detached_nofines": "portrait-semi-detached-nofines.png",
  "19BA_mid_terrace": "portrait-mid-terrace.png",
  "Flat_TM59Example4": "portrait-tm59-flat.png",
  "GroundFloorFlat_27BG_derived": "portrait-ground-floor-flat.png",
  "TopFloorFlat_17BG_derived": "portrait-top-floor-flat.png",
  "HighRiseFlat_EHS_derived": "portrait-high-rise-flat.png",
  "Bungalow_55AD_derived": "portrait-bungalow.png",
  "ModernHouse_PartL2021_derived": "portrait-modern-house.png",
};

function ArchetypeCard({ m, onOpen }: { m: ModelInfo; onOpen: () => void }) {
  const src = SOURCE_LABEL[m.source] ?? SOURCE_LABEL.template;
  const beds = (m.zone_names ?? []).filter((z) => /bed/i.test(z)).length;
  return (
    <article className="case-folder" aria-label={`Model dossier: ${m.name}`}>
      <span className="case-tab">{PORTRAIT[m.id] ? "" : m.id}</span>
      {PORTRAIT[m.id] && (
        <img className="portrait" src={`img/${PORTRAIT[m.id]}`} alt={`Illustration: ${m.name}`}
          loading="lazy"
          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
      )}
      <div className="case-body">
        <StatusPill status={m.source === "research" ? "SOURCE_VERIFIED" : m.source === "upload" ? "INFO" : "RESEARCH_ONLY"} />
        <h3 className="case-title" style={{ fontSize: 19 }}>{m.name}</h3>
        <p style={{ fontSize: 12.5, color: "var(--nb-ink-soft)", margin: "4px 0 10px" }}>{m.description || src.note}</p>
        <dl className="mono" style={{ margin: 0, display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 12px", fontSize: 12 }}>
          <dt className="subtle">ZONES</dt><dd style={{ margin: 0 }}>{m.n_zones ?? "?"}</dd>
          <dt className="subtle">BEDROOMS*</dt><dd style={{ margin: 0 }}>{beds || "—"}</dd>
          <dt className="subtle">FLOOR AREA</dt><dd style={{ margin: 0 }}>{m.floor_area_m2 != null ? `${m.floor_area_m2} m²` : "—"}</dd>
          <dt className="subtle">KIND</dt><dd style={{ margin: 0 }}>{src.label}</dd>
        </dl>
        <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
          <button className="nb-btn secondary" style={{ minHeight: 40 }} onClick={onOpen}>OPEN DOSSIER</button>
          <Link className="nb-btn" style={{ minHeight: 40 }} to={`/analyze?model=${encodeURIComponent(m.path)}`}>RUN ANALYSIS ›</Link>
        </div>
      </div>
    </article>
  );
}

function ModelDossier({ path, onClose }: { path: string; onClose: () => void }) {
  const [detail, setDetail] = useState<ModelDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDetail(null);
    setError(null);
    api.modelDetail(path).catch((e) => setError(String(e.message ?? e))).then((d) => { if (d) setDetail(d); });
  }, [path]);

  return (
    <section className="nb-card" style={{ marginBottom: 18, background: "var(--nb-bg)" }} aria-label="Model dossier">
      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, alignItems: "flex-start", flexWrap: "wrap" }}>
        <h2 className="section-h">Model dossier · {path.split("/").pop()}</h2>
        <button className="nb-btn secondary" style={{ minHeight: 36 }} onClick={onClose}>CLOSE ✕</button>
      </div>
      {error && <div className="note warn" style={{ marginTop: 10 }}><strong>Dossier unavailable.</strong> {error}</div>}
      {!detail && !error && <p className="mono subtle" style={{ marginTop: 10 }}>Parsing IDF — zones, objects, readiness, hash…</p>}
      {detail && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16, marginTop: 12 }}>
          <div className="card">
            <div className="card-head"><h3>Model summary</h3><span className="subtle">{detail.n_zones} zones</span></div>
            <dl className="mono" style={{ margin: 0, display: "grid", gridTemplateColumns: "auto 1fr", gap: "5px 12px", fontSize: 12 }}>
              <dt className="subtle">ENERGYPLUS</dt><dd style={{ margin: 0 }}>{detail.energyplus_version ?? "—"}</dd>
              <dt className="subtle">SIZE</dt><dd style={{ margin: 0 }}>{detail.size_kb} kB</dd>
              <dt className="subtle">ZONES</dt><dd style={{ margin: 0, wordBreak: "break-word" }}>{detail.zone_names.join(" · ")}</dd>
            </dl>
            <div style={{ marginTop: 10 }}>
              <Link className="nb-btn" style={{ minHeight: 40 }} to={`/analyze?model=${encodeURIComponent(detail.path)}`}>RUN ANALYSIS ›</Link>
            </div>
          </div>
          <div className="card">
            <div className="card-head"><h3>Readiness</h3><StatusPill status={detail.readiness.status} /></div>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5 }}>
              {detail.readiness.rows.slice(0, 8).map((row) => (
                <li key={row.check_id} style={{ marginBottom: 4 }}>
                  <StatusPill status={row.severity === "ok" ? "PASS" : row.severity} />{" "}
                  <span className="mono">{row.check_id}</span> — {row.detected.slice(0, 90)}
                </li>
              ))}
            </ul>
            {detail.readiness.rows.length > 8 && <p className="subtle">+ {detail.readiness.rows.length - 8} further checks — full matrix after running.</p>}
          </div>
          <div className="card">
            <div className="card-head"><h3>Object census</h3><span className="subtle">top IDF object types</span></div>
            <table className="data" style={{ minWidth: 0 }}>
              <tbody>
                {Object.entries(detail.object_census).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([t, n]) => (
                  <tr key={t}><td className="mono">{t}</td><td className="mono num">{n}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ gridColumn: "1 / -1" }}>
            <ProvenanceDrawer rows={[
              { k: "file", v: detail.path },
              { k: "sha-256", v: detail.sha256 },
              { k: "energyplus version", v: detail.energyplus_version ?? "unknown" },
              { k: "zones", v: String(detail.n_zones) },
            ]} summary="MODEL PROVENANCE" />
          </div>
        </div>
      )}
    </section>
  );
}
