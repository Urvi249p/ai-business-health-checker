"""
pdf.py — Convert AI-generated markdown to a polished Auditly PDF report.

Design system:
  - Clean white background, professional blue accents (#2563EB)
  - Plus Jakarta Sans feel via Helvetica (PDF-safe)
  - Clear section hierarchy with colored left-border accents
  - Styled SWOT table, phase cards, key recommendations
  - Consistent spacing and readable typography
"""

import os
import re

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, KeepTogether, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

PAGE_W, PAGE_H = A4
MARGIN_L = 50
MARGIN_R = 50
MARGIN_T = 50
MARGIN_B = 55

# ── Colour palette ────────────────────────────────────────────────────────────
C_BLUE       = HexColor("#2563EB")   # primary brand blue
C_BLUE_LIGHT = HexColor("#EFF6FF")   # light blue tint for backgrounds
C_BLUE_MID   = HexColor("#DBEAFE")   # mid blue for borders
C_GREEN      = HexColor("#10B981")   # success / strengths
C_GREEN_LIGHT= HexColor("#ECFDF5")
C_AMBER      = HexColor("#F59E0B")   # warning / weaknesses
C_AMBER_LIGHT= HexColor("#FFFBEB")
C_RED        = HexColor("#EF4444")   # threats
C_RED_LIGHT  = HexColor("#FEF2F2")
C_PURPLE     = HexColor("#8B5CF6")   # opportunities
C_PURPLE_LIGHT=HexColor("#F5F3FF")
C_NAVY       = HexColor("#111827")   # primary text
C_DARK       = HexColor("#1E293B")   # headings
C_MUTED      = HexColor("#6B7280")   # secondary text
C_BORDER     = HexColor("#E5E7EB")   # card borders
C_ROW_ALT    = HexColor("#F9FAFB")   # table alt row
C_WHITE      = colors.white
C_PAGE_BG    = HexColor("#F8F9FC")   # page background hint


