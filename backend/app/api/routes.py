import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError

from ..config import SimulationConfig
from ..simulation.engine import run_scenario
from .schemas import (
    ControllerDecisionResponse,
    EventResponse,
    FaultAnalysisResponse,
    ProtectionDiagnosticsResponse,
    RunRequest,
    RunResponse,
    SampleResponse,
    SummaryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


def get_default_config(request: Request) -> SimulationConfig:
    return request.app.state.default_config


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/config")
def default_config(config: Annotated[SimulationConfig, Depends(get_default_config)]) -> SimulationConfig:
    return config


@router.post("/simulations/run")
def run(
    config: Annotated[SimulationConfig, Depends(get_default_config)],
    request: RunRequest | None = None,
) -> RunResponse:
    submitted = request.model_dump(exclude_unset=True, exclude={"include_controller_trace"}) if request is not None else {}
    overrides = {
        key: value for key, value in submitted.items()
        if value is not None or key in ("fs101_bias", "generator_shutdown_seconds")
    }
    if overrides:
        try:
            config = SimulationConfig.model_validate(
                config.model_dump() | overrides,
                context={"normal_scenario": "initial_frequency_hz" in overrides},
            )
        except ValidationError as exc:
            errors = exc.errors(include_url=False, include_context=False, include_input=False)
            logger.warning("Rejected simulation configuration: %s", ", ".join(error["msg"] for error in errors))
            raise HTTPException(status_code=422, detail=errors) from exc

    result, fault_analysis = run_scenario(
        config, include_controller_trace=request.include_controller_trace if request is not None else False
    )
    return RunResponse(
        config=config,
        samples=[SampleResponse.from_sample(sample, config) for sample in result.samples],
        events=[EventResponse.model_validate(event) for event in result.events],
        violations=[EventResponse.model_validate(event) for event in result.violations],
        summary=SummaryResponse.model_validate(result.summary),
        fault_analysis=FaultAnalysisResponse.model_validate(fault_analysis) if fault_analysis is not None else None,
        protection_diagnostics=ProtectionDiagnosticsResponse.model_validate(result.protection_diagnostics),
        controller_trace=(
            [ControllerDecisionResponse.model_validate(decision) for decision in result.controller_trace]
            if result.controller_trace is not None else None
        ),
    )

