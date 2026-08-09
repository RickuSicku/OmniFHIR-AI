"""
OmniFHIR-AI Pipeline Orchestrator

End-to-end orchestration of the clinical data extraction pipeline:
  1. Ingest → gateway (detect type, parse/OCR)
  2. Extract → LLM (structured JSON via mistral)
  3. Validate → Pydantic schema validation
  4. Evaluate → HEDIS compliance rules engine
  5. Build FHIR → validated Observation resource
  6. Persist → save all artifacts to SQLite

Each stage is wrapped in try/except for graceful degradation.
Failed documents are logged to provenance and processing continues.
"""
import json
import logging
import os
from typing import Optional

from src.config import (
    EXTRACTION_MODEL,
    VISION_MODEL,
    STAGE_INGESTION,
    STAGE_OCR,
    STAGE_EXTRACTION,
    STAGE_VALIDATION,
    STAGE_RULES,
    STAGE_FHIR,
    STAGE_PERSIST,
    STATUS_COMPLETED,
    STATUS_FAILED,
    CONFIDENCE_THRESHOLD,
)
from src.db.models import initialize_database
from src.db import repository as repo
from src.ingestion.gateway import ingest_file, DocumentPayload
from src.ocr.ocr_orchestrator import run_ocr
from src.extraction.llm_client import extract_clinical_data
from src.extraction.schema import ExtractionResult
from src.rules.engine import RulesEngine
from src.fhir.observation_builder import build_observation, observation_to_dict
from src.provenance.tracker import ProvenanceTracker

logger = logging.getLogger(__name__)


