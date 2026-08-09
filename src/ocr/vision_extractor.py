"""
Vision-based OCR extractor using Ollama's llama3.2-vision model.

Primary OCR path — sends images directly to the vision model for rich
contextual text extraction that understands clinical document layouts.
"""
import base64
import json
import requests
from dataclasses import dataclass
from typing import Optional

from src.config import OLLAMA_BASE_URL, VISION_MODEL


@dataclass
class VisionOCRResult:
    """Result from the vision model OCR extraction."""

    extracted_text: str
    confidence: float  # 0.0 to 1.0
    model_used: str
    raw_response: Optional[str] = None


def _encode_image_base64(image_path: str) -> str:
    """Read an image file and return its base64-encoded string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_text_with_vision(image_path: str) -> VisionOCRResult:
    """Extract text from an image using the Ollama vision model.

    Sends the image to llama3.2-vision with a prompt optimized for
    clinical document OCR. The model returns both the extracted text
    and a self-assessed confidence score.

    Args:
        image_path: Absolute path to the image file.

    Returns:
        VisionOCRResult with extracted text and confidence.

    Raises:
        ConnectionError: If Ollama is not running.
        RuntimeError: If the vision model fails to process the image.
    """
    image_b64 = _encode_image_base64(image_path)

    prompt = (
        "You are a clinical document OCR system. Extract ALL visible text from this "
        "medical document image exactly as written. Preserve the original formatting, "
        "line breaks, and structure. Do not interpret or summarize — just transcribe. "
        "After the transcription, on a new line, provide a confidence score between "
        "0.0 and 1.0 indicating how readable the document was, in the format: "
        "CONFIDENCE: 0.XX"
    )

    payload = {
        "model": VISION_MODEL,
        "prompt": prompt,
        "images": [image_b64],
        "stream": False,
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
    except requests.ConnectionError:
        raise ConnectionError(
            f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
            "Ensure Ollama is running with: ollama serve"
        )
    except requests.RequestException as e:
        raise RuntimeError(f"Vision OCR request failed: {e}")

    result = response.json()
    raw_text = result.get("response", "")

    # Parse confidence from the model's response
    extracted_text, confidence = _parse_vision_response(raw_text)

    return VisionOCRResult(
        extracted_text=extracted_text,
        confidence=confidence,
        model_used=VISION_MODEL,
        raw_response=raw_text,
    )


def _parse_vision_response(raw_text: str) -> tuple[str, float]:
    """Parse the vision model's response to separate text from confidence.

    Args:
        raw_text: The raw response from the vision model.

    Returns:
        Tuple of (extracted_text, confidence_score).
    """
    lines = raw_text.strip().split("\n")
    confidence = 0.5  # Default if not parseable
    text_lines = []

    for line in lines:
        if line.strip().upper().startswith("CONFIDENCE:"):
            try:
                conf_str = line.split(":", 1)[1].strip()
                confidence = float(conf_str)
                confidence = max(0.0, min(1.0, confidence))
            except (ValueError, IndexError):
                confidence = 0.5
        else:
            text_lines.append(line)

    extracted_text = "\n".join(text_lines).strip()

    if not extracted_text:
        confidence = 0.0

    return extracted_text, confidence
