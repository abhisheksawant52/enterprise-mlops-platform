# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-08

### Added

- FastAPI control-plane API with `/health` and `/ready` probes and routers for
  training, deployments, and monitoring.
- Domain services: training orchestration, model registry client, deployment/
  rollout manager, drift/performance monitoring, and an end-to-end pipeline
  coordinator (train -> register -> deploy -> monitor).
- Multi-stage, non-root Dockerfile with a `/health` HEALTHCHECK.
- Terraform for core AWS MLOps infrastructure: EKS cluster, S3 model/artifact
  buckets, ECR, and an RDS PostgreSQL metadata database, with `storage` and
  `eks` modules plus `dev` and `prod` environments.
- Helm chart `mlops-platform` deploying the API on port 8000 (deployment,
  service, ingress, HPA, PDB, service account, config map, secret placeholder,
  and network policy).
- Open-source hygiene: LICENSE, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT.
- CI workflow (lint, tests, Docker build, Terraform validate, Helm lint),
  pre-commit hooks, issue/PR templates, CODEOWNERS, and Dependabot.

[0.1.0]: https://github.com/abhisheksawant52/enterprise-mlops-platform/releases/tag/v0.1.0
