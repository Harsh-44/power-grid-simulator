import pytest
from httpx import ASGITransport, AsyncClient

from app.config import SimulationConfig
from app.main import app

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client,
    ):
        yield client


async def test_default_run_endpoints(client):
    assert (await client.get("/api/health")).json() == {"status": "ok"}
    config = (await client.get("/api/config")).json()
    response = await client.post("/api/simulations/run")
    assert response.status_code == 200
    result = response.json()
    assert result["config"] == config
    assert config["duration_seconds"] == 120
    assert config["breaker_open_threshold_hz"] == 49.55
    assert len(result["samples"]) == 121
    assert result["samples"][0] == {
        "time_seconds": 0,
        "actual_frequency_hz": 50,
        "reported_frequency_hz": 50,
        "frequency_condition": "normal",
        "generator_state": "ON",
        "breaker_state": "CLOSED",
        "load_connected": True,
        "load_powered": True,
    }
    assert result["samples"][-1]["time_seconds"] == 120
    event = result["events"][0]
    assert event["time_seconds"] == 9
    assert event["type"] == "breaker_opened"
    assert event["component_id"] == "CB101"
    assert (event["previous_state"], event["new_state"]) == ("CLOSED", "OPEN")
    assert result["violations"] == []
    assert result["summary"]["load_powered_seconds"] == 87
    assert result["summary"]["load"]["connection_availability_pct"] == 72.5
    assert result["summary"]["frequency"]["within_limits_seconds"] == 120
    assert result["summary"]["generator"]["on_seconds"] == 120
    assert result["summary"]["breaker"]["switching_operations"] == 14
    assert result["fault_analysis"] is None
    assert result["controller_trace"] is None
    assert result["protection_diagnostics"]["findings"] == []


async def test_duration_override_is_per_run(client):
    response = await client.post("/api/simulations/run", json={"duration_seconds": 14})
    assert response.status_code == 200
    result = response.json()
    assert result["config"]["duration_seconds"] == 14
    assert len(result["samples"]) == 15
    assert result["summary"]["load_powered_seconds"] == 10
    assert (await client.get("/api/config")).json()["duration_seconds"] == 120


async def test_api_manual_and_shutdown_scenarios(client):
    url = "/api/simulations/run"
    manual = await client.post(url, json={
        "manual_state_testing": True, "initial_generator_state": "OFF",
        "initial_breaker_state": "CLOSED", "initial_frequency_hz": 49.45, "duration_seconds": 1,
    })
    assert manual.status_code == 200
    run = manual.json()
    assert run["samples"][-1]["actual_frequency_hz"] == 49.30
    assert run["samples"][-1]["load_connected"] and not run["samples"][-1]["load_powered"]
    assert run["summary"]["load"]["connected_without_generator_power_seconds"] == 1
    shutdown = await client.post(url, json={"duration_seconds": 4, "generator_shutdown_seconds": 2})
    assert shutdown.status_code == 200
    event = shutdown.json()["events"][0]
    assert (event["type"], event["time_seconds"], event["previous_state"], event["new_state"]) == (
        "generator_shutdown", 2, "ON", "OFF",
    )


async def test_fault_request_and_equivalent_normal_baseline(client):
    overrides = {"duration_seconds": 14, "initial_frequency_hz": 50.1, "breaker_open_threshold_hz": 49.75}
    schedule = {"start_seconds": 5, "duration_seconds": 7, "offset_hz": 0.5}
    response = await client.post("/api/simulations/run", json=overrides | {"fs101_bias": schedule})
    assert response.status_code == 200
    result = response.json()
    analysis = result["fault_analysis"]
    assert result["config"]["fs101_bias"] == schedule
    assert analysis["duration_seconds"] == 7
    assert analysis["start_seconds"] == 5
    assert analysis["end_seconds"] == 12
    assert analysis["max_measurement_error_hz"] == 0.5
    assert result["samples"][5]["reported_frequency_hz"] == result["samples"][5]["actual_frequency_hz"] + 0.5
    assert {"fault_activated", "fault_cleared"} <= {event["type"] for event in result["events"]}
    normal = (await client.post("/api/simulations/run", json=overrides)).json()
    assert analysis["comparison"]["normal_breaker_operations"] == normal["summary"]["breaker"]["switching_operations"]
    assert analysis["comparison"]["normal_load_connection_availability_pct"] == (
        normal["summary"]["load"]["connection_availability_pct"]
    )
    assert normal["fault_analysis"] is None


async def test_controller_trace_is_optional_and_separate(client):
    overrides = {
        "duration_seconds": 4,
        "fs101_bias": {"start_seconds": 1, "duration_seconds": 2, "offset_hz": -0.5},
    }
    response = await client.post("/api/simulations/run", json=overrides | {"include_controller_trace": True})
    assert response.status_code == 200
    result = response.json()
    untraced = (await client.post("/api/simulations/run", json=overrides)).json()
    assert untraced["controller_trace"] is None
    assert result["events"] == untraced["events"]
    assert result["config"] == untraced["config"]
    assert [entry["time_seconds"] for entry in result["controller_trace"]] == [0, 1, 2, 3]
    assert [(entry["previous_state"], entry["new_state"]) for entry in result["controller_trace"]] == [
        ("CLOSED", "CLOSED"), ("CLOSED", "OPEN"), ("OPEN", "OPEN"), ("OPEN", "CLOSED"),
    ]
    findings = result["protection_diagnostics"]
    assert findings["premature_opening_count"] == 1
    assert findings["missed_protective_opening_count"] == 0
    assert findings["findings"][0]["time_seconds"] == 1


