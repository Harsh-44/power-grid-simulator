from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.config import SimulationConfig
from app.simulation.engine import run_simulation
from app.simulation.models import BreakerState, EventType, GeneratorState


def configure(config: SimulationConfig, **overrides) -> SimulationConfig:
    return SimulationConfig.model_validate(config.model_dump() | overrides)


@pytest.mark.parametrize(("generator", "breaker", "frequency", "connected", "powered"), [
    ("ON", "CLOSED", "49.95", 1, 1),
    ("ON", "OPEN", "50.12", 0, 0),
    ("OFF", "CLOSED", "49.85", 1, 0),
    ("OFF", "OPEN", "50.00", 0, 0),
])
def test_manual_combinations(config, generator, breaker, frequency, connected, powered):
    case = configure(
        config, manual_state_testing=True, duration_seconds=1,
        initial_generator_state=generator, initial_breaker_state=breaker,
    )
    result = run_simulation(case, include_controller_trace=True)
    assert result.samples[-1].physical.actual_frequency_hz == Decimal(frequency)
    assert all(sample.physical.generator_state == generator and sample.physical.breaker_state == breaker
               for sample in result.samples)
    assert result.summary.load.connected_seconds == connected
    assert result.summary.load.powered_seconds == powered
    assert result.summary.load.connected_without_generator_power_seconds == connected - powered
    assert result.summary.breaker.switching_operations == 0
    assert result.controller_trace == ()


def test_shutdown_with_closed_breaker(config):
    case = configure(config, duration_seconds=12, generator_shutdown_seconds=3)
    result = run_simulation(case, include_controller_trace=True)
    assert result == run_simulation(case, include_controller_trace=True)
    assert result.samples[3].physical.generator_state is GeneratorState.ON
    assert result.samples[4].physical.breaker_state is BreakerState.CLOSED
    assert result.samples[4].physical.actual_frequency_hz == Decimal("49.70")
    assert all(sample.physical.generator_state is GeneratorState.OFF for sample in result.samples[4:])
    assert all(sample.physical.breaker_state is BreakerState.OPEN for sample in result.samples[5:])
    assert all(sample.physical.actual_frequency_hz == Decimal("49.70") for sample in result.samples[4:])
    assert [(event.type, event.time_seconds) for event in result.events] == [
        (EventType.GENERATOR_SHUTDOWN, 3),
        (EventType.LOAD_CONNECTED_UNPOWERED, 3),
        (EventType.BREAKER_OPENED, 4),
        (EventType.LOAD_CONNECTED_UNPOWERED_ENDED, 4),
    ]
    assert result.summary.generator.on_seconds == 3
    assert result.summary.generator.off_seconds == 9
    assert result.summary.generator.state_transitions == 1
    assert result.summary.load.connected_seconds == 4
    assert result.summary.load.powered_seconds == 3
    assert result.summary.load.connected_without_generator_power_seconds == 1
    assert result.controller_trace is not None
    assert 3 not in [decision.time_seconds for decision in result.controller_trace]
    assert result.controller_trace[3].generator_state is GeneratorState.OFF


def test_shutdown_with_open_breaker_on_fractional_grid(config):
    case = configure(
        config, duration_seconds=2, time_step_seconds="0.5", initial_breaker_state="OPEN",
        generator_shutdown_seconds=0,
    )
    result = run_simulation(case)
    assert all(sample.physical.actual_frequency_hz == 50 for sample in result.samples)
    assert result.events[0].time_seconds == 0
    assert result.events[0].type is EventType.GENERATOR_SHUTDOWN
    assert len(result.events) == 1
    assert result.summary.generator.off_seconds == 2
    assert result.summary.breaker.switching_operations == 0


def test_manual_unsafe_frequency_and_unpowered_connection(config):
    case = configure(
        config, manual_state_testing=True, duration_seconds=2, initial_frequency_hz="49.55",
        initial_generator_state="OFF", initial_breaker_state="CLOSED",
    )
    result = run_simulation(case)
    assert result.samples[-1].physical.actual_frequency_hz == Decimal("49.25")
    assert result.summary.frequency.under_frequency_sample_count == 2
    assert result.summary.frequency.under_frequency_episode_count == 1
    assert result.summary.frequency.closed_below_limit_seconds == Decimal(5) / 3
    assert result.summary.load.connected_without_generator_power_seconds == 2
    assert result.protection_diagnostics.findings == ()
    assert [(event.type, event.time_seconds) for event in result.events] == [
        (EventType.LOAD_CONNECTED_UNPOWERED, 0), (EventType.FREQUENCY_BELOW_LIMIT, 1),
    ]


@pytest.mark.parametrize("values", [
    {"generator_shutdown_seconds": 120},
    {"generator_shutdown_seconds": "0.5"},
    {"generator_shutdown_seconds": -1},
    {"generator_shutdown_seconds": 1, "initial_generator_state": "OFF"},
    {"generator_shutdown_seconds": 1, "manual_state_testing": True},
    {"manual_state_testing": True, "fs101_bias": {"start_seconds": 1, "duration_seconds": 1, "offset_hz": 1}},
])
def test_invalid_scenario_configuration(config, values):
    with pytest.raises(ValidationError):
        configure(config, **values)
