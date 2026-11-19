import pytest

from app.config import SimulationConfig, load_config


@pytest.fixture
def config() -> SimulationConfig:
    return load_config()

