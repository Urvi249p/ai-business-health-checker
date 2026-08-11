import asyncio
import os
from pathlib import Path

from src.agents.audit_crew.crew import AuditCrew
from src.config.database import (
    complete_job, fail_job,
    update_job_agent, update_job_status,
    get_interview_qa,
    delete_job,
    get_job_parent,
)
from src.config.settings import settings
from src.utils.logger import logger
from src.utils.pdf import convert_md_to_pdf


async def run_audit_background(
    job_id: str, 
    business_profile: dict
) -> None:
    """
    Run the audit crew pipeline in a background worker.
    Fetches interview Q&A from DB, formats it as enriched
    context, and passes everything to the crew pipeline.
    """
    try:
        logger.info(f"Audit job {job_id}: updating status to processing")
        await update_job_status(job_id, "processing")

        # Fetch interview Q&A saved during the interview phase
        qa_pairs = await get_interview_qa(job_id)

        # Format Q&A into a rich context block for agents
        enriched_context = None
        if qa_pairs:
            qa_lines = []
            qa_lines.append(
                "OWNER INTERVIEW — Additional Context"
            )
            qa_lines.append(
                "The business owner answered these targeted "
                "follow-up questions after completing the "
                "structured profile. Use these answers to "
                "ground your analysis in real facts and "
                "avoid generic recommendations."
            )
            qa_lines.append("")
            for i, pair in enumerate(qa_pairs, 1):
                qa_lines.append(
                    f"Q{i}: {pair.get('question', '')}"
                )
                qa_lines.append(
                    f"A{i}: {pair.get('answer', '')}"
                )
                qa_lines.append("")
            enriched_context = "\n".join(qa_lines)
            logger.info(
                f"Audit job {job_id}: loaded {len(qa_pairs)} "
                f"interview Q&A pairs into agent context"
            )
        else:
            logger.info(
                f"Audit job {job_id}: no interview Q&A found, "
                f"running with structured profile only"
            )

        logger.info(
            f"Audit job {job_id}: starting crew pipeline for "
            f"{business_profile.get('business_name', 'Unknown')}"
        )

        loop = asyncio.get_event_loop()
        audit_crew = AuditCrew()

        def on_agent_change(agent_role: str) -> None:
            asyncio.run_coroutine_threadsafe(
                update_job_agent(job_id, agent_role), loop
            )

        markdown_result = await loop.run_in_executor(
            None,
            audit_crew.run,
            business_profile,
            enriched_context,
            on_agent_change,
        )

        logger.info(
            f"Audit job {job_id}: crew finished, saving result"
        )
        result_path = os.path.join(
            settings.TEMP_DIR, f"{job_id}.pdf"
        )
        Path(settings.TEMP_DIR).mkdir(
            parents=True, exist_ok=True
        )
        business_name = (
            business_profile.get("business_name") or
            business_profile.get("Business Name") or
            "Business"
        ) if isinstance(business_profile, dict) else "Business"

        await asyncio.to_thread(
            convert_md_to_pdf,
            markdown_result,
            result_path,
            business_name,
            business_profile=business_profile,
        )

        await complete_job(job_id, result_path)
        logger.info(
            f"Audit job {job_id}: completed successfully"
        )

        # If this was a retry, delete the original failed job
        parent_id = await get_job_parent(job_id)
        if parent_id:
            await delete_job(parent_id)
            logger.info(
                f"Audit job {job_id}: deleted parent failed "
                f"job {parent_id} after successful retry"
            )

    except Exception as exc:
        error_message = str(exc)
        logger.error(
            f"Audit job {job_id} failed: {error_message}"
        )

        # If this was a retry job that failed, delete it
        # so the original failed job stays with its Retry button
        parent_id = await get_job_parent(job_id)
        if parent_id:
            await delete_job(job_id)
            logger.info(
                f"Audit job {job_id}: retry failed, deleted "
                f"retry job to restore original {parent_id}"
            )
        else:
            await fail_job(job_id, error_message)
