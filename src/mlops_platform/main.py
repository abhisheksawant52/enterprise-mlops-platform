"""FastAPI application for the MLOps control-plane.

Wires the domain routers together and exposes ``/health`` and ``/ready`` probes
used by Kubernetes and load balancers.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from . import __version__
from .api import deployment, health, monitoring, training
from .config import get_settings
from .logging_config import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Configure logging on startup and log clean shutdown."""

    settings = get_settings()
    configure_logging(level=settings.log_level, json_logs=settings.log_json)
    logger.info("Starting %s (env=%s)", settings.app_name, settings.environment)
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Application factory returning a configured :class:`FastAPI` instance."""

    settings = get_settings()
    app = FastAPI(
        title="Enterprise MLOps Platform",
        description="Control-plane API for training, registry, deployment, and monitoring.",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.settings = settings

    app.include_router(health.router)
    app.include_router(training.router)
    app.include_router(deployment.router)
    app.include_router(monitoring.router)
    return app


app = create_app()
