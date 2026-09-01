import { useEffect, useRef } from "react";
import * as echarts from "echarts";

/* Sequential temperature scale: cool -> warm through the OverheatLens ramp. */
export const TEMP_SCALE = [
  [0.0, "#47b9cf"],
  [0.26, "#a7dde1"],
  [0.5, "#d7ef78"],
  [0.72, "#f39a3c"],
  [0.88, "#e56f2f"],
  [1.0, "#c94436"],
] as const;

export const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

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
      if (!reduce) chartRef.current?.setOption({ animationDurationUpdate: 180 });
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