def _clean(text: str) -> str:
    # Step 1: Strip AI page headers FIRST
    # Handles: "Auditly — Business Audit Report Page 2 | Confidential"
    text = re.sub(
        r"Auditly\s*[\u2014\-\u2013]\s*Business Audit Report\s+Page\s+\d+[^\n]*",
        "", text, flags=re.IGNORECASE)
    text = re.sub(
        r"Business Audit Report\s+Page\s+\d+[^\n]*",
        "", text, flags=re.IGNORECASE)
    text = re.sub(r"Auditly\s+Page\s+\d+", "", text, flags=re.IGNORECASE)

    # Step 2: Remove duplicate cover lines AI adds
    text = re.sub(
        r"^BUSINESS AUDIT\s*&\s*STRATEGY REPORT\s*$",
        "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(
        r"^Business Audit\s*&\s*Strategy Report\s*$",
        "", text, flags=re.MULTILINE)
    text = re.sub(
        r"^-+\s*CONFIDENTIAL\s*-+$",
        "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^CONFIDENTIAL$", "", text, flags=re.MULTILINE)

    # Step 3: Currency BEFORE replacing ■ globally
    # "■1 L", "■5K" → "₹1 L", "₹5K"
    text = re.sub(r"■\s*(\d)", r"₹\1", text)
    text = re.sub(r"₹\s+(\d)", r"₹\1", text)

    # Step 4: Numbered list artifacts BEFORE global ■ replace
    # "1■■ Starter" → "1. Starter"
    text = re.sub(r"^(\d+)■+\s*", r"\1. ", text, flags=re.MULTILINE)

    # Step 5: Word-hyphen artifacts
    # "five■year■old" → "five-year-old"
    text = re.sub(r"(\w)■(\w)", r"\1-\2", text)

    # Step 6: Unicode encoding artifacts
    text = text.replace("\u25a0", "-").replace("■", "-")
    text = text.replace("\u2013", "\u2013").replace("\u2014", "\u2014")
    text = text.replace("\u2022", "\u2022").replace("\u00b7", "-")
    text = text.replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u00e2\u0080\u0099", "'")
    text = text.replace("\u00e2\u0080\u009c", '"')
    text = text.replace("\ufffd", "-")

    # Step 7: AI HTML tags
    text = re.sub(r"\s*<br\s*/?>\s*", " | ", text, flags=re.IGNORECASE)
    text = re.sub(r"<(?!/?b\b)[^>]+>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<b>(.*?)</b>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL)

    # Step 8: Escaped asterisks \* → *
    text = re.sub(r"\\\*", "*", text)

    # Step 9: H4 headers normalize to H3
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


def _build_styles() -> dict:
    base = dict(fontName="Helvetica", textColor=C_NAVY)
    return {
        # Cover / title
        "cover_title": ParagraphStyle("CoverTitle",
            fontName="Helvetica-Bold", fontSize=28, leading=36,
            textColor=C_DARK, spaceAfter=8),
        "cover_sub": ParagraphStyle("CoverSub",
            fontName="Helvetica", fontSize=13, leading=18,
            textColor=C_MUTED, spaceAfter=4),
        "cover_meta": ParagraphStyle("CoverMeta",
            fontName="Helvetica", fontSize=10, leading=14,
            textColor=C_MUTED, spaceAfter=2),

        # Section headings
        "h1": ParagraphStyle("H1",
            fontName="Helvetica-Bold", fontSize=20, leading=26,
            textColor=C_DARK, spaceBefore=24, spaceAfter=6),
        "h2": ParagraphStyle("H2",
            fontName="Helvetica-Bold", fontSize=14, leading=20,
            textColor=C_DARK, spaceBefore=18, spaceAfter=4),
        "h3": ParagraphStyle("H3",
            fontName="Helvetica-Bold", fontSize=11, leading=16,
            textColor=C_BLUE, spaceBefore=12, spaceAfter=3),

        # Body text
        "body": ParagraphStyle("Body",
            fontName="Helvetica", fontSize=10, leading=16,
            textColor=C_NAVY, spaceAfter=5),
        "body_muted": ParagraphStyle("BodyMuted",
            fontName="Helvetica", fontSize=9, leading=14,
            textColor=C_MUTED, spaceAfter=4),

        # Lists
        "bullet": ParagraphStyle("Bullet",
            fontName="Helvetica", fontSize=10, leading=15,
            textColor=C_NAVY, leftIndent=14, firstLineIndent=0,
            spaceAfter=3),
        "numbered": ParagraphStyle("Numbered",
            fontName="Helvetica", fontSize=10, leading=15,
            textColor=C_NAVY, leftIndent=14, spaceAfter=3),

        # Table cells
        "th": ParagraphStyle("TH",
            fontName="Helvetica-Bold", fontSize=9, leading=13,
            textColor=C_WHITE, alignment=TA_LEFT),
        "td": ParagraphStyle("TD",
            fontName="Helvetica", fontSize=9, leading=13,
            textColor=C_NAVY, alignment=TA_LEFT),
        "td_muted": ParagraphStyle("TDMuted",
            fontName="Helvetica", fontSize=8, leading=12,
            textColor=C_MUTED, alignment=TA_LEFT),

        # Special
        "label": ParagraphStyle("Label",
            fontName="Helvetica-Bold", fontSize=8, leading=12,
            textColor=C_BLUE, spaceBefore=0, spaceAfter=2),
        "executive": ParagraphStyle("Executive",
            fontName="Helvetica", fontSize=11, leading=18,
            textColor=C_NAVY, spaceAfter=6,
            leftIndent=16, rightIndent=16),
        "recommendation": ParagraphStyle("Recommendation",
            fontName="Helvetica-Bold", fontSize=10, leading=15,
            textColor=C_DARK, spaceAfter=2, leftIndent=20),
        "rec_body": ParagraphStyle("RecBody",
            fontName="Helvetica", fontSize=9, leading=14,
            textColor=C_MUTED, spaceAfter=6, leftIndent=20),
        "footer_text": ParagraphStyle("Footer",
            fontName="Helvetica", fontSize=8, leading=10,
            textColor=C_MUTED),
    }


def _cover_block(business_name: str, st: dict) -> list:
    """Generate a professional cover header block."""
    flowables = []

    # Top blue rule
    flowables.append(HRFlowable(
        width="100%", thickness=4, color=C_BLUE,
        spaceBefore=0, spaceAfter=20))

    # Eyebrow
    flowables.append(Paragraph(
        "<font color='#2563EB'><b>BUSINESS AUDIT &amp; STRATEGY REPORT</b></font>",
        ParagraphStyle("Eyebrow", fontName="Helvetica-Bold", fontSize=9,
            leading=12, textColor=C_BLUE, spaceAfter=8, tracking=80)))

    # Business name as title
    flowables.append(Paragraph(
        _escape(business_name), st["cover_title"]))

    # Confidential badge
    badge_data = [[Paragraph(
        "<font color='white'><b>  CONFIDENTIAL  </b></font>",
        ParagraphStyle("Badge", fontName="Helvetica-Bold", fontSize=8,
            leading=10, textColor=C_WHITE, alignment=TA_LEFT))]]
    badge = Table(badge_data, colWidths=[90])
    badge.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_BLUE),
        ("ROUNDEDCORNERS",(0, 0), (-1, -1), [4, 4, 4, 4]),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    flowables.append(badge)
    flowables.append(Spacer(1, 4))

    # Bottom rule
    flowables.append(HRFlowable(
        width="100%", thickness=1, color=C_BORDER,
        spaceBefore=12, spaceAfter=20))

    return flowables


