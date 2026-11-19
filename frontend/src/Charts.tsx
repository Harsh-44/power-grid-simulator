import { useMemo } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  usePlotArea,
  useXAxisInverseDataSnapScale,
} from "recharts";
import type { TooltipContentProps } from "recharts";
import type { FaultAnalysis, SimulationResult, SimulationSample } from "./api";
import { formatFrequency, formatTimestamp, frequencyConditions } from "./format";

const axisStyle = { fill: "#52647b", fontSize: 12 };
const axisLine = { stroke: "#cbd5e1" };
const frequencyTicks = new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const tooltipStyle = {
  border: "1px solid #dbe3ed",
  borderRadius: 8,
  padding: "4px 8px",
  boxShadow: "0 2px 8px rgb(15 23 42 / 0.08)",
  fontSize: 12,
};
const tooltipLabelStyle = { color: "#334155", fontWeight: 600 };
const playbackCursor = { stroke: "#0f766e", strokeWidth: 1.25, zIndex: 500 };
const hoverCursor = { stroke: "#94a3b8", strokeDasharray: "3 3" };
const panel = "flex min-h-0 min-w-0 flex-col rounded-xl border border-slate-200 bg-white shadow-sm";

const timeAxis = {
  type: "number",
  dataKey: "time_seconds",
  tickCount: 7,
  allowDataOverflow: true,
  height: 24,
  minTickGap: 16,
  tick: axisStyle,
  tickLine: false,
  axisLine,
  tickMargin: 6,
  tickFormatter: formatTimestamp,
} as const;

const timeLabel = (value: unknown) => formatTimestamp(Number(value));

type StateSeries = "generator" | "breaker";

interface ChartPoint {
  sample: Readonly<SimulationSample>;
  time_seconds: number;
  actual: number;
  reported: number;
  generator: 0 | 1;
  breaker: 0 | 1;
}

interface ChartProps {
  points: ChartPoint[];
  duration: number;
  currentTime: number;
  onSeek: (time: number) => void;
}

function ChartClickTarget({ onSeek }: { onSeek: ChartProps["onSeek"] }) {
  const plot = usePlotArea();
  const snapToSample = useXAxisInverseDataSnapScale();
  if (!plot || !snapToSample || plot.width <= 0 || plot.height <= 0) return null;
  return (
    <rect
      {...plot}
      fill="transparent"
      pointerEvents="all"
      aria-hidden="true"
      data-chart-seek=""
      className="cursor-crosshair"
      onClick={(event) => {
        const bounds = event.currentTarget.getBoundingClientRect();
        if (!bounds.width) return;
        const plotX = plot.x + (event.clientX - bounds.left) * (plot.width / bounds.width);
        const timestamp = snapToSample(plotX);
        if (typeof timestamp === "number") onSeek(timestamp);
      }}
    />
  );
}

function FrequencyTooltip({ active, payload }: TooltipContentProps) {
  const point = payload[0]?.payload as ChartPoint | undefined;
  if (!active || !point) return null;
  const { sample } = point;
  const unsafe = sample.frequency_condition !== "normal";
  return (
    <div className="pointer-events-none min-w-44 rounded-lg border border-slate-200 bg-white p-3 text-xs shadow-md">
      <p className="mb-1.5 font-semibold text-slate-900 tabular-nums">{formatTimestamp(sample.time_seconds)}</p>
      <dl className="grid grid-cols-[1fr_auto] gap-x-3 gap-y-1 text-slate-600">
        <dt>Actual frequency</dt>
        <dd className="text-right font-semibold text-blue-900 tabular-nums">{formatFrequency(sample.actual_frequency_hz)}</dd>
        <dt>FS101 reported</dt>
        <dd className="text-right font-semibold text-violet-900 tabular-nums">{formatFrequency(sample.reported_frequency_hz)}</dd>
        <dt>Frequency status</dt>
        <dd className={`text-right font-semibold ${unsafe ? "text-red-800" : "text-emerald-800"}`}>
          {frequencyConditions[sample.frequency_condition]}
        </dd>
        <dt>CB101 recorded state</dt>
        <dd className="text-right font-medium text-slate-800">{sample.breaker_state}</dd>
      </dl>
      <p className="mt-2 border-t border-slate-200 pt-1.5 text-[11px] text-slate-600">Click chart to seek</p>
    </div>
  );
}

