# Deployment Runbook

This runbook describes how to deploy and operate the MLOps control-plane.

## Prerequisites

- `kubectl` configured against the target EKS cluster.
- `helm` 3.15+.
- `terraform` 1.5+ with AWS credentials for the target account.
- The container image published to `ghcr.io/abhisheksawant52/enterprise-mlops-platform`.

## 1. Provision infrastructure

```bash
cd terraform
terraform init -backend-config=environments/dev/backend.hcl
terraform plan  -var-file=environments/dev/dev.tfvars
terraform apply -var-file=environments/dev/dev.tfvars
```

The metadata database password must be supplied out-of-band:

```bash
export TF_VAR_metadata_db_password="$(aws secretsmanager get-secret-value ...)"
```

## 2. Deploy the control-plane

```bash
helm upgrade --install mlops helm/mlops-platform \
  --namespace mlops --create-namespace \
  --set image.tag="$GIT_SHA"
```

## 3. Verify

```bash
kubectl -n mlops rollout status deployment/mlops-mlops-platform
kubectl -n mlops port-forward svc/mlops-mlops-platform 8000:8000 &
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/ready
```

## 4. Rollback

```bash
helm rollback mlops
```

For a model-level rollback of a serving deployment, call the API:

```bash
curl -X POST http://127.0.0.1:8000/deployments/<name>/rollback
```

## Monitoring & alerts

- Drift is flagged when the PSI score exceeds `MLOPS_DRIFT_THRESHOLD` (default 0.2).
- Serving accuracy below `MLOPS_MIN_SERVING_ACCURACY` (default 0.85) marks a
  deployment `degraded`. Investigate the upstream training data and re-run the
  pipeline.
