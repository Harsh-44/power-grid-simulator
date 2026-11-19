import { lazy, Suspense, useEffect, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import type { SimulationResult } from "./api";
import { configuredScenario, scenarioLabels } from "./api";
import Drawer from "./Drawer";
import { formatTimestamp } from "./format";
import RunDetails from "./RunDetails";
import RunOverview from "./RunOverview";
import StateInspector from "./StateInspector";

const Charts = lazy(() => import("./Charts"));
const transportStyle = "grid h-9 w-full place-items-center rounded-md border border-slate-200 text-slate-700 transition-colors enabled:cursor-pointer disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400";

function TransportButton({ icon, label, primary = false, disabled, onClick }: {
  icon: "reset" | "back" | "play" | "pause" | "forward";
  label: string;
  primary?: boolean;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={[
        transportStyle,
        primary
          ? "enabled:border-blue-200 enabled:bg-blue-100 enabled:text-blue-800 enabled:hover:border-blue-700 enabled:hover:bg-blue-700 enabled:hover:text-white"
          : "enabled:hover:bg-slate-100",
      ].join(" ")}
      disabled={disabled}
      onClick={onClick}
    >
      <span aria-hidden="true" className={"transport-icon transport-" + icon} />
    </button>
  );
}

export default function Playback({ result, pending, running, controls }: {
  result: SimulationResult;
  pending: boolean;
  running: boolean;
  controls: ReactNode;
}) {
  const { samples, fault_analysis: fault } = result;
  const lastIndex = samples.length - 1;
  const [{ index, playing }, setPlayback] = useState({ index: 0, playing: false });
  const timeline = useRef<HTMLInputElement>(null);
  const details = useRef<HTMLDialogElement>(null);
  const current = samples[index];
  const atEnd = index === lastIndex;
  const activeFault = fault !== null && current.time_seconds >= fault.start_seconds && current.time_seconds < fault.end_seconds;
  const scenario = scenarioLabels[configuredScenario(result.config)];

  useEffect(() => {
    if (!playing || index >= lastIndex) return;
    const timer = window.setTimeout(() => {
      setPlayback((state) => state.playing && state.index === index
        ? { index: index + 1, playing: index + 1 < lastIndex }
        : state);
    }, 1000);
    return () => window.clearTimeout(timer);
  }, [index, lastIndex, playing]);

  function seek(target: number) {
    setPlayback({ index: target, playing: false });
  }

  function seekToTime(time: number) {
    const target = samples.findIndex((sample) => sample.time_seconds === time);
    if (target >= 0) seek(target);
  }

  function seekFromDetails(time: number) {
    seekToTime(time);
    details.current?.close();
    timeline.current?.focus();
  }

  return (
    <>
      <div className="dashboard-columns grid min-h-0 flex-1 gap-4 lg:grid-cols-[20rem_minmax(0,1fr)] xl:grid-cols-[22rem_minmax(0,1fr)]">
        <aside aria-label="Run controls and state" className="dashboard-sidebar min-h-0 min-w-0 divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white shadow-sm">
          {controls}
          <RunOverview result={result} pending={pending} running={running} onDetails={() => details.current?.showModal()} />
          <section aria-label="Playback" className="grid grid-cols-[1fr_auto] items-center gap-3 p-4">
            <h2 className="text-sm font-semibold">Playback</h2>
            <span role="status" className={[
              "rounded-full px-2.5 py-1 text-xs font-medium",
              playing ? "bg-blue-50 text-blue-800" : "bg-slate-100 text-slate-700",
            ].join(" ")}>
              {atEnd ? "End of run" : playing ? "Playing" : "Paused"}
            </span>
            <div className="col-span-2 grid grid-cols-4 gap-2">
              <TransportButton icon="reset" label="Reset" disabled={index === 0 && !playing} onClick={() => seek(0)} />
              <TransportButton icon="back" label="Step backward" disabled={index === 0} onClick={() => seek(index - 1)} />
              <TransportButton
                icon={playing ? "pause" : "play"}
                label={playing ? "Pause" : "Play"}
                disabled={atEnd}
                primary
                onClick={() => setPlayback({ index, playing: !playing })}
              />
              <TransportButton icon="forward" label="Step forward" disabled={atEnd} onClick={() => seek(index + 1)} />
            </div>
            <div className="col-span-2 row-start-3 min-w-0">
              <label htmlFor="playback-time" className="sr-only">Timeline</label>
              <input
                ref={timeline}
                id="playback-time"
                type="range"
                min={0}
                max={lastIndex}
                step={1}
                value={index}
                aria-valuetext={formatTimestamp(current.time_seconds)}
                onChange={(event) => seek(event.currentTarget.valueAsNumber)}
                className="playback-scrubber block w-full"
                style={{ "--progress": ((index / Math.max(1, lastIndex)) * 100) + "%" } as CSSProperties}
              />
              <div className="mt-0.5 text-[13px] font-medium whitespace-nowrap text-slate-600 tabular-nums">
                <span className="font-semibold text-blue-800">{formatTimestamp(current.time_seconds)}</span>
                <span aria-hidden="true"> / </span>
                <span className="sr-only"> of </span>
                {formatTimestamp(samples[lastIndex].time_seconds)}
              </div>
            </div>
          </section>
          <StateInspector sample={current} activeFault={activeFault} />
        </aside>
        <section aria-label="Simulation graphs" className="flex min-h-0 min-w-0 flex-col">
          <Suspense fallback={<p role="status" className="grid min-h-48 flex-1 place-items-center text-[13px] text-slate-600">Loading charts…</p>}>
            <Charts result={result} currentTime={current.time_seconds} onSeek={seekToTime} />
          </Suspense>
        </section>
      </div>
      <Drawer
        panelRef={details}
        title="Run details"
        description={[scenario, formatTimestamp(samples[lastIndex].time_seconds), samples.length + " samples"].join(" · ")}
        presentation="modal"
      >
        <RunDetails result={result} onSeek={seekFromDetails} />
      </Drawer>
    </>
  );
}
