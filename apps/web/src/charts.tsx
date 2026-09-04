import { useEffect, useRef } from "react";
import * as echarts from "echarts";

/* Neo-Brutalist chart language: paper plot, ink axes, technical grid,
   flat black-outlined series, explicit thresholds. Never default ECharts. */

export const NB_INK = "#161616";
export const NB_PAPER = "#FBFAF6";
export const NB_GRID = "#D8CCB9";
export const NB_SERIES = ["#161616", "#F36D30", "#12C8B0", "#8167F5", "#FF4F85", "#4BD14A"];
export const NB_THRESHOLD = "#D63A2F";

/* Stepped heat bins — discrete classes, never soft continuous glow. */
export const NB_HEAT_BINS = ["#12C8B0", "#8FE3D4", "#FCDD28", "#F36D30", "#FF4F85", "#D63A2F"];

export const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/* Legacy ramp (kept for pages not yet migrated). */
export const TEMP_SCALE = [
  [0.0, "#12C8B0"],
  [0.26, "#8FE3D4"],
  [0.5, "#FCDD28"],
  [0.72, "#F36D30"],
  [0.88, "#FF4F85"],
  [1.0, "#D63A2F"],
] as const;

const AXIS_COMMON = {
  axisLine: { show: true, lineStyle: { color: NB_INK, width: 2 } },
  axisTick: { show: true, lineStyle: { color: NB_INK } },
  axisLabel: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 11 },
  splitLine: { lineStyle: { color: NB_GRID, type: [4, 4] as const } },
};

/** Base option fragment every figure merges in: paper background, ink text. */
export function nbBase(title?: string): echarts.EChartsOption {
  return {
    backgroundColor: NB_PAPER,
    textStyle: { fontFamily: "Inter, Arial, sans-serif", color: NB_INK },
    title: title
      ? {
          text: title,
          left: 4,
          textStyle: {
            fontFamily: "Arial Black, Arial, sans-serif",
            fontSize: 14,
            color: NB_INK,
          },
        }
      : undefined,
    grid: { left: 56, right: 16, top: 44, bottom: 40 },
    tooltip: {
      backgroundColor: "#FCDD28",
      borderColor: NB_INK,
      borderWidth: 2,
      textStyle: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 12 },
      extraCssText: "box-shadow: 4px 4px 0 #161616; border-radius: 4px;",
    },
    legend: {
      textStyle: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 11 },
      itemWidth: 18,
      itemHeight: 12,
      icon: "rect",
    },
  };
}

export function nbCategoryAxis(name: string, data: (string | number)[]): object {
  return { ...AXIS_COMMON, type: "category", name, data, nameTextStyle: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 11 } };
}

export function nbValueAxis(name: string, extra?: object): object {
  return { ...AXIS_COMMON, type: "value", name, nameTextStyle: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 11 }, ...(extra ?? {}) };
}

/** A dashed ink/red threshold line with a framed label. */
export function nbThresholdLine(value: number, label: string, color = NB_THRESHOLD): object {
  return {
    markLine: {
      silent: true,
      symbol: "none",
      lineStyle: { color, width: 2, type: [6, 4] as const },
      label: {
        formatter: label,
        fontFamily: "IBM Plex Mono, monospace",
        fontSize: 11,
        color: "#FBFAF6",
        backgroundColor: color,
        padding: [3, 6],
        borderRadius: 3,
      },
      data: [{ yAxis: value }],
    },
  };
}

export function useChart(
  ref: React.RefObject<HTMLDivElement | null>,
  option: echarts.EChartsOption | null,
  deps: unknown[],
): React.MutableRefObject<echarts.ECharts | null> {
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    // SVG renderer: crisp in-page figures and true SVG export (RULE 10 / §22.1).
    const chart = echarts.init(ref.current, undefined, { renderer: "svg" });
    chartRef.current = chart;
    const onResize = () => chart.resize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      chart.dispose();
      chartRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (ref.current && option) {
      chartRef.current?.setOption(option, { notMerge: true });
      if (!reduce) chartRef.current?.setOption({ animationDurationUpdate: 150 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return chartRef;
}

/* Accessible text summary for a chart (plan: charts need text alternatives). */
export function ChartSummary({ children }: { children: React.ReactNode }) {
  return <p className="sr-only-summary" style={{
    position: "absolute", width: 1, height: 1, overflow: "hidden",
    clip: "rect(0 0 0 0)", whiteSpace: "nowrap",
  }}>{children}</p>;
}
