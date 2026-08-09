"""
Database repository: CRUD operations for all OmniFHIR-AI tables.

Provides a clean data access layer between the pipeline/UI and SQLite.
"""
import json
import logging
from datetime import datetime
from typing import Optional

from src.db.models import get_connection

logger = logging.getLogger(__name__)


# ─── Batch Operations ────────────────────────────────────────────────────────

def create_batch(total_files: int) -> int:
    """Create a new processing batch and return its ID."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO batches (total_files) VALUES (?)",
            (total_files,),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_batch_progress(batch_id: int, processed: int, success: int, failed: int):
    """Update batch processing counters."""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE batches
               SET processed_count = ?, success_count = ?, failed_count = ?,
                   completed_at = CASE WHEN ? >= total_files THEN CURRENT_TIMESTAMP ELSE NULL END
               WHERE id = ?""",
            (processed, success, failed, processed, batch_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_batch(batch_id: int) -> Optional[dict]:
    """Get batch metadata by ID."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM batches WHERE id = ?", (batch_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ─── Document Operations ─────────────────────────────────────────────────────

def create_document(
    filename: str,
    file_type: str,
    file_path: str,
    modality: str,
    file_size_bytes: int = 0,
    batch_id: Optional[int] = None,
) -> int:
    """Insert a new document record and return its ID."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO documents
               (filename, file_type, file_path, modality, file_size_bytes, upload_batch_id, status)
               VALUES (?, ?, ?, ?, ?, ?, 'PROCESSING')""",
            (filename, file_type, file_path, modality, file_size_bytes, batch_id),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_document_status(doc_id: int, status: str, error_message: Optional[str] = None):
    """Update a document's processing status."""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE documents
               SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (status, error_message, doc_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_document(doc_id: int) -> Optional[dict]:
    """Get a document by ID."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_documents() -> list[dict]:
    """Get all documents ordered by creation date (newest first)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM documents ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_documents_by_batch(batch_id: int) -> list[dict]:
    """Get all documents in a specific batch."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM documents WHERE upload_batch_id = ? ORDER BY id",
            (batch_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ─── Extraction Operations ───────────────────────────────────────────────────

def create_extraction(
    document_id: int,
    raw_text: str,
    extracted_json: str,
    patient_id: str = "",
    test_name: str = "",
    test_value: float = 0.0,
    test_unit: str = "%",
    test_date: Optional[str] = None,
    source_snippet: str = "",
    confidence_score: float = 0.0,
    model_used: str = "",
    document_summary: str = "",
) -> int:
    """Insert an extraction result and return its ID."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO extractions
               (document_id, raw_text, extracted_json, patient_id, test_name,
                test_value, test_unit, test_date, source_snippet,
                confidence_score, model_used, document_summary)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                document_id, raw_text, extracted_json, patient_id, test_name,
                test_value, test_unit, test_date, source_snippet,
                confidence_score, model_used, document_summary,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_extraction_by_document(doc_id: int) -> Optional[dict]:
    """Get the most recent extraction for a document."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM extractions WHERE document_id = ? ORDER BY created_at DESC LIMIT 1",
            (doc_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ─── Compliance Operations ───────────────────────────────────────────────────

def create_compliance_result(
    extraction_id: int,
    document_id: int,
    measure_name: str,
    loinc_code: str,
    evaluated_value: float,
    is_compliant: bool,
    status: str,
    detail: str = "",
    measure_id: str = "",
    evaluated_unit: str = "%",
    threshold_description: str = "",
) -> int:
    """Insert a compliance evaluation result."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO compliance_results
               (extraction_id, document_id, measure_name, measure_id, loinc_code,
                evaluated_value, evaluated_unit, is_compliant, status, detail,
                threshold_description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                extraction_id, document_id, measure_name, measure_id, loinc_code,
                evaluated_value, evaluated_unit, is_compliant, status, detail,
                threshold_description,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_compliance_by_document(doc_id: int) -> Optional[dict]:
    """Get compliance result for a document."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM compliance_results WHERE document_id = ? ORDER BY created_at DESC LIMIT 1",
            (doc_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ─── FHIR Output Operations ─────────────────────────────────────────────────

def create_fhir_output(
    extraction_id: int,
    document_id: int,
    fhir_json: str,
    observation_id: str = "",
    is_valid: bool = True,
) -> int:
    """Insert a FHIR Observation output."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO fhir_outputs
               (extraction_id, document_id, fhir_json, observation_id, is_valid)
               VALUES (?, ?, ?, ?, ?)""",
            (extraction_id, document_id, fhir_json, observation_id, is_valid),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_fhir_output_by_document(doc_id: int) -> Optional[dict]:
    """Get the FHIR output for a document."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM fhir_outputs WHERE document_id = ? ORDER BY created_at DESC LIMIT 1",
            (doc_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_approved_fhir_outputs() -> list[dict]:
    """Get all FHIR outputs for approved documents."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT fo.* FROM fhir_outputs fo
               JOIN documents d ON fo.document_id = d.id
               JOIN reviews r ON r.document_id = d.id
               WHERE r.reviewer_action = 'APPROVED'
               AND r.id = (SELECT MAX(r2.id) FROM reviews r2 WHERE r2.document_id = d.id)
               ORDER BY fo.created_at"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ─── Review Operations ───────────────────────────────────────────────────────

def create_review(
    document_id: int,
    reviewer_action: str,
    reviewer_notes: str = "",
) -> int:
    """Insert a human review action."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO reviews (document_id, reviewer_action, reviewer_notes) VALUES (?, ?, ?)",
            (document_id, reviewer_action, reviewer_notes),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_latest_review(doc_id: int) -> Optional[dict]:
    """Get the most recent review for a document."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM reviews WHERE document_id = ? ORDER BY created_at DESC LIMIT 1",
            (doc_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ─── Provenance Operations ───────────────────────────────────────────────────

def create_provenance(
    document_id: int,
    stage_name: str,
    status: str,
    started_at: Optional[str] = None,
    completed_at: Optional[str] = None,
    duration_ms: Optional[int] = None,
    model_used: Optional[str] = None,
    error_message: Optional[str] = None,
    output_summary: Optional[str] = None,
    metadata_json: Optional[str] = None,
    batch_id: Optional[int] = None,
) -> int:
    """Insert a provenance record for a pipeline stage."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO provenance
               (document_id, batch_id, stage_name, status, started_at, completed_at,
                duration_ms, model_used, error_message, output_summary, metadata_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                document_id, batch_id, stage_name, status, started_at, completed_at,
                duration_ms, model_used, error_message, output_summary, metadata_json,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_provenance_by_document(doc_id: int) -> list[dict]:
    """Get all provenance records for a document, ordered by stage."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM provenance WHERE document_id = ? ORDER BY created_at",
            (doc_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ─── Dashboard Query Helpers ─────────────────────────────────────────────────

def get_dashboard_data() -> list[dict]:
    """Get aggregated data for the dashboard view.

    Returns a list of documents with their extraction, compliance,
    and review data joined together.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT
                d.id AS doc_id,
                d.filename,
                d.file_type,
                d.modality,
                d.status AS doc_status,
                d.error_message,
                d.created_at,
                e.test_value,
                e.test_unit,
                e.confidence_score,
                e.patient_id,
                e.test_name,
                cr.is_compliant,
                cr.status AS compliance_status,
                cr.detail AS compliance_detail,
                (SELECT r.reviewer_action FROM reviews r
                 WHERE r.document_id = d.id ORDER BY r.created_at DESC LIMIT 1)
                    AS review_status,
                (SELECT r.reviewer_notes FROM reviews r
                 WHERE r.document_id = d.id ORDER BY r.created_at DESC LIMIT 1)
                    AS review_notes
            FROM documents d
            LEFT JOIN extractions e ON e.document_id = d.id
                AND e.id = (SELECT MAX(e2.id) FROM extractions e2 WHERE e2.document_id = d.id)
            LEFT JOIN compliance_results cr ON cr.document_id = d.id
                AND cr.id = (SELECT MAX(cr2.id) FROM compliance_results cr2 WHERE cr2.document_id = d.id)
            ORDER BY
                CASE WHEN e.confidence_score IS NOT NULL AND e.confidence_score < 0.7 THEN 0 ELSE 1 END,
                d.created_at DESC"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_summary_statistics() -> dict:
    """Get aggregate counts for the dashboard summary row."""
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        completed = conn.execute(
            "SELECT COUNT(*) FROM documents WHERE status = 'COMPLETED'"
        ).fetchone()[0]
        failed = conn.execute(
            "SELECT COUNT(*) FROM documents WHERE status = 'FAILED'"
        ).fetchone()[0]
        compliant = conn.execute(
            "SELECT COUNT(*) FROM compliance_results WHERE is_compliant = 1"
        ).fetchone()[0]
        non_compliant = conn.execute(
            "SELECT COUNT(*) FROM compliance_results WHERE is_compliant = 0"
        ).fetchone()[0]
        pending_review = conn.execute(
            """SELECT COUNT(*) FROM documents d
               WHERE d.status = 'COMPLETED'
               AND NOT EXISTS (
                   SELECT 1 FROM reviews r WHERE r.document_id = d.id
               )"""
        ).fetchone()[0]
        approved = conn.execute(
            """SELECT COUNT(DISTINCT d.id) FROM documents d
               JOIN reviews r ON r.document_id = d.id
               WHERE r.reviewer_action = 'APPROVED'
               AND r.id = (SELECT MAX(r2.id) FROM reviews r2 WHERE r2.document_id = d.id)"""
        ).fetchone()[0]

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "pending_review": pending_review,
            "approved": approved,
        }
    finally:
        conn.close()


def get_export_data() -> list[dict]:
    """Get data formatted for CSV export."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT
                d.filename,
                d.file_type,
                d.modality,
                d.status AS processing_status,
                e.patient_id,
                e.test_name,
                e.test_value,
                e.test_unit,
                e.test_date,
                e.confidence_score,
                cr.status AS compliance_status,
                cr.detail AS compliance_detail,
                (SELECT r.reviewer_action FROM reviews r
                 WHERE r.document_id = d.id ORDER BY r.created_at DESC LIMIT 1)
                    AS review_status,
                (SELECT r.reviewer_notes FROM reviews r
                 WHERE r.document_id = d.id ORDER BY r.created_at DESC LIMIT 1)
                    AS review_notes,
                d.created_at
            FROM documents d
            LEFT JOIN extractions e ON e.document_id = d.id
                AND e.id = (SELECT MAX(e2.id) FROM extractions e2 WHERE e2.document_id = d.id)
            LEFT JOIN compliance_results cr ON cr.document_id = d.id
                AND cr.id = (SELECT MAX(cr2.id) FROM compliance_results cr2 WHERE cr2.document_id = d.id)
            ORDER BY d.created_at"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def clear_all_data():
    """Delete all data from all tables. Used for resetting the database."""
    conn = get_connection()
    try:
        for table in ["provenance", "reviews", "fhir_outputs", "compliance_results",
                       "extractions", "documents", "batches"]:
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
        logger.info("All database data cleared.")
    finally:
        conn.close()
