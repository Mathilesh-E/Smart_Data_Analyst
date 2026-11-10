"""
Module: Reporting & Serialization
Generates executive ReportLab PDF documents with dynamic canvas page numbering ("Page X of Y"),
as well as CSV, Excel (.xlsx), and JSON metadata packages.
"""
import io
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        if self._pageNumber > 1:
            self.drawString(54, 750, "Smart Data Analyst — Universal Analytics Executive Report")
            self.setStrokeColor(colors.HexColor("#334155"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_str)
        self.drawString(54, 36, f"Confidential & Automated Analysis • {datetime.now().strftime('%b %d, %Y')}")
        self.setStrokeColor(colors.HexColor("#334155"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        self.restoreState()

class ReportExporter:

    @staticmethod
    def generate_pdf(
        filename: str,
        df: pd.DataFrame,
        quality: Dict[str, Any],
        profile: Dict[str, Any],
        insights: List[Dict[str, Any]],
        cleaning_log: List[Dict[str, Any]] = None
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle("T1", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=colors.HexColor("#0f172a"), alignment=0)
        sub_style = ParagraphStyle("T2", parent=styles["Normal"], fontName="Helvetica", fontSize=10, leading=14, textColor=colors.HexColor("#64748b"))
        h1_style = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=colors.HexColor("#1e293b"), spaceBefore=14, spaceAfter=8)
        body_style = ParagraphStyle("B", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=13, textColor=colors.HexColor("#334155"))

        story = []
        story.append(Paragraph("Smart Data Analyst — Executive Report", title_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"Autonomous Profiling, Quality Audit, & Statistical Insights for <b>{filename}</b>", sub_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#6366f1"), spaceAfter=14))

        # Dataset Summary Table
        metrics = quality.get("metrics", {})
        score = quality.get("score", 0.0)
        status = quality.get("status", "N/A")

        summary_data = [
            [Paragraph("<b>Metric</b>", body_style), Paragraph("<b>Observed</b>", body_style), Paragraph("<b>Health Dimension</b>", body_style), Paragraph("<b>Audit Score</b>", body_style)],
            [Paragraph("Total Rows", body_style), Paragraph(f"{len(df):,}", body_style), Paragraph("Overall Health", body_style), Paragraph(f"<b>{score}/100</b> ({status})", body_style)],
            [Paragraph("Total Attributes", body_style), Paragraph(f"{len(df.columns):,}", body_style), Paragraph("Missing Cell Rate", body_style), Paragraph(f"{metrics.get('missing_pct', 0)}%", body_style)],
            [Paragraph("Total Cells", body_style), Paragraph(f"{len(df)*len(df.columns):,}", body_style), Paragraph("Duplicate Rows", body_style), Paragraph(f"{metrics.get('duplicate_rows', 0):,} ({metrics.get('duplicate_pct', 0)}%)", body_style)],
            [Paragraph("Completeness", body_style), Paragraph(f"{metrics.get('completeness_pct', 100)}%", body_style), Paragraph("Detected Outliers", body_style), Paragraph(f"{metrics.get('total_outliers', 0):,}", body_style)]
        ]
        t_sum = Table(summary_data, colWidths=[120, 120, 130, 134])
        t_sum.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5)
        ]))
        story.append(t_sum)
        story.append(Spacer(1, 12))

        # Quality Deductions
        story.append(Paragraph("1. Data Quality Deduction Audit", h1_style))
        story.append(Paragraph("Score is calculated as: <i>Q = 100 - (0.50M + 0.25D + 0.15C + 0.10I)</i>", body_style))
        story.append(Spacer(1, 6))

        deductions = quality.get("deductions", {})
        ded_table = [
            [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Weight</b>", body_style), Paragraph("<b>Deduction</b>", body_style)],
            [Paragraph("Missing Cells (M)", body_style), Paragraph("50%", body_style), Paragraph(f"-{deductions.get('missing', 0)} pts", body_style)],
            [Paragraph("Duplicate Rows (D)", body_style), Paragraph("25%", body_style), Paragraph(f"-{deductions.get('duplicates', 0)} pts", body_style)],
            [Paragraph("Constant Columns (C)", body_style), Paragraph("15%", body_style), Paragraph(f"-{deductions.get('constant', 0)} pts", body_style)],
            [Paragraph("Invalid / Empty Cells (I)", body_style), Paragraph("10%", body_style), Paragraph(f"-{deductions.get('invalid', 0)} pts", body_style)]
        ]
        t_ded = Table(ded_table, colWidths=[200, 140, 164])
        t_ded.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4)
        ]))
        story.append(t_ded)
        story.append(Spacer(1, 12))

        # Automated Insights
        story.append(Paragraph("2. Top Statistical Insights & Findings", h1_style))
        for item in insights[:8]:
            story.append(Paragraph(f"• <b>{item.get('title')}</b> — {item.get('description')}", body_style))
            story.append(Spacer(1, 4))

        # Cleaning Log
        if cleaning_log:
            story.append(Spacer(1, 10))
            story.append(Paragraph("3. Smart Cleaning Audit Trail", h1_style))
            c_table = [[Paragraph("<b>Time</b>", body_style), Paragraph("<b>Action</b>", body_style), Paragraph("<b>Target</b>", body_style), Paragraph("<b>Details</b>", body_style)]]
            for log in cleaning_log:
                c_table.append([
                    Paragraph(log.get("timestamp", ""), body_style),
                    Paragraph(log.get("action", ""), body_style),
                    Paragraph(log.get("column", ""), body_style),
                    Paragraph(log.get("description", ""), body_style)
                ])
            t_clean = Table(c_table, colWidths=[80, 110, 100, 214])
            t_clean.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f8fafc")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4)
            ]))
            story.append(t_clean)

        doc.build(story, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def to_csv_bytes(df: pd.DataFrame) -> bytes:
        return df.to_csv(index=False).encode("utf-8")

    @staticmethod
    def to_excel_bytes(df: pd.DataFrame) -> bytes:
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Cleaned_Data")
        return out.getvalue()

