import { useRef } from "react";
import { useChart, TEMP_SCALE, MONTHS } from "./charts";

/* The signature element: the thermal year ribbon — 365 days x 24 hours of the
 * real weather file, drawn as an instrument readout inside a hairline frame. */
export function ThermalRibbon({
  dryBulb,
  figNo,
  place,
  height = 190,
}: {
  dryBulb: (number | null)[];
  figNo: string;
  place: string;
  height?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);

  const valid = dryBulb.filter((v): v is number => v !== null);
  const min = valid.length ? Math.min(...valid) : 0;
  const max = valid.length ? Math.max(...valid) : 0;

  useChart(
    ref,
    {
      grid: { left: 34, right: 8, top: 8, bottom: 20 },
      xAxis: {
        type: "category",
        data: Array.from({ length: Math.ceil(dryBulb.length / 24) }, (_, i) => i + 1),
        axisLine: { lineStyle: { color: "#b7b8b3" } },
        axisTick: { show: false },
        axisLabel: {
          color: "#5e686e", fontFamily: "IBM Plex Mono", fontSize: 10,
          interval: (i: number) => [0, 30, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334].includes(i),
          formatter: (i: string) => MONTHS[monthOfDay(Number(i))],
        },
      },
      yAxis: {
        type: "category",
        data: ["24", "18", "12", "6", "0"],
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: "#5e686e", fontFamily: "IBM Plex Mono", fontSize: 10 },
        splitLine: { show: false },
      },
      visualMap: {
        show: false,
        min,
        max,
        inRange: { color: TEMP_SCALE.map((s) => s[1]) },
      },
      series: [{
        type: "heatmap",
        data: dryBulb.map((v, i) => [Math.floor(i / 24), 23 - (i % 24), v]),
        progressive: 4000,
      }],
      tooltip: {
        confine: true,
        formatter: (p: unknown) => {
          const params = p as { value: [number, number, number] };
          const day = params.value[0] + 1;
          const hour = 23 - params.value[1] + 1;
          return `${dayOfYearToDate(day)}, hour ${String(hour).padStart(2, "0")}:00 — ${params.value[2]?.toFixed(1) ?? "–"} °C`;
        },
      },
    },
    [dryBulb],
  );

  return (
    <div className="figure">
      <div ref={ref} style={{ height }} role="img"
        aria-label={`Thermal year ribbon for ${place}: hourly dry-bulb temperature, ${min.toFixed(1)} to ${max.toFixed(1)} degrees Celsius.`} />
      <div className="figure-caption">
        <span className="fig-no">{figNo}</span>
        <span>hourly dry-bulb temperature, {place}</span>
        <span style={{ marginLeft: "auto" }}>
          min {min.toFixed(1)} · max {max.toFixed(1)} °C
        </span>
      </div>
    </div>
  );
}

const MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
const MONTH_NAMES = MONTHS;

function monthOfDay(dayIndex0: number): number {
  let d = dayIndex0;
  for (let m = 0; m < 12; m++) {
    if (d < MONTH_DAYS[m]) return m;
    d -= MONTH_DAYS[m];
  }
  return 11;
}

function dayOfYearToDate(day1: number): string {
  let d = day1;
  for (let m = 0; m < 12; m++) {
    if (d <= MONTH_DAYS[m]) return `${d} ${MONTH_NAMES[m]}`;
    d -= MONTH_DAYS[m];
  }
  return `31 Dec`;
}