def process_single_document(
    file_path: str,
    batch_id: Optional[int] = None,
) -> dict:
    """Process a single document through the full pipeline.

    Args:
        file_path: Absolute path to the medical document.
        batch_id: Optional batch ID for grouping.

    Returns:
        A dict with processing results and status.
    """
    filename = os.path.basename(file_path)
    logger.info(f"{'='*60}")
    logger.info(f"Processing: {filename}")
    logger.info(f"{'='*60}")

    # Initialize the rules engine
    rules_engine = RulesEngine()

    # Create document record in DB
    file_type = os.path.splitext(file_path)[1].lower()
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    doc_id = repo.create_document(
        filename=filename,
        file_type=file_type,
        file_path=file_path,
        modality="unknown",
        file_size_bytes=file_size,
        batch_id=batch_id,
    )

    tracker = ProvenanceTracker(document_id=doc_id, batch_id=batch_id)
    result = {"doc_id": doc_id, "filename": filename, "status": STATUS_FAILED}

    # ── Stage 1: Ingestion ──────────────────────────────────────────────
    tracker.start_stage(STAGE_INGESTION)
    try:
        payload = ingest_file(file_path)
        repo.update_document_status(doc_id, "PROCESSING")
        # Update modality now that we know it
        from src.db.models import get_connection
        conn = get_connection()
        conn.execute("UPDATE documents SET modality = ? WHERE id = ?", (payload.modality, doc_id))
        conn.commit()
        conn.close()

        tracker.complete_stage(
            output_summary=f"Ingested as {payload.modality}. "
            f"Text length: {len(payload.raw_text or '')} chars. "
            f"Is image: {payload.is_image}",
            metadata={"modality": payload.modality, "file_size": payload.metadata.get("file_size_bytes", 0)},
        )
    except Exception as e:
        tracker.fail_stage(f"Ingestion failed: {str(e)}")
        repo.update_document_status(doc_id, STATUS_FAILED, f"FAILED_AT_{STAGE_INGESTION}: {str(e)}")
        result["error"] = f"FAILED_AT_{STAGE_INGESTION}: {str(e)}"
        return result

    # ── Stage 2: OCR (images only) ─────────────────────────────────────
    if payload.is_image:
        tracker.start_stage(STAGE_OCR, model_used=VISION_MODEL)
        try:
            ocr_result = run_ocr(file_path)
            payload.raw_text = ocr_result.final_text

            ocr_metadata = {
                "primary_source": ocr_result.primary_source,
                "confidence": ocr_result.final_confidence,
                "fallback_triggered": ocr_result.fallback_triggered,
                "discrepancy_detected": ocr_result.discrepancy_detected,
                "discrepancy_score": ocr_result.discrepancy_score,
                "flags": ocr_result.flags,
            }

            tracker.complete_stage(
                output_summary=f"OCR via {ocr_result.primary_source}. "
                f"Confidence: {ocr_result.final_confidence:.2f}. "
                f"Text length: {len(ocr_result.final_text)} chars. "
                f"Fallback: {ocr_result.fallback_triggered}. "
                f"Discrepancy: {ocr_result.discrepancy_detected}",
                metadata=ocr_metadata,
            )

            if not payload.raw_text.strip():
                raise ValueError("OCR produced no text output")

        except Exception as e:
            tracker.fail_stage(f"OCR failed: {str(e)}")
            repo.update_document_status(doc_id, STATUS_FAILED, f"FAILED_AT_{STAGE_OCR}: {str(e)}")
            result["error"] = f"FAILED_AT_{STAGE_OCR}: {str(e)}"
            return result

    # Verify we have text to work with
    if not payload.raw_text or not payload.raw_text.strip():
        error_msg = "No text available for extraction (file may be empty)"
        tracker.start_stage(STAGE_EXTRACTION)
        tracker.fail_stage(error_msg)
        repo.update_document_status(doc_id, STATUS_FAILED, f"FAILED_AT_{STAGE_EXTRACTION}: {error_msg}")
        result["error"] = f"FAILED_AT_{STAGE_EXTRACTION}: {error_msg}"
        return result

    # ── Stage 3: LLM Extraction ────────────────────────────────────────
    tracker.start_stage(STAGE_EXTRACTION, model_used=EXTRACTION_MODEL)
    try:
        extraction_result = extract_clinical_data(payload.raw_text)

        if not extraction_result.has_extractions:
            raise ValueError("LLM found no clinical data points in the document")

        primary = extraction_result.primary_extraction
        tracker.complete_stage(
            output_summary=f"Extracted {len(extraction_result.extractions)} data point(s). "
            f"Primary: {primary.test_name}={primary.test_value}{primary.test_unit} "
            f"(confidence: {primary.confidence_score:.2f})",
            metadata={
                "num_extractions": len(extraction_result.extractions),
                "primary_value": primary.test_value,
                "confidence": primary.confidence_score,
            },
        )
    except Exception as e:
        tracker.fail_stage(f"Extraction failed: {str(e)}")
        repo.update_document_status(doc_id, STATUS_FAILED, f"FAILED_AT_{STAGE_EXTRACTION}: {str(e)}")
        result["error"] = f"FAILED_AT_{STAGE_EXTRACTION}: {str(e)}"
        return result

    # ── Stage 3b: Validation ───────────────────────────────────────────
    primary = extraction_result.primary_extraction
    tracker.start_stage(STAGE_VALIDATION)
    try:
        # Pydantic validation already happened during extraction
        # This stage is for additional business logic validation
        if primary.confidence_score < CONFIDENCE_THRESHOLD:
            logger.warning(
                f"Low confidence extraction ({primary.confidence_score:.2f} < {CONFIDENCE_THRESHOLD}). "
                "Document will be flagged for priority review."
            )

        tracker.complete_stage(
            output_summary=f"Validation passed. Value: {primary.test_value}{primary.test_unit}. "
            f"Confidence: {primary.confidence_score:.2f}",
        )
    except Exception as e:
        tracker.fail_stage(f"Validation failed: {str(e)}")
        repo.update_document_status(doc_id, STATUS_FAILED, f"FAILED_AT_{STAGE_VALIDATION}: {str(e)}")
        result["error"] = f"FAILED_AT_{STAGE_VALIDATION}: {str(e)}"
        return result

    # Save extraction to DB
    extraction_id = repo.create_extraction(
        document_id=doc_id,
        raw_text=payload.raw_text,
        extracted_json=extraction_result.raw_llm_response or "",
        patient_id=primary.patient_id,
        test_name=primary.test_name,
        test_value=primary.test_value,
        test_unit=primary.test_unit,
        test_date=primary.test_date,
        source_snippet=primary.source_snippet,
        confidence_score=primary.confidence_score,
        model_used=EXTRACTION_MODEL,
        document_summary=extraction_result.document_summary or "",
    )

    # ── Stage 4: HEDIS Rules Engine ────────────────────────────────────
    tracker.start_stage(STAGE_RULES)
    compliance = None
    try:
        compliance = rules_engine.evaluate_by_test_name(
            test_name=primary.test_name,
            value=primary.test_value,
            unit=primary.test_unit,
        )

        if compliance:
            tracker.complete_stage(
                output_summary=f"{compliance.status}: {primary.test_value}{primary.test_unit} "
                f"(threshold: {compliance.threshold_description})",
                metadata={
                    "is_compliant": compliance.is_compliant,
                    "measure": compliance.measure_name,
                },
            )

            repo.create_compliance_result(
                extraction_id=extraction_id,
                document_id=doc_id,
                measure_name=compliance.measure_name,
                loinc_code=compliance.loinc_code,
                evaluated_value=compliance.evaluated_value,
                is_compliant=compliance.is_compliant,
                status=compliance.status,
                detail=compliance.detail,
                measure_id=getattr(compliance, "measure_id", ""),
                evaluated_unit=compliance.evaluated_unit,
                threshold_description=compliance.threshold_description,
            )
        else:
            tracker.complete_stage(
                output_summary="No matching HEDIS rule found for this test",
            )

    except Exception as e:
        tracker.fail_stage(f"Rules evaluation failed: {str(e)}")
        # Non-fatal: continue to FHIR generation even without compliance

    # ── Stage 5: FHIR Output ──────────────────────────────────────────
    tracker.start_stage(STAGE_FHIR)
    try:
        observation = build_observation(
            extraction=primary,
            compliance=compliance,
            source_file=filename,
        )
        fhir_json = observation.model_dump_json(exclude_none=True)

        tracker.complete_stage(
            output_summary=f"Built FHIR Observation: {observation.id}. "
            f"LOINC: {compliance.loinc_code if compliance else 'N/A'}",
        )

        repo.create_fhir_output(
            extraction_id=extraction_id,
            document_id=doc_id,
            fhir_json=fhir_json,
            observation_id=observation.id or "",
            is_valid=True,
        )
    except Exception as e:
        tracker.fail_stage(f"FHIR generation failed: {str(e)}")
        # Non-fatal: document is still marked as completed

    # ── Stage 6: Finalize ─────────────────────────────────────────────
    repo.update_document_status(doc_id, STATUS_COMPLETED)
    result["status"] = STATUS_COMPLETED
    result["patient_id"] = primary.patient_id
    result["test_value"] = primary.test_value
    result["test_unit"] = primary.test_unit
    result["confidence"] = primary.confidence_score
    result["compliance"] = compliance.status if compliance else "N/A"

    logger.info(
        f"✓ Completed: {filename} → {primary.test_name}={primary.test_value}{primary.test_unit} "
        f"→ {compliance.status if compliance else 'No rule matched'}"
    )

    return result


