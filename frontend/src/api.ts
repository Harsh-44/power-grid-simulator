export type GeneratorState = "ON" | "OFF";
export type BreakerState = "OPEN" | "CLOSED";
type FrequencyCondition = "normal" | "under_frequency" | "over_frequency";

export interface SensorBiasConfig {
  start_seconds: number;
  duration_seconds: number;
  offset_hz: number;
}

export interface SimulationConfig {
  duration_seconds: number;
  time_step_seconds: number;
  initial_frequency_hz: number;
  initial_generator_state: GeneratorState;
  initial_breaker_state: BreakerState;
  nominal_frequency_hz: number;
  lower_limit_hz: number;
  upper_limit_hz: number;
  frequency_rates_hz_per_second: {
    on_closed: number;
    on_open: number;
    off_closed: number;
    off_open: number;
  };
  breaker_open_threshold_hz: number;
  breaker_close_threshold_hz: number;
  fs101_bias: SensorBiasConfig | null;
  generator_shutdown_seconds: number | null;
  manual_state_testing: boolean;
}

export const scenarioLabels = {
  normal: "Normal operation",
  bias: "FS101 measurement fault",
  shutdown: "G101 generator failure",
  manual: "Manual state testing",
} as const;

export type Scenario = keyof typeof scenarioLabels;

export function configuredScenario(config: SimulationConfig): Scenario {
  if (config.manual_state_testing) return "manual";
  if (config.generator_shutdown_seconds != null) return "shutdown";
  return config.fs101_bias ? "bias" : "normal";
}

export interface SimulationSample {
  time_seconds: number;
  actual_frequency_hz: number;
  reported_frequency_hz: number;
  frequency_condition: FrequencyCondition;
  generator_state: GeneratorState;
  breaker_state: BreakerState;
  load_connected: boolean;
  load_powered: boolean;
}

export interface SimulationEvent {
  time_seconds: number | null;
  type:
    | "generator_shutdown"
    | "load_connected_unpowered"
    | "load_connected_unpowered_ended"
    | "fault_activated"
    | "fault_cleared"
    | "breaker_opened"
    | "breaker_closed"
    | "frequency_below_limit"
    | "frequency_above_limit"
    | "under_frequency_exited"
    | "over_frequency_exited"
    | "invalid_state";
  reason: string;
  component_id: string;
  previous_state: GeneratorState | BreakerState | null;
  new_state: GeneratorState | BreakerState | null;
}

const frequencyOverrideFields = [
  "initial_frequency_hz",
  "breaker_open_threshold_hz",
  "breaker_close_threshold_hz",
] as const;

export type SimulationOverrides = Pick<
  SimulationConfig,
  "duration_seconds" | (typeof frequencyOverrideFields)[number]
>;

export interface FaultAnalysis {
  start_seconds: number;
  end_seconds: number;
  duration_seconds: number;
  max_measurement_error_hz: number;
  breaker_operations: number;
  load_disconnected_seconds: number;
  actual_frequency_violation_count: number;
  comparison: {
    normal_breaker_operations: number;
    breaker_operations_delta: number;
    normal_load_connection_availability_pct: number;
    load_connection_availability_delta_pp: number;
  };
}

export interface ControllerDecision {
  time_seconds: number;
  reported_frequency_hz: number;
  generator_state: GeneratorState;
  previous_state: BreakerState;
  new_state: BreakerState;
  reason: string;
}

export interface ProtectionFinding {
  type: "premature_opening" | "missed_protective_opening";
  time_seconds: number;
  actual_frequency_hz: number;
  reported_frequency_hz: number;
  chosen_state: BreakerState;
  reference_state: BreakerState;
  reference_reason: string;
}

export interface SimulationResult {
  config: SimulationConfig;
  readonly samples: readonly Readonly<SimulationSample>[];
  readonly events: readonly Readonly<SimulationEvent>[];
  readonly violations: readonly Readonly<SimulationEvent>[];
  fault_analysis: FaultAnalysis | null;
  protection_diagnostics: {
    premature_opening_count: number;
    missed_protective_opening_count: number;
    findings: readonly Readonly<ProtectionFinding>[];
  };
  controller_trace: readonly Readonly<ControllerDecision>[] | null;
  summary: {
    min_actual_frequency_hz: number;
    max_actual_frequency_hz: number;
    load_powered_seconds: number;
    frequency: {
      min_actual_frequency_hz: number;
      max_actual_frequency_hz: number;
      average_actual_frequency_hz: number;
      within_limits_seconds: number;
      outside_limits_seconds: number;
      closed_below_limit_seconds: number;
      violating_sample_count: number;
      violation_episode_count: number;
      under_frequency_sample_count: number;
      over_frequency_sample_count: number;
      under_frequency_episode_count: number;
      over_frequency_episode_count: number;
      safety_violation_count: number;
      minimum_margin_hz: number;
    };
    load: {
      connected_seconds: number;
      disconnected_seconds: number;
      powered_seconds: number;
      connected_without_generator_power_seconds: number;
      connection_availability_pct: number;
      disconnection_episodes: number;
      longest_disconnection_seconds: number;
      average_disconnection_seconds: number;
    };
    generator: {
      on_seconds: number;
      off_seconds: number;
      on_pct: number;
      state_transitions: number;
      on_while_breaker_open_seconds: number;
    };
    breaker: {
      closed_seconds: number;
      open_seconds: number;
      open_operations: number;
      close_operations: number;
      switching_operations: number;
      open_intervals: number;
      longest_open_interval_seconds: number;
    };
  };
}

interface ValidationIssue {
  msg: string;
  loc?: (string | number)[];
  type?: string;
}

interface ApiError {
  detail?: string | { reason?: string } | ValidationIssue[];
}

const staleBackendMessage = "The running backend is out of date. Restart the backend from this project and run the simulation again.";

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, options);
  if (response.ok) return response.json() as Promise<T>;

  const body: ApiError | null = await response.json().catch(() => null);
  const detail = body?.detail;
  if (Array.isArray(detail)) {
    const rejectsField = (field: string) => detail.some(({ type, loc }) =>
      type === "extra_forbidden" && loc?.length === 2 && loc[0] === "body" && loc[1] === field
    );
    if (response.status === 422 && (
      frequencyOverrideFields.every(rejectsField)
      || ["fs101_bias", "include_controller_trace", "generator_shutdown_seconds", "manual_state_testing"].some(rejectsField)
    )) {
      throw new Error(staleBackendMessage);
    }
    throw new Error(detail.map((error) => error.msg).join(". "));
  }
  if (typeof detail === "string") throw new Error(detail);
  throw new Error(detail?.reason ?? `The backend returned HTTP ${response.status}.`);
}

export function getConfig(signal: AbortSignal): Promise<SimulationConfig> {
  return requestJson("/api/config", { signal });
}

export async function runSimulation(overrides: Partial<SimulationOverrides> & {
  fs101_bias?: SensorBiasConfig | null;
  generator_shutdown_seconds?: number | null;
  manual_state_testing?: boolean;
  initial_generator_state?: GeneratorState;
  initial_breaker_state?: BreakerState;
  include_controller_trace?: boolean;
}, signal?: AbortSignal): Promise<SimulationResult> {
  const result = await requestJson<SimulationResult>("/api/simulations/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(overrides),
    signal,
  });
  if (!result.protection_diagnostics) throw new Error(staleBackendMessage);
  return result;
}