def _section_header(title: str, st: dict, color=None) -> list:
    """Blue left-accented section header."""
    color = color or C_BLUE
    flowables = []
    flowables.append(Spacer(1, 8))

    # Colored top rule
    flowables.append(HRFlowable(
        width="100%", thickness=2, color=color,
        spaceBefore=0, spaceAfter=6))

    flowables.append(Paragraph(_fmt(title), st["h1"]))
    return flowables


def _executive_box(text: str, st: dict) -> list:
    """Light blue box for executive summary."""
    data = [[Paragraph(_fmt(text), st["executive"])]]
    tbl = Table(data, colWidths=[PAGE_W - MARGIN_L - MARGIN_R])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_BLUE_LIGHT),
        ("LINEAFTER",     (0, 0), (0, -1),  4, C_BLUE),
        ("LINEBEFORE",    (0, 0), (0, -1),  4, C_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BLUE_MID),
    ]))
    return [tbl, Spacer(1, 12)]


def _swot_table(rows: list, st: dict) -> list:
    """Render SWOT as a styled 2x2 colour-coded table."""
    usable = PAGE_W - MARGIN_L - MARGIN_R
    col_w = usable / 2

    swot_colors = {
        "strengths":    (C_GREEN,  C_GREEN_LIGHT),
        "weaknesses":   (C_AMBER,  C_AMBER_LIGHT),
        "opportunities":(C_PURPLE, C_PURPLE_LIGHT),
        "threats":      (C_RED,    C_RED_LIGHT),
    }

    # Try to detect SWOT structure from rows
    # Fall back to generic table if not SWOT
    header_row = rows[0] if rows else []
    is_swot = any(
        any(k in str(c).lower() for k in swot_colors)
        for c in header_row
    )

    if not is_swot or len(rows) < 2:
        return [_build_table(rows, st), Spacer(1, 10)]

    data = []
    for idx, row in enumerate(rows):
        while len(row) < 2:
            row.append("")
        if idx == 0:
            data.append([
                Paragraph(_fmt(row[0]), st["th"]),
                Paragraph(_fmt(row[1]) if len(row) > 1 else "", st["th"]),
            ])
        else:
            data.append([
                Paragraph(_fmt(row[0]), st["td"]),
                Paragraph(_fmt(row[1]) if len(row) > 1 else "", st["td"]),
            ])

    tbl = Table(data, colWidths=[col_w, col_w], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID",          (0, 0), (-1, -1), 0.5, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        *[("BACKGROUND", (0, idx), (-1, idx), C_ROW_ALT)
          for idx in range(2, len(data), 2)],
    ]))
    return [tbl, Spacer(1, 12)]


def _recommendation_block(num: int, title: str, body: str, st: dict) -> list:
    """Numbered recommendation card with blue left accent."""
    num_cell = Paragraph(
        f"<font color='white'><b>{num}</b></font>",
        ParagraphStyle("Num", fontName="Helvetica-Bold", fontSize=11,
            leading=14, textColor=C_WHITE, alignment=TA_CENTER))

    title_cell = Paragraph(f"<b>{_escape(title)}</b>", st["body"])
    body_cell  = Paragraph(_escape(body), st["body_muted"])

    inner = Table([[title_cell], [body_cell]],
        colWidths=[PAGE_W - MARGIN_L - MARGIN_R - 46])
    inner.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    outer = Table([[num_cell, inner]], colWidths=[36, PAGE_W - MARGIN_L - MARGIN_R - 46])
    outer.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0),  C_BLUE),
        ("BACKGROUND",    (1, 0), (1, 0),  C_BLUE_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BLUE_MID),
        ("LINEBEFORE",    (0, 0), (0, -1),  3, C_BLUE),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (0, -1),  0),
        ("RIGHTPADDING",  (0, 0), (0, -1),  0),
        ("LEFTPADDING",   (1, 0), (1, -1),  12),
        ("RIGHTPADDING",  (1, 0), (1, -1),  12),
    ]))
    return [outer, Spacer(1, 6)]


