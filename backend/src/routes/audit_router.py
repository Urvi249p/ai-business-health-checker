from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse

from src.config.database import create_job, get_job, get_jobs_by_user
from src.models.business_profile import BusinessProfile
from src.services.audit_service import run_audit_background
from src.services.business_profile_service import profile_to_context_string
from src.utils.auth_deps import get_current_user

router = APIRouter()


@router.post("/audit")
async def create_audit_job(
    payload: BusinessProfile,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Queue a new audit job and return the job ID immediately.

    Accepts a structured **BusinessProfile** body. The profile is converted
    to a formatted context string internally before being forwarded to the
    existing CrewAI pipeline — no agent changes required.
    """
    job_id = str(uuid4())

    # Convert the structured profile to a plain-text context string so the
    # existing CrewAI pipeline and database layer need no modifications.
    business_context = profile_to_context_string(payload)

    await create_job(job_id, business_context, user_id=current_user["id"])
    background_tasks.add_task(run_audit_background, job_id, business_context)

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Audit job queued successfully",
    }


@router.get("/audit/history")
async def get_audit_history(current_user: dict = Depends(get_current_user)) -> list[dict]:
    """Return the authenticated user's audit job history."""
    jobs = await get_jobs_by_user(current_user["id"])
    return [
        {
            "job_id": job["id"],
            "status": job["status"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
        }
        for job in jobs
    ]


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

    result_path = job.get("result_path")
    if not result_path or not Path(result_path).exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    return FileResponse(
        path=result_path,
        media_type="application/pdf",
        filename="audit_report.pdf",
    )
