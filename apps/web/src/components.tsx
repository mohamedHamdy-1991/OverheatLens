import { Fragment, useState } from "react";
import type { ReactNode } from "react";

const BASE = import.meta.env.BASE_URL || "./";

/* Page cover banner: a wide illustrated strip at the top of each lab page.
   Images live in public/img; a missing file simply hides itself. */
export function PageCover({ img, alt = "" }: { img: string; alt?: string }) {
  return (
    <img
      className="page-cover"
      src={`${BASE}img/${img}`}
      alt={alt}
      loading="lazy"
      onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
    />
  );
}

/* Status pill: icon + text + colour (never colour alone). */
export function StatusPill({ status }: { status: string }) {
  const s = status.toUpperCase();
  let cls = "pill-neutral";
  let label = s.replaceAll("_", " ");
  let icon: ReactNode = (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="5" cy="5" r="3.6" />
    </svg>
  );
  if (s === "PASS" || s === "OK" || s === "NO_FLAG" || s === "COMPLETE" || s === "SOURCE_VERIFIED" || s === "COMPATIBLE") {
    cls = "pill-pass";
    icon = (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="m1.8 5.4 2 2 4.4-5" />
      </svg>
    );
  } else if (s === "FAIL" || s === "ERROR" || s === "FATAL" || s === "INCOMPATIBLE") {
    cls = "pill-fail";
    icon = (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="m2 2 6 6M8 2l-6 6" />
      </svg>
    );
  } else if (s === "PASS_WITH_WARNINGS" || s === "WARNING" || s === "FLAG" || s === "STAGE" || s === "UNKNOWN") {
    cls = "pill-warn";
    icon = (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M5 1.2 9.2 8.6H.8Z" />
        <path d="M5 4v2.2M5 7.6v.2" />
      </svg>
    );
    if (s === "FLAG") label = "RISK FLAG";
  } else if (s === "INFO" || s === "RESEARCH_ONLY" || s === "SECONDARY_PENDING" || s === "PARTIAL" || s === "RESEARCH IMPLEMENTATION") {
    cls = "pill-info";
  }
  if (s === "SOURCE_VERIFIED") label = "SOURCE VERIFIED";
  if (s === "PASS_WITH_WARNINGS") label = "PASS · WARNINGS";
  if (s === "RESEARCH_ONLY") label = "RESEARCH ONLY";
  return <span className={`pill ${cls}`}>{icon}{label}</span>;
}

