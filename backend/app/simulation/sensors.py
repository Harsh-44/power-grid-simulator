from decimal import Decimal

from .models import PhysicalState


def read_frequency(state: PhysicalState) -> Decimal:
    """Return the ideal FS101 reading for the supplied physical state."""
    return state.actual_frequency_hz

