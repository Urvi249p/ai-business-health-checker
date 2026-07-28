from .styles import C_SLATE_BORDER, C_MUTED, MARGIN_L, MARGIN_R, PAGE_W

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

__all__ = ["_footer", "_no_footer_first"]
