# Enterprise MLOps Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/abhisheksawant52/enterprise-mlops-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/abhisheksawant52/enterprise-mlops-platform/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg)](https://fastapi.tiangolo.com/)
[![Terraform](https://img.shields.io/badge/Terraform-1.5+-7B42BC.svg)](https://www.terraform.io/)
[![Helm](https://img.shields.io/badge/Helm-3.15+-0F1689.svg)](https://helm.sh/)

An end-to-end MLOps control-plane that coordinates the model lifecycle —
**train, register, deploy, monitor** — on Kubernetes and AWS.

## Overview

The Enterprise MLOps Platform provides a single, stateless control-plane API
that stitches the four stages of the model lifecycle into a coherent pipeline.
It submits training jobs to a batch backend, registers the resulting artifacts
in a model registry, rolls new versions out to a serving layer with canary or
blue/green strategies, and continuously evaluates drift and serving performance.

It is aimed at platform and ML engineering teams who want a vendor-neutral
backbone: each stage is an independently testable service module behind a small
interface, so the training engine, registry, and serving runtime can be swapped
without touching pipeline logic.

The repository ships the application (FastAPI), the infrastructure to run it
(Terraform for EKS, S3, ECR, and RDS), and the deployment packaging (a Helm
chart), all named and wired consistently so the whole thing reads as one system.

## Architecture

```mermaid
flowchart LR
    Client[[Client / Scheduler]] --> API[FastAPI control-plane]

    subgraph CP["Control-plane"]
        API --> PIPE[Pipeline coordinator]
        PIPE --> TRAIN[Training orchestrator]
        PIPE --> REG[Registry client]
        PIPE --> DEP[Deployment manager]
        PIPE --> MON[Monitoring collector]
    end

    TRAIN -->|submit Job| EKS[(EKS training ns)]
    TRAIN -->|artifacts| S3[(S3 model bucket)]
    REG -->|versions & stages| MLF[MLflow registry]
    REG -->|metadata| RDS[(RDS PostgreSQL)]
    DEP -->|rollout| SERVE[(EKS serving)]
    MON -->|drift & metrics| OBS[Metrics store]
```

Components:

- **Control-plane API** — FastAPI app exposing `/health`, `/ready`, and routers
  for training, deployments, and monitoring.
- **Pipeline coordinator** — runs `train -> register -> deploy -> monitor`.
- **Training orchestrator** — submits and tracks batch training jobs.
- **Registry client** — typed abstraction over an MLflow-style registry.
- **Deployment manager** — rolling / canary / blue-green serving rollouts.
- **Monitoring collector** — PSI drift and serving-accuracy evaluation.

## Features

- End-to-end pipeline coordinating training, registration, deployment, and
  monitoring in a single call.
- Model registry abstraction with lifecycle stages (Staging / Production /
  Archived) and metric attachment.
- Canary, blue/green, and rolling deployment strategies with rollback.
- Drift detection via a population-stability index plus accuracy thresholds.
- Structured JSON logging and 12-factor configuration via `pydantic-settings`.
- Production-ready packaging: multi-stage non-root Docker image, Helm chart, and
  Terraform for the underlying AWS infrastructure.

## Tech Stack

Python 3.11+ · FastAPI · Uvicorn · Pydantic v2 · pydantic-settings · httpx ·
pytest · ruff · black · Docker · Terraform (AWS) · Helm · GitHub Actions

## Getting Started

### Prerequisites

- Python 3.11 or newer
- `make` (optional, for convenience targets)
- Docker, Terraform 1.5+, and Helm 3.15+ for the infra/deployment paths

### Install

```bash
python -m venv .venv && source .venv/bin/activate
make install            # pip install -e ".[dev]"
```

### Configure

```bash
cp .env.example .env
# edit .env — all variables are prefixed with MLOPS_
```

### Run

```bash
uvicorn mlops_platform.main:app --reload --port 8000
# then:
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

### Test & lint

```bash
make test
make lint
```

## Project Structure

```
.
├── src/mlops_platform/        # FastAPI control-plane package
│   ├── main.py                # app factory + router wiring
│   ├── config.py              # pydantic-settings configuration
│   ├── logging_config.py      # structured logging
│   ├── training.py            # training job orchestration
│   ├── registry.py            # model registry client
│   ├── deployment.py          # deployment / rollout manager
│   ├── monitoring.py          # drift & performance monitoring
│   ├── pipeline.py            # end-to-end coordinator
│   └── api/                   # HTTP routers (health, training, ...)
├── tests/                     # pytest suite
├── terraform/                 # AWS infra (EKS, S3, ECR, RDS)
│   ├── modules/{eks,storage}/ # reusable modules
│   └── environments/{dev,prod}/
├── helm/mlops-platform/       # Helm chart (port 8000)
├── docs/                      # architecture, ADRs, runbooks
├── Dockerfile                 # multi-stage, non-root, HEALTHCHECK
└── .github/workflows/ci.yml   # CI pipeline
```

## Configuration

All settings are read from `MLOPS_*` environment variables (see `.env.example`).

| Variable                      | Default                                        | Description                              |
| ----------------------------- | ---------------------------------------------- | ---------------------------------------- |
| `MLOPS_ENVIRONMENT`           | `dev`                                          | Deployment environment name.             |
| `MLOPS_LOG_LEVEL`             | `INFO`                                         | Root log level.                          |
| `MLOPS_PORT`                  | `8000`                                         | HTTP listen port.                        |
| `MLOPS_REGISTRY_URI`          | `http://mlflow.mlops.svc.cluster.local:5000`   | Model registry / tracking server URI.    |
| `MLOPS_MODEL_BUCKET`          | `mlops-models`                                 | S3 bucket for model artifacts.           |
| `MLOPS_ARTIFACT_BUCKET`       | `mlops-artifacts`                              | S3 bucket for pipeline artifacts.        |
| `MLOPS_METADATA_DB_DSN`       | `postgresql://mlops:...@localhost:5432/mlops`  | Metadata database DSN (no real secrets). |
| `MLOPS_DRIFT_THRESHOLD`       | `0.2`                                          | PSI score above which drift is flagged.  |
| `MLOPS_MIN_SERVING_ACCURACY`  | `0.85`                                         | Minimum acceptable serving accuracy.     |

## Deployment

### Infrastructure (Terraform)

```bash
cd terraform
terraform init -backend-config=environments/dev/backend.hcl
terraform apply -var-file=environments/dev/dev.tfvars
```

Provisions an EKS cluster, S3 model/artifact buckets, an ECR repository, and an
RDS PostgreSQL metadata database. See [`terraform/`](terraform/) and the two
modules under [`terraform/modules/`](terraform/modules/).

### Application (Helm)

```bash
helm upgrade --install mlops helm/mlops-platform \
  --namespace mlops --create-namespace \
  --set image.tag="$GIT_SHA"
```

The chart deploys the control-plane on port 8000 with a Deployment, Service,
optional Ingress, HPA, PodDisruptionBudget, ServiceAccount, ConfigMap, Secret
placeholder, and NetworkPolicy. See the [deployment runbook](docs/runbooks/deployment.md)
and [architecture notes](docs/architecture.md).

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) and our
[Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Please report vulnerabilities as described in [SECURITY.md](SECURITY.md).

## License

Released under the [MIT License](LICENSE).
