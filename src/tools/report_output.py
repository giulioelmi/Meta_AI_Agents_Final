from __future__ import annotations

import os
import re
from datetime import datetime

def _strip_html(text: str) -> str:
    no_tags = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", no_tags).strip()


def write_report_pdf(report_text: str, output_dir: str) -> str:
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.pdfgen import canvas
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency 'reportlab'. Install it with: pip install -r requirements.txt"
        ) from exc

    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_dir, f"dispatch_report_{ts}.pdf")

    pdf = canvas.Canvas(out_path, pagesize=LETTER)
    width, height = LETTER
    y = height - 50

    lines = _strip_html(report_text).splitlines() or ["(empty report)"]
    for raw in lines:
        line = raw.strip() or ""
        chunks = [line[i:i + 100] for i in range(0, len(line), 100)] or [""]
        for chunk in chunks:
            if y < 50:
                pdf.showPage()
                y = height - 50
            pdf.drawString(50, y, chunk)
            y -= 14

    pdf.save()
    return out_path
