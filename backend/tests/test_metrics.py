from dataclasses import replace
from decimal import Decimal

import pytest

from app.config import SimulationConfig
from app.simulation.engine import initialize, run_simulation
from app.simulation.metrics import summarize_run
from app.simulation.models import EventType, GeneratorState


def test_default_operational_metrics(config: SimulationConfig) -> None:
    result = run_simulation(config)
    summary = result.summary
    assert result == run_simulation(config)
    assert len(result.samples) == 121
    assert summary.frequency.min_actual_frequency_hz == Decimal("49.51")
    assert summary.frequency.max_actual_frequency_hz == Decimal("50.11")
    assert summary.frequency.within_limits_seconds == 120
    assert summary.frequency.safety_violation_count == len(result.violations) == 0
    assert summary.frequency.violating_sample_count == summary.frequency.violation_episode_count == 0
    assert summary.frequency.outside_limits_seconds == summary.frequency.closed_below_limit_seconds == 0
    assert result.protection_diagnostics.findings == ()
    assert summary.frequency.minimum_margin_hz == Decimal("0.01")

    assert summary.load.connected_seconds == summary.load.powered_seconds == 87
    assert summary.load.disconnected_seconds == 33
    assert summary.load.connection_availability_pct == Decimal("72.5")
    assert summary.load.disconnection_episodes == 7
    assert summary.load.longest_disconnection_seconds == 5
    assert summary.load.average_disconnection_seconds == Decimal(33) / 7

    assert summary.generator.on_seconds == 120
    assert summary.generator.off_seconds == 0
    assert summary.generator.on_pct == 100
    assert summary.generator.state_transitions == 0
    assert summary.generator.on_while_breaker_open_seconds == 33

    assert summary.breaker.closed_seconds == 87
    assert summary.breaker.open_seconds == 33
    assert summary.breaker.open_operations == 7
    assert summary.breaker.close_operations == 7
    assert summary.breaker.switching_operations == 14
    assert summary.breaker.open_intervals == 7
    assert summary.breaker.longest_open_interval_seconds == 5


@pytest.mark.parametrize(
    ("initial_breaker", "initial_hz", "duration", "open_time", "opens", "closes"),
    [
        ("CLOSED", "50.00", 9, 0, 0, 0),   # The final sample reaches the opening threshold.
        ("CLOSED", "50.00", 10, 1, 1, 0),  # The open interval extends through the end.
        ("OPEN", "50.00", 1, 0, 0, 1),     # Closure at t = 0 leaves no elapsed open interval.
        ("OPEN", "49.76", 2, 2, 0, 0),     # An initial open interval ends at the run boundary.
        ("OPEN", "49.76", 3, 2, 0, 1),     # Starting open supplies an interval but no open event.
    ],
)
def test_breaker_operations_and_elapsed_intervals(
    config: SimulationConfig, initial_breaker: str, initial_hz: str, duration: int,
    open_time: int, opens: int, closes: int,
) -> None:
    config = SimulationConfig.model_validate(
        config.model_dump()
        | {
            "initial_breaker_state": initial_breaker,
            "initial_frequency_hz": initial_hz,
            "duration_seconds": duration,
        }
    )
    result = run_simulation(config)
    summary = result.summary
    assert summary.load.connected_seconds + summary.load.disconnected_seconds == duration
    assert summary.load.disconnection_episodes == summary.breaker.open_intervals == int(open_time > 0)
    assert summary.load.longest_disconnection_seconds == open_time
    assert summary.load.average_disconnection_seconds == summary.breaker.open_seconds == open_time
    assert summary.breaker.open_operations == opens
    assert summary.breaker.close_operations == closes
    assert summary.breaker.switching_operations == opens + closes
    assert all(event.time_seconds < duration for event in result.events)


def test_fractional_cadence_and_recovery(config: SimulationConfig) -> None:
    config = SimulationConfig.model_validate(
        config.model_dump()
        | {
            "duration_seconds": "1.5",
            "time_step_seconds": "0.5",
            "initial_breaker_state": "OPEN",
            "initial_frequency_hz": "49.88",
        }
    )
    result = run_simulation(config)
    assert len(result.samples) == 4
    assert result.events[0].time_seconds == Decimal("1.0")
    assert result.summary.load.connected_seconds == Decimal("0.5")
    assert result.summary.load.disconnected_seconds == Decimal("1.0")
    assert result.summary.generator.on_while_breaker_open_seconds == Decimal("1.0")
    assert result.summary.frequency.within_limits_seconds == Decimal("1.5")


def test_generator_off_and_initially_connected(config: SimulationConfig) -> None:
    config = SimulationConfig.model_validate(config.model_dump() | {"initial_generator_state": "OFF"})
    result = run_simulation(config)
    assert result.samples[0].physical.load_connected
    assert not result.samples[0].physical.load_powered
    assert result.events[0].time_seconds == 0
    assert result.summary.generator.off_seconds == 120
    assert result.summary.generator.on_seconds == result.summary.generator.on_pct == 0
    assert result.summary.generator.on_while_breaker_open_seconds == result.summary.load.powered_seconds == 0
    assert result.summary.load.longest_disconnection_seconds == 120
    assert result.summary.frequency.average_actual_frequency_hz == Decimal("50")
    assert result.summary.frequency.within_limits_seconds == 120


def test_generator_metrics_distinguish_connection_from_supply(config: SimulationConfig) -> None:
    initial = initialize(config)
    off = replace(initial, physical=replace(initial.physical, time_seconds=Decimal(1), generator_state=GeneratorState.OFF))
    on = replace(initial, physical=replace(initial.physical, time_seconds=Decimal(2)))
    summary = summarize_run([initial, off, on], [], config)
    assert summary.load.connected_seconds == 2
    assert summary.load.powered_seconds == 1
    assert summary.generator.on_seconds == summary.generator.off_seconds == 1
    assert summary.generator.on_pct == 50
    assert summary.generator.state_transitions == 2


def test_frequency_metrics_use_actual_trajectory_across_both_limits(config: SimulationConfig) -> None:
    rates = config.frequency_rates_hz_per_second.model_dump() | {"on_open": 2}
    config = SimulationConfig.model_validate(
        config.model_dump()
        | {
            "duration_seconds": 1,
            "initial_frequency_hz": "49.25",
            "initial_breaker_state": "OPEN",
            "frequency_rates_hz_per_second": rates,
        }
    )
    result = run_simulation(config, sensor=lambda _: Decimal("49.50"))
    frequency = result.summary.frequency
    assert frequency.min_actual_frequency_hz == Decimal("49.25")
    assert frequency.max_actual_frequency_hz == Decimal("51.25")
    assert frequency.average_actual_frequency_hz == Decimal("50.25")
    assert frequency.within_limits_seconds == Decimal("0.5")
    assert frequency.outside_limits_seconds == Decimal("0.5")
    assert frequency.closed_below_limit_seconds == 0
    assert frequency.minimum_margin_hz == Decimal("-0.75")
    assert frequency.safety_violation_count == len(result.violations) == 2
    assert [event.time_seconds for event in result.violations] == [0, 1]
    assert [event.type for event in result.events] == [
        EventType.FREQUENCY_BELOW_LIMIT, EventType.UNDER_FREQUENCY_EXITED, EventType.FREQUENCY_ABOVE_LIMIT,
    ]
