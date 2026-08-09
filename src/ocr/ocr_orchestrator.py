"""
OCR Orchestrator: Dual-channel OCR with vision-primary, Tesseract fallback,
and cross-validation discrepancy detection.

Pipeline:
1. Run vision model OCR (primary)
2. If confidence < threshold → run Tesseract (fallback)
3. If both ran → cross-check with fuzzy matching, flag discrepancies
"""
import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Optional

from src.config import CONFIDENCE_THRESHOLD, OCR_DISCREPANCY_THRESHOLD
from src.ocr.vision_extractor import extract_text_with_vision, VisionOCRResult
from src.ocr.tesseract_extractor import extract_text_with_tesseract, TesseractOCRResult

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Consolidated result from the dual-channel OCR orchestrator."""

    final_text: str
    final_confidence: float
    primary_source: str  # "vision" or "tesseract"
    vision_result: Optional[VisionOCRResult] = None
    tesseract_result: Optional[TesseractOCRResult] = None
    fallback_triggered: bool = False
    discrepancy_detected: bool = False
    discrepancy_score: Optional[float] = None  # Similarity ratio 0.0-1.0
    flags: list[str] = field(default_factory=list)


def _compute_similarity(text_a: str, text_b: str) -> float:
    """Compute fuzzy similarity ratio between two text strings.

    Uses difflib's SequenceMatcher for a quick, reasonable similarity metric.

    Args:
        text_a: First text string.
        text_b: Second text string.

    Returns:
        Similarity ratio between 0.0 (completely different) and 1.0 (identical).
    """
    if not text_a or not text_b:
        return 0.0

    # Normalize: lowercase and collapse whitespace for comparison
    norm_a = " ".join(text_a.lower().split())
    norm_b = " ".join(text_b.lower().split())

    return SequenceMatcher(None, norm_a, norm_b).ratio()


def run_ocr(image_path: str) -> OCRResult:
    """Execute the dual-channel OCR pipeline on an image.

    1. Attempt vision model OCR (primary).
    2. If vision confidence < threshold, fall back to Tesseract.
    3. If both results exist, cross-validate and flag discrepancies.

    Args:
        image_path: Absolute path to the image file.

    Returns:
        OCRResult with the best extracted text and audit metadata.
    """
    result = OCRResult(
        final_text="",
        final_confidence=0.0,
        primary_source="vision",
    )

    # ── Step 1: Vision Model OCR (Primary) ──────────────────────────────
    try:
        vision_result = extract_text_with_vision(image_path)
        result.vision_result = vision_result
        result.final_text = vision_result.extracted_text
        result.final_confidence = vision_result.confidence
        logger.info(
            f"Vision OCR completed: confidence={vision_result.confidence:.2f}, "
            f"chars={len(vision_result.extracted_text)}"
        )
    except Exception as e:
        logger.warning(f"Vision OCR failed: {e}. Falling back to Tesseract.")
        result.flags.append(f"VISION_FAILED: {str(e)}")
        result.fallback_triggered = True

    # ── Step 2: Tesseract Fallback ──────────────────────────────────────
    needs_fallback = (
        result.fallback_triggered
        or result.final_confidence < CONFIDENCE_THRESHOLD
        or not result.final_text.strip()
    )

    if needs_fallback:
        result.fallback_triggered = True
        logger.info("Tesseract fallback triggered.")

        try:
            tesseract_result = extract_text_with_tesseract(image_path)
            result.tesseract_result = tesseract_result

            # Use Tesseract result if vision failed or Tesseract is more confident
            if not result.final_text.strip() or (
                tesseract_result.confidence > result.final_confidence
            ):
                result.final_text = tesseract_result.extracted_text
                result.final_confidence = tesseract_result.confidence
                result.primary_source = "tesseract"
                logger.info(
                    f"Using Tesseract result: confidence={tesseract_result.confidence:.2f}"
                )
        except Exception as e:
            logger.error(f"Tesseract OCR also failed: {e}")
            result.flags.append(f"TESSERACT_FAILED: {str(e)}")

    # ── Step 3: Cross-Validation ────────────────────────────────────────
    if result.vision_result and result.tesseract_result:
        vision_text = result.vision_result.extracted_text
        tesseract_text = result.tesseract_result.extracted_text

        if vision_text and tesseract_text:
            similarity = _compute_similarity(vision_text, tesseract_text)
            result.discrepancy_score = round(similarity, 3)

            if similarity < OCR_DISCREPANCY_THRESHOLD:
                result.discrepancy_detected = True
                result.flags.append(
                    f"OCR_DISCREPANCY: Vision and Tesseract outputs differ "
                    f"(similarity={similarity:.2f} < threshold={OCR_DISCREPANCY_THRESHOLD}). "
                    f"Flagged for human review."
                )
                logger.warning(
                    f"OCR discrepancy detected: similarity={similarity:.2f}. "
                    "Document flagged for HITL review."
                )

    # Final validation
    if not result.final_text.strip():
        result.flags.append("NO_TEXT_EXTRACTED: Both OCR channels produced empty output.")
        result.final_confidence = 0.0

    return result
