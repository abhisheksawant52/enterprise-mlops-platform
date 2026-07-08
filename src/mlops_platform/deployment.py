"""Model deployment and rollout management.

Coordinates promoting a registered model version into a serving deployment,
supporting canary and blue/green rollout strategies. The actual apply step is
abstracted behind :meth:`DeploymentManager._apply` so it can target a KServe
InferenceService, a Seldon Deployment, or a plain Kubernetes Deployment.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from .config import Settings, get_settings
from .logging_config import get_logger
from .registry import ModelStage, ModelVersion

logger = get_logger(__name__)


class RolloutStrategy(str, Enum):
    """Supported rollout strategies for model serving deployments."""

    ROLLING = "rolling"
    CANARY = "canary"
    BLUE_GREEN = "blue_green"


class DeploymentState(str, Enum):
    """State of a serving deployment."""

    PENDING = "pending"
    PROGRESSING = "progressing"
    HEALTHY = "healthy"
    ROLLED_BACK = "rolled_back"


class DeploymentSpec(BaseModel):
    """Desired state for a model serving deployment."""

    model_name: str
    model_version: str
    strategy: RolloutStrategy = RolloutStrategy.CANARY
    canary_weight: int = Field(default=10, ge=0, le=100)
    replicas: int = Field(default=2, ge=1)


class Deployment(BaseModel):
    """Observed state of a model serving deployment."""

    name: str
    model_name: str
    model_version: str
    strategy: RolloutStrategy
    state: DeploymentState = DeploymentState.PENDING
    endpoint: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DeploymentManager:
    """Manages serving deployments and rollouts for registered models."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._deployments: dict[str, Deployment] = {}

    def deploy(self, spec: DeploymentSpec) -> Deployment:
        """Roll out ``spec`` and return the resulting deployment state."""

        name = f"{spec.model_name}-serving"
        endpoint = f"https://{spec.model_name}.serving.{self._settings.environment}.internal"
        logger.info(
            "Deploying %s v%s via %s strategy (replicas=%d)",
            spec.model_name,
            spec.model_version,
            spec.strategy.value,
            spec.replicas,
        )
        self._apply(spec)
        deployment = Deployment(
            name=name,
            model_name=spec.model_name,
            model_version=spec.model_version,
            strategy=spec.strategy,
            state=DeploymentState.PROGRESSING,
            endpoint=endpoint,
        )
        self._deployments[name] = deployment
        return deployment

    def promote(self, version: ModelVersion, spec: DeploymentSpec) -> Deployment:
        """Promote a model version to production and deploy it.

        Only versions already marked :attr:`ModelStage.PRODUCTION` are eligible;
        other stages are deployed as canaries regardless of requested strategy.
        """

        if version.stage is not ModelStage.PRODUCTION:
            logger.warning(
                "Version %s is stage %s; forcing canary rollout",
                version.version,
                version.stage.value,
            )
            spec = spec.model_copy(update={"strategy": RolloutStrategy.CANARY})
        return self.deploy(spec)

    def rollback(self, name: str) -> Deployment:
        """Roll a deployment back to its previous healthy revision."""

        deployment = self._deployments[name]
        deployment.state = DeploymentState.ROLLED_BACK
        deployment.updated_at = datetime.now(timezone.utc)
        logger.warning("Rolled back deployment %s", name)
        return deployment

    def get(self, name: str) -> Deployment | None:
        """Return a deployment by name, or ``None`` if unknown."""

        return self._deployments.get(name)

    def _apply(self, spec: DeploymentSpec) -> None:
        """Apply the rendered serving manifest to the cluster (abstracted)."""

        logger.debug("Applying serving manifest for %s", spec.model_name)
