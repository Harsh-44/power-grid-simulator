from decimal import Decimal

from ..config import SimulationConfig
from .models import BreakerState, GeneratorState
from .physics import next_frequency


def decide_breaker(
    reading: Decimal,
    generator_state: GeneratorState,
    breaker_state: BreakerState,
    config: SimulationConfig,
) -> tuple[BreakerState, str]:
    if generator_state is GeneratorState.OFF:
        return BreakerState.OPEN, "G101 is off and cannot supply the station load."

    if breaker_state is BreakerState.CLOSED and reading <= config.breaker_open_threshold_hz:
        return (
            BreakerState.OPEN,
            f"The reading is at or below the {config.breaker_open_threshold_hz} Hz opening threshold.",
        )

    projected = next_frequency(reading, generator_state, BreakerState.CLOSED, config)
    if projected < config.lower_limit_hz:
        return (
            BreakerState.OPEN,
            f"A closed breaker would project {projected} Hz from FS101, below the {config.lower_limit_hz} Hz limit.",
        )

    if reading >= config.breaker_close_threshold_hz:
        return (
            BreakerState.CLOSED,
            f"The reading meets the {config.breaker_close_threshold_hz} Hz recovery threshold.",
        )

    return breaker_state, "No switching condition was met."

