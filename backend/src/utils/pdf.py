"""
pdf.py — Auditly Business Audit Report PDF Generator

Design system: Slate & Emerald
  - Deep Slate headings (#1E293B)
  - Emerald Green accents (#059669)
  - Clean white background
  - Full-page cover with business name and date
  - Color-coded SWOT 2x2 grid
  - Phase cards for 90-day plan
  - 90-Day timeline chart
  - SWOT radar chart
  - Numbered recommendation cards
"""

import io
import os
import re
import math
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle, Image,
)

PAGE_W, PAGE_H = A4
MARGIN_L = 50
MARGIN_R = 50
MARGIN_T = 50
MARGIN_B = 55
USABLE_W = PAGE_W - MARGIN_L - MARGIN_R

# ── Slate & Emerald Colour Palette ───────────────────────────────────────────
C_SLATE        = HexColor("#1E293B")   # primary headings
C_SLATE_MID    = HexColor("#475569")   # section rules / subheadings
C_SLATE_LIGHT  = HexColor("#F1F5F9")   # card backgrounds
C_SLATE_BORDER = HexColor("#CBD5E1")   # borders

C_EMERALD      = HexColor("#059669")   # primary accent
C_EMERALD_LIGHT= HexColor("#D1FAE5")   # emerald tint backgrounds
C_EMERALD_MID  = HexColor("#A7F3D0")   # emerald borders

C_GREEN        = HexColor("#059669")   # strengths
C_GREEN_LIGHT  = HexColor("#D1FAE5")
C_AMBER        = HexColor("#D97706")   # weaknesses
C_AMBER_LIGHT  = HexColor("#FEF3C7")
C_TEAL         = HexColor("#0891B2")   # opportunities
C_TEAL_LIGHT   = HexColor("#CFFAFE")
C_ROSE         = HexColor("#E11D48")   # threats
C_ROSE_LIGHT   = HexColor("#FFE4E6")

C_BODY         = HexColor("#334155")   # body text
C_MUTED        = HexColor("#64748B")   # muted / secondary text
C_WHITE        = colors.white
C_ROW_ALT      = HexColor("#F8FAFC")   # table alt rows

# Phase colors for 90-day plan
_PHASE_COLORS  = [C_EMERALD, HexColor("#0891B2"), HexColor("#7C3AED")]
_PHASE_LIGHTS  = [C_EMERALD_LIGHT, C_TEAL_LIGHT, HexColor("#EDE9FE")]


# ── Markdown Cleaner ─────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    # Step 1: Strip AI page headers
    text = re.sub(
        r"Auditly\s*[\u2014\-\u2013]\s*Business Audit Report\s+Page\s+\d+[^\n]*",
        "", text, flags=re.IGNORECASE)
    text = re.sub(
        r"Business Audit Report\s+Page\s+\d+[^\n]*",
        "", text, flags=re.IGNORECASE)
    text = re.sub(r"Auditly\s+Page\s+\d+", "", text, flags=re.IGNORECASE)

    # Step 2: Remove duplicate cover lines
    text = re.sub(r"^BUSINESS AUDIT\s*&\s*STRATEGY REPORT\s*$",
        "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^Business Audit\s*&\s*Strategy Report\s*$",
        "", text, flags=re.MULTILINE)
    text = re.sub(r"^-+\s*CONFIDENTIAL\s*-+$",
        "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^CONFIDENTIAL$", "", text, flags=re.MULTILINE)

    # Step 3: Currency BEFORE removing ■ globally
    text = re.sub(r"[\u25a0■]\s*(\d)", r"Rs. \1", text)
    text = re.sub(r"₹\s*(\d)", r"Rs. \1", text)

    # Step 4: Numbered list artifacts
    text = re.sub(r"^(\d+)[\u25a0■]+\s*", r"\1. ", text, flags=re.MULTILINE)

    # Step 5: Word-hyphen artifacts
    text = re.sub(r"(\w)[\u25a0■](\w)", r"\1-\2", text)

    # Step 6: Remaining Unicode artifacts
    text = text.replace("\u25a0", "-").replace("■", "-")
    text = text.replace("\u2013", "\u2013").replace("\u2014", "\u2014")
    text = text.replace("\u2022", "\u2022").replace("\u00b7", "-")
    text = text.replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u00e2\u0080\u0099", "'")
    text = text.replace("\u00e2\u0080\u009c", '"')
    text = text.replace("\ufffd", "-")

    # Step 7: HTML tags
    text = re.sub(r"\s*<br\s*/?>\s*", " | ", text, flags=re.IGNORECASE)
    text = re.sub(r"<(?!/?b\b)[^>]+>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<b>(.*?)</b>", r"**\1**", text,
        flags=re.IGNORECASE | re.DOTALL)

    # Step 8: Escaped asterisks
    text = re.sub(r"\\\*", "*", text)

    # Step 9: H4 → H3
    text = re.sub(r"^####\s+", "### ", text, flags=re.MULTILINE)

    # Step 10: Excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fmt(text: str) -> str:
    text = _clean(text)
    parts = re.split(r"(\*\*.+?\*\*)", text, flags=re.DOTALL)
    out = []
    for p in parts:
        if p.startswith("**") and p.endswith("**"):
            out.append("<b>" + _escape(p[2:-2]) + "</b>")
        else:
            out.append(_escape(p))
    return "".join(out)


