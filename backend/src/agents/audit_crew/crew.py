"""Crew wrapper to run the audit workflow and return a Markdown report."""

from crewai import Crew
from crewai.process import Process

from src.agents.audit_crew.agents import get_agents
from src.agents.audit_crew.tasks import get_tasks
from src.utils.logger import logger


class AuditCrew:
    """Encapsulates the audit crew pipeline."""

    def run(self, business_profile: dict, enriched_context: str = None, on_agent_change=None) -> str:
        """Build and execute the crew with enriched interview context."""
        agents = get_agents()
        tasks = get_tasks(agents, business_profile, enriched_context)  # ← updated call

        if on_agent_change and tasks:
            on_agent_change(tasks[0].agent.role)

        def on_task_complete(task_output):
            completed_index = on_task_complete.counter
            next_index = completed_index + 1
            on_task_complete.counter += 1
            if next_index < len(tasks) and on_agent_change:
                on_agent_change(tasks[next_index].agent.role)

        on_task_complete.counter = 0

        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            task_callback=on_task_complete,
        )

        logger.info("AuditCrew: kickoff started with enriched context")
        result = crew.kickoff()
        logger.info("AuditCrew: kickoff finished")
        return str(result)