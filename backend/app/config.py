import logging
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, StrictBool, ValidationError, ValidationInfo, model_validator

from .simulation.models import BreakerState, GeneratorState

logger = logging.getLogger(__name__)
DEFAULT_CONFIG_PATH = Path(__file__).with_name("default.json")

ConfigNumber = Annotated[
    Decimal,
    Field(allow_inf_nan=False, max_digits=16, decimal_places=8),
    PlainSerializer(float, return_type=float, when_used="json"),
]
PositiveSeconds = Annotated[ConfigNumber, Field(gt=0)]
NonnegativeSeconds = Annotated[ConfigNumber, Field(ge=0)]


class FrequencyRates(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    on_closed: ConfigNumber
    on_open: ConfigNumber
    off_closed: ConfigNumber
    off_open: ConfigNumber


class SensorBiasConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    start_seconds: Annotated[ConfigNumber, Field(ge=0)]
    duration_seconds: PositiveSeconds
    offset_hz: ConfigNumber

    @property
    def end_seconds(self) -> Decimal:
        return self.start_seconds + self.duration_seconds


class SimulationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    duration_seconds: PositiveSeconds
    time_step_seconds: PositiveSeconds
    initial_frequency_hz: ConfigNumber
    initial_generator_state: GeneratorState
    initial_breaker_state: BreakerState
    nominal_frequency_hz: ConfigNumber
    lower_limit_hz: ConfigNumber
    upper_limit_hz: ConfigNumber
    frequency_rates_hz_per_second: FrequencyRates
    breaker_open_threshold_hz: ConfigNumber
    breaker_close_threshold_hz: ConfigNumber
    fs101_bias: SensorBiasConfig | None = None
    generator_shutdown_seconds: NonnegativeSeconds | None = None
    manual_state_testing: StrictBool = False

    @model_validator(mode="after")
    def validate_operating_parameters(self, info: ValidationInfo) -> Self:
        if self.duration_seconds % self.time_step_seconds:
            raise ValueError("duration_seconds must be an exact multiple of time_step_seconds")
        if not self.lower_limit_hz < self.nominal_frequency_hz < self.upper_limit_hz:
            raise ValueError("nominal_frequency_hz must be strictly between the frequency limits")
        if not (
            self.lower_limit_hz
            <= self.breaker_open_threshold_hz
            < self.breaker_close_threshold_hz
            <= self.upper_limit_hz
        ):
            raise ValueError("breaker thresholds must be ordered and within the frequency limits")
        if not self.manual_state_testing and info.context and info.context.get("normal_scenario"):
            if not self.lower_limit_hz <= self.initial_frequency_hz <= self.upper_limit_hz:
                raise ValueError("initial_frequency_hz must be within the frequency limits for a normal scenario")
        bias = self.fs101_bias
        shutdown = self.generator_shutdown_seconds
        if sum((bias is not None, shutdown is not None, self.manual_state_testing)) > 1:
            raise ValueError("Select only one diagnostic or failure scenario")
        if shutdown is not None:
            if self.initial_generator_state is not GeneratorState.ON:
                raise ValueError("G101 must start ON for a scheduled shutdown")
            if shutdown % self.time_step_seconds or shutdown >= self.duration_seconds:
                raise ValueError("Shutdown must be on the simulation time grid before the final timestamp")
        if bias is not None:
            if bias.start_seconds % self.time_step_seconds or bias.end_seconds % self.time_step_seconds:
                raise ValueError("FS101 fault start and end must be on the simulation time grid")
            if bias.end_seconds > self.duration_seconds:
                raise ValueError("FS101 fault must end by the last sample")
        return self


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> SimulationConfig:
    """Load and validate a configuration from disk."""
    try:
        return SimulationConfig.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        reasons = ", ".join(error["msg"] for error in exc.errors(include_input=False))
        logger.error("Could not load simulation configuration from %s: %s", path, reasons)
        raise
    except OSError as exc:
        logger.error("Could not load simulation configuration from %s: %s", path, exc.strerror)
        raise