# ── Styles ───────────────────────────────────────────────────────────────────

def _build_styles() -> dict:
    return {
        "cover_eyebrow": ParagraphStyle("CoverEyebrow",
            fontName="Helvetica-Bold", fontSize=9, leading=12,
            textColor=C_EMERALD, spaceAfter=12, tracking=120),
        "cover_title": ParagraphStyle("CoverTitle",
            fontName="Helvetica-Bold", fontSize=34, leading=42,
            textColor=C_WHITE, spaceAfter=16),
        "cover_sub": ParagraphStyle("CoverSub",
            fontName="Helvetica", fontSize=13, leading=18,
            textColor=HexColor("#CBD5E1"), spaceAfter=8),
        "cover_meta": ParagraphStyle("CoverMeta",
            fontName="Helvetica", fontSize=10, leading=14,
            textColor=HexColor("#94A3B8"), spaceAfter=4),
        "cover_footer": ParagraphStyle("CoverFooter",
            fontName="Helvetica", fontSize=9, leading=12,
            textColor=HexColor("#64748B"), spaceAfter=0),

        "h1": ParagraphStyle("H1",
            fontName="Helvetica-Bold", fontSize=18, leading=24,
            textColor=C_SLATE, spaceBefore=20, spaceAfter=6),
        "h2": ParagraphStyle("H2",
            fontName="Helvetica-Bold", fontSize=13, leading=18,
            textColor=C_SLATE, spaceBefore=16, spaceAfter=4),
        "h3": ParagraphStyle("H3",
            fontName="Helvetica-Bold", fontSize=11, leading=15,
            textColor=C_EMERALD, spaceBefore=10, spaceAfter=3),

        "body": ParagraphStyle("Body",
            fontName="Helvetica", fontSize=10, leading=16,
            textColor=C_BODY, spaceAfter=5),
        "body_muted": ParagraphStyle("BodyMuted",
            fontName="Helvetica", fontSize=9, leading=14,
            textColor=C_MUTED, spaceAfter=4),

        "bullet": ParagraphStyle("Bullet",
            fontName="Helvetica", fontSize=10, leading=15,
            textColor=C_BODY, leftIndent=16, spaceAfter=3),

        "executive": ParagraphStyle("Executive",
            fontName="Helvetica", fontSize=11, leading=18,
            textColor=C_SLATE, spaceAfter=6,
            leftIndent=16, rightIndent=16),

        "th": ParagraphStyle("TH",
            fontName="Helvetica-Bold", fontSize=9, leading=13,
            textColor=C_WHITE, alignment=TA_LEFT),
        "td": ParagraphStyle("TD",
            fontName="Helvetica", fontSize=9, leading=13,
            textColor=C_BODY, alignment=TA_LEFT),
        "td_muted": ParagraphStyle("TDMuted",
            fontName="Helvetica", fontSize=8, leading=12,
            textColor=C_MUTED, alignment=TA_LEFT),

        "rec_title": ParagraphStyle("RecTitle",
            fontName="Helvetica-Bold", fontSize=10, leading=14,
            textColor=C_SLATE, spaceAfter=2),
        "rec_body": ParagraphStyle("RecBody",
            fontName="Helvetica", fontSize=9, leading=13,
            textColor=C_MUTED, spaceAfter=0),

        "phase_title": ParagraphStyle("PhaseTitle",
            fontName="Helvetica-Bold", fontSize=10, leading=14,
            textColor=C_WHITE),
    }


