import type { ReactNode } from "react";

/* Status pill: icon + text + colour (never colour alone). */
export function StatusPill({
  status,
}: {
  status: string;
}) {
  const s = status.toUpperCase();
  let cls = "pill-neutral";
  let label = s.replaceAll("_", " ");
  let icon: ReactNode = (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.6">
      <circle cx="5" cy="5" r="3.6" />
    </svg>
  );
  if (s === "PASS" || s === "OK" || s === "NO_FLAG" || s === "COMPLETE" || s === "SOURCE_VERIFIED") {
    cls = "pill-pass";
    icon = (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.6">
        <path d="m1.8 5.4 2 2 4.4-5" />
      </svg>
    );
  } else if (s === "FAIL" || s === "ERROR") {
    cls = "pill-fail";
    icon = (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.6">
        <path d="m2 2 6 6M8 2l-6 6" />
      </svg>
    );
  } else if (s === "PASS_WITH_WARNINGS" || s === "WARNING" || s === "FLAG" || s === "STAGE") {
    cls = "pill-warn";
    icon = (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.4">
        <path d="M5 1.2 9.2 8.6H.8Z" />
        <path d="M5 4v2.2M5 7.6v.2" />
      </svg>
    );
    if (s === "FLAG") label = "RISK FLAG";
  } else if (s === "INFO" || s === "RESEARCH_ONLY" || s === "SECONDARY_PENDING" || s === "PARTIAL") {
    cls = "pill-info";
  }
  if (s === "SOURCE_VERIFIED") label = "SOURCE VERIFIED";
  if (s === "PASS_WITH_WARNINGS") label = "PASS · WARNINGS";
  return <span className={`pill ${cls}`}>{icon}{label}</span>;
}

/* Journal-figure wrapper: hairline frame + mono caption row. */
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
