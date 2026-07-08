# ADR-0001: Control-plane on EKS with an MLflow-style registry

- Status: Accepted
- Date: 2026-07-08

## Context

We need an end-to-end MLOps platform that orchestrates training, model
registration, deployment, and monitoring, while remaining vendor-neutral enough
to swap individual backends (training engine, registry, serving runtime).

## Decision

- Run a stateless FastAPI **control-plane** on **Amazon EKS**, deployed via Helm.
- Persist model artifacts in **S3**, container images in **ECR**, and
  experiment/registry metadata in **RDS PostgreSQL**.
- Abstract the model registry behind `ModelRegistryClient` so an MLflow tracking
  server (the default) can be replaced without touching pipeline code.
- Represent each lifecycle stage as an independent service module coordinated by
  `MLOpsPipeline`, keeping stages independently testable.

## Consequences

- The control-plane holds no durable state, so it scales horizontally and is
  safe to redeploy at any time.
- Backend swaps (training engine, serving runtime) are localised to a single
  module and its interface.
- Infrastructure is reproducible through Terraform modules with per-environment
  variable and backend files.