# ── Cover Page ───────────────────────────────────────────────────────────────

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
    meta_line = "  ·  ".join(meta_parts) if meta_parts else "Business Audit"

    detail_parts = []
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
        [Paragraph(_escape(meta_line),
            ParagraphStyle("CM", fontName="Helvetica", fontSize=13,
                leading=18, textColor=C_MUTED))],
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


# ── Section Header ────────────────────────────────────────────────────────────

def _section_header(title: str, st: dict) -> list:
    return [
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=2, color=C_EMERALD,
            spaceBefore=0, spaceAfter=6),
        Paragraph(_fmt(title), st["h1"]),
        Spacer(1, 4),
    ]


# ── Executive Summary Box ─────────────────────────────────────────────────────

def _executive_box(text: str, st: dict) -> list:
    data = [[Paragraph(_fmt(text), st["executive"])]]
    tbl = Table(data, colWidths=[USABLE_W])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), C_EMERALD_LIGHT),
        ("LINEBEFORE",    (0,0), (0,-1),  4, C_EMERALD),
        ("TOPPADDING",    (0,0), (-1,-1), 14),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("LEFTPADDING",   (0,0), (-1,-1), 16),
        ("RIGHTPADDING",  (0,0), (-1,-1), 16),
        ("BOX",           (0,0), (-1,-1), 0.5, C_EMERALD_MID),
    ]))
    return [tbl, Spacer(1, 12)]


# ── Tables ───────────────────────────────────────────────────────────────────

def _is_md_sep(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and bool(re.match(r"^[\|\s\-:]+$", s))


def _parse_md_row(line: str) -> list:
    line = line.strip().strip("|")
    return [_clean(c.strip()) for c in line.split("|")]


def _build_table(rows: list, st: dict) -> Table:
    col_count = max(len(r) for r in rows)
    col_w = USABLE_W / col_count

    data = []
    for idx, row in enumerate(rows):
        while len(row) < col_count:
            row.append("")
        sty = st["th"] if idx == 0 else st["td"]
        data.append([Paragraph(_fmt(c), sty) for c in row])

    alt = [("BACKGROUND", (0,idx), (-1,idx), C_ROW_ALT)
           for idx in range(2, len(data), 2)]

    tbl = Table(data, colWidths=[col_w]*col_count, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  C_SLATE),
        ("TEXTCOLOR",     (0,0), (-1,0),  C_WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("LINEBELOW",     (0,0), (-1,0),  2, C_EMERALD),
        ("GRID",          (0,0), (-1,-1), 0.4, C_SLATE_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        *alt,
    ]))
    return tbl


