from dataclasses import replace

from ..config import SimulationConfig
from .models import EventType, GeneratorState, PhysicalState, SimulationEvent


def apply_scheduled_shutdown(
    state: PhysicalState, config: SimulationConfig,
) -> tuple[PhysicalState, SimulationEvent | None]:
    if state.time_seconds != config.generator_shutdown_seconds or state.generator_state is GeneratorState.OFF:
        return state, None
    return replace(state, generator_state=GeneratorState.OFF), SimulationEvent(
        state.time_seconds, EventType.GENERATOR_SHUTDOWN, "Scheduled loss of G101 generation.",
        component_id="G101", previous_state=GeneratorState.ON, new_state=GeneratorState.OFF,
    )


def unpowered_connection_event(before: PhysicalState, applied: PhysicalState) -> SimulationEvent | None:
    was_unpowered = before.time_seconds != 0 and before.load_connected and not before.load_powered
    is_unpowered = applied.load_connected and not applied.load_powered
    if was_unpowered == is_unpowered:
        return None
    if is_unpowered:
        return SimulationEvent(
            applied.time_seconds, EventType.LOAD_CONNECTED_UNPOWERED,
            "L101 remains connected with G101 off and no confirmed generator power.", component_id="L101",
        )
    return SimulationEvent(
        applied.time_seconds, EventType.LOAD_CONNECTED_UNPOWERED_ENDED,
        "L101 is no longer connected without generator power.", component_id="L101",
    )
