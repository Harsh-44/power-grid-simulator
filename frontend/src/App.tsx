import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { configuredScenario, getConfig, runSimulation, scenarioLabels } from "./api";
import type { Scenario, SimulationConfig, SimulationResult } from "./api";
import Drawer from "./Drawer";
import Playback from "./Playback";
import RunConfiguration, { hasPendingSettings, makeDraft, runButtonStyle } from "./RunConfiguration";
import type { ConfigurationDraft } from "./RunConfiguration";

export default function App() {
  const [config, setConfig] = useState<SimulationConfig | null>(null);
  const [draft, setDraft] = useState<ConfigurationDraft | null>(null);
  const [scenario, setScenario] = useState<Scenario>("normal");
  const [completed, setCompleted] = useState<{ id: number; result: SimulationResult } | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(true);
  const configuration = useRef<HTMLDialogElement>(null);
  const configurationForm = useRef<HTMLFormElement>(null);
  const pending = Boolean(completed && draft && hasPendingSettings(draft, scenario, completed.result));

  useEffect(() => {
    const abort = new AbortController();

    async function loadDashboard() {
      try {
        const defaults = await getConfig(abort.signal);
        if (abort.signal.aborted) return;
        setConfig(defaults);
        setDraft(makeDraft(defaults));
        setScenario(configuredScenario(defaults));
      } catch {
        if (!abort.signal.aborted) {
          setError("Could not load the configuration. Check that the backend is running, then reload.");
          setRunning(false);
        }
        return;
      }

      try {
        const initial = await runSimulation({}, abort.signal);
        if (!abort.signal.aborted) setCompleted({ id: 0, result: initial });
      } catch (error) {
        if (!abort.signal.aborted) setError(error instanceof Error ? error.message : "The simulation failed.");
      } finally {
        if (!abort.signal.aborted) setRunning(false);
      }
    }

    void loadDashboard();
    return () => abort.abort();
  }, []);

  function submitRun() {
    const form = configurationForm.current;
    if (!form) return;
    if (!form.checkValidity()) {
      configuration.current?.showModal();
      form.reportValidity();
      return;
    }
    form.requestSubmit();
  }

  async function handleRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (running || !draft) return;
    const form = new FormData(event.currentTarget);
    setError("");
    setRunning(true);
    try {
      const result = await runSimulation({
        duration_seconds: Number(form.get("duration_seconds")),
        initial_frequency_hz: Number(form.get("initial_frequency_hz")),
        breaker_open_threshold_hz: scenario === "manual" ? undefined : Number(form.get("breaker_open_threshold_hz")),
        breaker_close_threshold_hz: scenario === "manual" ? undefined : Number(form.get("breaker_close_threshold_hz")),
        fs101_bias: scenario === "bias" ? {
          start_seconds: Number(form.get("fault_start_seconds")),
          duration_seconds: Number(form.get("fault_duration_seconds")),
          offset_hz: Number(form.get("fault_offset_hz")),
        } : config?.fs101_bias ? null : undefined,
        generator_shutdown_seconds: scenario === "shutdown"
          ? Number(draft.shutdown) : config?.generator_shutdown_seconds != null ? null : undefined,
        manual_state_testing: scenario === "manual" ? true : config?.manual_state_testing ? false : undefined,
        initial_generator_state: scenario === "manual" ? draft.generator : scenario === "shutdown" ? "ON" : undefined,
        initial_breaker_state: scenario === "manual" ? draft.breaker : undefined,
        include_controller_trace: form.has("include_controller_trace") || undefined,
      });
      setCompleted((previous) => ({ id: (previous?.id ?? 0) + 1, result }));
      configuration.current?.close();
    } catch (error) {
      setError(error instanceof Error ? error.message : "The simulation failed.");
    } finally {
      setRunning(false);
    }
  }

  const controls = (
    <section aria-label="Simulation controls" className="space-y-3 p-4">
      <h2 className="text-sm font-semibold">Simulation</h2>
      <label className="grid gap-1 text-[13px] font-medium text-slate-600">
        <span>Scenario</span>
        <span className="relative min-w-0">
          <select
            disabled={!config || running}
            className="h-9 w-full appearance-none rounded-md border border-slate-300 bg-white pr-7 pl-2.5 text-[13px] font-medium text-slate-900 enabled:cursor-pointer enabled:hover:border-slate-400 disabled:text-slate-500"
            value={scenario}
            onChange={(event) => {
              const next = event.currentTarget.value as Scenario;
              setScenario(next);
              if (next !== "normal") configuration.current?.showModal();
            }}
          >
            {Object.entries(scenarioLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <span aria-hidden="true" className="pointer-events-none absolute top-[14px] right-3 size-[6px] rotate-45 border-r border-b border-slate-500" />
        </span>
      </label>
      <div className="grid grid-cols-[auto_1fr] gap-2">
        <button
          type="button"
          aria-haspopup="dialog"
          disabled={!config || running}
          onClick={() => configuration.current?.showModal()}
          className="h-9 rounded-md border border-slate-300 bg-white px-3 text-[13px] font-semibold text-slate-700 transition-colors enabled:cursor-pointer enabled:hover:bg-slate-100 disabled:opacity-60"
        >
          Configure
        </button>
        <button type="button" disabled={!config || running} className={runButtonStyle + " enabled:cursor-pointer"} onClick={submitRun}>
          {running ? "Running…" : "Run Simulation"}
        </button>
      </div>
    </section>
  );

  return (
    <div className="dashboard flex min-h-dvh flex-col bg-[#f3f6fa] text-slate-900">
      <header className="shrink-0 border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-[112rem] flex-wrap items-center justify-between gap-x-6 gap-y-2 px-4 py-2.5 sm:px-6">
          <div className="flex min-w-0 items-center gap-2.5">
            <div aria-hidden="true" className="flex size-8 shrink-0 items-end justify-center gap-0.5 rounded-md bg-blue-700 pb-2">
              <span className="h-2 w-[3px] rounded-sm bg-blue-200" />
              <span className="h-4 w-[3px] rounded-sm bg-white" />
              <span className="h-3 w-[3px] rounded-sm bg-blue-200" />
            </div>
            <h1 className="text-[17px] leading-tight font-semibold tracking-tight sm:text-lg">
              Arctic Station Power Grid Simulator
            </h1>
          </div>
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-[112rem] min-h-0 flex-1 flex-col gap-3 px-4 py-3 sm:px-6">
        {error && (
          <p role="alert" className="shrink-0 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-[13px] text-red-900">
            {error}
          </p>
        )}
        {completed ? (
          <Playback key={completed.id} result={completed.result} pending={pending} running={running} controls={controls} />
        ) : (
          <div className="grid items-start gap-4 lg:grid-cols-[20rem_minmax(0,1fr)]">
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm">{controls}</div>
            {running && (
              <p role="status" className="grid min-h-48 place-items-center rounded-lg border border-slate-200 bg-white text-[13px] font-medium text-slate-600">
                {config ? "Running simulation…" : "Loading configuration…"}
              </p>
            )}
          </div>
        )}
      </main>
      <Drawer panelRef={configuration} title="Configure simulation" description={`Next run · ${scenarioLabels[scenario]}`}>
        {config && draft && (
          <RunConfiguration
            config={config}
            draft={draft}
            scenario={scenario}
            running={running}
            error={error}
            formRef={configurationForm}
            onChange={setDraft}
            onSubmit={handleRun}
          />
        )}
      </Drawer>
    </div>
  );
}