/* Standard edition badge: always shows the exact rule-pack edition. */
export function StandardBadge({ packId, version }: { packId: string; version?: string }) {
  const researchOnly = packId === "uk_tm59_2026";
  return (
    <span style={{ display: "inline-flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
      <span className="nb-chip">{packId}{version ? ` · v${version}` : ""}</span>
      {researchOnly ? <StatusPill status="RESEARCH_ONLY" /> : null}
    </span>
  );
}

/* Journal-figure wrapper: framed + mono caption row. */
export function Figure({
  figNo,
  caption,
  meta,
  children,
  ariaLabel,
}: {
  figNo: string;
  caption: ReactNode;
  meta?: ReactNode;
  children: ReactNode;
  ariaLabel?: string;
}) {
  return (
    <figure className="figure" style={{ margin: 0 }} aria-label={ariaLabel}>
      {children}
      <figcaption className="figure-caption">
        <span className="fig-no">{figNo}</span>
        <span>{caption}</span>
        {meta ? <span style={{ marginLeft: "auto" }}>{meta}</span> : null}
      </figcaption>
    </figure>
  );
}

/* Oversized verdict banner: PASS / FAIL / INCOMPLETE / RESEARCH. */
export function ResultVerdict({
  verdict,
  detail,
}: {
  verdict: "PASS" | "FAIL" | "INCOMPLETE" | "RESEARCH";
  detail?: ReactNode;
}) {
  const cls = verdict === "PASS" ? "pass" : verdict === "FAIL" ? "fail" : verdict === "RESEARCH" ? "research" : "incomplete";
  const mark = verdict === "PASS" ? "✓ PASS" : verdict === "FAIL" ? "✕ FAIL" : verdict === "RESEARCH" ? "◈ RESEARCH" : "? INCOMPLETE";
  return (
    <div className={`verdict ${cls}`} role="status" aria-label={`Assessment result: ${verdict}`}>
      <span className="v-mark">{mark}</span>
      <div style={{ fontSize: 13, maxWidth: "60ch" }}>{detail}</div>
    </div>
  );
}

/* Threshold-margin bar: how close a criterion is to its limit. */
export function MarginBar({
  label,
  value,
  limit,
  unit,
  higherIsWorse = true,
}: {
  label: string;
  value: number;
  limit: number;
  unit: string;
  higherIsWorse?: boolean;
}) {
  const over = higherIsWorse ? value > limit : value < limit;
  const span = Math.max(Math.abs(limit), Math.abs(value), 1e-9);
  const fillPct = Math.min(100, (Math.abs(value) / (span * 1.25)) * 100);
  const limitPct = Math.min(100, (Math.abs(limit) / (span * 1.25)) * 100);
  const margin = value - limit;
  return (
    <div className="margin-row">
      <span style={{ fontFamily: "var(--nb-font-mono)", fontSize: 11.5, fontWeight: 700 }}>{label}</span>
      <div className="margin-track" role="img" aria-label={`${label}: ${value} ${unit}, limit ${limit} ${unit}`}>
        <div className={`margin-fill${over ? " over" : ""}`} style={{ width: `${fillPct}%` }} />
        <div className="margin-limit" style={{ left: `${limitPct}%` }} title={`Limit: ${limit} ${unit}`} />
      </div>
      <span style={{ fontFamily: "var(--nb-font-mono)", fontSize: 11.5, whiteSpace: "nowrap" }}>
        {value.toFixed(1)} / {limit.toFixed(1)} {unit}
        <strong style={{ color: over ? "var(--nb-danger)" : "#1e7a3c" }}>
          {" "}{over ? "−" : "+"}{Math.abs(margin).toFixed(1)}
        </strong>
      </span>
    </div>
  );
}

/* Readiness matrix row: ERROR / WARNING / INFORMATION with explanation. */
export function ReadinessRow({
  label,
  status,
  detail,
}: {
  label: string;
  status: "PASS" | "WARNING" | "FAIL" | "INFO";
  detail: string;
}) {
  return (
    <tr>
      <td style={{ fontWeight: 700 }}>{label}</td>
      <td><StatusPill status={status} /></td>
      <td>{detail}</td>
    </tr>
  );
}

/* Provenance drawer: hashes, versions, run ID — inspectable, not cluttering. */
export function ProvenanceDrawer({
  rows,
  summary = "RESULT PROVENANCE",
}: {
  rows: { k: string; v: string }[];
  summary?: string;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ border: "var(--nb-border-2)", borderRadius: "var(--nb-radius-sm)", background: "var(--nb-bg)" }}>
      <button
        className="nb-btn secondary"
        style={{ width: "100%", justifyContent: "space-between", border: "none", boxShadow: "none" }}
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span style={{ fontFamily: "var(--nb-font-mono)", fontSize: 12 }}>{summary}</span>
        <span aria-hidden="true">{open ? "▾" : "▸"}</span>
      </button>
      {open ? (
        <dl style={{ margin: 0, padding: "0 16px 14px", display: "grid", gridTemplateColumns: "minmax(120px,180px) 1fr", gap: "6px 12px", fontSize: 12 }}>
          {rows.map((r) => (
            <Fragment key={r.k}>
              <dt style={{ fontFamily: "var(--nb-font-mono)", fontSize: 10.5, textTransform: "uppercase", color: "var(--nb-ink-soft)" }}>{r.k}</dt>
              <dd className="mono" style={{ margin: 0, wordBreak: "break-all" }}>{r.v}</dd>
            </Fragment>
          ))}
        </dl>
      ) : null}
    </div>
  );
}

/* Expandable method explainer. */
export function MethodNote({ title = "WHAT DOES THIS MEAN?", children }: { title?: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ marginTop: 10 }}>
      <button className="nb-btn secondary" style={{ minHeight: 38, fontSize: 12 }} onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        {open ? "▾" : "▸"} {title}
      </button>
      {open ? <div className="note" style={{ marginTop: 8 }}>{children}</div> : null}
    </div>
  );
}

/* Empty state with generated illustration slot (falls back gracefully). */
export function EmptyState({
  img,
  alt,
  title,
  body,
  action,
}: {
  img: string;
  alt: string;
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <img src={`${BASE}img/${img}`} alt={alt} onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
      <h3>{title}</h3>
      <p>{body}</p>
      {action}
    </div>
  );
}
