from collections import Counter
from collections.abc import Sequence
from decimal import Decimal
from itertools import pairwise

from ..config import SensorBiasConfig, SimulationConfig
from .diagnostics import classify_frequency
from .models import (
    BaselineComparison,
    BreakerSummary,
    EventType,
    FaultAnalysis,
    FrequencyCondition,
    FrequencySummary,
    GeneratorState,
    GeneratorSummary,
    LoadSummary,
    Sample,
    SimulationEvent,
    SimulationResult,
    Summary,
)


def summarize_run(
    samples: Sequence[Sample], events: Sequence[SimulationEvent], config: SimulationConfig
) -> Summary:
    """Summarize a complete, validated simulation history."""
    zero = Decimal(0)
    duration = samples[-1].physical.time_seconds - samples[0].physical.time_seconds
    generator_on = powered = disconnected = current_open = longest_open = zero
    generator_transitions = open_intervals = 0

    # Each end sample carries the component states that applied during the interval.
    for previous, current in pairwise(samples):
        state = current.physical
        elapsed = state.time_seconds - previous.physical.time_seconds
        if state.load_connected:
            current_open = zero
        else:
            open_intervals += current_open == 0
            current_open += elapsed
            disconnected += elapsed
            longest_open = max(longest_open, current_open)

        if state.generator_state is GeneratorState.ON:
            generator_on += elapsed
        if state.load_powered:
            powered += elapsed
        generator_transitions += state.generator_state is not previous.physical.generator_state

    connected = duration - disconnected
    event_counts = Counter(event.type for event in events)
    opens = event_counts[EventType.BREAKER_OPENED]
    closes = event_counts[EventType.BREAKER_CLOSED]
    return Summary(
        frequency=_frequency_summary(samples, event_counts, config, duration),
        load=LoadSummary(
            connected_seconds=connected,
            disconnected_seconds=disconnected,
            powered_seconds=powered,
            connection_availability_pct=connected * 100 / duration,
            disconnection_episodes=open_intervals,
            longest_disconnection_seconds=longest_open,
            average_disconnection_seconds=disconnected / open_intervals if open_intervals else zero,
        ),
        generator=GeneratorSummary(
            on_seconds=generator_on,
            off_seconds=duration - generator_on,
            on_pct=generator_on * 100 / duration,
            state_transitions=generator_transitions,
            on_while_breaker_open_seconds=generator_on - powered,
        ),
        breaker=BreakerSummary(
            closed_seconds=connected,
            open_seconds=disconnected,
            open_operations=opens,
            close_operations=closes,
            switching_operations=opens + closes,
            open_intervals=open_intervals,
            longest_open_interval_seconds=longest_open,
        ),
    )


def _frequency_summary(
    samples: Sequence[Sample], event_counts: Counter[EventType], config: SimulationConfig, duration: Decimal
) -> FrequencySummary:
    lower, upper = config.lower_limit_hz, config.upper_limit_hz
    minimum = maximum = samples[0].physical.actual_frequency_hz
    area = outside_limits = closed_below_limit = Decimal(0)
    sample_counts = Counter(classify_frequency(sample.physical.actual_frequency_hz, config) for sample in samples)

    for previous, current in pairwise(samples):
        start, end = previous.physical, current.physical
        elapsed = end.time_seconds - start.time_seconds
        low, high = sorted((start.actual_frequency_hz, end.actual_frequency_hz))
        minimum, maximum = min(minimum, low), max(maximum, high)
        area += elapsed * (low + high) / 2
        below = _seconds_below(low, high, lower, elapsed)
        above = _seconds_below(-high, -low, -upper, elapsed)
        outside_limits += below + above
        if end.load_connected:
            closed_below_limit += below

    return FrequencySummary(
        min_actual_frequency_hz=minimum,
        max_actual_frequency_hz=maximum,
        average_actual_frequency_hz=area / duration,
        within_limits_seconds=duration - outside_limits,
        outside_limits_seconds=outside_limits,
        closed_below_limit_seconds=closed_below_limit,
        under_frequency_sample_count=sample_counts[FrequencyCondition.UNDER_FREQUENCY],
        over_frequency_sample_count=sample_counts[FrequencyCondition.OVER_FREQUENCY],
        under_frequency_episode_count=event_counts[EventType.FREQUENCY_BELOW_LIMIT],
        over_frequency_episode_count=event_counts[EventType.FREQUENCY_ABOVE_LIMIT],
        minimum_margin_hz=min(minimum - lower, upper - maximum),
    )


def _seconds_below(low: Decimal, high: Decimal, limit: Decimal, elapsed: Decimal) -> Decimal:
    if low >= limit:
        return Decimal(0)
    if high <= limit:
        return elapsed
    return elapsed * (limit - low) / (high - low)


def summarize_fault(result: SimulationResult, baseline: Summary, bias: SensorBiasConfig) -> FaultAnalysis:
    summary = result.summary
    operations = summary.breaker.switching_operations
    availability = summary.load.connection_availability_pct
    baseline_operations = baseline.breaker.switching_operations
    baseline_availability = baseline.load.connection_availability_pct

    return FaultAnalysis(
        start_seconds=bias.start_seconds,
        end_seconds=bias.end_seconds,
        duration_seconds=bias.duration_seconds,
        max_measurement_error_hz=max(
            abs(sample.reported_frequency_hz - sample.physical.actual_frequency_hz) for sample in result.samples
        ),
        breaker_operations=operations,
        load_disconnected_seconds=summary.load.disconnected_seconds,
        actual_frequency_violation_count=summary.frequency.violating_sample_count,
        comparison=BaselineComparison(
            normal_breaker_operations=baseline_operations,
            breaker_operations_delta=operations - baseline_operations,
            normal_load_connection_availability_pct=baseline_availability,
            load_connection_availability_delta_pp=availability - baseline_availability,
        ),
    )
