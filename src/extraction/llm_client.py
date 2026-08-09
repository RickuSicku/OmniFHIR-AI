"""
Ollama LLM client for structured clinical data extraction.

Wraps the Ollama HTTP API for both text (mistral) and vision (llama3.2-vision)
models with JSON format enforcement and retry logic.
"""
import json
import logging
import time
from typing import Optional

import requests

from src.config import OLLAMA_BASE_URL, EXTRACTION_MODEL
from src.extraction.prompts import build_extraction_prompt, EXTRACTION_JSON_SCHEMA
from src.extraction.schema import ExtractionResult, ClinicalExtraction

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # Exponential backoff: 2^retry seconds


def _call_ollama(
    model: str,
    prompt: str,
    format_json: bool = True,
    timeout: int = 120,
) -> str:
    """Make a raw API call to Ollama's generate endpoint.

    Args:
        model: The Ollama model name to use.
        prompt: The prompt string.
        format_json: If True, enforce JSON output format.
        timeout: Request timeout in seconds.

    Returns:
        The raw response text from the model.

    Raises:
        ConnectionError: If Ollama is not reachable.
        RuntimeError: If the model returns an error after retries.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if format_json:
        payload["format"] = "json"

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
                "Ensure Ollama is running: ollama serve"
            )
        except requests.RequestException as e:
            last_error = e
            wait_time = RETRY_BACKOFF_BASE ** attempt
            logger.warning(
                f"Ollama request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                f"Retrying in {wait_time}s..."
            )
            time.sleep(wait_time)

    raise RuntimeError(f"Ollama request failed after {MAX_RETRIES} retries: {last_error}")


def extract_clinical_data(clinical_text: str) -> ExtractionResult:
    """Extract structured clinical data from normalized text using the LLM.

    Sends the clinical text to the mistral model with a few-shot prompt
    and JSON format enforcement. Parses and validates the response into
    Pydantic models.

    Args:
        clinical_text: The normalized raw text from a medical document.

    Returns:
        ExtractionResult with validated clinical extractions.

    Raises:
        ConnectionError: If Ollama is not running.
        RuntimeError: If extraction fails after retries.
    """
    prompt = build_extraction_prompt(clinical_text)

    logger.info(f"Sending extraction request to {EXTRACTION_MODEL}...")
    raw_response = _call_ollama(
        model=EXTRACTION_MODEL,
        prompt=prompt,
        format_json=True,
    )

    logger.info(f"Received response ({len(raw_response)} chars). Parsing...")

    # Parse JSON response
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        return ExtractionResult(
            extractions=[],
            document_summary="LLM returned invalid JSON",
            raw_llm_response=raw_response,
        )

    # Build ExtractionResult from parsed JSON
    extractions = []
    raw_extractions = parsed.get("extractions", [])

    for ext_data in raw_extractions:
        try:
            extraction = ClinicalExtraction(
                patient_id=ext_data.get("patient_id", "UNKNOWN"),
                test_name=ext_data.get("test_name", "Unknown Test"),
                test_value=float(ext_data.get("test_value", 0)),
                test_unit=ext_data.get("test_unit", "%"),
                test_date=ext_data.get("test_date"),
                source_snippet=ext_data.get("source_snippet", ""),
                confidence_score=float(ext_data.get("confidence_score", 0.5)),
            )
            extractions.append(extraction)
        except Exception as e:
            logger.warning(f"Skipping invalid extraction entry: {e}")
            continue

    result = ExtractionResult(
        extractions=extractions,
        document_summary=parsed.get("document_summary", ""),
        raw_llm_response=raw_response,
    )

    logger.info(
        f"Extraction complete: {len(extractions)} clinical data points found. "
        f"Primary: {result.primary_extraction}"
    )

    return result
