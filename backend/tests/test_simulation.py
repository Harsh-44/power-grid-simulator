from dataclasses import replace
from decimal import Decimal

import pytest

from app.config import SimulationConfig
from app.simulation.diagnostics import SimulationInvariantError
from app.simulation.engine import initialize, run_simulation, step
from app.simulation.models import BreakerState, EventType, GeneratorState
from app.simulation.physics import advance_physics


@pytest.mark.parametrize(
    ("generator", "breaker", "frequency"),
    [
        (GeneratorState.ON, BreakerState.CLOSED, "49.95"),
        (GeneratorState.ON, BreakerState.OPEN, "50.12"),
        (GeneratorState.OFF, BreakerState.CLOSED, "49.85"),
        (GeneratorState.OFF, BreakerState.OPEN, "50.00"),
    ],
)
def test_physics(config, generator, breaker, frequency):
    initial = initialize(config).physical
    state = replace(initial, generator_state=generator, breaker_state=breaker)
    updated = advance_physics(state, config)

    assert state.actual_frequency_hz == Decimal("50.00")
    assert updated.actual_frequency_hz == Decimal(frequency)
    assert updated.time_seconds == Decimal(1)
    assert updated.generator_state is generator
    assert updated.breaker_state is breaker


def test_initial_state(config):
    sample = initialize(config)
    assert sample.physical.time_seconds == Decimal(0)
    assert sample.physical.actual_frequency_hz == sample.reported_frequency_hz == Decimal("50.00")
    assert sample.physical.generator_state is GeneratorState.ON
    assert sample.physical.breaker_state is BreakerState.CLOSED
    assert sample.physical.load_connected
    assert sample.physical.load_powered


def test_single_step_with_fractional_time(config):
    config = SimulationConfig.model_validate(config.model_dump() | {"time_step_seconds": "0.5"})
    initial = initialize(config)
    result = step(initial, config)
    assert result.sample.physical.time_seconds == Decimal("0.5")
    assert result.sample.physical.actual_frequency_hz == Decimal("49.975")
    assert result.sample.reported_frequency_hz == Decimal("49.975")
    assert result.events == ()


def test_normal_run_is_deterministic_and_safe(config):
    result = run_simulation(config)
    assert result == run_simulation(config)
    assert len(result.samples) == 121
    assert [sample.physical.time_seconds for sample in result.samples] == list(range(121))
    assert result.violations == ()
    for sample in result.samples:
        state = sample.physical
        assert config.lower_limit_hz <= state.actual_frequency_hz <= config.upper_limit_hz
        if state.breaker_state is BreakerState.CLOSED:
            assert state.actual_frequency_hz >= config.lower_limit_hz
        assert state.generator_state is GeneratorState.ON
        assert sample.reported_frequency_hz == state.actual_frequency_hz


def test_normal_breaker_switches_and_powered_time(config):
    result = run_simulation(config)
    first_open, first_close = result.events[:2]
    assert (first_open.type, first_open.time_seconds) == (EventType.BREAKER_OPENED, Decimal(9))
    assert (first_close.type, first_close.time_seconds) == (EventType.BREAKER_CLOSED, Decimal(13))
    assert result.samples[9].reported_frequency_hz == config.breaker_open_threshold_hz
    for sample in result.samples[10:14]:
        assert not sample.physical.load_connected
        assert not sample.physical.load_powered
    assert result.samples[12].reported_frequency_hz < config.breaker_close_threshold_hz
    assert result.samples[13].reported_frequency_hz >= config.breaker_close_threshold_hz
    assert result.samples[14].physical.load_powered

    short_config = SimulationConfig.model_validate(config.model_dump() | {"duration_seconds": 14})
    assert run_simulation(short_config).summary.load_powered_seconds == Decimal(10)


def test_controller_projects_closed_frequency_before_hysteresis_would_open(config):
    config = SimulationConfig.model_validate(
        config.model_dump() | {"time_step_seconds": 2, "initial_frequency_hz": "49.58"}
    )
    result = step(initialize(config), config)
    assert result.sample.physical.breaker_state is BreakerState.OPEN
    assert result.sample.physical.actual_frequency_hz == Decimal("49.82")
    assert "below" in result.events[0].reason


