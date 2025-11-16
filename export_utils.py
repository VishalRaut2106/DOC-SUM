import base64
from fpdf import FPDF
import streamlit as st


def export_as_pdf(content, filename):
    """Export content as a PDF file."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)
    pdf_output = pdf.output(dest="S").encode("latin-1")
    b64 = base64.b64encode(pdf_output)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download as PDF</a>'


def export_as_markdown(content, filename):
    """Export content as a Markdown file."""
    b64 = base64.b64encode(content.encode()).decode()
    return f'<a href="data:file/markdown;base64,{b64}" download="{filename}.md">Download as Markdown</a>'
