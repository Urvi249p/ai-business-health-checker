"""
interview_service.py — AI-powered business interview.

Generates personalized follow-up questions based on
the structured business profile from the form, then
builds an enriched profile combining form data and
interview Q&A for the audit agents.
"""

import json
from src.config.settings import settings
from src.utils.logger import logger


QUESTION_GENERATION_PROMPT = """
You are a senior business consultant preparing to
duct a deep audit of a business. The business
owner has completed a structured profile form.

BUSINESS PROFILE:
{profile_text}

Your task is to generate exactly 4 targeted follow-up
questions that will significantly improve the quality
of the audit report.

Rules:
- Only ask what is NOT already clear from the profile
- Each question must unlock a specific insight about:
  pricing depth, operational reality, customer
  psychology, competitive situation, or growth blockers
- Ask compound questions to save the owner time
e.g. "What do you charge AND how did you decide
  that price?"
- Be conversational, not clinical or robotic
- Tailor EVERY question to THIS specific business type
- Do NOT ask about goals or challenges — already captured
- Do NOT ask generic questions

Return ONLY a valid JSON array of exactly 4 strings.
Example format: ["Question 1?", "Question 2?", "Question 3?", "Question 4?"]
No explanation, no preamble, just the JSON array.
"""


PROFILE_ENRICHMENT_PROMPT = """
You are a senior business analyst. A business owner
completed a profile form AND answered follow-up
interview questions. Combine both sources into one
enriched business profile.

ORIGINAL STRUCTURED PROFILE:
{profile_text}

INTERVIEW Q&A:
{qa_text}

Extract any additional structured data from the
interview answers and add it to the profile.
Look for:
- Specific price points or revenue figures mentioned
- Competitor names mentioned
- Specific operational details
- Customer behaviour insights
- Any goals or plans mentioned

Return a valid JSON object that is the original
profile enriched with an "interview_insights" key
containing a clean summary of what was learned
from the interview, and an "interview_qa" key
containing the raw Q&A pairs.

Return ONLY valid JSON. No explanation, no preamble.
"""


def _format_profile(profile: dict) -> str:
    return "\n".join([
        f"Business Name:         {profile.get('business_name', 'N/A')}",
        f"Business Type:         {profile.get('business_type', 'N/A')}",
        f"Location:              {profile.get('location', 'N/A')}",
        f"Years in Business:     {profile.get('years_in_business', 'N/A')}",
        f"Team Size:             {profile.get('team_size', 'N/A')}",
        f"Business Model:        {profile.get('business_model', 'N/A')}",
        f"Customer Type:         {profile.get('customer_type', 'N/A')}",
        f"Monthly Revenue:       {profile.get('monthly_revenue_range', 'N/A')}",
        f"Customer Sources:      {', '.join(profile.get('customer_sources', []))}",
        f"Marketing Channels:    {', '.join(profile.get('current_marketing_channels', []))}",
        f"Biggest Challenges:    {', '.join(profile.get('biggest_challenges', []))}",
        f"Goals:                 {', '.join(profile.get('goals', []))}",
        f"Additional Notes:      {profile.get('additional_notes', 'N/A')}",
    ])


def _format_qa(qa_pairs: list[dict]) -> str:
    lines = []
    for i, pair in enumerate(qa_pairs, 1):
        lines.append(f"Q{i}: {pair.get('question', '')}")
        lines.append(f"A{i}: {pair.get('answer', '')}")
        lines.append("")
    return "\n".join(lines)


async def generate_interview_questions(business_profile: dict) -> list[str]:
    """
    Call the LLM to generate 4 personalized follow-up
    questions based on the structured business profile.
    Falls back to 4 generic questions if LLM fails.
    """
    from crewai.llm import LLM

    try:
        profile_text = _format_profile(business_profile)
        prompt = QUESTION_GENERATION_PROMPT.format(
            profile_text=profile_text
        )

        llm = LLM(
            model=settings.MODEL_NAME,
            api_key=settings.OPENAI_API_KEY
        )

        response = llm.call([{"role": "user", "content": prompt}])

        text = response.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        questions = json.loads(text)

        if isinstance(questions, list) and len(questions) >= 3:
            logger.info(f"Generated {len(questions)} interview questions")
            return questions[:4]

    except Exception as e:
        logger.error(f"Failed to generate interview questions: {e}")

    return [
        f"What does a typical working day look like for you and your team at {business_profile.get('business_name', 'your business')}?",
        f"What are your current prices for your main products or services, and how did you decide on those prices?",
        f"Who are your biggest competitors and what do you think makes customers choose you over them?",
        f"What has been your biggest win in the last 6 months and what do you think caused it?",
    ]


async def build_enriched_profile(
    business_profile: dict,
    qa_pairs: list[dict]
) -> dict:
    """
    Combine the structured business profile with
    interview Q&A to create an enriched profile
    for the audit agents.
    Falls back to appending raw Q&A if LLM fails.
    """
    from crewai.llm import LLM

    try:
        profile_text = _format_profile(business_profile)
        qa_text = _format_qa(qa_pairs)

        prompt = PROFILE_ENRICHMENT_PROMPT.format(
            profile_text=profile_text,
            qa_text=qa_text,
        )

        llm = LLM(
            model=settings.MODEL_NAME,
            api_key=settings.OPENAI_API_KEY
        )

        response = llm.call([{"role": "user", "content": prompt}])

        text = response.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        enriched = json.loads(text)

        if isinstance(enriched, dict):
            logger.info("Successfully built enriched business profile")
            return enriched

    except Exception as e:
        logger.error(f"Failed to build enriched profile: {e}")

    enriched_fallback = dict(business_profile)
    enriched_fallback["interview_qa"] = qa_pairs
    enriched_fallback["interview_insights"] = " | ".join([
        f"{pair.get('answer', '')}"
        for pair in qa_pairs
    ])
    return enriched_fallback


def format_context_for_agents(enriched_profile: dict) -> str:
    """Rich, agent-ready context combining profile + interview."""
    profile_text = _format_profile(enriched_profile)
    qa_text = _format_qa(enriched_profile.get("interview_qa", []))
    insights = enriched_profile.get("interview_insights", "No interview insights available.")

    return f"""
=== OWNER INTERVIEW + ENRICHED BUSINESS PROFILE ===

{profile_text}

INTERVIEW INSIGHTS (Critical Context):
{insights}

RAW INTERVIEW Q&A:
{qa_text if qa_text.strip() else "No Q&A provided."}

Use this owner-provided information to make your analysis highly specific and actionable. Prioritize real details from the interview over generic assumptions.
""".strip()
