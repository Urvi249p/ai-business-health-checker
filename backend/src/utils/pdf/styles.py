from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle

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

__all__ = [
    "PAGE_W", "PAGE_H", "MARGIN_L", "MARGIN_R", "MARGIN_T", "MARGIN_B", "USABLE_W",
    "C_SLATE", "C_SLATE_MID", "C_SLATE_LIGHT", "C_SLATE_BORDER",
    "C_EMERALD", "C_EMERALD_LIGHT", "C_EMERALD_MID",
    "C_GREEN", "C_GREEN_LIGHT",
    "C_AMBER", "C_AMBER_LIGHT",
    "C_TEAL", "C_TEAL_LIGHT",
    "C_ROSE", "C_ROSE_LIGHT",
    "C_BODY", "C_MUTED", "C_WHITE", "C_ROW_ALT",
    "_PHASE_COLORS", "_PHASE_LIGHTS",
    "_build_styles"
]
