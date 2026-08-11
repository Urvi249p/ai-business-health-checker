from reportlab.platypus.flowables import HRFlowable, PageBreak
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from .styles import C_SLATE, C_WHITE, C_EMERALD, C_SLATE_BORDER, C_ROW_ALT, C_GREEN, C_GREEN_LIGHT, C_AMBER, C_AMBER_LIGHT, C_TEAL, C_TEAL_LIGHT, C_ROSE, C_ROSE_LIGHT, C_SLATE_MID, C_SLATE_LIGHT, C_BODY, USABLE_W
from .utils import _fmt, _escape

def _build_table(rows: list, st: dict) -> Table:
    col_count = max(len(r) for r in rows)
    col_w = USABLE_W / col_count

    data = []
    for idx, row in enumerate(rows):
        while len(row) < col_count:
            row.append("")
        sty = st["th"] if idx == 0 else st["td"]
        safe_row = []
        for c in row:
            # Ensure cell is always a string
            if isinstance(c, list):
                c = " ".join(str(x) for x in c)
            elif not isinstance(c, str):
                c = str(c)
            # Truncate extremely long cells to
            # prevent layout overflow
            if len(c) > 500:
                c = c[:497] + "..."
            safe_row.append(Paragraph(_fmt(c), sty))
        data.append(safe_row)

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
    """
    Render SWOT as color-coded cards.
    Detects SWOT by header content OR falls back
    to positional assignment if exactly 2 columns
    are present and we are in the SWOT section.
    """
    if not rows or len(rows) < 2:
        return [_build_table(rows, st), Spacer(1, 10)]

    header = [c.lower().strip() for c in rows[0]]
    swot_keys = ["strengths", "weaknesses", 
                 "opportunities", "threats"]

    # Primary detection: exact SWOT keywords in headers
    is_swot = any(
        any(k in h for k in swot_keys) 
        for h in header
    )

    # Fallback detection: 2-column table with 
    # S/W or O/T content in first data row
    if not is_swot and len(header) == 2 and len(rows) > 1:
        first_row_text = " ".join(rows[1]).lower()
        swot_content_hints = [
            "strength", "weakness", "opportunit", 
            "threat", "internal", "external",
            "advantage", "limitation", "risk", "market"
        ]
        hint_count = sum(
            1 for hint in swot_content_hints 
            if hint in first_row_text
        )
        if hint_count >= 2:
            is_swot = True
            # Assign standard SWOT headers based on 
            # which pair this likely is
            col0 = header[0]
            col1 = header[1]
            # Detect if this is S/W or O/T table
            ot_hints = ["opportunit", "threat", 
                        "external", "positive", 
                        "helpful", "harmful"]
            is_ot = any(h in col0 or h in col1 
                       for h in ot_hints)
            if is_ot:
                rows[0] = ["Opportunities", "Threats"]
            else:
                rows[0] = ["Strengths", "Weaknesses"]
            header = [c.lower() for c in rows[0]]

    if not is_swot:
        return [_build_table(rows, st), Spacer(1, 10)]

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
                quadrants.append(
                    (h.title(), accent, bg, letter))
                break
        else:
            quadrants.append(
                (h.title(), C_SLATE_MID, C_SLATE_LIGHT, "?"))

    # Collect cell content from all data rows
    contents = ["" for _ in header]
    for row in rows[1:]:
        for ci, cell in enumerate(row):
            if ci < len(contents):
                sep = " " if contents[ci] else ""
                contents[ci] += sep + cell.strip()

    # Build color-coded cards
    def make_cell(idx):
        if idx >= len(quadrants):
            # Return empty Table cell, not bare Paragraph
            # Bare Paragraph causes 'not iterable' error
            empty = Table(
                [[Paragraph("", st["td"])]],
                colWidths=[col_w - 4]
            )
            empty.setStyle(TableStyle([
                ("TOPPADDING",    (0,0),(-1,-1), 0),
                ("BOTTOMPADDING", (0,0),(-1,-1), 0),
                ("LEFTPADDING",   (0,0),(-1,-1), 0),
                ("RIGHTPADDING",  (0,0),(-1,-1), 0),
            ]))
            return empty
        label, accent, bg, letter = quadrants[idx]
        content = contents[idx] if idx < len(contents) else ""
        header_para = Paragraph(
            f"<font color='white'><b>{_escape(label)}</b></font>",
            ParagraphStyle("SWOTHead", 
                fontName="Helvetica-Bold",
                fontSize=9, leading=12, 
                textColor=C_WHITE))
        body_para = Paragraph(_fmt(content),
            ParagraphStyle("SWOTBody", 
                fontName="Helvetica",
                fontSize=8, leading=12, 
                textColor=C_BODY))
        inner = Table(
            [[header_para], [Spacer(1, 4)], [body_para]],
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
        right = make_cell(i+1)
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


__all__ = ['_build_table', '_swot_table']
