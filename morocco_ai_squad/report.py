from __future__ import annotations

from datetime import datetime
from io import BytesIO

from fpdf import FPDF


class SquadPDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(180, 20, 35)
        self.cell(0, 10, "Morocco World Cup 2026 AI Squad Analyzer", ln=True, align="C")
        self.ln(2)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Generated {datetime.utcnow():%Y-%m-%d %H:%M UTC}", align="C")


def build_pdf(report_text: str) -> bytes:
    pdf = SquadPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(30, 30, 30)

    for paragraph in report_text.split("\n"):
        line = paragraph.strip()
        if not line:
            pdf.ln(4)
            continue
        if len(line) < 55 and not line.endswith("."):
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(0, 110, 68)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 7, line, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", size=11)
            pdf.set_text_color(30, 30, 30)
        else:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 6, line, new_x="LMARGIN", new_y="NEXT")

    out = BytesIO()
    pdf.output(out)
    return out.getvalue()