def _footer(canvas, doc) -> None:
    canvas.saveState()
    y = 18
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_L, y + 12, PAGE_W - MARGIN_R, y + 12)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(C_MUTED)
    canvas.drawString(MARGIN_L, y, "Auditly — Business Audit Report")
    canvas.drawRightString(PAGE_W - MARGIN_R, y, f"Page {doc.page}  |  Confidential")
    canvas.restoreState()


def _is_md_sep(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and bool(re.match(r"^[\|\s\-:]+$", s))


def _parse_md_row(line: str) -> list:
    line = line.strip().strip("|")
    return [_clean(c.strip()) for c in line.split("|")]


def _build_table(rows: list, st: dict) -> Table:
    usable = PAGE_W - MARGIN_L - MARGIN_R
    col_count = max(len(r) for r in rows)
    col_w = usable / col_count

    data = []
    for idx, row in enumerate(rows):
        while len(row) < col_count:
            row.append("")
        sty = st["th"] if idx == 0 else st["td"]
        data.append([Paragraph(_fmt(c), sty) for c in row])

    tbl = Table(data, colWidths=[col_w] * col_count, repeatRows=1)
    alt = [("BACKGROUND", (0, idx), (-1, idx), C_ROW_ALT)
           for idx in range(2, len(data), 2)]

    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("LINEBELOW",     (0, 0), (-1, 0), 2, C_BLUE),
        ("GRID",          (0, 0), (-1, -1), 0.4, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        *alt,
    ]))
    return tbl


def _looks_plain_table(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith("-") or s.startswith("#") or s.startswith("|"):
        return False
    return bool(re.search(r"\S {2,}\S", s)) or "\t" in s


def _split_plain(line: str) -> list:
    parts = re.split(r" {2,}|\t", line.strip())
    return [p.strip() for p in parts if p.strip()]


def _profile_table(fields: list, st: dict) -> Table:
    """Render business profile as a clean 2-col key-value table."""
    usable = PAGE_W - MARGIN_L - MARGIN_R
    data = []
    for label, value in fields:
        data.append([
            Paragraph(f"<b>{_escape(label)}</b>", st["td"]),
            Paragraph(_escape(str(value)), st["td"]),
        ])
    tbl = Table(data, colWidths=[usable * 0.35, usable * 0.65])
    tbl.setStyle(TableStyle([
        ("GRID",          (0, 0), (-1, -1), 0.4, C_BORDER),
        ("BACKGROUND",    (0, 0), (0, -1),  C_BLUE_LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        *[("BACKGROUND", (0, idx), (-1, idx), C_ROW_ALT)
          for idx in range(1, len(data), 2)],
    ]))
    return tbl


# ── Phase card for 90-day plan ────────────────────────────────────────────────

_PHASE_COLORS = [C_BLUE, C_GREEN, C_PURPLE]
_PHASE_BG     = [C_BLUE_LIGHT, C_GREEN_LIGHT, C_PURPLE_LIGHT]


def _phase_header(title: str, phase_idx: int, st: dict) -> list:
    color    = _PHASE_COLORS[phase_idx % 3]
    bg_color = _PHASE_BG[phase_idx % 3]
    data = [[Paragraph(f"<font color='white'><b>{_escape(title)}</b></font>",
        ParagraphStyle("PhaseH", fontName="Helvetica-Bold", fontSize=10,
            leading=14, textColor=C_WHITE))]]
    tbl = Table(data, colWidths=[PAGE_W - MARGIN_L - MARGIN_R])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), color),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
    ]))
    return [tbl]


