"""Liveness and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from ..config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
def health() -> dict[str, str]:
    """Return a static liveness payload."""

    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
def ready() -> dict[str, str]:
    """Return readiness including the resolved environment name."""

    settings = get_settings()
    return {"status": "ready", "environment": settings.environment}
