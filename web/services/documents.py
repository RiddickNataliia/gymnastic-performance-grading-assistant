import pandas as pd
from datetime import datetime
import zipfile
import os

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

class DocumentService():
    @classmethod
    def generate_pdf_elements(self, exercise: str, data: pd.DataFrame, first_name: str, last_name: str, now: datetime):
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title", parent=styles["Heading1"], alignment=1, spaceAfter=12)
        footer_style = ParagraphStyle("Footer", parent=styles["Normal"], alignment=0, fontSize=8, textColor=colors.grey)
        
        elements.append(Paragraph(f"Results: {exercise} {first_name} {last_name}", title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        table_data = [list(data.columns)] + data.values.tolist()
        
        wrapped_table_data = []
        for row in table_data:
            wrapped_row = [Paragraph(str(cell), styles["Normal"]) for cell in row]
            wrapped_table_data.append(wrapped_row)
        
        results_table = Table(wrapped_table_data)
        results_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.dodgerblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white])
        ]))
        elements.append(results_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        elements.append(Paragraph(now.strftime("%Y/%m/%d - %H:%M"), footer_style))
        
        return elements

    @classmethod
    def create_pdf(self, pdf_filename: str, elements: list):
        doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
        doc.build(elements)

    @classmethod
    def create_csv(self, csv_filename: str, data: pd.DataFrame):
        data.to_csv(csv_filename, index=False)

    @classmethod
    def create_zipfile(self, zip_filename: str, video_path: str, csv_filename: str, pdf_filename: str, base_name: str):
        video_ext = os.path.splitext(video_path)[1]

        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            zipf.write(csv_filename)
            zipf.write(pdf_filename)
            zipf.write(video_path, arcname=f"{base_name}{video_ext}")

    @classmethod
    def remove_files(self, files: list[str]):
        for f in files:
            if os.path.exists(f):
                os.remove(f)