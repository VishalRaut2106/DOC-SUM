import io
import PyPDF2
import pytesseract
from PIL import Image
import streamlit as st
# Define a file size limit in bytes (e.g., 10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n\n"
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def extract_text_from_image(image_file):
    """Extract text from an image using OCR."""
    try:
        # Open the image using PIL
        image = Image.open(image_file)
        
        # Use pytesseract to extract text
        text = pytesseract.image_to_string(image, lang='eng')
        return text
    except Exception as e:
        st.error(f"Error extracting text from image: {str(e)}")
        return ""

def process_file(uploaded_file):
    """Process the uploaded file and extract text."""
    if uploaded_file is None:
        return ""
    
    # Check if the file size is within the limit
    if uploaded_file.size > MAX_FILE_SIZE:
        st.error(f"File size exceeds the limit of {MAX_FILE_SIZE / (1024 * 1024)} MB.")
        return ""

    # Get the file type
    file_type = uploaded_file.type
    
    # Process based on file type
    if "pdf" in file_type:
        return extract_text_from_pdf(uploaded_file)
    elif "image" in file_type:
        return extract_text_from_image(uploaded_file)
    else:
        st.error("Unsupported file type. Please upload a PDF or image file.")
        return "" 