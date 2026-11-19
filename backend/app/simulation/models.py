from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class GeneratorState(StrEnum):
    ON = "ON"
    OFF = "OFF"


class BreakerState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"


class FrequencyCondition(StrEnum):
    NORMAL = "normal"
    UNDER_FREQUENCY = "under_frequency"
    OVER_FREQUENCY = "over_frequency"


@dataclass(frozen=True, slots=True)
class PhysicalState:
    time_seconds: Decimal
    actual_frequency_hz: Decimal
    generator_state: GeneratorState
    breaker_state: BreakerState

    @property
    def load_connected(self) -> bool:
        return self.breaker_state is BreakerState.CLOSED

    @property
    def load_powered(self) -> bool:
        return self.load_connected and self.generator_state is GeneratorState.ON


@dataclass(frozen=True, slots=True)
class Sample:
    physical: PhysicalState
    reported_frequency_hz: Decimal


FrequencySensor = Callable[[PhysicalState], Decimal]


class EventType(StrEnum):
    GENERATOR_SHUTDOWN = "generator_shutdown"
    LOAD_CONNECTED_UNPOWERED = "load_connected_unpowered"
    LOAD_CONNECTED_UNPOWERED_ENDED = "load_connected_unpowered_ended"
    FAULT_ACTIVATED = "fault_activated"
    FAULT_CLEARED = "fault_cleared"
    BREAKER_OPENED = "breaker_opened"
    BREAKER_CLOSED = "breaker_closed"
    FREQUENCY_BELOW_LIMIT = "frequency_below_limit"
    FREQUENCY_ABOVE_LIMIT = "frequency_above_limit"
    UNDER_FREQUENCY_EXITED = "under_frequency_exited"
    OVER_FREQUENCY_EXITED = "over_frequency_exited"
    INVALID_STATE = "invalid_state"


@dataclass(frozen=True, slots=True)
class SimulationEvent:
    time_seconds: Decimal | None
    type: EventType
    reason: str
    component_id: str = "SIMULATION"
    previous_state: BreakerState | GeneratorState | None = None
    new_state: BreakerState | GeneratorState | None = None

    @property
    def is_frequency_entry(self) -> bool:
        return self.type in (EventType.FREQUENCY_BELOW_LIMIT, EventType.FREQUENCY_ABOVE_LIMIT)


@dataclass(frozen=True, slots=True)
class ControllerDecision:
    time_seconds: Decimal
    reported_frequency_hz: Decimal
    generator_state: GeneratorState
    previous_state: BreakerState
    new_state: BreakerState
    reason: str


@dataclass(frozen=True, slots=True)
class StepResult:
    sample: Sample
    events: tuple[SimulationEvent, ...]
    controller_decision: ControllerDecision | None = None


@dataclass(frozen=True, slots=True)
class FrequencySummary:
    min_actual_frequency_hz: Decimal
    max_actual_frequency_hz: Decimal
    average_actual_frequency_hz: Decimal
    within_limits_seconds: Decimal
    outside_limits_seconds: Decimal
    closed_below_limit_seconds: Decimal
    under_frequency_sample_count: int
    over_frequency_sample_count: int
    under_frequency_episode_count: int
    over_frequency_episode_count: int
    minimum_margin_hz: Decimal

    @property
    def violating_sample_count(self) -> int:
        return self.under_frequency_sample_count + self.over_frequency_sample_count

    @property
    def violation_episode_count(self) -> int:
        return self.under_frequency_episode_count + self.over_frequency_episode_count

    @property
    def safety_violation_count(self) -> int:
        return self.violating_sample_count


@dataclass(frozen=True, slots=True)
class LoadSummary:
    connected_seconds: Decimal
    disconnected_seconds: Decimal
    powered_seconds: Decimal
    connection_availability_pct: Decimal
    disconnection_episodes: int
    longest_disconnection_seconds: Decimal
    average_disconnection_seconds: Decimal

    @property
    def connected_without_generator_power_seconds(self) -> Decimal:
        return self.connected_seconds - self.powered_seconds


@dataclass(frozen=True, slots=True)
class GeneratorSummary:
    on_seconds: Decimal
    off_seconds: Decimal
    on_pct: Decimal
    state_transitions: int
    on_while_breaker_open_seconds: Decimal


@dataclass(frozen=True, slots=True)
class BreakerSummary:
    closed_seconds: Decimal
    open_seconds: Decimal
    open_operations: int
    close_operations: int
    switching_operations: int
    open_intervals: int
    longest_open_interval_seconds: Decimal


@dataclass(frozen=True, slots=True)
class Summary:
    frequency: FrequencySummary
    load: LoadSummary
    generator: GeneratorSummary
    breaker: BreakerSummary

    @property
    def min_actual_frequency_hz(self) -> Decimal:
        return self.frequency.min_actual_frequency_hz

    @property
    def max_actual_frequency_hz(self) -> Decimal:
        return self.frequency.max_actual_frequency_hz

    @property
    def load_powered_seconds(self) -> Decimal:
        return self.load.powered_seconds


@dataclass(frozen=True, slots=True)
class BaselineComparison:
    normal_breaker_operations: int
    breaker_operations_delta: int
    normal_load_connection_availability_pct: Decimal
    load_connection_availability_delta_pp: Decimal


@dataclass(frozen=True, slots=True)
class FaultAnalysis:
    start_seconds: Decimal
    end_seconds: Decimal
    duration_seconds: Decimal
    max_measurement_error_hz: Decimal
    breaker_operations: int
    load_disconnected_seconds: Decimal
    actual_frequency_violation_count: int
    comparison: BaselineComparison


class ProtectionFindingType(StrEnum):
    PREMATURE_OPENING = "premature_opening"
    MISSED_PROTECTIVE_OPENING = "missed_protective_opening"


@dataclass(frozen=True, slots=True)
class ProtectionFinding:
    type: ProtectionFindingType
    time_seconds: Decimal
    actual_frequency_hz: Decimal
    reported_frequency_hz: Decimal
    chosen_state: BreakerState
    reference_state: BreakerState
    reference_reason: str


@dataclass(frozen=True, slots=True)
class ProtectionDiagnostics:
    findings: tuple[ProtectionFinding, ...]

    @property
    def premature_opening_count(self) -> int:
        return sum(finding.type is ProtectionFindingType.PREMATURE_OPENING for finding in self.findings)

    @property
    def missed_protective_opening_count(self) -> int:
        return sum(finding.type is ProtectionFindingType.MISSED_PROTECTIVE_OPENING for finding in self.findings)


@dataclass(frozen=True, slots=True)
class SimulationResult:
    samples: tuple[Sample, ...]
    events: tuple[SimulationEvent, ...]
    summary: Summary
    protection_diagnostics: ProtectionDiagnostics
    controller_trace: tuple[ControllerDecision, ...] | None = None

    @property
    def violations(self) -> tuple[SimulationEvent, ...]:
        return tuple(event for event in self.events if event.is_frequency_entry)

