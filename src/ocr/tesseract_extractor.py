"""
Tesseract-based OCR extractor using pytesseract.

Fallback OCR path — used when the vision model's confidence falls below
the configured threshold, or for cross-validation of vision results.
"""
from dataclasses import dataclass
from typing import Optional

import pytesseract
from PIL import Image


@dataclass
class TesseractOCRResult:
    """Result from Tesseract OCR extraction."""

    extracted_text: str
    confidence: float  # Average word confidence 0.0 to 1.0
    raw_data: Optional[dict] = None


def extract_text_with_tesseract(image_path: str) -> TesseractOCRResult:
    """Extract text from an image using Tesseract OCR.

    Opens the image, runs Tesseract with detailed data output to calculate
    per-word confidence, and returns the extracted text with an average
    confidence score.

    Args:
        image_path: Absolute path to the image file.

    Returns:
        TesseractOCRResult with extracted text and confidence.

    Raises:
        RuntimeError: If Tesseract is not installed or fails.
    """
    try:
        img = Image.open(image_path)
    except Exception as e:
        raise RuntimeError(f"Cannot open image for Tesseract OCR: {e}")

    # Get detailed data with per-word confidence scores
    try:
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract OCR is not installed. Install it from: "
            "https://github.com/tesseract-ocr/tesseract"
        )
    except Exception as e:
        raise RuntimeError(f"Tesseract OCR failed: {e}")

    # Build text and calculate average confidence
    words = []
    confidences = []

    for i, word in enumerate(data["text"]):
        word = word.strip()
        if word:
            words.append(word)
            conf = int(data["conf"][i])
            if conf > 0:  # Tesseract uses -1 for non-word elements
                confidences.append(conf)

    extracted_text = " ".join(words)
    avg_confidence = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0

    return TesseractOCRResult(
        extracted_text=extracted_text,
        confidence=round(avg_confidence, 3),
        raw_data=data,
    )
