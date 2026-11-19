from decimal import Decimal

from ..config import SensorBiasConfig
from .models import EventType, SimulationEvent


def apply_sensor_bias(measurement_hz: Decimal, time: Decimal, bias: SensorBiasConfig | None) -> Decimal:
    if (
        bias is not None
        and bias.start_seconds <= time < bias.end_seconds
        and isinstance(measurement_hz, Decimal)
        and measurement_hz.is_finite()
    ):
        return measurement_hz + bias.offset_hz
    return measurement_hz


def bias_transition_at(time: Decimal, bias: SensorBiasConfig | None) -> SimulationEvent | None:
    if bias is None:
        return None
    if time == bias.start_seconds:
        return SimulationEvent(
            time,
            EventType.FAULT_ACTIVATED,
            f"FS101 measurement bias of {bias.offset_hz:+f} Hz activated.",
            component_id="FS101",
        )
    if time == bias.end_seconds:
        return SimulationEvent(
            time, EventType.FAULT_CLEARED, "FS101 measurement bias cleared.", component_id="FS101"
        )
    return None
