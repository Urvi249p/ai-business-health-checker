from crewai import Agent
from crewai.llm import LLM

from src.config.settings import settings


def _create_llm() -> LLM:
    """Create the LLM instance used by all audit agents."""
    return LLM(model=settings.MODEL_NAME, api_key=settings.OPENAI_API_KEY)


def get_agents() -> list[Agent]:
    """Return the five audit agents used by the CrewAI pipeline."""
    llm = _create_llm()

    return [
        Agent(
            role="Business Analyst",
            goal="Extract and structure key business information from the structured profile provided",
            backstory=(
                "You are an expert business analyst with 15 years of experience analyzing "
                "businesses across industries. You identify core business model, target market, "
                "revenue streams, and operational strengths from structured business data."
            ),
            llm=llm,
            tools=[],
            verbose=True,
        ),
        Agent(
            role="Strategic SWOT Analyst",
            goal="Produce a detailed SWOT analysis based on the structured business profile",
            backstory=(
                "You are a strategic consultant who has conducted SWOT analyses for hundreds "
                "of businesses. You identify non-obvious strengths, realistic weaknesses, "
                "genuine market opportunities, and credible threats directly from business facts."
            ),
            llm=llm,
            tools=[],
            verbose=True,
        ),
        Agent(
            role="Pricing Strategy Consultant",
            goal="Recommend the optimal pricing model and strategy for the business",
            backstory=(
                "You are a pricing expert who has helped startups and SMEs find their ideal "
                "pricing strategy. You consider perceived value, customer segments, business "
                "goals, and industry norms to recommend actionable pricing approaches."
            ),
            llm=llm,
            tools=[],
            verbose=True,
        ),
        Agent(
            role="Growth Strategy Consultant",
            goal="Create a detailed 90-day action plan to grow the business",
            backstory=(
                "You are a growth strategist who specializes in practical, executable growth "
                "plans for small and medium businesses. You focus on quick wins, measurable "
                "milestones, and realistic timelines tailored to the business's actual situation."
            ),
            llm=llm,
            tools=[],
            verbose=True,
        ),
        Agent(
            role="Business Report Writer",
            goal=(
                "Assemble all research and analysis into a professional, well-structured "
                "business audit report in Markdown"
            ),
            backstory=(
                "You are a professional business report writer who transforms raw analysis "
                "into polished, executive-ready reports. You write clearly, use proper "
                "Markdown formatting with headers and sections, and make complex insights "
                "easy to understand for business owners."
            ),
            llm=llm,
            tools=[],
            verbose=True,
        ),
    ]