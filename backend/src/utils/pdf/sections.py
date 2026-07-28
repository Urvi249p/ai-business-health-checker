from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle
from .styles import (
    C_EMERALD, C_EMERALD_LIGHT, C_EMERALD_MID,
    USABLE_W, _PHASE_COLORS
)
from .utils import _fmt, _escape

def _section_header(title: str, st: dict) -> list:
    return [
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=2, color=C_EMERALD,
            spaceBefore=0, spaceAfter=6),
        Paragraph(_fmt(title), st["h1"]),
        Spacer(1, 4),
    ]


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

__all__ = ["_section_header", "_executive_box", "_phase_header"]