def _swot_table(rows: list, st: dict) -> list:
    """Detect SWOT table and render as color-coded 2x2 grid."""
    if not rows or len(rows) < 2:
        return [_build_table(rows, st), Spacer(1,10)]

    header = [c.lower() for c in rows[0]]
    swot_keys = ["strengths", "weaknesses", "opportunities", "threats"]
    is_swot = any(any(k in h for k in swot_keys) for h in header)

    if not is_swot:
        return [_build_table(rows, st), Spacer(1,10)]

    # Map columns to SWOT quadrants
    swot_map = {
        "strengths":     (C_GREEN,  C_GREEN_LIGHT,  "S"),
        "weaknesses":    (C_AMBER,  C_AMBER_LIGHT,  "W"),
        "opportunities": (C_TEAL,   C_TEAL_LIGHT,   "O"),
        "threats":       (C_ROSE,   C_ROSE_LIGHT,   "T"),
    }

    col_w = USABLE_W / 2
    quadrants = []
    for h in header:
        for key, (accent, bg, letter) in swot_map.items():
            if key in h:
                quadrants.append((h.title(), accent, bg, letter))
                break
        else:
            quadrants.append((h.title(), C_SLATE_MID, C_SLATE_LIGHT, "?"))

    # Collect cell content from all data rows
    contents = ["" for _ in header]
    for row in rows[1:]:
        for ci, cell in enumerate(row):
            if ci < len(contents):
                contents[ci] += (" " if contents[ci] else "") + cell.strip()

    # Build 2x2 grid — pair up quadrants
    def make_cell(idx):
        if idx >= len(quadrants):
            return Paragraph("", st["td"])
        label, accent, bg, letter = quadrants[idx]
        content = contents[idx] if idx < len(contents) else ""
        header_para = Paragraph(
            f"<font color='white'><b>{_escape(label)}</b></font>",
            ParagraphStyle("SWOTHead", fontName="Helvetica-Bold",
                fontSize=9, leading=12, textColor=C_WHITE))
        body_para = Paragraph(_fmt(content),
            ParagraphStyle("SWOTBody", fontName="Helvetica",
                fontSize=8, leading=12, textColor=C_BODY))
        inner = Table(
            [[header_para], [Spacer(1,4)], [body_para]],
            colWidths=[col_w - 20])
        inner.setStyle(TableStyle([
            ("TOPPADDING",    (0,0),(-1,-1), 0),
            ("BOTTOMPADDING", (0,0),(-1,-1), 0),
            ("LEFTPADDING",   (0,0),(-1,-1), 0),
            ("RIGHTPADDING",  (0,0),(-1,-1), 0),
        ]))
        outer = Table([[inner]], colWidths=[col_w - 4])
        outer.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), bg),
            ("LINEBEFORE",    (0,0),(0,-1),  4, accent),
            ("BOX",           (0,0),(-1,-1), 0.5, accent),
            ("TOPPADDING",    (0,0),(-1,-1), 10),
            ("BOTTOMPADDING", (0,0),(-1,-1), 10),
            ("LEFTPADDING",   (0,0),(-1,-1), 12),
            ("RIGHTPADDING",  (0,0),(-1,-1), 10),
        ]))
        return outer

    pairs = []
    for i in range(0, len(quadrants), 2):
        left  = make_cell(i)
        right = make_cell(i+1) if i+1 < len(quadrants) else Paragraph("", st["td"])
        pairs.append([left, right])

    grid = Table(pairs, colWidths=[col_w, col_w],
        hAlign="LEFT", vAlign="TOP")
    grid.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 2),
        ("RIGHTPADDING",  (0,0),(-1,-1), 2),
    ]))
    return [grid, Spacer(1, 12)]


# ── Phase Card ───────────────────────────────────────────────────────────────

def _phase_header(title: str, phase_idx: int, st: dict) -> list:
    color = _PHASE_COLORS[phase_idx % 3]
    data = [[Paragraph(
        f"<font color='white'><b>{_escape(title)}</b></font>",
        st["phase_title"])]]
    tbl = Table(data, colWidths=[USABLE_W])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), color),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 16),
        ("RIGHTPADDING",  (0,0),(-1,-1), 16),
    ]))
    return [tbl, Spacer(1,4)]


# ── Recommendation Card ───────────────────────────────────────────────────────

def _recommendation_block(num: int, title: str, body: str, st: dict) -> list:
    num_cell = Paragraph(
        f"<font color='white'><b>{num}</b></font>",
        ParagraphStyle("RN", fontName="Helvetica-Bold", fontSize=12,
            leading=15, textColor=C_WHITE, alignment=TA_CENTER))

    title_p = Paragraph(f"<b>{_escape(title)}</b>", st["rec_title"])
    body_p  = Paragraph(_escape(body), st["rec_body"]) if body else Spacer(1,0)

    inner = Table([[title_p],[body_p]], colWidths=[USABLE_W - 52])
    inner.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 0),
        ("BOTTOMPADDING", (0,0),(-1,-1), 0),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ]))

    outer = Table([[num_cell, inner]], colWidths=[40, USABLE_W-52])
    outer.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,0),   C_EMERALD),
        ("BACKGROUND",    (1,0),(1,0),   C_EMERALD_LIGHT),
        ("BOX",           (0,0),(-1,-1), 0.5, C_EMERALD_MID),
        ("LINEBEFORE",    (0,0),(0,-1),  3, C_EMERALD),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(0,-1),  0),
        ("RIGHTPADDING",  (0,0),(0,-1),  0),
        ("LEFTPADDING",   (1,0),(1,-1),  12),
        ("RIGHTPADDING",  (1,0),(1,-1),  12),
    ]))
    return [outer, Spacer(1,6)]


