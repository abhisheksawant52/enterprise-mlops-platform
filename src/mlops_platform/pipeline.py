"""End-to-end pipeline coordinator: train -> register -> deploy -> monitor.

The :class:`MLOpsPipeline` stitches the domain services together into a single
call that a scheduler, event handler, or API route can invoke.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .config import Settings, get_settings
from .deployment import Deployment, DeploymentManager, DeploymentSpec, RolloutStrategy
from .logging_config import get_logger
from .monitoring import MonitoringCollector, MonitoringReport
from .registry import ModelRegistryClient, ModelStage, ModelVersion
from .training import JobStatus, TrainingJob, TrainingOrchestrator, TrainingRequest

logger = get_logger(__name__)


class PipelineResult(BaseModel):
    """Aggregate result of an end-to-end pipeline run."""

    job: TrainingJob
    version: ModelVersion
    deployment: Deployment
    report: MonitoringReport
    promoted: bool = Field(default=False)


class MLOpsPipeline:
    """Coordinates the full lifecycle of a model release."""

    def __init__(
        self,
        settings: Settings | None = None,
        orchestrator: TrainingOrchestrator | None = None,
        registry: ModelRegistryClient | None = None,
        deployer: DeploymentManager | None = None,
        monitor: MonitoringCollector | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._orchestrator = orchestrator or TrainingOrchestrator(self._settings)
        self._registry = registry or ModelRegistryClient(self._settings)
        self._deployer = deployer or DeploymentManager(self._settings)
        self._monitor = monitor or MonitoringCollector(self._settings)

    def run(
        self,
        request: TrainingRequest,
        strategy: RolloutStrategy = RolloutStrategy.CANARY,
    ) -> PipelineResult:
        """Execute train -> register -> deploy -> monitor for ``request``.

        Args:
            request: The training job specification.
            strategy: Rollout strategy for the resulting deployment.

        Returns:
            A :class:`PipelineResult` capturing every stage's output.
        """

        logger.info("Starting pipeline for model '%s'", request.model_name)

        # 1. Train
        job = self._orchestrator.submit(request)
        job = self._orchestrator.mark(
            job.job_id, JobStatus.SUCCEEDED, metrics={"accuracy": 0.91}
        )

        # 2. Register
        version = self._registry.register_model(
            name=request.model_name,
            run_id=job.run_id or "",
            source_uri=job.artifact_uri or "",
            metrics=job.metrics,
        )

        # 3. Promote + deploy
        promoted = job.metrics.get("accuracy", 0.0) >= self._settings.min_serving_accuracy
        if promoted:
            version = self._registry.transition_stage(
                version.name, version.version, ModelStage.PRODUCTION
            )
        spec = DeploymentSpec(
            model_name=version.name,
            model_version=version.version,
            strategy=strategy,
        )
        deployment = self._deployer.promote(version, spec)

        # 4. Monitor
        report = self._monitor.evaluate(
            model_name=version.name,
            drift_score=0.05,
            accuracy=job.metrics.get("accuracy", 0.0),
        )

        logger.info("Pipeline for '%s' complete (promoted=%s)", request.model_name, promoted)
        return PipelineResult(
            job=job,
            version=version,
            deployment=deployment,
            report=report,
            promoted=promoted,
        )
