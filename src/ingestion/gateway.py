"""
Ingestion Gateway: MIME-type detection and routing to appropriate parsers.

This module acts as the entry point for the pipeline's data ingestion layer,
conceptually simulating Cotiviti's Edifecs interoperability gateway.
"""
import os
from dataclasses import dataclass, field
from typing import Optional

from src.config import (
    SUPPORTED_TEXT_TYPES,
    SUPPORTED_PDF_TYPES,
    SUPPORTED_DOCX_TYPES,
    SUPPORTED_IMAGE_TYPES,
    ALL_SUPPORTED_TYPES,
)
from src.ingestion.text_parser import parse_text_file
from src.ingestion.pdf_parser import parse_pdf_file
from src.ingestion.docx_parser import parse_docx_file


@dataclass
class DocumentPayload:
    """Normalized output from the ingestion gateway."""

    file_path: str
    file_name: str
    file_type: str  # Extension, e.g. ".pdf"
    modality: str  # "text", "pdf", "docx", "image"
    raw_text: Optional[str] = None  # Extracted text (None for images until OCR)
    is_image: bool = False
    metadata: dict = field(default_factory=dict)


def detect_modality(file_path: str) -> str:
    """Determine the modality category from the file extension.

    Args:
        file_path: Path to the file.

    Returns:
        One of: "text", "pdf", "docx", "image"

    Raises:
        ValueError: If the file type is not supported.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext in SUPPORTED_TEXT_TYPES:
        return "text"
    elif ext in SUPPORTED_PDF_TYPES:
        return "pdf"
    elif ext in SUPPORTED_DOCX_TYPES:
        return "docx"
    elif ext in SUPPORTED_IMAGE_TYPES:
        return "image"
    else:
        raise ValueError(
            f"Unsupported file type '{ext}' for file: {file_path}. "
            f"Supported types: {ALL_SUPPORTED_TYPES}"
        )


def ingest_file(file_path: str) -> DocumentPayload:
    """Ingest a single file through the gateway.

    Detects the file type, routes to the appropriate parser, and returns
    a normalized DocumentPayload. Image files are marked for OCR processing
    in a subsequent pipeline stage.

    Args:
        file_path: Absolute path to the file to ingest.

    Returns:
        A DocumentPayload with extracted text (or None for images).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file type is unsupported or parsing fails.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_name = os.path.basename(file_path)
    file_type = os.path.splitext(file_path)[1].lower()
    modality = detect_modality(file_path)

    payload = DocumentPayload(
        file_path=file_path,
        file_name=file_name,
        file_type=file_type,
        modality=modality,
        metadata={
            "file_size_bytes": os.path.getsize(file_path),
        },
    )

    if modality == "text":
        payload.raw_text = parse_text_file(file_path)
    elif modality == "pdf":
        payload.raw_text = parse_pdf_file(file_path)
    elif modality == "docx":
        payload.raw_text = parse_docx_file(file_path)
    elif modality == "image":
        payload.is_image = True
        # raw_text remains None — will be filled by OCR stage
    else:
        raise ValueError(f"Unhandled modality: {modality}")

    return payload
