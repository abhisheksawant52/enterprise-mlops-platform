"""Application configuration via ``pydantic-settings``.

Settings are read from environment variables (prefixed with ``MLOPS_``) or an
optional ``.env`` file. See ``.env.example`` for the full list of knobs.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the MLOps control-plane."""

    model_config = SettingsConfigDict(
        env_prefix="MLOPS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Service metadata
    app_name: str = Field(default="enterprise-mlops-platform")
    environment: str = Field(default="dev", description="Deployment environment name.")
    log_level: str = Field(default="INFO", description="Root log level.")
    log_json: bool = Field(default=True, description="Emit structured JSON logs.")

    # HTTP server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # Model registry (e.g. MLflow tracking/registry server)
    registry_uri: str = Field(
        default="http://mlflow.mlops.svc.cluster.local:5000",
        description="Base URI of the model registry / tracking server.",
    )
    registry_timeout_seconds: float = Field(default=10.0)

    # Object storage for artifacts and models
    artifact_bucket: str = Field(default="mlops-artifacts")
    model_bucket: str = Field(default="mlops-models")
    aws_region: str = Field(default="us-east-1")

    # Metadata database (RDS/Postgres) — placeholder DSN, no secrets committed.
    metadata_db_dsn: str = Field(
        default="postgresql://mlops:changeme@localhost:5432/mlops",
        description="SQLAlchemy-style DSN for the metadata database.",
    )

    # Training backend
    training_namespace: str = Field(default="mlops-training")
    training_image: str = Field(default="ghcr.io/abhisheksawant52/mlops-trainer:latest")

    # Monitoring thresholds
    drift_threshold: float = Field(
        default=0.2, description="PSI/KS drift score above which a model is flagged."
    )
    min_serving_accuracy: float = Field(default=0.85)


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""

    return Settings()
