from pydantic import BaseModel, ConfigDict, StrictBool

from ..config import ConfigNumber, NonnegativeSeconds, PositiveSeconds, SensorBiasConfig, SimulationConfig
from ..simulation.diagnostics import classify_frequency
from ..simulation.models import BreakerState, EventType, FrequencyCondition, GeneratorState, ProtectionFindingType, Sample


class RunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    duration_seconds: PositiveSeconds | None = None
    initial_frequency_hz: ConfigNumber | None = None
    breaker_open_threshold_hz: ConfigNumber | None = None
    breaker_close_threshold_hz: ConfigNumber | None = None
    fs101_bias: SensorBiasConfig | None = None
    generator_shutdown_seconds: NonnegativeSeconds | None = None
    manual_state_testing: StrictBool | None = None
    initial_generator_state: GeneratorState | None = None
    initial_breaker_state: BreakerState | None = None
    include_controller_trace: StrictBool = False


class SampleResponse(BaseModel):
    time_seconds: float
    actual_frequency_hz: float
    reported_frequency_hz: float
    frequency_condition: FrequencyCondition
    generator_state: GeneratorState
    breaker_state: BreakerState
    load_connected: bool
    load_powered: bool

    @classmethod
    def from_sample(cls, sample: Sample, config: SimulationConfig) -> "SampleResponse":
        state = sample.physical
        return cls(
            time_seconds=float(state.time_seconds),
            actual_frequency_hz=float(state.actual_frequency_hz),
            reported_frequency_hz=float(sample.reported_frequency_hz),
            frequency_condition=classify_frequency(state.actual_frequency_hz, config),
            generator_state=state.generator_state,
            breaker_state=state.breaker_state,
            load_connected=state.load_connected,
            load_powered=state.load_powered,
        )


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time_seconds: float | None
    type: EventType
    reason: str
    component_id: str
    previous_state: BreakerState | GeneratorState | None
    new_state: BreakerState | GeneratorState | None


class FrequencySummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    min_actual_frequency_hz: float
    max_actual_frequency_hz: float
    average_actual_frequency_hz: float
    within_limits_seconds: float
    outside_limits_seconds: float
    closed_below_limit_seconds: float
    violating_sample_count: int
    violation_episode_count: int
    under_frequency_sample_count: int
    over_frequency_sample_count: int
    under_frequency_episode_count: int
    over_frequency_episode_count: int
    safety_violation_count: int
    minimum_margin_hz: float


class LoadSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    connected_seconds: float
    disconnected_seconds: float
    powered_seconds: float
    connected_without_generator_power_seconds: float
    connection_availability_pct: float
    disconnection_episodes: int
    longest_disconnection_seconds: float
    average_disconnection_seconds: float


class GeneratorSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    on_seconds: float
    off_seconds: float
    on_pct: float
    state_transitions: int
    on_while_breaker_open_seconds: float


class BreakerSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    closed_seconds: float
    open_seconds: float
    open_operations: int
    close_operations: int
    switching_operations: int
    open_intervals: int
    longest_open_interval_seconds: float


class SummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    min_actual_frequency_hz: float
    max_actual_frequency_hz: float
    load_powered_seconds: float
    frequency: FrequencySummaryResponse
    load: LoadSummaryResponse
    generator: GeneratorSummaryResponse
    breaker: BreakerSummaryResponse


class BaselineComparisonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    normal_breaker_operations: int
    breaker_operations_delta: int
    normal_load_connection_availability_pct: float
    load_connection_availability_delta_pp: float


class FaultAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start_seconds: float
    end_seconds: float
    duration_seconds: float
    max_measurement_error_hz: float
    breaker_operations: int
    load_disconnected_seconds: float
    actual_frequency_violation_count: int
    comparison: BaselineComparisonResponse


class ControllerDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    time_seconds: float
    reported_frequency_hz: float
    generator_state: GeneratorState
    previous_state: BreakerState
    new_state: BreakerState
    reason: str


class ProtectionFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: ProtectionFindingType
    time_seconds: float
    actual_frequency_hz: float
    reported_frequency_hz: float
    chosen_state: BreakerState
    reference_state: BreakerState
    reference_reason: str


class ProtectionDiagnosticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    premature_opening_count: int
    missed_protective_opening_count: int
    findings: list[ProtectionFindingResponse]


class RunResponse(BaseModel):
    config: SimulationConfig
    samples: list[SampleResponse]
    events: list[EventResponse]
    violations: list[EventResponse]
    summary: SummaryResponse
    fault_analysis: FaultAnalysisResponse | None = None
    protection_diagnostics: ProtectionDiagnosticsResponse
    controller_trace: list[ControllerDecisionResponse] | None = None