# ── Charts ───────────────────────────────────────────────────────────────────

def _make_swot_radar(business_profile: dict) -> Image | None:
    """Generate a SWOT radar chart from business profile data."""
    try:
        categories = ["Strengths", "Weaknesses\n(inverted)", "Opportunities", "Threats\n(inverted)"]
        labels_short = ["Strengths", "Weaknesses", "Opportunities", "Threats"]

        # Score based on profile richness
        strengths_score = min(10, (
            (2 if business_profile.get("years_in_business", 0) and
                int(business_profile.get("years_in_business", 0)) > 2 else 0) +
            (2 if business_profile.get("team_size", 0) and
                int(business_profile.get("team_size", 1)) > 1 else 0) +
            (2 if len(business_profile.get("customer_sources", [])) > 1 else 1) +
            (2 if len(business_profile.get("current_marketing_channels", [])) > 1 else 1) +
            (2 if business_profile.get("additional_notes") else 0)
        ))
        challenges = len(business_profile.get("biggest_challenges", []))
        weaknesses_score = min(10, max(2, 10 - challenges * 1.5))
        goals = len(business_profile.get("goals", []))
        opportunities_score = min(10, max(3, goals * 2 + 2))
        threats_score = min(10, max(2, challenges * 1.2 + 1))

        values = [strengths_score, weaknesses_score, opportunities_score, threats_score]
        N = 4
        angles = [n / float(N) * 2 * math.pi for n in range(N)]
        angles += angles[:1]
        values_plot = values + values[:1]

        fig, ax = plt.subplots(figsize=(4.5, 4.5), subplot_kw=dict(polar=True),
            facecolor="white")

        ax.set_facecolor("#F8FAFC")
        ax.plot(angles, values_plot, "o-", linewidth=2,
            color="#059669", markersize=6)
        ax.fill(angles, values_plot, alpha=0.15, color="#059669")

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels_short, size=10, fontweight="bold",
            color="#1E293B")
        ax.set_ylim(0, 10)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(["2", "4", "6", "8", "10"], size=7, color="#94A3B8")
        ax.grid(color="#CBD5E1", linewidth=0.6)
        ax.spines["polar"].set_color("#CBD5E1")

        ax.set_title("Business Position Overview", size=11,
            fontweight="bold", color="#1E293B", pad=16)

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
            facecolor="white", edgecolor="none")
        plt.close(fig)
        buf.seek(0)

        img = Image(buf, width=220, height=220)
        return img
    except Exception:
        return None


def _make_timeline_chart(business_profile: dict) -> Image | None:
    """Generate a 90-day growth timeline chart."""
    try:
        fig, ax = plt.subplots(figsize=(7, 2.8), facecolor="white")
        ax.set_facecolor("white")

        phases = [
            ("Phase 1\nDays 1–30", "#059669", "Quick Wins & Foundation"),
            ("Phase 2\nDays 31–60", "#0891B2", "Growth Experiments"),
            ("Phase 3\nDays 61–90", "#7C3AED", "Scale & Measure"),
        ]

        bar_height = 0.5
        y_positions = [0.75, 0.45, 0.15]

        for i, ((label, color, desc), y) in enumerate(zip(phases, y_positions)):
            start = i * 30
            width = 30

            # Background track
            ax.barh(y, 90, left=0, height=bar_height * 0.4,
                color="#F1F5F9", zorder=1)

            # Phase bar
            ax.barh(y, width, left=start, height=bar_height * 0.7,
                color=color, alpha=0.85, zorder=2,
                linewidth=0)

            # Phase label on bar
            ax.text(start + width/2, y, label.split("\n")[0],
                ha="center", va="center",
                fontsize=8, fontweight="bold", color="white", zorder=3)

            # Description to right
            ax.text(92, y, desc,
                ha="left", va="center",
                fontsize=8, color="#475569")

        ax.set_xlim(-2, 160)
        ax.set_ylim(-0.05, 1.0)
        ax.set_xticks([0, 30, 60, 90])
        ax.set_xticklabels(["Day 0", "Day 30", "Day 60", "Day 90"],
            fontsize=8, color="#64748B")
        ax.set_yticks([])

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color("#CBD5E1")
        ax.tick_params(axis="x", colors="#94A3B8", length=3)

        ax.set_title("90-Day Growth Roadmap", fontsize=10,
            fontweight="bold", color="#1E293B", pad=10, loc="left")

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
            facecolor="white", edgecolor="none")
        plt.close(fig)
        buf.seek(0)

        img = Image(buf, width=USABLE_W, height=110)
        return img
    except Exception:
        return None


