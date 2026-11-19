import logging
from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal

from ..config import SimulationConfig
from .controller import decide_breaker
from .diagnostics import assess_breaker_protection, check_invariants, frequency_transition_events
from .faults import apply_sensor_bias, bias_transition_at
from .metrics import summarize_fault, summarize_run
from .models import (
    BreakerState,
    ControllerDecision,
    EventType,
    FaultAnalysis,
    FrequencySensor,
    PhysicalState,
    Sample,
    SimulationEvent,
    SimulationResult,
    StepResult,
)
from .physics import advance_physics
from .scenarios import apply_scheduled_shutdown, unpowered_connection_event
from .sensors import read_frequency

logger = logging.getLogger(__name__)
controller_logger = logging.getLogger(f"{__name__}.controller")


def _observe(state: PhysicalState, config: SimulationConfig, sensor: FrequencySensor) -> Sample:
    measurement = sensor(state)
    return Sample(state, apply_sensor_bias(measurement, state.time_seconds, config.fs101_bias))


def _sample_events(
    sample: Sample, config: SimulationConfig, *, previous: Sample | None = None
) -> tuple[SimulationEvent, ...]:
    transition = bias_transition_at(sample.physical.time_seconds, config.fs101_bias)
    conditions = frequency_transition_events(sample, config, previous=previous)
    return (transition, *conditions) if transition is not None else conditions


def _log_events(events: Sequence[SimulationEvent]) -> None:
    for event in events:
        logger.debug("At %s s [%s] %s", event.time_seconds, event.type, event.reason)


def initialize(config: SimulationConfig, *, sensor: FrequencySensor = read_frequency) -> Sample:
    state = PhysicalState(
        time_seconds=Decimal(0),
        actual_frequency_hz=config.initial_frequency_hz,
        generator_state=config.initial_generator_state,
        breaker_state=config.initial_breaker_state,
    )
    sample = _observe(state, config, sensor)
    check_invariants(sample, config, expected_time=Decimal(0))
    return sample


def step(
    current: Sample,
    config: SimulationConfig,
    *,
    sensor: FrequencySensor = read_frequency,
    include_controller_trace: bool = False,
) -> StepResult:
    """Use the current FS101 reading, switch at the interval start, then advance and sample."""
    check_invariants(current, config)
    state, shutdown = apply_scheduled_shutdown(current.physical, config)
    events = [shutdown] if shutdown is not None else []
    decision = None
    # A closed breaker at shutdown is held for that interval before the interlock can open it.
    if not config.manual_state_testing and not (shutdown is not None and state.load_connected):
        state, breaker_event, decision = _apply_breaker_control(
            state, current.reported_frequency_hz, config, include_controller_trace=include_controller_trace,
        )
        if breaker_event is not None:
            events.append(breaker_event)
    if config.manual_state_testing or config.generator_shutdown_seconds is not None:
        connection_event = unpowered_connection_event(current.physical, state)
        if connection_event is not None:
            events.append(connection_event)

    updated = advance_physics(state, config)
    sample = _observe(updated, config, sensor)
    check_invariants(sample, config, expected_time=state.time_seconds + config.time_step_seconds)
    events.extend(_sample_events(sample, config, previous=current))
    _log_events(events)
    return StepResult(sample, tuple(events), decision)


def _apply_breaker_control(
    state: PhysicalState, reading: Decimal, config: SimulationConfig, *, include_controller_trace: bool,
) -> tuple[PhysicalState, SimulationEvent | None, ControllerDecision | None]:
    breaker_state, rationale = decide_breaker(reading, state.generator_state, state.breaker_state, config)
    reason = f"FS101 reported {reading} Hz. {rationale}"
    decision = (
        ControllerDecision(state.time_seconds, reading, state.generator_state, state.breaker_state, breaker_state, rationale)
        if include_controller_trace else None
    )
    controller_logger.debug("At %s s CB101 chose %s. %s", state.time_seconds, breaker_state, reason)
    if breaker_state is state.breaker_state:
        return state, None, decision
    event_type = EventType.BREAKER_OPENED if breaker_state is BreakerState.OPEN else EventType.BREAKER_CLOSED
    event = SimulationEvent(
        state.time_seconds, event_type, reason, component_id="CB101",
        previous_state=state.breaker_state, new_state=breaker_state,
    )
    return replace(state, breaker_state=breaker_state), event, decision


def run_simulation(
    config: SimulationConfig, *, sensor: FrequencySensor = read_frequency, include_controller_trace: bool = False
) -> SimulationResult:
    """Run an entire simulation in discrete time, including the initial sample."""
    current = initialize(config, sensor=sensor)
    samples = [current]
    events = list(_sample_events(current, config))
    _log_events(events)
    trace: list[ControllerDecision] | None = [] if include_controller_trace else None

    for _ in range(int(config.duration_seconds / config.time_step_seconds)):
        outcome = step(current, config, sensor=sensor, include_controller_trace=include_controller_trace)
        current = outcome.sample
        samples.append(current)
        events.extend(outcome.events)
        if trace is not None and outcome.controller_decision is not None:
            trace.append(outcome.controller_decision)

    summary = summarize_run(samples, events, config)
    if summary.frequency.violating_sample_count:
        logger.warning(
            "Simulation recorded %d out-of-range samples across %d episodes",
            summary.frequency.violating_sample_count,
            summary.frequency.violation_episode_count,
        )
    return SimulationResult(
        tuple(samples), tuple(events), summary, assess_breaker_protection(samples, config),
        tuple(trace) if trace is not None else None,
    )


def run_scenario(
    config: SimulationConfig, *, include_controller_trace: bool = False
) -> tuple[SimulationResult, FaultAnalysis | None]:
    """Run the configured scenario and compare an injected bias with an ideal FS101 run."""
    result = run_simulation(config, include_controller_trace=include_controller_trace)
    bias = config.fs101_bias
    if bias is None:
        return result, None

    baseline = run_simulation(config.model_copy(update={"fs101_bias": None}))
    return result, summarize_fault(result, baseline.summary, bias)