function FrequencyChart({
  points,
  duration,
  currentTime,
  onSeek,
  lower,
  nominal,
  upper,
  fault,
}: ChartProps & { lower: number; nominal: number; upper: number; fault: FaultAnalysis | null }) {
  let min = lower;
  let max = upper;
  for (const point of points) {
    min = Math.min(min, point.actual, point.reported);
    max = Math.max(max, point.actual, point.reported);
  }
  const padding = (max - min) * 0.12;
  const showReported = points.some((point) => point.actual !== point.reported);
  const references = [
    { name: "Lower", value: lower, color: "#92400e" },
    { name: "Nominal", value: nominal, color: "#52647b" },
    { name: "Upper", value: upper, color: "#92400e" },
  ];

  return (
    <section className={panel}>
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-x-4 gap-y-1.5 px-3 py-3 sm:px-4">
        <h2 className="text-[15px] font-semibold tracking-tight">Bus frequency <span className="pl-1 text-xs font-medium text-slate-600">FS101</span></h2>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-700">
          <span className="inline-flex items-center gap-1.5">
            <span aria-hidden="true" className="w-4 border-t-2 border-blue-700" />
            {showReported ? "Actual frequency" : "Actual and FS101 reported"}
          </span>
          {showReported && (
            <span className="inline-flex items-center gap-1.5">
              <span aria-hidden="true" className="w-4 border-t-2 border-dashed border-violet-700" /> FS101 reported
            </span>
          )}
          {fault && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2 py-0.5 text-amber-900">
              <span aria-hidden="true" className="h-2.5 w-3 rounded-sm bg-amber-200" />
              Bias window {formatTimestamp(fault.start_seconds)}–{formatTimestamp(fault.end_seconds)}
            </span>
          )}
        </div>
      </div>
      <div className="chart-plot h-[260px] min-h-0 min-w-0 sm:h-[316px]">
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
          <LineChart data={points} margin={{ top: 6, right: 100, bottom: 6, left: 10 }}>
            <CartesianGrid vertical={false} stroke="#e3eaf2" />
            <XAxis {...timeAxis} domain={[0, duration]} />
            <YAxis
              width={47}
              domain={[min - padding, max + padding]}
              tickCount={5}
              tick={axisStyle}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => frequencyTicks.format(value)}
            />
            {fault && (
              <>
                <ReferenceArea x1={fault.start_seconds} x2={fault.end_seconds} fill="#fde68a" fillOpacity={0.26} stroke="none" />
                <ReferenceLine x={fault.start_seconds} stroke="#b7792b" strokeOpacity={0.5} strokeDasharray="3 3" />
                <ReferenceLine x={fault.end_seconds} stroke="#b7792b" strokeOpacity={0.5} strokeDasharray="3 3" />
              </>
            )}
            {references.map(({ name, value, color }) => (
              <ReferenceLine
                key={name}
                y={value}
                stroke={color}
                strokeDasharray="5 4"
                label={{
                  value: `${name} ${formatFrequency(value)}`,
                  position: "right",
                  fill: color,
                  fontSize: 11,
                }}
              />
            ))}
            <ReferenceLine x={currentTime} {...playbackCursor} />
            <Tooltip
              content={FrequencyTooltip}
              cursor={hoverCursor}
              isAnimationActive={false}
            />
            <Line
              name="Actual frequency"
              dataKey="actual"
              type="linear"
              stroke="#1d4ed8"
              strokeWidth={2.25}
              dot={false}
              isAnimationActive={false}
            />
            {showReported && (
              <Line
                name="FS101 reported"
                dataKey="reported"
                type="linear"
                stroke="#7650ad"
                strokeDasharray="5 4"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            )}
            <ChartClickTarget onSeek={onSeek} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function StateChart({
  points,
  duration,
  currentTime,
  onSeek,
  series,
  title,
  states,
}: ChartProps & { series: StateSeries; title: string; states: [string, string] }) {
  const stateLabel = (value: number) => `${value} ${states[value]}`;
  return (
    <section className={panel}>
      <h2 className="shrink-0 px-3 py-2 text-[13px] font-semibold sm:px-4">{title}</h2>
      <div className="chart-plot h-[124px] min-h-0 min-w-0 sm:h-[144px]">
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
          <LineChart data={points} margin={{ top: 6, right: 18, bottom: 5, left: 7 }}>
            <CartesianGrid vertical={false} stroke="#edf1f6" />
            <XAxis {...timeAxis} domain={[0, duration]} tickCount={5} />
            <YAxis width={82} domain={[-0.2, 1.2]} ticks={[0, 1]} tickFormatter={stateLabel} tick={axisStyle} tickLine={false} axisLine={false} />
            <ReferenceLine x={currentTime} {...playbackCursor} />
            <Tooltip
              labelFormatter={timeLabel}
              formatter={(value) => [stateLabel(Number(value)), title]}
              isAnimationActive={false}
              cursor={hoverCursor}
              contentStyle={tooltipStyle}
              labelStyle={tooltipLabelStyle}
            />
            <Line
              dataKey={series}
              type="stepBefore"
              stroke="#3a5678"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <ChartClickTarget onSeek={onSeek} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

export default function Charts({ result, currentTime, onSeek }: {
  result: SimulationResult;
  currentTime: number;
  onSeek: ChartProps["onSeek"];
}) {
  const points = useMemo<ChartPoint[]>(
    () => result.samples.map((sample) => ({
      sample,
      time_seconds: sample.time_seconds,
      actual: sample.actual_frequency_hz,
      reported: sample.reported_frequency_hz,
      generator: sample.generator_state === "ON" ? 1 : 0,
      breaker: sample.breaker_state === "CLOSED" ? 1 : 0,
    })),
    [result.samples],
  );
  const config = result.config;
  const common = { points, duration: config.duration_seconds, currentTime, onSeek };
  return (
    <div className="chart-workspace grid min-h-0 min-w-0 gap-3">
      <FrequencyChart
        {...common}
        lower={config.lower_limit_hz}
        nominal={config.nominal_frequency_hz}
        upper={config.upper_limit_hz}
        fault={result.fault_analysis}
      />
      <div className="grid min-h-0 min-w-0 gap-3 md:grid-cols-2">
        <StateChart {...common} series="generator" title="Generator G101" states={["OFF", "ON"]} />
        <StateChart {...common} series="breaker" title="Circuit Breaker CB101" states={["OPEN", "CLOSED"]} />
      </div>
    </div>
  );
}

