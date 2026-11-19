import logging
from collections.abc import Sequence
from decimal import Decimal
from itertools import pairwise

from ..config import SimulationConfig
from .controller import decide_breaker
from .models import (
    BreakerState,
    EventType,
    FrequencyCondition,
    GeneratorState,
    ProtectionDiagnostics,
    ProtectionFinding,
    ProtectionFindingType,
    Sample,
    SimulationEvent,
)

logger = logging.getLogger(__name__)


class SimulationInvariantError(RuntimeError):
    def __init__(self, event: SimulationEvent) -> None:
        super().__init__(event.reason)
        self.event = event


def check_invariants(
    sample: Sample,
    config: SimulationConfig,
    *,
    expected_time: Decimal | None = None,
) -> None:
    state = sample.physical
    time = state.time_seconds
    valid_time = isinstance(time, Decimal) and time.is_finite() and time >= 0
    if not valid_time:
        reason = "Simulation time must be a finite, nonnegative number."
    elif expected_time is not None and time != expected_time:
        reason = f"Expected a sample at {expected_time} s, received {time} s."
    elif time % config.time_step_seconds:
        reason = f"Sample at {time} s is off the {config.time_step_seconds} s time grid."
    elif not isinstance(state.generator_state, GeneratorState):
        reason = "G101 has an invalid generator state."
    elif not isinstance(state.breaker_state, BreakerState):
        reason = "CB101 has an invalid breaker state."
    elif not _finite_frequency(state.actual_frequency_hz):
        reason = "Actual bus frequency must be a finite number."
    elif not _finite_frequency(sample.reported_frequency_hz):
        reason = "FS101 reported frequency must be a finite number."
    else:
        return

    logger.error("Simulation invariant violated at %s s: %s", time if valid_time else "unknown", reason)
    raise SimulationInvariantError(SimulationEvent(time if valid_time else None, EventType.INVALID_STATE, reason))


def _finite_frequency(value: Decimal) -> bool:
    return isinstance(value, Decimal) and value.is_finite()


def classify_frequency(actual_frequency_hz: Decimal, config: SimulationConfig) -> FrequencyCondition:
    if actual_frequency_hz < config.lower_limit_hz:
        return FrequencyCondition.UNDER_FREQUENCY
    if actual_frequency_hz > config.upper_limit_hz:
        return FrequencyCondition.OVER_FREQUENCY
    return FrequencyCondition.NORMAL


def frequency_transition_events(
    sample: Sample, config: SimulationConfig, *, previous: Sample | None = None
) -> tuple[SimulationEvent, ...]:
    state = sample.physical
    time = state.time_seconds
    frequency = state.actual_frequency_hz
    condition = classify_frequency(frequency, config)
    before = (
        classify_frequency(previous.physical.actual_frequency_hz, config)
        if previous is not None else FrequencyCondition.NORMAL
    )
    if before is condition:
        return ()

    events = []
    if before is not FrequencyCondition.NORMAL:
        event_type = (
            EventType.UNDER_FREQUENCY_EXITED if before is FrequencyCondition.UNDER_FREQUENCY
            else EventType.OVER_FREQUENCY_EXITED
        )
        events.append(
            SimulationEvent(
                time,
                event_type,
                f"Actual bus frequency {frequency} Hz exited {before.value.replace('_', '-')}.",
                component_id="BUS",
            )
        )
    if condition is FrequencyCondition.UNDER_FREQUENCY:
        events.append(SimulationEvent(
            time, EventType.FREQUENCY_BELOW_LIMIT,
            f"Actual bus frequency {frequency} Hz is below {config.lower_limit_hz} Hz.", component_id="BUS",
        ))
    elif condition is FrequencyCondition.OVER_FREQUENCY:
        events.append(SimulationEvent(
            time, EventType.FREQUENCY_ABOVE_LIMIT,
            f"Actual bus frequency {frequency} Hz is above {config.upper_limit_hz} Hz.", component_id="BUS",
        ))
    return tuple(events)


def assess_breaker_protection(samples: Sequence[Sample], config: SimulationConfig) -> ProtectionDiagnostics:
    """Compare closed-breaker decisions with the ideal-reading policy after the run."""
    if config.manual_state_testing:
        return ProtectionDiagnostics(())
    findings = []
    for before, after in pairwise(samples):
        state = before.physical
        actual = state.actual_frequency_hz
        reported = before.reported_frequency_hz
        if state.breaker_state is not BreakerState.CLOSED or actual == reported or state.generator_state is not after.physical.generator_state:
            continue
        reference, reason = decide_breaker(actual, state.generator_state, state.breaker_state, config)
        chosen = after.physical.breaker_state
        if chosen is reference:
            continue
        finding_type = (
            ProtectionFindingType.PREMATURE_OPENING if chosen is BreakerState.OPEN
            else ProtectionFindingType.MISSED_PROTECTIVE_OPENING
        )
        findings.append(ProtectionFinding(
            type=finding_type,
            time_seconds=state.time_seconds,
            actual_frequency_hz=actual,
            reported_frequency_hz=reported,
            chosen_state=chosen,
            reference_state=reference,
            reference_reason=reason,
        ))
    return ProtectionDiagnostics(tuple(findings))

