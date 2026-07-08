"""Model registry client abstraction.

Wraps an MLflow-style tracking/registry server behind a small, typed interface
so the rest of the platform does not depend on a specific vendor SDK. Network
calls are made through ``httpx`` and are intentionally thin — the goal is a
coherent abstraction, not a production client.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

import httpx
from pydantic import BaseModel, Field

from .config import Settings, get_settings
from .logging_config import get_logger

logger = get_logger(__name__)


class ModelStage(str, Enum):
    """Lifecycle stages a registered model version can occupy."""

    NONE = "None"
    STAGING = "Staging"
    PRODUCTION = "Production"
    ARCHIVED = "Archived"


class ModelVersion(BaseModel):
    """A single registered version of a model."""

    name: str
    version: str
    stage: ModelStage = ModelStage.NONE
    run_id: str | None = None
    source_uri: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: dict[str, float] = Field(default_factory=dict)


class RegistryError(RuntimeError):
    """Raised when the registry returns an unexpected response."""


class ModelRegistryClient:
    """Typed client for a model registry / tracking server."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._base_url = self._settings.registry_uri.rstrip("/")
        self._timeout = self._settings.registry_timeout_seconds

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self._base_url, timeout=self._timeout)

    def register_model(
        self,
        name: str,
        run_id: str,
        source_uri: str,
        metrics: dict[str, float] | None = None,
    ) -> ModelVersion:
        """Register a new model version produced by a training run.

        Args:
            name: Registered model name.
            run_id: Identifier of the training run that produced the artifact.
            source_uri: URI of the stored model artifact (e.g. ``s3://...``).
            metrics: Optional evaluation metrics to attach.

        Returns:
            The newly created :class:`ModelVersion`.
        """

        payload = {"name": name, "run_id": run_id, "source": source_uri}
        logger.info("Registering model '%s' from run '%s'", name, run_id)
        with self._client() as client:
            response = client.post("/api/2.0/mlflow/model-versions/create", json=payload)
        version = self._parse_version(response, name, run_id, source_uri, metrics)
        return version

    def get_latest_version(
        self, name: str, stage: ModelStage = ModelStage.PRODUCTION
    ) -> ModelVersion | None:
        """Return the latest model version in ``stage`` (or ``None``)."""

        logger.debug("Fetching latest '%s' version in stage %s", name, stage.value)
        with self._client() as client:
            response = client.get(
                "/api/2.0/mlflow/registered-models/get-latest-versions",
                params={"name": name, "stages": stage.value},
            )
        if response.status_code == httpx.codes.NOT_FOUND:
            return None
        return self._parse_version(response, name, None, None, None, stage=stage)

    def transition_stage(self, name: str, version: str, stage: ModelStage) -> ModelVersion:
        """Transition a model version to a new lifecycle ``stage``."""

        logger.info("Transitioning %s v%s -> %s", name, version, stage.value)
        with self._client() as client:
            client.post(
                "/api/2.0/mlflow/model-versions/transition-stage",
                json={"name": name, "version": version, "stage": stage.value},
            )
        return ModelVersion(name=name, version=version, stage=stage)

    @staticmethod
    def _parse_version(
        response: httpx.Response,
        name: str,
        run_id: str | None,
        source_uri: str | None,
        metrics: dict[str, float] | None,
        stage: ModelStage = ModelStage.NONE,
    ) -> ModelVersion:
        try:
            body = response.json()
        except ValueError as exc:  # pragma: no cover - defensive
            raise RegistryError("Registry returned a non-JSON response") from exc
        info = body.get("model_version", body)
        return ModelVersion(
            name=name,
            version=str(info.get("version", "1")),
            stage=ModelStage(info.get("current_stage", stage.value)),
            run_id=run_id or info.get("run_id"),
            source_uri=source_uri or info.get("source"),
            metrics=metrics or {},
        )
