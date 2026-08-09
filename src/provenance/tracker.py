"""
Pipeline provenance tracker: records timing, model usage, and status
for each stage of document processing.
"""
import json
import time
import logging
from datetime import datetime, timezone
from typing import Optional

from src.db import repository as repo

logger = logging.getLogger(__name__)


class ProvenanceTracker:
    """Tracks pipeline stage execution for audit trail purposes.

    Usage:
        tracker = ProvenanceTracker(document_id=1, batch_id=1)
        tracker.start_stage("STAGE_1_INGESTION")
        # ... do work ...
        tracker.complete_stage(output_summary="Parsed 1200 chars from PDF")
    """

    def __init__(self, document_id: int, batch_id: Optional[int] = None):
        self.document_id = document_id
        self.batch_id = batch_id
        self._current_stage: Optional[str] = None
        self._stage_start: Optional[float] = None
        self._stage_start_iso: Optional[str] = None

    def start_stage(self, stage_name: str, model_used: Optional[str] = None):
        """Mark the beginning of a pipeline stage.

        Args:
            stage_name: The stage identifier (e.g., STAGE_1_INGESTION).
            model_used: The LLM model used in this stage (if any).
        """
        self._current_stage = stage_name
        self._stage_start = time.time()
        self._stage_start_iso = datetime.now(timezone.utc).isoformat()
        self._model_used = model_used

        logger.info(f"[Doc {self.document_id}] Starting stage: {stage_name}")

    def complete_stage(
        self,
        output_summary: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        """Mark a stage as successfully completed and persist to DB.

        Args:
            output_summary: Brief description of what the stage produced.
            metadata: Additional key-value data to store (serialized as JSON).
        """
        if not self._current_stage or not self._stage_start:
            logger.warning("complete_stage called without a matching start_stage")
            return

        duration_ms = int((time.time() - self._stage_start) * 1000)
        completed_at = datetime.now(timezone.utc).isoformat()

        repo.create_provenance(
            document_id=self.document_id,
            batch_id=self.batch_id,
            stage_name=self._current_stage,
            status="COMPLETED",
            started_at=self._stage_start_iso,
            completed_at=completed_at,
            duration_ms=duration_ms,
            model_used=getattr(self, "_model_used", None),
            output_summary=output_summary,
            metadata_json=json.dumps(metadata) if metadata else None,
        )

        logger.info(
            f"[Doc {self.document_id}] Completed stage: {self._current_stage} "
            f"({duration_ms}ms)"
        )

        self._current_stage = None
        self._stage_start = None

    def fail_stage(
        self,
        error_message: str,
        metadata: Optional[dict] = None,
    ):
        """Mark a stage as failed and persist to DB.

        Args:
            error_message: Description of what went wrong.
            metadata: Additional context about the failure.
        """
        duration_ms = 0
        completed_at = datetime.now(timezone.utc).isoformat()

        if self._stage_start:
            duration_ms = int((time.time() - self._stage_start) * 1000)

        stage = self._current_stage or "UNKNOWN_STAGE"

        repo.create_provenance(
            document_id=self.document_id,
            batch_id=self.batch_id,
            stage_name=stage,
            status="FAILED",
            started_at=self._stage_start_iso,
            completed_at=completed_at,
            duration_ms=duration_ms,
            model_used=getattr(self, "_model_used", None),
            error_message=error_message,
            metadata_json=json.dumps(metadata) if metadata else None,
        )

        logger.error(
            f"[Doc {self.document_id}] Failed at stage: {stage} — {error_message}"
        )

        self._current_stage = None
        self._stage_start = None
