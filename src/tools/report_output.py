from __future__ import annotations

import html
import os
import re
from datetime import datetime
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _pdf_escape(value: str) -> str:
    return html.escape(value, quote=False)


def _remove_code_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:html)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _strip_tags(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _paragraph_html(value: str) -> str:
    value = html.unescape(value.strip())
    value = re.sub(r"<\s*/?\s*span[^>]*>", "", value, flags=re.IGNORECASE)
    value = re.sub(r"<\s*br\s*/?\s*>", "<br/>", value, flags=re.IGNORECASE)
    value = re.sub(r"<\s*b\s*>", "<b>", value, flags=re.IGNORECASE)
    value = re.sub(r"<\s*/\s*b\s*>", "</b>", value, flags=re.IGNORECASE)
    value = re.sub(r"<\s*strong\s*>", "<b>", value, flags=re.IGNORECASE)
    value = re.sub(r"<\s*/\s*strong\s*>", "</b>", value, flags=re.IGNORECASE)
    value = re.sub(r"<\s*i\s*>", "<i>", value, flags=re.IGNORECASE)
    value = re.sub(r"<\s*/\s*i\s*>", "</i>", value, flags=re.IGNORECASE)
    value = re.sub(r"<\s*em\s*>", "<i>", value, flags=re.IGNORECASE)
    value = re.sub(r"<\s*/\s*em\s*>", "</i>", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    return value.strip()


def _extract_table(table_html: str, styles) -> Table | None:
    rows: list[list[Paragraph]] = []
    raw_rows = re.findall(r"<tr\b[^>]*>(.*?)</tr>", table_html, flags=re.IGNORECASE | re.DOTALL)
    for raw_row in raw_rows:
        cells = re.findall(r"<t[hd]\b[^>]*>(.*?)</t[hd]>", raw_row, flags=re.IGNORECASE | re.DOTALL)
        if cells:
            rows.append([Paragraph(_pdf_escape(_strip_tags(cell)), styles["TableCell"]) for cell in cells])

    if not rows:
        return None

    column_count = max(len(row) for row in rows)
    for row in rows:
        while len(row) < column_count:
            row.append(Paragraph("", styles["TableCell"]))

    usable_width = LETTER[0] - 1.2 * inch
    col_widths = [usable_width / column_count] * column_count

    table = Table(rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _list_items(list_html: str) -> list[str]:
    return [
        _pdf_escape(_strip_tags(item))
        for item in re.findall(r"<li\b[^>]*>(.*?)</li>", list_html, flags=re.IGNORECASE | re.DOTALL)
        if _strip_tags(item)
    ]


def _plain_blocks(text: str) -> Iterable[str]:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?(?:p|div|section|article)\b[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?h[1-3]\b[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    for block in re.split(r"\n{2,}|\n(?=[A-Z0-9][A-Za-z0-9 /&()-]{2,60}$)", text):
        block = re.sub(r"\s+", " ", block).strip()
        if block:
            yield block


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#111827"),
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#111827"),
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubHeading",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#374151"),
            spaceBefore=8,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#111827"),
        )
    )
    return styles


def _html_to_flowables(report_text: str):
    styles = _build_styles()
    flowables = []

    text = _remove_code_fence(report_text)
    parts = re.split(r"(<table\b.*?</table>|<[uo]l\b.*?</[uo]l>|<h[1-3]\b.*?</h[1-3]>)", text, flags=re.IGNORECASE | re.DOTALL)

    title_seen = False
    for part in parts:
        part = part.strip()
        if not part:
            continue

        if re.match(r"<table\b", part, flags=re.IGNORECASE):
            table = _extract_table(part, styles)
            if table:
                flowables.extend([Spacer(1, 4), table, Spacer(1, 8)])
            continue

        if re.match(r"<[uo]l\b", part, flags=re.IGNORECASE):
            items = _list_items(part)
            if items:
                flowables.append(
                    ListFlowable(
                        [ListItem(Paragraph(item, styles["ReportBody"])) for item in items],
                        bulletType="bullet",
                        leftIndent=16,
                    )
                )
                flowables.append(Spacer(1, 4))
            continue

        heading = re.match(r"<(h[1-3])\b[^>]*>(.*?)</\1>", part, flags=re.IGNORECASE | re.DOTALL)
        if heading:
            tag, body = heading.groups()
            label = _strip_tags(body)
            if not label:
                continue
            if tag.lower() == "h1" and not title_seen:
                flowables.append(Paragraph(_pdf_escape(label), styles["ReportTitle"]))
                title_seen = True
            elif tag.lower() == "h3":
                flowables.append(Paragraph(_pdf_escape(label), styles["SubHeading"]))
            else:
                flowables.append(Paragraph(_pdf_escape(label), styles["SectionHeading"]))
            continue

        for block in _plain_blocks(part):
            if not title_seen and "executive dispatch report" in block.lower():
                flowables.append(Paragraph("Executive Dispatch Report", styles["ReportTitle"]))
                title_seen = True
            else:
                flowables.append(Paragraph(_pdf_escape(_strip_tags(block)), styles["ReportBody"]))

    return flowables or [Paragraph("(empty report)", styles["ReportBody"])]


def _page_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(0.6 * inch, 0.38 * inch, "SeeWeeS Specialty Dispatch Report")
    canvas.drawRightString(LETTER[0] - 0.6 * inch, 0.38 * inch, f"Page {doc.page}")
    canvas.restoreState()


def write_report_pdf(report_text: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_dir, f"dispatch_report_{ts}.pdf")

    doc = SimpleDocTemplate(
        out_path,
        pagesize=LETTER,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.6 * inch,
        title="SeeWeeS Specialty Dispatch Report",
    )
    doc.build(_html_to_flowables(report_text), onFirstPage=_page_footer, onLaterPages=_page_footer)
    return out_path
