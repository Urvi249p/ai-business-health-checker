"""Crew wrapper to run the audit workflow and return a Markdown report."""

import asyncio
from crewai import Crew
from crewai.process import Process

from src.agents.audit_crew.agents import get_agents
from src.agents.audit_crew.tasks import get_tasks
from src.config.database import update_job_agent
from src.utils.logger import logger


class AuditCrew:
    """Encapsulates the audit crew pipeline."""

    def run(self, business_profile: dict, job_id: str = None) -> str:
        """Build and execute the crew, then return the final report text."""
        agents = get_agents()
        tasks = get_tasks(agents, business_profile)

        # Attach step callback to track agent progress
        def on_task_complete(task_output):
            if job_id:
                completed_index = on_task_complete.counter
                next_index = completed_index + 1
                on_task_complete.counter += 1
                if next_index <= 4:
                    asyncio.run(update_job_agent(job_id, next_index))
                    logger.info(f"AuditCrew: agent {next_index} now active for job {job_id}")

        on_task_complete.counter = 0

        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            task_callback=on_task_complete,
        )

        logger.info("AuditCrew: kickoff started")
        # Set agent 0 as active immediately
        if job_id:
            asyncio.run(update_job_agent(job_id, 0))

        result = crew.kickoff()
        logger.info("AuditCrew: kickoff finished")

        return str(result)