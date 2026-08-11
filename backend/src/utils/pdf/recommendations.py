from reportlab.platypus.flowables import HRFlowable, PageBreak
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from .styles import C_SLATE, C_EMERALD, C_EMERALD_LIGHT, C_EMERALD_MID, C_WHITE, USABLE_W
from .utils import _escape, _fmt

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


__all__ = ['_recommendation_block']