async def test_explicit_null_disables_configured_bias(client, config, monkeypatch):
    customized = SimulationConfig.model_validate(
        config.model_dump() | {"fs101_bias": {"start_seconds": 0, "duration_seconds": 1, "offset_hz": 0.5}}
    )
    monkeypatch.setattr(app.state, "default_config", customized)
    configured = (await client.post("/api/simulations/run")).json()
    normal = (await client.post("/api/simulations/run", json={"fs101_bias": None})).json()
    assert configured["fault_analysis"] is not None
    assert normal["fault_analysis"] is None
    assert normal["config"]["fs101_bias"] is None


async def test_frequency_and_threshold_overrides_apply_only_to_the_run(client):
    defaults = (await client.get("/api/config")).json()
    overrides = {
        "duration_seconds": 14,
        "initial_frequency_hz": 50.1,
        "breaker_open_threshold_hz": 49.75,
        "breaker_close_threshold_hz": 50.1,
    }
    response = await client.post("/api/simulations/run", json=overrides)
    assert response.status_code == 200
    result = response.json()
    assert result["config"] == defaults | overrides
    assert result["samples"][0]["actual_frequency_hz"] == 50.1
    assert [(event["time_seconds"], event["new_state"]) for event in result["events"]] == [
        (7, "OPEN"),
        (10, "CLOSED"),
    ]
    assert (await client.get("/api/config")).json() == defaults


async def test_abnormal_run_returns_samples_and_violations(client, config, monkeypatch):
    abnormal = SimulationConfig.model_validate(
        config.model_dump() | {"initial_frequency_hz": 49.45, "duration_seconds": 1}
    )
    monkeypatch.setattr(app.state, "default_config", abnormal)
    response = await client.post("/api/simulations/run")
    assert response.status_code == 200
    result = response.json()
    assert result["samples"][0]["reported_frequency_hz"] == 49.45
    assert result["samples"][0]["frequency_condition"] == "under_frequency"
    assert result["samples"][1]["frequency_condition"] == "normal"
    frequency = result["summary"]["frequency"]
    assert frequency["safety_violation_count"] == frequency["violating_sample_count"] == 1
    assert frequency["minimum_margin_hz"] == -0.05
    assert frequency["violation_episode_count"] == 1
    assert frequency["outside_limits_seconds"] == pytest.approx(5 / 12)
    assert frequency["closed_below_limit_seconds"] == 0
    assert result["violations"] == result["events"][:1]
    assert [event["type"] for event in result["events"]] == [
        "frequency_below_limit", "breaker_opened", "under_frequency_exited",
    ]


async def test_valid_overrides_can_produce_an_unclamped_violation(client, config, monkeypatch):
    rates = config.frequency_rates_hz_per_second.model_dump() | {"on_open": 1}
    customized = SimulationConfig.model_validate(
        config.model_dump() | {"frequency_rates_hz_per_second": rates}
    )
    monkeypatch.setattr(app.state, "default_config", customized)
    response = await client.post(
        "/api/simulations/run",
        json={"duration_seconds": 1, "initial_frequency_hz": 49.75, "breaker_open_threshold_hz": 49.75},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["samples"][-1]["actual_frequency_hz"] == 50.75
    assert result["samples"][-1]["frequency_condition"] == "over_frequency"
    assert result["violations"][0]["component_id"] == "BUS"
    assert result["violations"][0]["time_seconds"] == 1


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"duration_seconds": 1.5}, "exact multiple"),
        ({"duration_seconds": 0}, "greater than 0"),
        ({"initial_frequency_hz": 49}, "initial_frequency_hz must be within"),
        ({"initial_frequency_hz": 51}, "initial_frequency_hz must be within"),
        ({"initial_frequency_hz": "NaN"}, "finite number"),
        ({"breaker_open_threshold_hz": "Infinity"}, "finite number"),
        ({"breaker_open_threshold_hz": 49.49}, "thresholds must be ordered"),
        ({"breaker_close_threshold_hz": 50.51}, "thresholds must be ordered"),
        ({"breaker_open_threshold_hz": 50, "breaker_close_threshold_hz": 50}, "thresholds must be ordered"),
        ({"breaker_open_threshold_hz": 50.1, "breaker_close_threshold_hz": 50}, "thresholds must be ordered"),
        ({"time_step_seconds": 2}, "Extra inputs"),
        ({"include_controller_trace": "true"}, "valid boolean"),
        (
            {"duration_seconds": 3, "fs101_bias": {"start_seconds": 2, "duration_seconds": 2, "offset_hz": 0.5}},
            "must end by the last sample",
        ),
    ],
)
async def test_invalid_overrides_return_422(client, override, message):
    response = await client.post("/api/simulations/run", json=override)
    assert response.status_code == 422
    assert message in response.json()["detail"][0]["msg"]

