"""Training job orchestration and submission.

Provides a small orchestrator that submits training jobs to a Kubernetes-style
batch backend and tracks their lifecycle. The submission call is abstracted so
the platform can target Kubeflow, Argo Workflows, or a plain Job controller.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from .config import Settings, get_settings
from .logging_config import get_logger

logger = get_logger(__name__)


class JobStatus(str, Enum):
    """Lifecycle status of a training job."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TrainingRequest(BaseModel):
    """Parameters describing a training job to submit."""

    model_name: str = Field(..., description="Name to register the resulting model under.")
    dataset_uri: str = Field(..., description="URI of the training dataset.")
    hyperparameters: dict[str, float | int | str] = Field(default_factory=dict)
    image: str | None = Field(default=None, description="Override trainer image.")
    max_runtime_minutes: int = Field(default=120, ge=1)


class TrainingJob(BaseModel):
    """State of a submitted training job."""

    job_id: str
    model_name: str
    status: JobStatus = JobStatus.PENDING
    run_id: str | None = None
    artifact_uri: str | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TrainingOrchestrator:
    """Submits and tracks training jobs against the batch backend."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._jobs: dict[str, TrainingJob] = {}

    def submit(self, request: TrainingRequest) -> TrainingJob:
        """Submit a training job and return its initial state.

        In a real deployment this renders a Job/Workflow manifest and applies it
        to the ``training_namespace``. Here we record the intent and generate a
        deterministic run identifier.
        """

        job_id = f"train-{uuid.uuid4().hex[:12]}"
        run_id = uuid.uuid4().hex
        image = request.image or self._settings.training_image
        logger.info(
            "Submitting training job %s for model '%s' (image=%s, ns=%s)",
            job_id,
            request.model_name,
            image,
            self._settings.training_namespace,
        )
        job = TrainingJob(
            job_id=job_id,
            model_name=request.model_name,
            status=JobStatus.PENDING,
            run_id=run_id,
            artifact_uri=f"s3://{self._settings.model_bucket}/{request.model_name}/{run_id}",
        )
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> TrainingJob | None:
        """Return a tracked job by id, or ``None`` if unknown."""

        return self._jobs.get(job_id)

    def mark(
        self,
        job_id: str,
        status: JobStatus,
        metrics: dict[str, float] | None = None,
    ) -> TrainingJob:
        """Update the status (and optional metrics) of a tracked job."""

        job = self._jobs[job_id]
        job.status = status
        if metrics:
            job.metrics.update(metrics)
        logger.info("Job %s -> %s", job_id, status.value)
        return job
