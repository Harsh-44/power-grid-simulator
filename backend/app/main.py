import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api.routes import router
from .api.schemas import EventResponse
from .config import load_config
from .simulation.diagnostics import SimulationInvariantError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.default_config = load_config()
    yield


app = FastAPI(title="Arctic Station Power Grid Simulator", lifespan=lifespan)
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{key: error[key] for key in ("loc", "msg", "type")} for error in exc.errors()]
    logger.warning("Rejected invalid API request: %s", ", ".join(error["msg"] for error in errors))
    return JSONResponse(status_code=422, content={"detail": errors})


@app.exception_handler(SimulationInvariantError)
async def invalid_simulation(_: Request, exc: SimulationInvariantError) -> JSONResponse:
    event = EventResponse.model_validate(exc.event)
    return JSONResponse(status_code=500, content={"detail": event.model_dump(mode="json")})

