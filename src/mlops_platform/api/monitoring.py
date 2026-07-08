"""Monitoring endpoints for drift and performance evaluation."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..monitoring import MonitoringCollector, MonitoringReport

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

_collector = MonitoringCollector()


class EvaluationRequest(BaseModel):
    """Inputs for a monitoring evaluation."""

    model_name: str
    drift_score: float = Field(..., ge=0.0)
    accuracy: float = Field(..., ge=0.0, le=1.0)


@router.post("/evaluate", response_model=MonitoringReport)
def evaluate(request: EvaluationRequest) -> MonitoringReport:
    """Evaluate a deployment against configured drift/accuracy thresholds."""

    return _collector.evaluate(
        model_name=request.model_name,
        drift_score=request.drift_score,
        accuracy=request.accuracy,
    )
