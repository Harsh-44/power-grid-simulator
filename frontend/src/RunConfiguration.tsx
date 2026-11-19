import type { FormEventHandler, Ref } from "react";
import { configuredScenario } from "./api";
import type { BreakerState, GeneratorState, Scenario, SensorBiasConfig, SimulationConfig, SimulationOverrides, SimulationResult } from "./api";

const groups = [
  {
    label: "Simulation",
    fields: [
      { name: "duration_seconds", label: "Duration (s)" },
      { name: "initial_frequency_hz", label: "Initial bus frequency (Hz)" },
    ],
  },
  {
    label: "Controller",
    fields: [
      { name: "breaker_open_threshold_hz", label: "CB101 opening threshold (Hz)" },
      { name: "breaker_close_threshold_hz", label: "CB101 recovery threshold (Hz)" },
    ],
  },
] as const;

const faultFields = [
  { name: "start_seconds", label: "Fault start (s)", placeholder: "e.g. 5" },
  { name: "duration_seconds", label: "Fault duration (s)", placeholder: "e.g. 20" },
  { name: "offset_hz", label: "FS101 offset (Hz)", placeholder: "e.g. 0.5" },
] as const;

export interface ConfigurationDraft {
  fields: Record<keyof SimulationOverrides, string>;
  bias: Record<keyof SensorBiasConfig, string>;
  trace: boolean;
  shutdown: string;
  generator: GeneratorState;
  breaker: BreakerState;
}

export function makeDraft(config: SimulationConfig): ConfigurationDraft {
  return {
    fields: {
      duration_seconds: String(config.duration_seconds),
      initial_frequency_hz: String(config.initial_frequency_hz),
      breaker_open_threshold_hz: String(config.breaker_open_threshold_hz),
      breaker_close_threshold_hz: String(config.breaker_close_threshold_hz),
    },
    bias: {
      start_seconds: config.fs101_bias?.start_seconds.toString() ?? "",
      duration_seconds: config.fs101_bias?.duration_seconds.toString() ?? "",
      offset_hz: config.fs101_bias?.offset_hz.toString() ?? "",
    },
    trace: false,
    shutdown: config.generator_shutdown_seconds?.toString() ?? "",
    generator: config.initial_generator_state,
    breaker: config.initial_breaker_state,
  };
}

export function hasPendingSettings(draft: ConfigurationDraft, scenario: Scenario, result: SimulationResult) {
  const used = result.config;
  return scenario !== configuredScenario(used)
    || (scenario !== "manual" && draft.trace !== Boolean(result.controller_trace))
    || groups.some(({ fields, label }) => (scenario !== "manual" || label !== "Controller") && fields.some(({ name }) =>
      draft.fields[name] === "" || Number(draft.fields[name]) !== used[name]))
    || (scenario === "bias" && faultFields.some(({ name }) =>
      draft.bias[name] === "" || Number(draft.bias[name]) !== used.fs101_bias?.[name]))
    || (scenario === "shutdown" && (draft.shutdown === "" || Number(draft.shutdown) !== used.generator_shutdown_seconds))
    || (scenario === "manual" && (draft.generator !== used.initial_generator_state || draft.breaker !== used.initial_breaker_state));
}

const inputStyle = "h-9 w-full min-w-0 rounded-md border border-slate-300 bg-white px-3 text-sm tabular-nums disabled:bg-slate-100";
export const runButtonStyle = "h-9 whitespace-nowrap rounded-md bg-blue-700 px-4 text-[13px] font-semibold text-white transition-colors enabled:hover:bg-blue-800 disabled:opacity-60";

