import asyncio
import os
from pathlib import Path

from src.agents.audit_crew.crew import AuditCrew
from src.config.database import complete_job, fail_job, update_job_status
from src.config.settings import settings
from src.utils.logger import logger
from src.utils.pdf import convert_md_to_pdf


async def run_audit_background(job_id: str, business_description: str) -> None:
    """Run the audit crew pipeline in a background worker and persist the result."""
    try:
        logger.info(f"Audit job {job_id}: updating status to processing")
        await update_job_status(job_id, "processing")

        logger.info(f"Audit job {job_id}: starting crew pipeline")
        loop = asyncio.get_event_loop()
        audit_crew = AuditCrew()
        markdown_result = await loop.run_in_executor(
            None, audit_crew.run, business_description
        )

        logger.info(f"Audit job {job_id}: crew finished, saving result")
        result_path = os.path.join(settings.TEMP_DIR, f"{job_id}.pdf")
        Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(convert_md_to_pdf, markdown_result, result_path)

        await complete_job(job_id, result_path)
        logger.info(f"Audit job {job_id}: completed successfully")
    except Exception as exc:
        error_message = str(exc)
        logger.error(f"Audit job {job_id} failed: {error_message}")
        await fail_job(job_id, error_message)
