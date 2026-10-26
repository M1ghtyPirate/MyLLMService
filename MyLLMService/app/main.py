from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config.settings import Settings

from . import __version__
from .middleware import request_context_middleware
from .api.jokes import router as jokes_router
from .state import AppState


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.state = AppState()
    yield

settings = Settings()
app = FastAPI(
    title="MyLLMService",
    version=__version__,
    lifespan=lifespan,
)

app.middleware("http")(request_context_middleware)

app.include_router(jokes_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/", tags=["meta"])
async def index() -> dict[str, str]:
    return {"message": "See /docs for Swagger UI, /redoc for ReDoc"}