export default function RunConfiguration({
  config, draft, scenario, running, error, formRef, onChange, onSubmit,
}: {
  config: SimulationConfig;
  draft: ConfigurationDraft;
  scenario: Scenario;
  running: boolean;
  error: string;
  formRef: Ref<HTMLFormElement>;
  onChange: (draft: ConfigurationDraft) => void;
  onSubmit: FormEventHandler<HTMLFormElement>;
}) {
  return (
    <form ref={formRef} onSubmit={onSubmit} className="space-y-4">
      {error && <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-[13px] text-red-900">{error}</p>}
      <fieldset disabled={running} className="grid gap-4">
        {groups.filter(({ label }) => scenario !== "manual" || label !== "Controller").map(({ label, fields }) => (
          <section key={label} className="rounded-lg border border-slate-200 bg-white p-4">
            <h3 className="mb-3 text-sm font-semibold">{label}</h3>
            <div className="grid gap-3 min-[420px]:grid-cols-2">
              {fields.map(({ name, label }) => {
                const duration = name === "duration_seconds";
                return (
                  <label key={name} className="grid gap-1 text-[13px] font-medium text-slate-700">
                    {label}
                    <input
                      name={name}
                      type="number"
                      min={duration ? config.time_step_seconds : scenario === "manual" ? undefined : config.lower_limit_hz}
                      max={duration || scenario === "manual" ? undefined : config.upper_limit_hz}
                      step={duration ? config.time_step_seconds : "any"}
                      required
                      value={draft.fields[name]}
                      onChange={(event) => onChange({ ...draft, fields: { ...draft.fields, [name]: event.currentTarget.value } })}
                      className={inputStyle}
                    />
                  </label>
                );
              })}
            </div>
          </section>
        ))}
        {scenario === "bias" && (
          <section className="rounded-lg border border-amber-200 bg-white p-4">
            <h3 className="mb-3 text-sm font-semibold">Fault settings</h3>
            <div className="grid gap-3 min-[420px]:grid-cols-2">
              {faultFields.map(({ name, label, placeholder }) => (
                <label key={name} className="grid gap-1 text-[13px] font-medium text-slate-700">
                  {label}
                  <input
                    name={`fault_${name}`}
                    type="number"
                    min={name === "duration_seconds" ? config.time_step_seconds : name === "start_seconds" ? 0 : undefined}
                    step={name === "offset_hz" ? "any" : config.time_step_seconds}
                    required
                    value={draft.bias[name]}
                    onChange={(event) => onChange({ ...draft, bias: { ...draft.bias, [name]: event.currentTarget.value } })}
                    placeholder={placeholder}
                    className={inputStyle}
                  />
                </label>
              ))}
            </div>
          </section>
        )}
        {scenario === "shutdown" && (
          <section className="rounded-lg border border-slate-200 bg-white p-4">
            <h3 className="mb-2 text-sm font-semibold">Generator failure</h3>
            <label className="grid gap-1 text-[13px] font-medium">
              Shutdown time (s)
              <input name="generator_shutdown_seconds" type="number" min={0} step={config.time_step_seconds} required
                value={draft.shutdown} onChange={(event) => onChange({ ...draft, shutdown: event.currentTarget.value })}
                className={inputStyle} />
            </label>
          </section>
        )}
        {scenario === "manual" && (
          <section className="space-y-3 rounded-lg border border-amber-200 bg-white p-4 text-[13px]">
            <h3 className="font-semibold">Manual state testing</h3>
            <p className="text-amber-900">Diagnostic simulation. Automatic breaker control is disabled for the run. Safety checks stay active.</p>
            <div className="grid grid-cols-2 gap-3">
              <label className="grid gap-1 font-medium">
                Initial G101 state
                <select className={inputStyle} value={draft.generator} onChange={(event) =>
                  onChange({ ...draft, generator: event.currentTarget.value as GeneratorState })}>
                  <option>ON</option><option>OFF</option>
                </select>
              </label>
              <label className="grid gap-1 font-medium">
                Initial CB101 state
                <select className={inputStyle} value={draft.breaker} onChange={(event) =>
                  onChange({ ...draft, breaker: event.currentTarget.value as BreakerState })}>
                  <option>CLOSED</option><option>OPEN</option>
                </select>
              </label>
            </div>
          </section>
        )}
        {scenario !== "manual" && <label className="flex items-center gap-2 text-[13px] font-medium text-slate-700">
          <input
            type="checkbox"
            name="include_controller_trace"
            checked={draft.trace}
            onChange={(event) => onChange({ ...draft, trace: event.currentTarget.checked })}
            className="size-4 accent-blue-700"
          />
          Include controller debug trace
        </label>}
        <button type="submit" className={`${runButtonStyle} justify-self-start`}>
          {running ? "Running simulation…" : "Run Simulation"}
        </button>
      </fieldset>
    </form>
  );
}