def process_batch(file_paths: list[str]) -> dict:
    """Process a batch of documents through the pipeline.

    Args:
        file_paths: List of absolute paths to medical documents.

    Returns:
        Batch summary with per-file results.
    """
    initialize_database()

    batch_id = repo.create_batch(total_files=len(file_paths))
    results = []
    success_count = 0
    failed_count = 0

    logger.info(f"Starting batch {batch_id}: {len(file_paths)} file(s)")

    for i, file_path in enumerate(file_paths, 1):
        logger.info(f"\n[Batch {batch_id}] Processing file {i}/{len(file_paths)}")

        result = process_single_document(file_path, batch_id=batch_id)
        results.append(result)

        if result["status"] == STATUS_COMPLETED:
            success_count += 1
        else:
            failed_count += 1

        repo.update_batch_progress(
            batch_id=batch_id,
            processed=i,
            success=success_count,
            failed=failed_count,
        )

    summary = {
        "batch_id": batch_id,
        "total": len(file_paths),
        "success": success_count,
        "failed": failed_count,
        "results": results,
    }

    logger.info(
        f"\nBatch {batch_id} complete: "
        f"{success_count}/{len(file_paths)} succeeded, "
        f"{failed_count}/{len(file_paths)} failed"
    )

    return summary


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import glob
    from src.config import SAMPLE_DATA_DIR

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Find all supported files in sample_data/
    supported_extensions = ("*.txt", "*.pdf", "*.docx", "*.png", "*.jpg", "*.jpeg", "*.tiff", "*.tif")
    files = []
    for ext in supported_extensions:
        files.extend(glob.glob(os.path.join(SAMPLE_DATA_DIR, ext)))

    if not files:
        print(f"No files found in {SAMPLE_DATA_DIR}. Run generate_test_data.py first.")
    else:
        print(f"Found {len(files)} file(s) to process.")
        summary = process_batch(files)
        print(f"\n{'='*60}")
        print(f"BATCH SUMMARY")
        print(f"{'='*60}")
        print(f"Total: {summary['total']}")
        print(f"Success: {summary['success']}")
        print(f"Failed: {summary['failed']}")
        for r in summary["results"]:
            status_icon = "✓" if r["status"] == STATUS_COMPLETED else "✗"
            print(f"  {status_icon} {r['filename']}: {r.get('compliance', r.get('error', 'N/A'))}")
