try:
    import pymupdf as fitz
except ImportError:
    import fitz
import io
import re
from typing import Union

def extract_text_from_pdf(pdf_source: Union[str, bytes, io.BytesIO]) -> str:
    """
    Extracts plain text from a PDF file using PyMuPDF (fitz).
    
    Args:
        pdf_source: Can be a file path (str), raw bytes (bytes), 
                    or a file-like object (io.BytesIO / Streamlit UploadedFile).
                    
    Returns:
        Extracted text as a clean string.
    """
    pdf_document = None
    try:
        if isinstance(pdf_source, str):
            pdf_document = fitz.open(pdf_source)
        elif isinstance(pdf_source, bytes):
            pdf_document = fitz.open(stream=pdf_source, filetype="pdf")
        elif hasattr(pdf_source, "read"):
            # Handle Streamlit UploadedFile or BytesIO
            file_bytes = pdf_source.read()
            # Reset stream position if possible
            if hasattr(pdf_source, "seek"):
                pdf_source.seek(0)
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        else:
            raise ValueError("Unsupported PDF input source type.")

        extracted_pages = []
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text = page.get_text("text")
            if text.strip():
                extracted_pages.append(text)

        full_text = "\n\n".join(extracted_pages)
        return clean_text(full_text)

    except Exception as e:
        raise RuntimeError(f"Error parsing PDF file: {str(e)}")
    finally:
        if pdf_document:
            pdf_document.close()

def clean_text(text: str) -> str:
    """
    Cleans and normalizes extracted text.
    """
    if not text:
        return ""
    # Replace non-breaking spaces and extra spaces
    text = text.replace('\xa0', ' ')
    # Normalize multiple newlines to double line breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Normalize spaces within lines
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.split('\n')]
    return '\n'.join(lines).strip()
