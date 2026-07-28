from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from .styles import (
    C_SLATE, C_WHITE, C_EMERALD, C_SLATE_BORDER, C_ROW_ALT,
    C_GREEN, C_GREEN_LIGHT, C_AMBER, C_AMBER_LIGHT,
    C_TEAL, C_TEAL_LIGHT, C_ROSE, C_ROSE_LIGHT,
    C_SLATE_MID, C_SLATE_LIGHT, C_BODY, USABLE_W
)
from .utils import _fmt, _escape

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

__all__ = ["_build_table", "_swot_table"]
