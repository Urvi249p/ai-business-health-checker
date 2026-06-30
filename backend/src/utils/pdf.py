"""
pdf.py — Convert AI-generated markdown/semi-structured text to a polished PDF.

Handles:
  - ■ and other encoding artifacts -> proper hyphens/dashes
  - Raw <b>...</b> tags the AI outputs literally
  - Markdown tables (|col|col|) -> styled ReportLab tables
  - Plain-text tables (2+ space aligned columns) -> styled tables
  - Headings (#, ##, ###), bullets, numbered lists, bold (**text**)
"""

import os
import re

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    HRFlowable, KeepTogether, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

PAGE_W, PAGE_H = A4
MARGIN = 45

C_NAVY    = HexColor("#1a1a2e")
C_DARK    = HexColor("#16213e")
C_ACCENT  = HexColor("#0f3460")
C_TEAL    = HexColor("#00897b")
C_HDR_BG  = HexColor("#1a1a2e")
C_ROW_ALT = HexColor("#edf2f7")
C_BORDER  = HexColor("#b0bec5")
C_BODY    = HexColor("#2d2d2d")
C_WHITE   = colors.white
C_RULE    = HexColor("#0f3460")
C_MUTED   = HexColor("#78909c")


def _clean(text: str) -> str:
    text = text.replace("\u25a0", "-").replace("■", "-")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2022", "-").replace("\u00b7", "-")
    text = text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    # Raw <b> tags AI sometimes emits literally
    text = re.sub(r"<b>(.*?)</b>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL)
    # Remove injected page headers
    text = re.sub(r"Business Audit Report\s+Page\s+\d+\s*(Confidential)?", "", text)
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
    return {
        "h1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=22,
            leading=28, textColor=C_NAVY, spaceBefore=20, spaceAfter=10),
        "h2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=15,
            leading=20, textColor=C_DARK, spaceBefore=16, spaceAfter=6),
        "h3": ParagraphStyle("H3", fontName="Helvetica-Bold", fontSize=12,
            leading=16, textColor=C_ACCENT, spaceBefore=12, spaceAfter=4),
        "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=10,
            leading=15, textColor=C_BODY, spaceAfter=6),
        "bullet": ParagraphStyle("Bullet", fontName="Helvetica", fontSize=10,
            leading=14, textColor=C_BODY, leftIndent=16, spaceAfter=4),
        "th": ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=9,
            leading=12, textColor=C_WHITE, alignment=TA_LEFT),
        "td": ParagraphStyle("TD", fontName="Helvetica", fontSize=9,
            leading=12, textColor=C_BODY, alignment=TA_LEFT),
    }


def _footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(C_MUTED)
    y = 20
    canvas.drawString(MARGIN, y, "Business Audit Report")
    canvas.drawRightString(PAGE_W - MARGIN, y, f"Page {doc.page}")
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, y + 10, PAGE_W - MARGIN, y + 10)
    canvas.restoreState()


def _is_md_sep(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and bool(re.match(r"^[\|\s\-:]+$", s))


def _parse_md_row(line: str) -> list:
    line = line.strip().strip("|")
    return [_clean(c.strip()) for c in line.split("|")]


def _build_table(rows: list, st: dict) -> Table:
    usable = PAGE_W - 2 * MARGIN
    col_count = max(len(r) for r in rows)
    col_w = usable / col_count

    data = []
    for idx, row in enumerate(rows):
        while len(row) < col_count:
            row.append("")
        sty = st["th"] if idx == 0 else st["td"]
        data.append([Paragraph(_fmt(c), sty) for c in row])

    tbl = Table(data, colWidths=[col_w] * col_count, repeatRows=1)
    alt = []
    for idx in range(1, len(data)):
        bg = C_ROW_ALT if idx % 2 == 0 else C_WHITE
        alt.append(("BACKGROUND", (0, idx), (-1, idx), bg))

    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_HDR_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("LINEBELOW",     (0, 0), (-1, 0), 1.5, C_TEAL),
        ("GRID",          (0, 0), (-1, -1), 0.4, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
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


def convert_md_to_pdf(markdown_text: str, output_path: str) -> None:
    try:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        st = _build_styles()
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=MARGIN, bottomMargin=MARGIN + 15,
        )

        story = []
        text = _clean(markdown_text)
        lines = text.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()
            s = line.strip()

            if not s:
                story.append(Spacer(1, 6))
                i += 1
                continue

            if re.match(r"^[-*_]{3,}$", s):
                story.append(HRFlowable(width="100%", thickness=1,
                    color=C_RULE, spaceBefore=4, spaceAfter=10))
                i += 1
                continue

            if re.match(r"^# [^#]", s):
                story.append(Spacer(1, 6))
                story.append(Paragraph(_fmt(s[2:]), st["h1"]))
                story.append(HRFlowable(width="100%", thickness=2,
                    color=C_ACCENT, spaceBefore=4, spaceAfter=8))
                i += 1
                continue

            if re.match(r"^## [^#]", s):
                story.append(Spacer(1, 4))
                story.append(Paragraph(_fmt(s[3:]), st["h2"]))
                story.append(HRFlowable(width="100%", thickness=0.8,
                    color=C_TEAL, spaceBefore=2, spaceAfter=6))
                i += 1
                continue

            if s.startswith("### "):
                story.append(Paragraph(_fmt(s[4:]), st["h3"]))
                i += 1
                continue

            # Markdown table
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

            # Bullet
            bm = re.match(r"^[-*•]\s+(.+)$", s)
            if bm:
                story.append(Paragraph("• " + _fmt(bm.group(1)), st["bullet"]))
                i += 1
                continue

            # Numbered
            nm = re.match(r"^(\d+)[.)]\s+(.+)$", s)
            if nm:
                story.append(Paragraph(
                    f"<b>{nm.group(1)}.</b> " + _fmt(nm.group(2)), st["bullet"]))
                i += 1
                continue

            # Plain text table detection
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

            story.append(Paragraph(_fmt(s), st["body"]))
            i += 1

        if not story:
            story.append(Paragraph("No content available.", st["body"]))

        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)

    except Exception as exc:
        raise RuntimeError(f"Failed to generate PDF: {exc}") from exc