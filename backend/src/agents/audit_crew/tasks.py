"""CrewAI task definitions for the audit workflow."""

from crewai import Task


def get_tasks(agents: list, business_profile: dict, enriched_context: str = None) -> list[Task]:
    """Return the five ordered tasks for the audit crew with rich interview context."""

    profile_text = f"""
    Business Name:          {business_profile.get('business_name', 'N/A')}
    Business Type:          {business_profile.get('business_type', 'N/A')}
    Location:               {business_profile.get('location', 'N/A')}
    Years in Business:      {business_profile.get('years_in_business', 'N/A')}
    Team Size:              {business_profile.get('team_size', 'N/A')}
    Business Model:         {business_profile.get('business_model', 'N/A')}
    Customer Type:          {business_profile.get('customer_type', 'N/A')}
    Monthly Revenue Range:  {business_profile.get('monthly_revenue_range', 'N/A')}
    Customer Sources:       {', '.join(business_profile.get('customer_sources', []))}
    Marketing Channels:     {', '.join(business_profile.get('current_marketing_channels', []))}
    Biggest Challenges:     {', '.join(business_profile.get('biggest_challenges', []))}
    Goals:                  {', '.join(business_profile.get('goals', []))}
    Additional Notes:       {business_profile.get('additional_notes', 'N/A')}
    """

    context_block = f"\n\n{enriched_context}" if enriched_context else ""

    task1 = Task(
        agent=agents[0],
        description=f"""
            Analyze the following structured business profile and owner interview responses.
            {context_block}

            BUSINESS PROFILE:
            {profile_text}

            Analyze and document:
            - Core business model and industry positioning
            - Products or services offered and their value proposition
            - Target customer segment and how they are currently reached
            - Revenue model and financial health indicators
            - Geographic presence and market scope
            - Team capacity relative to business size
            - Key operational strengths based on the facts provided
            - Current challenges the owner has identified
            - Alignment between stated goals and current operations
            - Any interview insights that clearly add depth to the business picture
        """,
        expected_output=(
            "A structured business analysis covering all dimensions in clear sections, "
            "grounded entirely in the provided profile data and interview context."
        ),
    )

    task2 = Task(
        agent=agents[1],
        description=f"""
            Using the business analysis from Task 1 and the original business profile below,
            produce a comprehensive SWOT analysis grounded in facts — not generic statements.
            {context_block}

            BUSINESS PROFILE:
            {profile_text}

            For each quadrant provide at least 4 specific, evidence-based points:

            - Strengths: internal advantages this business demonstrably has
              (e.g. if team_size is small and years_in_business is high → lean, experienced operation)
            - Weaknesses: internal limitations evident from the profile
              (e.g. if customer_sources is only walk-ins → limited digital reach)
            - Opportunities: external trends or gaps this business can realistically exploit
              given its location, business model, and goals
            - Threats: external risks relevant to this business type, location, and market

            Every point must be specific to THIS business. No generic filler.
            Use interview details where they materially strengthen the assessment.
        """,
        expected_output=(
            "A detailed SWOT analysis with at least 4 specific, evidence-based points "
            "per quadrant in Markdown format."
        ),
        context=[task1],
    )

    task3 = Task(
        agent=agents[2],
        description=f"""
            Based on the business profile, SWOT analysis, and owner interview context,
            recommend the optimal pricing strategy for this business.
            {context_block}

            BUSINESS PROFILE:
            {profile_text}

            Your recommendations must account for:
            1. The business model ({business_profile.get('business_model', 'N/A')})
               and customer type ({business_profile.get('customer_type', 'N/A')})
            2. The monthly revenue range ({business_profile.get('monthly_revenue_range', 'N/A')})
               to ensure pricing is realistic
            3. The identified challenges: {', '.join(business_profile.get('biggest_challenges', []))}
            4. The stated goals: {', '.join(business_profile.get('goals', []))}

            Provide:
            - Recommended pricing model with clear justification
            - Specific price points or ranges where possible
            - Quick pricing wins the business can implement immediately
            - Pricing mistakes to avoid given their situation
            - How the interview context changes or supports the pricing recommendation
        """,
        expected_output=(
            "A pricing strategy recommendation with model choice, suggested price points, "
            "justification, and immediate action steps."
        ),
        context=[task1, task2],
    )

    task4 = Task(
        agent=agents[3],
        description=f"""
            Create a practical, realistic 90-day growth action plan for this business.
            Every action must be grounded in the actual business situation — not generic advice.
            {context_block}

            BUSINESS PROFILE:
            {profile_text}

            Structure the plan as 3 phases:

            Phase 1 — Days 1–30: Quick wins and foundation
            (Focus on the biggest challenges: {', '.join(business_profile.get('biggest_challenges', []))})

            Phase 2 — Days 31–60: Growth experiments
            (Leverage existing channels: {', '.join(business_profile.get('customer_sources', []))})

            Phase 3 — Days 61–90: Scale and measure
            (Work toward goals: {', '.join(business_profile.get('goals', []))})

            For each phase provide:
            - 3 to 5 specific actions with clear owners (founder, marketing, sales, etc.)
            - Success metrics for each action
            - Expected outcome by end of phase

            Be realistic given team size of {business_profile.get('team_size', 'N/A')} people.
            Make the plan reflect real interview details whenever available.
        """,
        expected_output=(
            "A 90-day growth action plan with specific actions, owners, metrics, "
            "and expected outcomes for each phase — tailored to this exact business."
        ),
        context=[task1, task2, task3],
    )

    task5 = Task(
        agent=agents[4],
        description=f"""
            Assemble a complete professional business audit report in Markdown format
            using the outputs from all previous tasks.
            {context_block}

            Use this exact structure:

            # Business Audit & Strategy Report
            ### {{Business Name}} — Confidential

            ## Executive Summary
            (3-4 sentence overview of the business and the most important findings)

            ## Business Profile & Analysis
            (from Task 1 output — structured and well formatted)

            ## SWOT Analysis
            (from Task 2 output — use a clean table or well-structured sections)

            ## Pricing Strategy
            (from Task 3 output)

            ## 90-Day Growth Action Plan
            (from Task 4 output — use a clear phase-by-phase structure)

            ## Key Recommendations
            (top 5 most important actions the business should take, prioritized by impact)

            ---
            *Report generated by Business Audit AI*

            Make it professional, well-formatted, and ready to present to a business owner.
            Use proper Markdown: ## headers, **bold** for emphasis, bullet points and tables.
            The report should feel like it was written by a senior consultant, not generated by AI.
            IMPORTANT: Incorporate specific insights from the owner interview provided in the context.
            Make recommendations feel personalized and grounded in real owner feedback.
        """,
        expected_output=(
            "A complete, professional business audit report in Markdown format "
            "covering all sections with consistent formatting throughout."
        ),
        context=[task1, task2, task3, task4],
    )

    return [task1, task2, task3, task4, task5]