def test_controller_rejects_reconnection_if_closed_interval_would_be_unsafe(config):
    rates = config.frequency_rates_hz_per_second.model_dump() | {"on_closed": "-0.60"}
    config = SimulationConfig.model_validate(
        config.model_dump()
        | {"initial_breaker_state": "OPEN", "frequency_rates_hz_per_second": rates}
    )
    result = step(initialize(config), config)
    assert result.sample.physical.breaker_state is BreakerState.OPEN
    assert result.sample.physical.actual_frequency_hz == Decimal("50.12")
    assert result.events == ()


def test_controller_uses_sampled_fs101_reading(config):
    sample = replace(initialize(config), reported_frequency_hz=Decimal("49.55"))
    result = step(sample, config)
    assert result.sample.physical.breaker_state is BreakerState.OPEN
    assert result.sample.physical.actual_frequency_hz == Decimal("50.12")


def test_sensor_is_observed_once_per_sample(config):
    calls = []

    def sensor(state):
        calls.append(state.time_seconds)
        return state.actual_frequency_hz

    result = run_simulation(config, sensor=sensor)
    assert calls == [sample.physical.time_seconds for sample in result.samples]


def test_generator_off_disconnects_load_without_counting_initial_sample(config):
    config = SimulationConfig.model_validate(config.model_dump() | {"initial_generator_state": "OFF"})
    result = run_simulation(config)
    assert result.samples[0].physical.load_connected
    assert not result.samples[0].physical.load_powered
    assert not result.samples[1].physical.load_connected
    assert result.events[0].time_seconds == Decimal(0)
    assert result.events[0].type is EventType.BREAKER_OPENED
    assert result.summary.load_powered_seconds == 0
    assert result.summary.min_actual_frequency_hz == result.summary.max_actual_frequency_hz == Decimal("50.00")


def test_abnormal_initial_frequency_is_recorded_without_clamping(config):
    config = SimulationConfig.model_validate(
        config.model_dump() | {"initial_frequency_hz": "49.45", "duration_seconds": 1}
    )
    result = run_simulation(config)
    assert result.samples[0].physical.actual_frequency_hz == Decimal("49.45")
    assert result.samples[1].physical.actual_frequency_hz == Decimal("49.57")
    assert [(event.type, event.time_seconds) for event in result.violations] == [(EventType.FREQUENCY_BELOW_LIMIT, 0)]
    assert (result.events[-1].type, result.events[-1].time_seconds) == (EventType.UNDER_FREQUENCY_EXITED, 1)
    assert result.summary.frequency.closed_below_limit_seconds == 0


def test_configured_recovery_can_overshoot_upper_limit(config):
    rates = config.frequency_rates_hz_per_second.model_dump() | {"on_open": "1.1"}
    config = SimulationConfig.model_validate(
        config.model_dump() | {
            "frequency_rates_hz_per_second": rates,
            "duration_seconds": 1,
            "initial_frequency_hz": "49.55",
        }
    )
    result = run_simulation(config)
    assert result.samples[1].physical.actual_frequency_hz == Decimal("50.65")
    assert [event.type for event in result.violations] == [EventType.FREQUENCY_ABOVE_LIMIT]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("actual_frequency_hz", Decimal("NaN"), "Actual bus frequency"),
        ("time_seconds", Decimal("0.5"), "off the"),
        ("generator_state", "UNAVAILABLE", "invalid generator state"),
        ("breaker_state", "UNAVAILABLE", "invalid breaker state"),
    ],
)
def test_invalid_state_raises_with_structured_event(config, field, value, message):
    sample = initialize(config)
    invalid = replace(sample, physical=replace(sample.physical, **{field: value}))
    with pytest.raises(SimulationInvariantError, match=message) as exc:
        step(invalid, config)
    assert exc.value.event.type is EventType.INVALID_STATE


def test_invalid_sensor_reading_raises(config):
    with pytest.raises(SimulationInvariantError, match="FS101"):
        initialize(config, sensor=lambda _: Decimal("Infinity"))

