import re
from reportlab.platypus.flowables import HRFlowable, PageBreak
from reportlab.platypus import Paragraph, Spacer, KeepTogether
from .styles import C_EMERALD, C_SLATE_MID, C_BODY, C_SLATE_BORDER
from .utils import _clean, _fmt, _is_md_sep, _parse_md_row, _looks_plain_table, _split_plain
from .sections import _section_header, _executive_box, _phase_header
from .tables import _build_table, _swot_table
from .recommendations import _recommendation_block

def parse_markdown(
    markdown_text: str,
    story: list,
    st: dict,
    business_name: str,
    business_profile: dict,
    timeline_img,
) -> None:
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
                if phase_idx == 0 and timeline_img:
                    story.append(Spacer(1, 8))
                    story.append(timeline_img)
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
                try:
                    if swot_detected:
                        story.extend(_swot_table(rows, st))
                    else:
                        story.append(KeepTogether(
                            [_build_table(rows, st), 
                             Spacer(1, 10)]))
                except Exception as tbl_err:
                    import logging
                    _pdf_logger = logging.getLogger(
                        "pdf.parser"
                    )
                    _pdf_logger.error(
                        f"Table render failed: {tbl_err}"
                    )
                    _pdf_logger.error(
                        f"Row count: {len(rows)}"
                    )
                    _pdf_logger.error(
                        f"Header row: {rows[0] if rows else 'empty'}"
                    )
                    for ri, row in enumerate(rows[:3]):
                        _pdf_logger.error(
                            f"Row {ri} types: "
                            f"{[type(c).__name__ for c in row]}"
                        )
                        _pdf_logger.error(
                            f"Row {ri} values: "
                            f"{[str(c)[:80] for c in row]}"
                        )
                    # Fallback to plain text
                    for row in rows:
                        row_text = " | ".join(
                            str(c) for c in row if c
                        )
                        if row_text.strip():
                            story.append(Paragraph(
                                _fmt(row_text), st["body"]))
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


__all__ = ["parse_markdown"]
