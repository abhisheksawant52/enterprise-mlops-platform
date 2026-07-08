"""Drift and performance metrics collection.

Collects serving-time metrics and evaluates data/prediction drift against
configured thresholds. Drift here is a simplified population-stability style
score; the interface is what matters for the platform's coherence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from .config import Settings, get_settings
from .logging_config import get_logger

logger = get_logger(__name__)


class HealthVerdict(str, Enum):
    """Overall verdict for a monitored deployment."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DRIFTED = "drifted"


class MetricSample(BaseModel):
    """A single observed serving metric."""

    name: str
    value: float
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MonitoringReport(BaseModel):
    """Result of evaluating a deployment's health."""

    model_name: str
    drift_score: float
    accuracy: float
    verdict: HealthVerdict
    samples: list[MetricSample] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MonitoringCollector:
    """Collects metrics and evaluates model/deployment health."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @staticmethod
    def population_stability_index(
        expected: list[float], actual: list[float]
    ) -> float:
        """Compute a simple population-stability index (PSI).

        Args:
            expected: Baseline distribution proportions (must sum to ~1).
            actual: Observed distribution proportions (must sum to ~1).

        Returns:
            The PSI value; higher means more drift.
        """

        if len(expected) != len(actual) or not expected:
            raise ValueError("expected and actual must be non-empty, equal length")
        import math

        psi = 0.0
        for exp, act in zip(expected, actual):
            exp_c = max(exp, 1e-6)
            act_c = max(act, 1e-6)
            psi += (act_c - exp_c) * math.log(act_c / exp_c)
        return round(psi, 6)

    def evaluate(
        self,
        model_name: str,
        drift_score: float,
        accuracy: float,
        samples: list[MetricSample] | None = None,
    ) -> MonitoringReport:
        """Evaluate a deployment against configured thresholds."""

        if drift_score >= self._settings.drift_threshold:
            verdict = HealthVerdict.DRIFTED
        elif accuracy < self._settings.min_serving_accuracy:
            verdict = HealthVerdict.DEGRADED
        else:
            verdict = HealthVerdict.HEALTHY

        logger.info(
            "Monitoring %s: drift=%.4f acc=%.4f -> %s",
            model_name,
            drift_score,
            accuracy,
            verdict.value,
        )
        return MonitoringReport(
            model_name=model_name,
            drift_score=drift_score,
            accuracy=accuracy,
            verdict=verdict,
            samples=samples or [],
            evaluated_at=datetime.now(timezone.utc),
        )
