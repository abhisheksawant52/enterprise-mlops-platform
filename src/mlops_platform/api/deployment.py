"""Model deployment endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..deployment import Deployment, DeploymentManager, DeploymentSpec

router = APIRouter(prefix="/deployments", tags=["deployments"])

_manager = DeploymentManager()


@router.post("", response_model=Deployment, status_code=status.HTTP_201_CREATED)
def create_deployment(spec: DeploymentSpec) -> Deployment:
    """Roll out a serving deployment for a registered model version."""

    return _manager.deploy(spec)


@router.post("/{name}/rollback", response_model=Deployment)
def rollback_deployment(name: str) -> Deployment:
    """Roll a deployment back to its previous healthy revision."""

    if _manager.get(name) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="deployment not found")
    return _manager.rollback(name)
