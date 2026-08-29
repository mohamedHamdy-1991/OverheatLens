import { useState } from "react";
import type * as echarts from "echarts";

/* RULE 10 / plan §22: every figure exports SVG, PNG, the plotted data as CSV,
 * and its caption. Exports are generated from the live chart instance and the
 * same arrays that fed it — never re-derived in a second implementation. */

function download(name: string, data: BlobPart, mime: string) {
  const url = URL.createObjectURL(new Blob([data], { type: mime }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export function ExportBar({
  chartRef,
  figureName,
  csv,
  caption,
}: {
  chartRef: React.MutableRefObject<echarts.ECharts | null>;
  figureName: string;
  csv: { header: string[]; rows: (string | number | null)[][] };
  caption: string;
}) {
  const [done, setDone] = useState<string | null>(null);

  const flash = (what: string) => {
    setDone(what);
    window.setTimeout(() => setDone(null), 1600);
  };

  const exportSvg = () => {
    const chart = chartRef.current;
    if (!chart) return;
    const svg = chart.renderToSVGString();
    download(`${figureName}.svg`, svg, "image/svg+xml");
    flash("SVG saved");
  };
  const exportPng = () => {
    const chart = chartRef.current;
    if (!chart) return;
    const url = chart.getDataURL({ type: "png", pixelRatio: 3, backgroundColor: "#ffffff" });
    const a = document.createElement("a");
    a.href = url;
    a.download = `${figureName}.png`;
    a.click();
    flash("PNG saved");
  };
  const exportCsv = () => {
    const esc = (v: string | number | null) =>
      v === null ? "" : typeof v === "string" && /[",\n]/.test(v) ? `"${v.replaceAll('"', '""')}"` : String(v);
    const text = [csv.header.map(esc).join(","), ...csv.rows.map((r) => r.map(esc).join(","))].join("\n");
    download(`${figureName}.csv`, text, "text/csv");
    flash("CSV saved");
  };
  const copyCaption = async () => {
    try {
      await navigator.clipboard.writeText(caption);
      flash("Caption copied");
    } catch {
      flash("Clipboard unavailable");
    }
  };

  const btn: React.CSSProperties = {
    border: "1px solid var(--line)", background: "var(--surface)",
    color: "var(--brand-dark)", borderRadius: 5, cursor: "pointer",
    fontFamily: "var(--font-mono)", fontSize: 10.5, padding: "3px 8px",
  };

  return (
    <span style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
      {done && <span style={{ fontFamily: "var(--font-mono)", fontSize: 10.5, color: "var(--pass)" }}>{done}</span>}
      <button style={btn} onClick={exportSvg}>SVG</button>
      <button style={btn} onClick={exportPng}>PNG</button>
      <button style={btn} onClick={exportCsv}>CSV</button>
      <button style={btn} onClick={copyCaption}>Copy caption</button>
    </span>
  );
}