# ── Footer ────────────────────────────────────────────────────────────────────

def _footer(canvas, doc) -> None:
    canvas.saveState()
    y = 18
    canvas.setStrokeColor(C_SLATE_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_L, y + 12, PAGE_W - MARGIN_R, y + 12)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(C_MUTED)
    canvas.drawString(MARGIN_L, y, "Auditly — Business Audit Report")
    canvas.drawRightString(PAGE_W - MARGIN_R, y,
        f"Page {doc.page}  |  Confidential")
    canvas.restoreState()


def _no_footer_first(canvas, doc) -> None:
    """No footer on cover page."""
    pass


# ── Plain table helpers ───────────────────────────────────────────────────────

def _looks_plain_table(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith("-") or s.startswith("#") or s.startswith("|"):
        return False
    return bool(re.search(r"\S {2,}\S", s)) or "\t" in s


def _split_plain(line: str) -> list:
    parts = re.split(r" {2,}|\t", line.strip())
    return [p.strip() for p in parts if p.strip()]


# ── Main PDF Builder ──────────────────────────────────────────────────────────

def convert_md_to_pdf(
    markdown_text: str,
    output_path: str,
    business_name: str = "Business",
    business_profile: dict = None,
) -> None:
    try:
        business_profile = business_profile or {}

        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        st = _build_styles()
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            leftMargin=MARGIN_L, rightMargin=MARGIN_R,
            topMargin=MARGIN_T, bottomMargin=MARGIN_B,
        )

        story = []

        # ── Cover page ────────────────────────────────────────────────────
        story.extend(_cover_page(business_name, business_profile, st))

        # ── Charts page ───────────────────────────────────────────────────
        radar  = _make_swot_radar(business_profile)
        timeline = _make_timeline_chart(business_profile)

        if radar or timeline:
            if radar and timeline:
                chart_row = Table(
                    [[radar, timeline]],
                    colWidths=[230, USABLE_W - 230]
                )
                chart_row.setStyle(TableStyle([
                    ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                    ("LEFTPADDING",   (0,0),(-1,-1), 0),
                    ("RIGHTPADDING",  (0,0),(-1,-1), 0),
                    ("TOPPADDING",    (0,0),(-1,-1), 0),
                    ("BOTTOMPADDING", (0,0),(-1,-1), 0),
                ]))
                story.append(chart_row)
            elif radar:
                story.append(radar)
            elif timeline:
                story.append(timeline)
            story.append(Spacer(1, 16))

        # ── Parse markdown ────────────────────────────────────────────────
        text  = _clean(markdown_text)
        lines = text.splitlines()
        i     = 0

        in_executive   = False
        exec_buffer    = []
        phase_idx      = -1
        rec_idx        = 0
        in_rec_section = False
        swot_detected  = False

        while i < len(lines):
            line = lines[i].rstrip()
            s    = line.strip()

            # Blank line
            if not s:
                if exec_buffer:
                    story.extend(_executive_box(" ".join(exec_buffer), st))
                    exec_buffer = []
                    in_executive = False
                story.append(Spacer(1, 5))
                i += 1
                continue

            # Horizontal rule
            if re.match(r"^[-*_]{3,}$", s):
                story.append(HRFlowable(width="100%", thickness=0.5,
                    color=C_SLATE_BORDER, spaceBefore=6, spaceAfter=10))
                i += 1
                continue

            # H1 — skip if it's just the report title
            if re.match(r"^# [^#]", s):
                title_text = s[2:].strip()
                title_lower = title_text.lower()
                if ("business audit" in title_lower or
                    "strategy report" in title_lower or
                    title_lower == business_name.lower()):
                    i += 1
                    continue
                story.append(Spacer(1, 10))
                story.extend(_section_header(title_text, st))
                i += 1
                continue

            # H2
            if re.match(r"^## [^#]", s):
                heading = s[3:].strip()
                in_executive   = "executive summary" in heading.lower()
                in_rec_section = "recommendation" in heading.lower()
                swot_detected  = "swot" in heading.lower()

                phase_match = re.search(
                    r"(phase\s*\d|days?\s*\d)", heading.lower())
                if phase_match:
                    phase_idx += 1
                    story.extend(_phase_header(heading, phase_idx, st))

                    # Insert timeline chart before first phase
                    if phase_idx == 0 and timeline:
                        story.append(Spacer(1, 8))
                        story.append(timeline)
                        story.append(Spacer(1, 8))
                else:
                    story.append(Spacer(1, 6))
                    story.append(HRFlowable(width="100%", thickness=1.5,
                        color=C_EMERALD, spaceBefore=0, spaceAfter=4))
                    story.append(Paragraph(_fmt(heading), st["h2"]))
                i += 1
                continue

            # H3
            if s.startswith("### "):
                heading = s[4:].strip()
                # Skip duplicate business name subheading
                if heading.lower() == business_name.lower() or \
                   "confidential" in heading.lower():
                    i += 1
                    continue
                story.append(Paragraph(_fmt(heading), st["h3"]))
                i += 1
                continue

            # Markdown table
            if s.startswith("|"):
                tbl_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    tbl_lines.append(lines[i])
                    i += 1
                rows = [_parse_md_row(l) for l in tbl_lines
                        if not _is_md_sep(l)]
                if rows:
                    story.append(Spacer(1, 6))
                    if swot_detected:
                        story.extend(_swot_table(rows, st))
                        swot_detected = False
                    else:
                        story.append(KeepTogether(
                            [_build_table(rows, st), Spacer(1, 10)]))
                continue

            # Bullet
            bm = re.match(r"^[-*•]\s+(.+)$", s)
            if bm:
                content = bm.group(1)
                if in_executive:
                    exec_buffer.append(content)
                else:
                    story.append(Paragraph(
                        "  <b>•</b>  " + _fmt(content), st["bullet"]))
                i += 1
                continue

            # Numbered list
            nm = re.match(r"^(\d+)[.)]\s+(.+)$", s)
            if nm:
                num, content = nm.group(1), nm.group(2)
                if in_rec_section:
                    rec_idx += 1
                    j = i + 1
                    body_lines = []
                    while j < len(lines):
                        ns = lines[j].strip()
                        if not ns:
                            break
                        if re.match(r"^(\d+)[.)]\s+", ns) or \
                           ns.startswith("#"):
                            break
                        body_lines.append(ns)
                        j += 1
                    body = " ".join(body_lines)
                    story.extend(
                        _recommendation_block(rec_idx, content, body, st))
                    i = j
                else:
                    story.append(Paragraph(
                        f"  <b>{num}.</b>  " + _fmt(content), st["bullet"]))
                    i += 1
                continue

            # Executive buffer
            if in_executive and s:
                exec_buffer.append(s)
                i += 1
                continue

            # Plain table
            if _looks_plain_table(s):
                plain = []
                while i < len(lines):
                    ls = lines[i].strip()
                    if not ls or ls.startswith("#") or ls.startswith("|"):
                        break
                    cols = _split_plain(lines[i])
                    if len(cols) >= 2:
                        plain.append(cols)
                        i += 1
                    else:
                        break
                if len(plain) >= 2:
                    story.append(Spacer(1, 6))
                    story.append(KeepTogether(
                        [_build_table(plain, st), Spacer(1, 10)]))
                else:
                    for r in plain:
                        story.append(Paragraph(
                            _fmt(" ".join(r)), st["body"]))
                continue

            # Italic / footnote
            if s.startswith("*") and s.endswith("*") and \
               not s.startswith("**"):
                story.append(Paragraph(
                    _fmt(s.strip("*")), st["body_muted"]))
                i += 1
                continue

            # Default body
            story.append(Paragraph(_fmt(s), st["body"]))
            i += 1

        # Flush executive buffer
        if exec_buffer:
            story.extend(_executive_box(" ".join(exec_buffer), st))

        if not story:
            story.append(Paragraph("No content available.", st["body"]))

        def _first_page(canvas, doc):
            _no_footer_first(canvas, doc)

        def _later_pages(canvas, doc):
            _footer(canvas, doc)

        doc.build(story,
            onFirstPage=_first_page,
            onLaterPages=_later_pages)

    except Exception as exc:
        raise RuntimeError(f"Failed to generate PDF: {exc}") from exc