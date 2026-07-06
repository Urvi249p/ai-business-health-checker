from typing import List, Optional
from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.config.database import create_job, get_job, get_jobs_by_user
from src.services.audit_service import run_audit_background
from src.utils.auth_deps import get_current_user
from src.utils.report_access import REPORT_RETENTION_SECONDS, get_report_availability

router = APIRouter()


class AuditRequest(BaseModel):
    business_name: str = Field(..., min_length=2, description="Name of the business")
    business_type: str = Field(..., min_length=2, description="Type/industry of the business")
    location: Optional[str] = Field(None, description="City or region")
    years_in_business: Optional[int] = Field(None, description="How many years in operation")
    team_size: Optional[int] = Field(None, description="Number of employees")
    business_model: Optional[str] = Field(None, description="B2B, B2C, D2C, etc.")
    customer_type: Optional[str] = Field(None, description="Retail, Enterprise, etc.")
    monthly_revenue_range: Optional[str] = Field(None, description="e.g. ₹1L-₹5L")
    customer_sources: List[str] = Field(default=[], description="Where customers come from")
    current_marketing_channels: List[str] = Field(default=[], description="Active marketing channels")
    biggest_challenges: List[str] = Field(default=[], description="Top business challenges")
    goals: List[str] = Field(default=[], description="Business goals")
    additional_notes: Optional[str] = Field(None, description="Any extra context")


@router.post("/audit")
async def create_audit_job(
    payload: AuditRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Queue a new audit job and return the job ID immediately."""
    job_id = str(uuid4())
    business_profile = payload.model_dump()

    await create_job(job_id, business_profile, user_id=current_user["id"])
    background_tasks.add_task(run_audit_background, job_id, business_profile)

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Audit job queued successfully",
    }


@router.get("/audit/history")
async def get_audit_history(current_user: dict = Depends(get_current_user)) -> list[dict]:
    """Return the authenticated user's audit job history."""
    jobs = await get_jobs_by_user(current_user["id"])
    history = []
    for job in jobs:
        availability = get_report_availability(job)
        history.append(
            {
                "job_id": job["id"],
                "status": job["status"],
                "created_at": job["created_at"],
                "updated_at": job["updated_at"],
                "result_path": job.get("result_path"),
                "report_available": availability["report_available"],
                "report_expires_at": availability["report_expires_at"],
                "report_retention_seconds": REPORT_RETENTION_SECONDS,
            }
        )
    return history


@router.get("/audit/{job_id}/status")
async def get_audit_status(job_id: str, current_user: dict = Depends(get_current_user)) -> dict:
    """Return the current status of an audit job."""
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.get("user_id") and job["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this job")

    return {
        "job_id": job["id"],
        "status": job["status"],
        "current_agent": job.get("current_agent", 0),
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "error": job.get("error"),
    }


@router.get("/audit/{job_id}/download")
async def download_audit_report(job_id: str, current_user: dict = Depends(get_current_user)) -> FileResponse:
    """Return the generated audit report PDF once the job is complete."""
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.get("user_id") and job["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this job")

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report not ready yet. Current status: {job['status']}",
        )

    availability = get_report_availability(job)
    if not availability["report_available"]:
        raise HTTPException(status_code=404, detail="Report is no longer available for download")

    result_path = job.get("result_path")
    if not result_path or not Path(result_path).exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    return FileResponse(
        path=result_path,
        media_type="application/pdf",
        filename="audit_report.pdf",
    )
