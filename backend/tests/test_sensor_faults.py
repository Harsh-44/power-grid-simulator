from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.config import SimulationConfig
from app.simulation.diagnostics import SimulationInvariantError
from app.simulation.engine import initialize, run_scenario, run_simulation
from app.simulation.models import BreakerState, EventType


def with_bias(config: SimulationConfig, **fault: str | int) -> SimulationConfig:
    return SimulationConfig.model_validate(config.model_dump() | {"fs101_bias": fault})


def test_bias_changes_only_sensor_at_inclusive_start_and_exclusive_end(config):
    config = with_bias(config, start_seconds=2, duration_seconds=3, offset_hz="-0.5")
    result = run_simulation(config, include_controller_trace=True)
    errors = [sample.reported_frequency_hz - sample.physical.actual_frequency_hz for sample in result.samples]
    assert errors[:7] == [0, 0, Decimal("-0.5"), Decimal("-0.5"), Decimal("-0.5"), 0, 0]
    start = result.samples[2]
    assert start.physical.actual_frequency_hz == Decimal("49.90")
    assert start.physical.breaker_state is BreakerState.CLOSED
    assert start.reported_frequency_hz == Decimal("49.40")
    assert result.samples[3].physical.actual_frequency_hz == Decimal("50.02")
    assert result.samples[3].physical.breaker_state is BreakerState.OPEN

    assert [event.type for event in result.events if event.time_seconds == 2] == [
        EventType.FAULT_ACTIVATED, EventType.BREAKER_OPENED,
    ]
    assert [event.type for event in result.events if event.time_seconds == 5] == [
        EventType.FAULT_CLEARED, EventType.BREAKER_CLOSED,
    ]
    assert result.controller_trace is not None
    decision = result.controller_trace[2]
    assert decision.time_seconds == 2
    assert decision.new_state is BreakerState.OPEN
    assert decision.reported_frequency_hz == Decimal("49.40")


def test_positive_bias_can_mask_real_underfrequency(config):
    biased = with_bias(config, start_seconds=5, duration_seconds=20, offset_hz="0.5")
    result, analysis = run_scenario(biased)
    normal = run_simulation(config)
    low = result.samples[11]
    assert low.physical.actual_frequency_hz == Decimal("49.45")
    assert low.reported_frequency_hz == Decimal("49.95")
    assert low.physical.breaker_state is BreakerState.CLOSED
    assert normal.samples[11].physical.breaker_state is BreakerState.OPEN
    assert [event.type for event in result.violations if event.time_seconds == 11] == [
        EventType.FREQUENCY_BELOW_LIMIT,
    ]
    assert [event.time_seconds for event in result.events] == sorted(event.time_seconds for event in result.events)
    assert analysis is not None
    assert (analysis.start_seconds, analysis.end_seconds, analysis.duration_seconds) == (5, 25, 20)
    assert analysis.max_measurement_error_hz == Decimal("0.5")
    assert analysis.actual_frequency_violation_count == sum(
        not config.lower_limit_hz <= sample.physical.actual_frequency_hz <= config.upper_limit_hz
        for sample in result.samples
    )
    assert analysis.load_disconnected_seconds == result.summary.load.disconnected_seconds
    assert analysis.breaker_operations == result.summary.breaker.switching_operations
    comparison = analysis.comparison
    assert comparison.normal_breaker_operations == normal.summary.breaker.switching_operations
    assert comparison.breaker_operations_delta == analysis.breaker_operations - comparison.normal_breaker_operations
    assert comparison.normal_load_connection_availability_pct == normal.summary.load.connection_availability_pct
    assert comparison.load_connection_availability_delta_pp == (
        result.summary.load.connection_availability_pct - normal.summary.load.connection_availability_pct
    )
    assert (result, analysis) == run_scenario(biased)


def test_fault_at_fractional_time_grid_boundaries(config):
    config = SimulationConfig.model_validate(config.model_dump() | {"duration_seconds": "1.5", "time_step_seconds": "0.5"})
    config = with_bias(config, start_seconds=0, duration_seconds="1.5", offset_hz="0.25")
    result = run_simulation(config)
    initial = result.samples[0]
    assert initial.physical.actual_frequency_hz == Decimal("50")
    assert initial.reported_frequency_hz == Decimal("50.25")
    assert result.events[0].type is EventType.FAULT_ACTIVATED
    assert result.events[0].time_seconds == 0
    assert result.samples[-2].reported_frequency_hz - result.samples[-2].physical.actual_frequency_hz == Decimal("0.25")
    final = result.samples[-1]
    assert final.physical.time_seconds == Decimal("1.5")
    assert final.reported_frequency_hz == final.physical.actual_frequency_hz
    assert result.events[-1].type is EventType.FAULT_CLEARED
    assert result.events[-1].time_seconds == final.physical.time_seconds


def test_zero_bias_preserves_normal_samples_and_metrics(config):
    normal, normal_analysis = run_scenario(config)
    assert normal_analysis is None
    biased = with_bias(config, start_seconds=0, duration_seconds=12, offset_hz=0)
    result, analysis = run_scenario(biased)
    assert result.samples == normal.samples
    assert result.summary == normal.summary
    assert analysis is not None
    assert analysis.max_measurement_error_hz == 0
    assert analysis.comparison.breaker_operations_delta == 0
    assert analysis.comparison.load_connection_availability_delta_pp == 0


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"start_seconds": -1}, "greater than or equal to 0"),
        ({"duration_seconds": 0}, "greater than 0"),
        ({"start_seconds": "0.25"}, "on the simulation time grid"),
        ({"duration_seconds": "2.25"}, "on the simulation time grid"),
        ({"start_seconds": 120}, "must end by the last sample"),
        ({"offset_hz": "NaN"}, "finite number"),
    ],
)
def test_invalid_bias_schedule(config, override, message):
    fault = {"start_seconds": 2, "duration_seconds": 2, "offset_hz": "0.3"} | override
    with pytest.raises(ValidationError, match=message):
        with_bias(config, **fault)


def test_bias_preserves_sensor_invariant_checks(config):
    biased = with_bias(config, start_seconds=0, duration_seconds=1, offset_hz="0.5")
    with pytest.raises(SimulationInvariantError, match="FS101 reported frequency"):
        initialize(biased, sensor=lambda _: Decimal("sNaN"))
