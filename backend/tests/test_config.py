import pytest
from pydantic import ValidationError

from app.config import SimulationConfig, load_config


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"duration_seconds": 0}, "greater than 0"),
        ({"time_step_seconds": -1}, "greater than 0"),
        ({"duration_seconds": 1.5}, "exact multiple"),
        ({"initial_frequency_hz": "NaN"}, "finite number"),
        ({"initial_generator_state": "RUNNING"}, "ON"),
        ({"initial_breaker_state": "ON"}, "CLOSED"),
        ({"nominal_frequency_hz": 51}, "strictly between"),
        ({"breaker_open_threshold_hz": 49.4}, "thresholds must be ordered"),
        ({"breaker_close_threshold_hz": 50.6}, "thresholds must be ordered"),
        ({"breaker_close_threshold_hz": 49.55}, "thresholds must be ordered"),
        ({"frequency_rates_hz_per_second": {"on_closed": -0.05}}, "on_open"),
        ({"typo": 1}, "Extra inputs"),
    ],
)
def test_invalid_configuration(config, overrides, message):
    with pytest.raises(ValidationError, match=message):
        SimulationConfig.model_validate(config.model_dump() | overrides)


def test_invalid_configuration_file_is_logged(tmp_path, caplog):
    path = tmp_path / "invalid.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValidationError, match="duration_seconds"):
        load_config(path)
    assert "Could not load simulation configuration" in caplog.text

