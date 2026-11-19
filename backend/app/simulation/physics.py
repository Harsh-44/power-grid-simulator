from dataclasses import replace
from decimal import Decimal

from ..config import SimulationConfig
from .models import BreakerState, GeneratorState, PhysicalState


def next_frequency(
    frequency_hz: Decimal,
    generator: GeneratorState,
    breaker: BreakerState,
    config: SimulationConfig,
) -> Decimal:
    rates = config.frequency_rates_hz_per_second
    if generator is GeneratorState.ON:
        rate = rates.on_closed if breaker is BreakerState.CLOSED else rates.on_open
    else:
        rate = rates.off_closed if breaker is BreakerState.CLOSED else rates.off_open
    return frequency_hz + rate * config.time_step_seconds


def advance_physics(state: PhysicalState, config: SimulationConfig) -> PhysicalState:
    return replace(
        state,
        time_seconds=state.time_seconds + config.time_step_seconds,
        actual_frequency_hz=next_frequency(
            state.actual_frequency_hz, state.generator_state, state.breaker_state, config
        ),
    )

