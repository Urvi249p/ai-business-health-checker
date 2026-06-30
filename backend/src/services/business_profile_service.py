"""
services/business_profile_service.py — Conversion helper.

Converts a structured BusinessProfile object into a plain-text context
string that is forwarded to the existing CrewAI pipeline unchanged.
"""
from src.models.business_profile import BusinessProfile


def profile_to_context_string(profile: BusinessProfile) -> str:
    """
    Serialize a BusinessProfile into a human-readable context string.

    The output format is intentionally similar to what a user might have
    typed in the old free-text `business_description` field, so that the
    existing CrewAI agents require no modifications.

    Example output::

        Business Type: Bakery
        Years in Business: 4
        Team Size: 8
        Customer Type: B2C
        Customer Sources:
        - Walk-ins
        - Instagram

        Biggest Challenges:
        - Low repeat customers
        - Pricing

        Goals:
        - Increase Revenue

        Additional Notes:
        We make custom cakes.
    """
    lines: list[str] = [
        f"Business Type: {profile.business_type.value}",
        f"Years in Business: {profile.years_in_business}",
        f"Team Size: {profile.team_size}",
        f"Customer Type: {profile.customer_type.value}",
    ]

    # --- Customer Sources ---
    lines.append("Customer Sources:")
    for source in profile.customer_sources:
        lines.append(f"- {source}")

    lines.append("")  # blank line separator

    # --- Biggest Challenges ---
    lines.append("Biggest Challenges:")
    for challenge in profile.biggest_challenges:
        lines.append(f"- {challenge}")

    lines.append("")  # blank line separator

    # --- Goals ---
    lines.append("Goals:")
    for goal in profile.goals:
        lines.append(f"- {goal.value}")

    # --- Additional Notes (optional) ---
    if profile.additional_notes:
        lines.append("")
        lines.append("Additional Notes:")
        lines.append(profile.additional_notes)

    return "\n".join(lines)
