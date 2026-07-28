import os
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from .styles import _build_styles, MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B, USABLE_W
from .cover import _cover_page
from .charts import _make_swot_radar, _make_timeline_chart
from .parser import parse_markdown
from .footer import _footer, _no_footer_first

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
        parse_markdown(markdown_text, story, st, business_name, business_profile, timeline)

        def _first_page(canvas, doc):
            _no_footer_first(canvas, doc)

        def _later_pages(canvas, doc):
            _footer(canvas, doc)

        doc.build(story,
            onFirstPage=_first_page,
            onLaterPages=_later_pages)

    except Exception as exc:
        raise RuntimeError(f"Failed to generate PDF: {exc}") from exc

__all__ = ["convert_md_to_pdf"]
