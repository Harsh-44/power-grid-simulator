import type { SimulationEvent, SimulationResult } from "./api";
import { formatFrequency, formatTimestamp } from "./format";

const eventLabels = {
  generator_shutdown: { label: "Generator shutdown", tone: "bg-amber-100 text-amber-900" },
  load_connected_unpowered: { label: "Load connected without generator power", tone: "bg-amber-100 text-amber-900" },
  load_connected_unpowered_ended: { label: "Unpowered connection ended", tone: "bg-slate-100 text-slate-700" },
  fault_activated: { label: "Fault activated", tone: "bg-amber-100 text-amber-900" },
  fault_cleared: { label: "Fault cleared", tone: "bg-emerald-50 text-emerald-900" },
  breaker_opened: { label: "Breaker opened", tone: "bg-slate-100 text-slate-700" },
  breaker_closed: { label: "Breaker closed", tone: "bg-slate-100 text-slate-700" },
  frequency_below_limit: { label: "Entered under-frequency", tone: "bg-red-100 text-red-900" },
  frequency_above_limit: { label: "Entered over-frequency", tone: "bg-red-100 text-red-900" },
  under_frequency_exited: { label: "Exited under-frequency", tone: "bg-emerald-50 text-emerald-900" },
  over_frequency_exited: { label: "Exited over-frequency", tone: "bg-emerald-50 text-emerald-900" },
  invalid_state: { label: "Invalid state", tone: "bg-red-100 text-red-900" },
} satisfies Record<SimulationEvent["type"], { label: string; tone: string }>;

function TimeJump({ time, onSeek }: { time: number | null; onSeek: (time: number) => void }) {
  if (time === null) return <span>Time unavailable</span>;
  const label = formatTimestamp(time);
  return (
    <button
      type="button"
      aria-label={`Jump to ${label}`}
      onClick={() => onSeek(time)}
      className="whitespace-nowrap rounded bg-slate-100 px-2 py-1 font-medium text-blue-800 tabular-nums hover:bg-blue-100"
    >
      {label}
    </button>
  );
}

function EventLog({ events, onSeek }: { events: SimulationResult["events"]; onSeek: (time: number) => void }) {
  return (
    <details className="border-t border-slate-200 pt-3">
      <summary className="cursor-pointer font-semibold">Operational events ({events.length})</summary>
      {events.length === 0 ? (
        <p className="mt-2 text-sm text-slate-600">No operational events in this run.</p>
      ) : (
        <>
          <p className="mt-2 text-sm text-slate-600">
            Select a time to inspect its sample. A switch at that time applies to the following interval.
          </p>
          <ol className="mt-2 divide-y divide-slate-200 text-[13px]">
            {events.map((event) => (
              <li key={`${event.time_seconds}-${event.type}`} className="grid grid-cols-[auto_minmax(0,1fr)] items-start gap-x-3 py-2">
                <div className="min-w-12">
                  <TimeJump time={event.time_seconds} onSeek={onSeek} />
                </div>
                <div>
                  <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                    <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${eventLabels[event.type].tone}`}>
                      {eventLabels[event.type].label}
                    </span>
                    <span className="font-semibold text-slate-700">{event.component_id}</span>
                    {event.previous_state && event.new_state && (
                      <span className="text-xs text-slate-600">{event.previous_state} → {event.new_state}</span>
                    )}
                  </div>
                  <p className="mt-0.5 text-slate-600">{event.reason}</p>
                </div>
              </li>
            ))}
          </ol>
        </>
      )}
    </details>
  );
}

function ControllerTrace({
  trace,
  onSeek,
}: {
  trace: NonNullable<SimulationResult["controller_trace"]>;
  onSeek: (time: number) => void;
}) {
  return (
    <details className="border-t border-slate-200 pt-3">
      <summary className="cursor-pointer font-semibold">Controller debug trace ({trace.length})</summary>
      <div className="mt-2 max-h-80 overflow-auto">
        <table aria-label="Controller decisions by time" className="w-full min-w-[32rem] text-left text-sm">
          <thead className="sticky top-0 bg-white text-slate-600">
            <tr>
              {["Time", "FS101 reported", "G101", "CB101 decision", "Reason"].map((heading) => (
                <th key={heading} scope="col" className="p-2 font-medium">{heading}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {trace.map((decision) => (
              <tr key={decision.time_seconds}>
                <td className="p-2"><TimeJump time={decision.time_seconds} onSeek={onSeek} /></td>
                <td className="whitespace-nowrap p-2 tabular-nums">{formatFrequency(decision.reported_frequency_hz)}</td>
                <td className="p-2">{decision.generator_state}</td>
                <td className="whitespace-nowrap p-2">{decision.previous_state} → {decision.new_state}</td>
                <td className="p-2">{decision.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}

export default function RunDiagnostics({ result, onSeek }: { result: SimulationResult; onSeek: (time: number) => void }) {
  const { protection_diagnostics: protection, events, controller_trace: trace } = result;
  return (
    <>
      <EventLog events={events} onSeek={onSeek} />
      <details className="border-t border-slate-200 pt-3">
        <summary className="cursor-pointer font-semibold">Breaker protection diagnostics</summary>
        <dl className="mt-2 flex flex-wrap gap-x-6 gap-y-2 text-sm">
          <div>
            <dt className="text-slate-600">Premature openings</dt>
            <dd className="font-medium">{protection.premature_opening_count}</dd>
          </div>
          <div>
            <dt className="text-slate-600">Missed protective openings</dt>
            <dd className="font-medium">{protection.missed_protective_opening_count}</dd>
          </div>
        </dl>
        {protection.findings.length > 0 && (
          <ol className="mt-2 max-h-80 divide-y divide-slate-200 overflow-auto text-sm">
            {protection.findings.map((finding) => (
              <li key={finding.time_seconds} className="space-y-1 py-2">
                <div className="flex flex-wrap items-baseline gap-2">
                  <TimeJump time={finding.time_seconds} onSeek={onSeek} />
                  <strong>{finding.type === "premature_opening" ? "Premature opening" : "Missed protective opening"}</strong>
                </div>
                <p className="text-slate-700">
                  Actual {formatFrequency(finding.actual_frequency_hz)} · FS101 {formatFrequency(finding.reported_frequency_hz)}
                </p>
                <p className="text-slate-700">CB101 chose {finding.chosen_state}. With ideal FS101 it would choose {finding.reference_state}.</p>
                <p className="text-slate-600">{finding.reference_reason}</p>
              </li>
            ))}
          </ol>
        )}
      </details>
      {trace && <ControllerTrace trace={trace} onSeek={onSeek} />}
    </>
  );
}
