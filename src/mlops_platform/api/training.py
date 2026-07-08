"""Training job submission endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..training import TrainingJob, TrainingOrchestrator, TrainingRequest

router = APIRouter(prefix="/training", tags=["training"])

_orchestrator = TrainingOrchestrator()


@router.post("/jobs", response_model=TrainingJob, status_code=status.HTTP_201_CREATED)
def submit_job(request: TrainingRequest) -> TrainingJob:
    """Submit a new training job."""

    return _orchestrator.submit(request)


@router.get("/jobs/{job_id}", response_model=TrainingJob)
def get_job(job_id: str) -> TrainingJob:
    """Fetch the state of a previously submitted training job."""

    job = _orchestrator.get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return job
