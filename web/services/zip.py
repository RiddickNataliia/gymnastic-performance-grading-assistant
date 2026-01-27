import pandas as pd
import zipfile
import os

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

class DocumentService():
    @classmethod
    def generate_pdf_elements(self, exercise: str, data: pd.DataFrame, first_name: str, last_name: str, time: str):
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

        parts = time.split("-")
        time_string_format = f"{parts[0]}/{parts[1]}/{parts[2]} - {parts[3]}:{parts[4]}:{parts[5]}"
        
        elements.append(Paragraph(time_string_format, footer_style))
        
        return elements

    @classmethod
    def create_pdf(self, pdf_filename: str, elements: list):
        doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
        doc.build(elements)

import os
import zipfile
from pathlib import Path

class ZipService():
    def __init__(self, export_path: str, rating_path: str, videos_path: str):
        self.export_path = export_path
        self.rating_path = rating_path
        self.videos_path = videos_path
    
    def create_zip(self, base_name: str, tmp_video_path: str):
        extension = Path(tmp_video_path).suffix
        export_path_base = f"{self.export_path}/{base_name}"
        zip_file = f"{export_path_base}.zip"

        pdf_arc = f"{base_name}.pdf"
        pdf_file = f"{export_path_base}.pdf"

        csv_arc = f"{base_name}.csv"
        video_arc = f"{base_name}{extension}"

        csv_path = f"{self.rating_path}/{csv_arc}"
        video_path = f"{self.videos_path}/{video_arc}"

        data = pd.read_csv(csv_path)
        data = data.replace("✅", "correct")

        parts = base_name.split("-")
        exercise = parts[0]
        first_name = parts[1]
        last_name = parts[2]
        time = "-".join(parts[3:9])

        elements = DocumentService.generate_pdf_elements(exercise, data, first_name, last_name, time)
        DocumentService.create_pdf(pdf_file, elements)

        with zipfile.ZipFile(zip_file, "w") as zipf:
            zipf.write(csv_path, csv_arc)
            zipf.write(video_path, video_arc)
            zipf.write(pdf_file, pdf_arc)

        if Path(pdf_file).exists():
            os.remove(pdf_file)

        return zip_file
