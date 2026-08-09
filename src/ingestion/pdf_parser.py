"""
PDF parser using pypdf for extracting text from PDF documents.
"""
from pypdf import PdfReader


def parse_pdf_file(file_path: str) -> str:
    """Extract and concatenate text from all pages of a PDF.

    Args:
        file_path: Absolute path to the .pdf file.

    Returns:
        Concatenated text from all PDF pages.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If no text could be extracted.
        Exception: If the PDF is corrupt or unreadable.
    """
    reader = PdfReader(file_path)
    pages_text = []

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages_text.append(text.strip())

    if not pages_text:
        raise ValueError(
            f"No text could be extracted from PDF: {file_path}. "
            "The file may be image-based (scanned) or corrupt."
        )

    return "\n\n".join(pages_text)
