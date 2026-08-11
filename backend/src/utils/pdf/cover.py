from reportlab.platypus.flowables import HRFlowable, PageBreak
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from .styles import C_SLATE, C_EMERALD, C_WHITE, C_MUTED, C_SLATE_BORDER
from .utils import _escape
from datetime import datetime, timezone

def _cover_page(business_name: str, business_profile: dict, st: dict) -> list:
    """Full-page dark cover with business name and metadata."""
    flowables = []

    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    industry = business_profile.get("business_type", "")
    location = business_profile.get("location", "")
    team     = business_profile.get("team_size", "")
    revenue  = business_profile.get("monthly_revenue_range", "")

    # Dark full-page cover table
    meta_parts = []
    if industry: meta_parts.append(industry)
    if location:  meta_parts.append(location)
    meta_line = "  ·  ".join(meta_parts) if meta_parts else ""

    years = business_profile.get("years_in_business", "")
    detail_parts = []
    if years:   detail_parts.append(f"Est. {years} years")
    if team:    detail_parts.append(f"Team: {team}")
    if revenue: detail_parts.append(f"Revenue: {revenue}")
    detail_line = "  ·  ".join(detail_parts) if detail_parts else ""

    cover_content = [
        # Top emerald rule
        [HRFlowable(width="100%", thickness=4, color=C_EMERALD,
            spaceBefore=0, spaceAfter=28)],
        [Paragraph("BUSINESS AUDIT &amp; STRATEGY REPORT",
            ParagraphStyle("CE", fontName="Helvetica-Bold", fontSize=9,
                leading=12, textColor=C_EMERALD, tracking=120))],
        [Spacer(1, 16)],
        [Paragraph(_escape(business_name),
            ParagraphStyle("CT", fontName="Helvetica-Bold", fontSize=32,
                leading=40, textColor=C_SLATE))],
        [Spacer(1, 8)],
        *([Paragraph(_escape(meta_line),
            ParagraphStyle("CM", fontName="Helvetica", fontSize=13,
                leading=18, textColor=C_MUTED))]
          if meta_line else []),
    ]

    if detail_line:
        cover_content.append([Spacer(1, 4)])
        cover_content.append([Paragraph(_escape(detail_line),
            ParagraphStyle("CD", fontName="Helvetica", fontSize=11,
                leading=15, textColor=C_MUTED))])

    cover_content += [
        [Spacer(1, 32)],
        [HRFlowable(width="100%", thickness=0.5, color=C_SLATE_BORDER,
            spaceBefore=0, spaceAfter=20)],
        [Paragraph(f"Prepared by Auditly AI  ·  {today}",
            ParagraphStyle("CF", fontName="Helvetica", fontSize=9,
                leading=12, textColor=C_MUTED))],
        [Paragraph("5-Agent Business Analysis System",
            ParagraphStyle("CF2", fontName="Helvetica", fontSize=9,
                leading=12, textColor=C_MUTED))],
    ]

    for item in cover_content:
        flowables.extend(item)

    flowables.append(PageBreak())
    return flowables


__all__ = ['_cover_page']
