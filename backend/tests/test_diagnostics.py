from decimal import Decimal

from app.config import SimulationConfig
from app.simulation.engine import run_simulation
from app.simulation.models import BreakerState, EventType, ProtectionFindingType


def configured(config: SimulationConfig, **overrides: object) -> SimulationConfig:
    return SimulationConfig.model_validate(config.model_dump() | overrides)


def test_negative_bias_reference_events_and_safety_metrics(config):
    config = configured(config, fs101_bias={"start_seconds": 5, "duration_seconds": 90, "offset_hz": "-0.50"})
    result = run_simulation(config)
    switches = [event for event in result.events if event.type in (EventType.BREAKER_OPENED, EventType.BREAKER_CLOSED)]
    assert len(switches) == len({event.time_seconds for event in switches}) == 14
    assert result.summary.breaker.switching_operations == 14
    assert len(result.events) == 26  # 14 changes, 10 frequency transitions, and two fault events.
    assert [event.time_seconds for event in result.events] == sorted(event.time_seconds for event in result.events)
    assert [event.time_seconds for event in result.events if event.type is EventType.FAULT_ACTIVATED] == [5]
    assert [event.time_seconds for event in result.events if event.type is EventType.FAULT_CLEARED] == [95]
    assert [event.time_seconds for event in result.violations] == [12, 27, 54, 68, 83]
    assert [event.time_seconds for event in result.events if event.type is EventType.OVER_FREQUENCY_EXITED] == [
        14, 28, 55, 69, 86,
    ]
    frequency = result.summary.frequency
    assert frequency.over_frequency_sample_count == frequency.violating_sample_count == 8
    assert frequency.over_frequency_episode_count == frequency.violation_episode_count == 5
    assert frequency.under_frequency_sample_count == frequency.under_frequency_episode_count == 0
    assert frequency.outside_limits_seconds == Decimal(221) / 30
    assert frequency.closed_below_limit_seconds == 0
    assert result.protection_diagnostics.premature_opening_count == 6
    assert result.protection_diagnostics.missed_protective_opening_count == 0


def test_trace_captures_each_step_before_during_and_after_the_bias(config):
    config = configured(config, fs101_bias={"start_seconds": 5, "duration_seconds": 90, "offset_hz": "-0.50"})
    untraced = run_simulation(config)
    traced = run_simulation(config, include_controller_trace=True)
    assert untraced.controller_trace is None
    assert traced.samples == untraced.samples
    assert traced.events == untraced.events
    assert traced.summary == untraced.summary
    assert traced.protection_diagnostics == untraced.protection_diagnostics
    trace = traced.controller_trace
    assert trace is not None
    assert [decision.time_seconds for decision in trace] == list(range(120))
    assert any(decision.previous_state is decision.new_state for decision in trace)
    for before, decision, after in zip(traced.samples[:-1], trace, traced.samples[1:], strict=True):
        assert decision.time_seconds == before.physical.time_seconds
        assert decision.reported_frequency_hz == before.reported_frequency_hz
        assert decision.previous_state is before.physical.breaker_state
        assert decision.new_state is after.physical.breaker_state
        assert decision.reason


def test_premature_opening_uses_same_predecision_state(config):
    config = configured(config, fs101_bias={"start_seconds": 2, "duration_seconds": 3, "offset_hz": "-0.50"})
    result = run_simulation(config)
    diagnostic, = result.protection_diagnostics.findings
    assert diagnostic.type is ProtectionFindingType.PREMATURE_OPENING
    assert diagnostic.time_seconds == 2
    assert diagnostic.actual_frequency_hz == Decimal("49.90")
    assert diagnostic.reported_frequency_hz == Decimal("49.40")
    assert diagnostic.chosen_state is BreakerState.OPEN
    assert diagnostic.reference_state is BreakerState.CLOSED


def test_missed_openings_are_per_decision_and_exposure_is_elapsed_time(config):
    config = configured(
        config, duration_seconds=2, initial_frequency_hz="49.55",
        fs101_bias={"start_seconds": 0, "duration_seconds": 2, "offset_hz": "0.50"},
    )
    result = run_simulation(config)
    frequency = result.summary.frequency
    assert frequency.violating_sample_count == frequency.under_frequency_episode_count == 1
    assert frequency.outside_limits_seconds == frequency.closed_below_limit_seconds == 1
    assert result.summary.breaker.switching_operations == 0
    assert [(finding.type, finding.time_seconds) for finding in result.protection_diagnostics.findings] == [
        (ProtectionFindingType.MISSED_PROTECTIVE_OPENING, 0),
        (ProtectionFindingType.MISSED_PROTECTIVE_OPENING, 1),
    ]
    assert [(event.type, event.time_seconds) for event in result.events] == [
        (EventType.FAULT_ACTIVATED, 0), (EventType.FAULT_CLEARED, 2), (EventType.FREQUENCY_BELOW_LIMIT, 2),
    ]


def test_closed_exposure_counts_partial_intervals_and_protection_uses_projection(config):
    rates = config.frequency_rates_hz_per_second.model_dump() | {"on_closed": "-0.75"}
    config = configured(
        config, duration_seconds=1, frequency_rates_hz_per_second=rates,
        fs101_bias={"start_seconds": 0, "duration_seconds": 1, "offset_hz": "1"},
    )
    result = run_simulation(config)
    frequency = result.summary.frequency
    assert frequency.outside_limits_seconds == frequency.closed_below_limit_seconds == Decimal(1) / 3
    diagnostic, = result.protection_diagnostics.findings
    assert diagnostic.type is ProtectionFindingType.MISSED_PROTECTIVE_OPENING
    assert diagnostic.time_seconds == 0
    assert "project" in diagnostic.reference_reason
