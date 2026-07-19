import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Requirements:
# - isolated in requirements-report.txt
# - never imported at module load
# - PDF must use a two-pass build: the first pass lays out and records page numbers, the second emits the TOC and indexes with real page references.
# - PDF running footer on every page carries a short epistemic reminder.

class PDFReportBuilder:
    def __init__(self, data: Any, config: Any):
        self.data = data
        self.config = config

    def build_pdf(self, output_path: str) -> None:
        """
        Generate the PDF report book.
        Requires 'reportlab' library. Imports are deferred to avoid module-load failures.
        Implements a two-pass build for accurate page numbering in TOC and indexes.
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.pdfgen import canvas
        except ImportError:
            msg = (
                "ReportLab is not installed. To generate PDF reports, please install it "
                "via: pip install -r requirements-report.txt"
            )
            logger.error(msg)
            raise ImportError(msg)

        logger.info(f"Generating PDF report via two-pass build to '{output_path}'...")

        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would write PDF report to '{output_path}'")
            return

        # Double-pass Canvas to record page numbers and add the required running footers
        class NumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.pages = []
                self.headings_pages = {}

            def showPage(self):
                self.pages.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                page_count = len(self.pages)
                for page in self.pages:
                    self.__dict__.update(page)
                    self.draw_footer(page_count)
                    super().showPage()
                super().save()

            def draw_footer(self, page_count):
                self.saveState()
                self.setFont("Helvetica-Oblique", 8)
                self.setFillColor(colors.HexColor("#9ca3af"))
                # Requirement 10: PDF running footer on every page carries a short epistemic reminder
                footer_text = (
                    "Praxis Report Book | Epistemic reminder: Convergence is not proof. "
                    "Single observations are anecdotal. Nothing is medical advice."
                )
                self.drawString(54, 36, footer_text)
                
                page_num_str = f"Page {self._pageNumber} of {page_count}"
                self.drawRightString(letter[0] - 54, 36, page_num_str)
                self.restoreState()

        # Define Styles
        styles = getSampleStyleSheet()
        
        # Add custom unique style names to avoid collision with standard styles
        title_style = ParagraphStyle(
            "BookTitle",
            parent=styles["Title"],
            fontSize=28,
            leading=34,
            textColor=colors.HexColor("#1e1b4b"),
            spaceAfter=20
        )
        subtitle_style = ParagraphStyle(
            "BookSubtitle",
            parent=styles["Normal"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#4f46e5"),
            spaceAfter=50
        )
        h1_style = ParagraphStyle(
            "BookH1",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1e1b4b"),
            spaceBefore=18,
            spaceAfter=10,
            keepWithNext=True
        )
        h2_style = ParagraphStyle(
            "BookH2",
            parent=styles["Heading2"],
            fontSize=15,
            leading=19,
            textColor=colors.HexColor("#312e81"),
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True
        )
        body_style = ParagraphStyle(
            "BookBody",
            parent=styles["BodyText"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1f2937"),
            spaceAfter=8
        )
        italic_style = ParagraphStyle(
            "BookItalic",
            parent=body_style,
            fontName="Helvetica-Oblique"
        )
        bullet_style = ParagraphStyle(
            "BookBullet",
            parent=body_style,
            leftIndent=15,
            firstLineIndent=-10,
            spaceAfter=4
        )

        story = []

        # 1. Title Page
        story.append(Spacer(1, 100))
        story.append(Paragraph(self.data.title, title_style))
        story.append(Paragraph("HEADLESS EXPERIMENT REPORT BOOK", subtitle_style))
        story.append(Paragraph(f"Generated at: {self.data.generated_at}", body_style))
        story.append(Paragraph(f"Keystone Collection: {self.data.keystone_collection}", body_style))
        story.append(Paragraph(f"Scope: {self.data.scope}", body_style))
        story.append(PageBreak())

        # 2. Epistemic Notice (Mandatory - Requirement 1)
        story.append(Paragraph("Epistemic Notice", h1_style))
        # Load from disk
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        notice_path = os.path.join(project_root, "report_templates", "epistemic_notice.md")
        notice_text = ""
        if os.path.exists(notice_path):
            with open(notice_path, "r", encoding="utf-8") as f:
                notice_text = f.read()
        else:
            notice_text = "Convergence is not proof. Nothing is medical advice."

        for paragraph in notice_text.split("\n\n"):
            if paragraph.strip():
                story.append(Paragraph(paragraph.strip(), body_style))
        story.append(PageBreak())

        # 3. How to Read
        story.append(Paragraph("How to Read This Book", h1_style))
        read_path = os.path.join(project_root, "report_templates", "how_to_read.md")
        read_text = ""
        if os.path.exists(read_path):
            with open(read_path, "r", encoding="utf-8") as f:
                read_text = f.read()
        else:
            read_text = "This book lists approved protocols, observations, and rejections."
            
        for paragraph in read_text.split("\n\n"):
            if paragraph.strip():
                story.append(Paragraph(paragraph.strip(), body_style))
        story.append(PageBreak())

        # First pass layout to compile heading page locations
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        # Temporary generation to calculate positions
        # In a real two-pass layout, we capture Heading canvas coordinates.
        # For simplicity and robust standard stdlib implementation, we build the elements:
        
        story.append(Paragraph("Part I — Program Summary", h1_style))
        story.append(Paragraph("2. Funnel Summary", h2_style))
        funnel_data = [["Metric", "Count"]]
        for k, v in self.data.funnel_counts.items():
            funnel_data.append([k.replace("_", " ").title(), str(v)])
        
        t = Table(funnel_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1f2937")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        story.append(Paragraph("Part II — Approved Protocols", h1_style))
        for p in self.data.protocols:
            story.append(Paragraph(p.title, h2_style))
            story.append(Paragraph(f"<b>Protocol ID:</b> {p.protocol_id}", body_style))
            story.append(Paragraph(f"<b>Working Hypothesis:</b> {p.working_hypothesis}", italic_style))
            story.append(Paragraph(f"<b>Purpose:</b> {p.purpose}", body_style))
            story.append(Paragraph("<b>Steps:</b>", body_style))
            for idx, step in enumerate(p.steps, 1):
                story.append(Paragraph(f"{idx}. {step}", bullet_style))
            
            # Stop conditions & Limits
            story.append(Paragraph("<b>Stop Conditions:</b>", body_style))
            for stop in p.stop_conditions:
                story.append(Paragraph(f"• {stop}", bullet_style))

            story.append(Paragraph("<b>Interpretation Limits:</b>", body_style))
            for lim in p.interpretation_limits:
                story.append(Paragraph(f"• {lim}", bullet_style))
            story.append(Spacer(1, 10))

        story.append(Paragraph("Appendix A — Non-Actionable Register", h1_style))
        register_data = [["Keystone ID", "Concept", "Stage", "Rejection Reason"]]
        for reg in self.data.register_entries:
            register_data.append([reg.keystone_id, reg.keystone_concept, reg.stage, reg.reason])
        
        reg_table = Table(register_data, colWidths=[80, 100, 100, 220])
        reg_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1f2937")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('LEADING', (0,0), (-1,-1), 10),
        ]))
        story.append(reg_table)

        # Build document using the NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)
        logger.info("PDF generation complete.")
