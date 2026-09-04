import { useRef } from "react";
import { useChart, NB_HEAT_BINS, NB_INK, NB_PAPER, MONTHS } from "./charts";
import { ExportBar } from "./ExportBar";

/* The signature element: the thermal year ribbon — 365 days x 24 hours of the
 * real weather file, drawn as an instrument readout inside a hairline frame. */
export function ThermalRibbon({
  dryBulb,
  figNo,
  place,
  height = 190,
  compact = false,
  hoursPerDay = 24,
}: {
  dryBulb: (number | null)[];
  figNo: string;
  place: string;
  height?: number;
  compact?: boolean;
  hoursPerDay?: 1 | 24;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useChart(ref, null, []);

  const valid = dryBulb.filter((v): v is number => v !== null);
  const min = valid.length ? Math.min(...valid) : 0;
  const max = valid.length ? Math.max(...valid) : 0;

  useChart(
    ref,
    {
      backgroundColor: NB_PAPER,
      grid: { left: 34, right: 8, top: 8, bottom: 20 },
      xAxis: {
        type: "category",
        data: Array.from({ length: Math.ceil(dryBulb.length / hoursPerDay) }, (_, i) => i + 1),
        axisLine: { show: true, lineStyle: { color: NB_INK, width: 2 } },
        axisTick: { show: false },
        axisLabel: {
          color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 10,
          interval: (i: number) => [0, 30, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334].includes(i),
          formatter: (i: string) => MONTHS[monthOfDay(Number(i))],
        },
      },
      yAxis: {
        type: "category",
        data: hoursPerDay === 24 ? ["24", "18", "12", "6", "0"] : ["day"],
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 10 },
        splitLine: { show: false },
      },
      visualMap: {
        show: false,
        min,
        max,
        inRange: { color: NB_HEAT_BINS },
      },
      series: [{
        type: "heatmap",
        data: hoursPerDay === 24
          ? dryBulb.map((v, i) => [Math.floor(i / 24), 23 - (i % 24), v])
          : dryBulb.map((v, i) => [i, 0, v]),
        progressive: 4000,
        itemStyle: { borderWidth: 0 },
      }],
      tooltip: {
        confine: true,
        backgroundColor: "#FCDD28",
        borderColor: NB_INK,
        borderWidth: 2,
        textStyle: { color: NB_INK, fontFamily: "IBM Plex Mono, monospace", fontSize: 12 },
        extraCssText: "box-shadow: 4px 4px 0 #161616; border-radius: 4px;",
        formatter: (p: unknown) => {
          const params = p as { value: [number, number, number] };
          const day = params.value[0] + 1;
          const hour = 24 - params.value[1];
          const hTxt = hoursPerDay === 24 ? `, hour ${String(hour).padStart(2, "0")}:00` : " (daily mean)";
          return `${dayOfYearToDate(day)}${hTxt} — ${params.value[2]?.toFixed(1) ?? "–"} °C`;
        },
      },
    },
    [dryBulb],
  );

  const caption = `${hoursPerDay === 24 ? "Hourly" : "Daily-mean"} dry-bulb temperature, ${place} (thermal year ribbon, ${valid.length} records, ${min.toFixed(1)} to ${max.toFixed(1)} °C). Source: OverheatLens core EPW engine.`;

  return (
    <div className="figure">
      <div ref={ref} style={{ height }} role="img"
        aria-label={`Thermal year ribbon for ${place}: hourly dry-bulb temperature, ${min.toFixed(1)} to ${max.toFixed(1)} degrees Celsius.`} />
      <div className="figure-caption">
        <span className="fig-no">{figNo}</span>
        <span>{hoursPerDay === 24 ? "hourly" : "daily-mean"} dry-bulb temperature, {place}</span>
        <span style={{ marginLeft: "auto" }}>
          min {min.toFixed(1)} · max {max.toFixed(1)} °C
        </span>
        {!compact && (
          <ExportBar
            chartRef={chartRef}
            figureName={`fig_thermal_ribbon_${place.replace(/\W+/g, "_").toLowerCase()}`}
            caption={caption}
            csv={{
              header: hoursPerDay === 24 ? ["day_of_year", "hour_ending", "dry_bulb_c"] : ["day_of_year", "dry_bulb_c"],
              rows: hoursPerDay === 24
                ? dryBulb.map((v, i) => [Math.floor(i / 24) + 1, (i % 24) + 1, v])
                : dryBulb.map((v, i) => [i + 1, v]),
            }}
          />
        )}
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
