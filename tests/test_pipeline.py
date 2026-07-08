"""Unit tests for the pipeline coordinator and registry abstraction."""

from __future__ import annotations

from mlops_platform.deployment import DeploymentState, RolloutStrategy
from mlops_platform.monitoring import HealthVerdict
from mlops_platform.pipeline import MLOpsPipeline
from mlops_platform.registry import ModelRegistryClient, ModelStage, ModelVersion
from mlops_platform.training import TrainingRequest


class _StubRegistry(ModelRegistryClient):
    """Registry stub that avoids any network I/O."""

    def register_model(self, name, run_id, source_uri, metrics=None):  # type: ignore[override]
        return ModelVersion(
            name=name,
            version="1",
            run_id=run_id,
            source_uri=source_uri,
            metrics=metrics or {},
        )

    def transition_stage(self, name, version, stage):  # type: ignore[override]
        return ModelVersion(name=name, version=version, stage=stage)


def test_pipeline_runs_end_to_end() -> None:
    pipeline = MLOpsPipeline(registry=_StubRegistry())
    request = TrainingRequest(model_name="churn-model", dataset_uri="s3://data/churn.parquet")

    result = pipeline.run(request, strategy=RolloutStrategy.CANARY)

    assert result.promoted is True
    assert result.version.stage is ModelStage.PRODUCTION
    assert result.deployment.state is DeploymentState.PROGRESSING
    assert result.report.verdict is HealthVerdict.HEALTHY


def test_psi_detects_drift() -> None:
    from mlops_platform.monitoring import MonitoringCollector

    stable = MonitoringCollector.population_stability_index([0.5, 0.5], [0.5, 0.5])
    drifted = MonitoringCollector.population_stability_index([0.9, 0.1], [0.1, 0.9])
    assert stable == 0.0
    assert drifted > stable
