import re

def _clean(text: str) -> str:
    # Step 1: Strip AI page headers
    text = re.sub(
        r"Auditly\s*[\u2014\-\u2013]\s*Business Audit Report\s+Page\s+\d+[^\n]*",
        "", text, flags=re.IGNORECASE)
    text = re.sub(
        r"Business Audit Report\s+Page\s+\d+[^\n]*",
        "", text, flags=re.IGNORECASE)
    text = re.sub(r"Auditly\s+Page\s+\d+", "", text, flags=re.IGNORECASE)

    # Step 2: Remove duplicate cover lines
    text = re.sub(r"^BUSINESS AUDIT\s*&\s*STRATEGY REPORT\s*$",
        "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^Business Audit\s*&\s*Strategy Report\s*$",
        "", text, flags=re.MULTILINE)
    text = re.sub(r"^-+\s*CONFIDENTIAL\s*-+$",
        "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^CONFIDENTIAL$", "", text, flags=re.MULTILINE)

    # Step 3: Currency BEFORE removing ■ globally
    text = re.sub(r"[\u25a0■]\s*(\d)", r"Rs. \1", text)
    text = re.sub(r"₹\s*(\d)", r"Rs. \1", text)

    # Step 4: Numbered list artifacts
    text = re.sub(r"^(\d+)[\u25a0■]+\s*", r"\1. ", text, flags=re.MULTILINE)

    # Step 5: Word-hyphen artifacts
    text = re.sub(r"(\w)[\u25a0■](\w)", r"\1-\2", text)

    # Step 6: Remaining Unicode artifacts
    text = text.replace("\u25a0", "-").replace("■", "-")
    text = text.replace("\u2013", "\u2013").replace("\u2014", "\u2014")
    text = text.replace("\u2022", "\u2022").replace("\u00b7", "-")
    text = text.replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u00e2\u0080\u0099", "'")
    text = text.replace("\u00e2\u0080\u009c", '"')
    text = text.replace("\ufffd", "-")

    # Step 7: HTML tags
    text = re.sub(r"\s*<br\s*/?>\s*", " | ", text, flags=re.IGNORECASE)
    text = re.sub(r"<(?!/?b\b)[^>]+>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<b>(.*?)</b>", r"**\1**", text,
        flags=re.IGNORECASE | re.DOTALL)

    # Step 8: Escaped asterisks
    text = re.sub(r"\\\*", "*", text)

    # Step 9: H4 → H3
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


def _is_md_sep(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and bool(re.match(r"^[\|\s\-:]+$", s))


def _parse_md_row(line: str) -> list:
    line = line.strip().strip("|")
    return [_clean(c.strip()) for c in line.split("|")]


def _looks_plain_table(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith("-") or s.startswith("#") or s.startswith("|"):
        return False
    return bool(re.search(r"\S {2,}\S", s)) or "\t" in s


def _split_plain(line: str) -> list:
    parts = re.split(r" {2,}|\t", line.strip())
    return [p.strip() for p in parts if p.strip()]

__all__ = [
    "_clean",
    "_escape",
    "_fmt",
    "_is_md_sep",
    "_parse_md_row",
    "_looks_plain_table",
    "_split_plain",
]