def convert_md_to_pdf(markdown_text: str, output_path: str,
                      business_name: str = "Business") -> None:
    try:
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
        text  = _clean(markdown_text)
        lines = text.splitlines()
        i     = 0

        # Track state for smart rendering
        in_executive   = False
        exec_buffer    = []
        phase_idx      = -1
        rec_idx        = 0
        rec_buffer     = {}   # {title: body}
        in_rec_section = False

        while i < len(lines):
            line = lines[i].rstrip()
            s    = line.strip()

            # ── Blank line ────────────────────────────────────────────────
            if not s:
                if exec_buffer:
                    story.extend(_executive_box(" ".join(exec_buffer), st))
                    exec_buffer = []
                    in_executive = False
                story.append(Spacer(1, 5))
                i += 1
                continue

            # ── Horizontal rule ───────────────────────────────────────────
            if re.match(r"^[-*_]{3,}$", s):
                story.append(HRFlowable(width="100%", thickness=0.5,
                    color=C_BORDER, spaceBefore=6, spaceAfter=10))
                i += 1
                continue

            # ── H1 ────────────────────────────────────────────────────────
            if re.match(r"^# [^#]", s):
                title_text = s[2:].strip()
                # Cover block for first H1
                if len(story) == 0 or all(
                    isinstance(f, (Spacer, HRFlowable)) for f in story
                ):
                    story.extend(_cover_block(business_name, st))
                    # Still render the H1 as subtitle if it differs from name
                    if title_text.lower() != business_name.lower():
                        story.append(Paragraph(_fmt(title_text), st["h2"]))
                else:
                    story.append(Spacer(1, 10))
                    story.append(Paragraph(_fmt(title_text), st["h1"]))
                    story.append(HRFlowable(width="100%", thickness=2,
                        color=C_BLUE, spaceBefore=4, spaceAfter=10))
                i += 1
                continue

            # ── H2 ────────────────────────────────────────────────────────
            if re.match(r"^## [^#]", s):
                heading = s[3:].strip()
                in_executive   = "executive summary" in heading.lower()
                in_rec_section = "recommendation" in heading.lower()

                # Phase detection for 90-day plan
                phase_match = re.search(r"(phase\s*\d|days?\s*\d)", heading.lower())
                if phase_match:
                    phase_idx += 1
                    story.extend(_phase_header(heading, phase_idx, st))
                    story.append(Spacer(1, 4))
                else:
                    story.append(Spacer(1, 6))
                    story.append(HRFlowable(width="100%", thickness=1.5,
                        color=C_BLUE, spaceBefore=0, spaceAfter=4))
                    story.append(Paragraph(_fmt(heading), st["h2"]))
                i += 1
                continue

            # ── H3 ────────────────────────────────────────────────────────
            if s.startswith("### "):
                heading = s[4:].strip()
                story.append(Paragraph(_fmt(heading), st["h3"]))
                i += 1
                continue

            # ── Markdown table ────────────────────────────────────────────
            if s.startswith("|"):
                tbl_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    tbl_lines.append(lines[i])
                    i += 1
                rows = [_parse_md_row(l) for l in tbl_lines if not _is_md_sep(l)]
                if rows:
                    story.append(Spacer(1, 6))
                    story.append(KeepTogether([_build_table(rows, st), Spacer(1, 10)]))
                continue

            # ── Bullet ───────────────────────────────────────────────────
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

            # ── Numbered list ─────────────────────────────────────────────
            nm = re.match(r"^(\d+)[.)]\s+(.+)$", s)
            if nm:
                num, content = nm.group(1), nm.group(2)
                if in_rec_section:
                    rec_idx += 1
                    # Look ahead for body text
                    j = i + 1
                    body_lines = []
                    while j < len(lines):
                        ns = lines[j].strip()
                        if not ns:
                            break
                        if re.match(r"^(\d+)[.)]\s+", ns) or ns.startswith("#"):
                            break
                        body_lines.append(ns)
                        j += 1
                    body = " ".join(body_lines)
                    story.extend(_recommendation_block(rec_idx, content, body, st))
                    i = j
                else:
                    story.append(Paragraph(
                        f"  <b>{num}.</b>  " + _fmt(content), st["bullet"]))
                    i += 1
                continue

            # ── Executive summary buffer ──────────────────────────────────
            if in_executive and s:
                exec_buffer.append(s)
                i += 1
                continue

            # ── Plain text table ──────────────────────────────────────────
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
                    story.append(KeepTogether([_build_table(plain, st), Spacer(1, 10)]))
                else:
                    for r in plain:
                        story.append(Paragraph(_fmt(" ".join(r)), st["body"]))
                continue

            # ── Italic / footnote line ────────────────────────────────────
            if s.startswith("*") and s.endswith("*") and not s.startswith("**"):
                story.append(Paragraph(
                    _fmt(s.strip("*")), st["body_muted"]))
                i += 1
                continue

            # ── Default body paragraph ────────────────────────────────────
            story.append(Paragraph(_fmt(s), st["body"]))
            i += 1

        # Flush any remaining executive buffer
        if exec_buffer:
            story.extend(_executive_box(" ".join(exec_buffer), st))

        if not story:
            story.append(Paragraph("No content available.", st["body"]))

        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)

    except Exception as exc:
        raise RuntimeError(f"Failed to generate PDF: {exc}") from exc