"""Crew wrapper to run the audit workflow and return a Markdown report."""

from crewai import Crew
from crewai.process import Process

from src.agents.audit_crew.agents import get_agents
from src.agents.audit_crew.tasks import get_tasks
from src.utils.logger import logger


class AuditCrew:
    """Encapsulates the audit crew pipeline."""

    def run(self, business_description: str) -> str:
        """Build and execute the crew, then return the final report text."""
        agents = get_agents()
        tasks = get_tasks(agents, business_description)

        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

        logger.info("AuditCrew: kickoff started")
        result = crew.kickoff()
        logger.info("AuditCrew: kickoff finished")

        return str(result)
