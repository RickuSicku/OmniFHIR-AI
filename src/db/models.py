"""
SQLite database schema and initialization for OmniFHIR-AI.

Defines all tables for documents, extractions, compliance results,
FHIR outputs, reviews, provenance tracking, and batch metadata.
"""
import os
import sqlite3
import logging

from src.config import DB_PATH, DATA_DIR

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
-- Batch processing metadata
CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    total_files INTEGER NOT NULL DEFAULT 0,
    processed_count INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Ingested documents
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size_bytes INTEGER,
    modality TEXT NOT NULL,
    upload_batch_id INTEGER,
    status TEXT NOT NULL DEFAULT 'PENDING',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_batch_id) REFERENCES batches(id)
);

-- LLM extraction results
CREATE TABLE IF NOT EXISTS extractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    raw_text TEXT,
    extracted_json TEXT,
    patient_id TEXT,
    test_name TEXT,
    test_value REAL,
    test_unit TEXT,
    test_date TEXT,
    source_snippet TEXT,
    confidence_score REAL,
    model_used TEXT,
    document_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- HEDIS compliance evaluation results
CREATE TABLE IF NOT EXISTS compliance_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    extraction_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    measure_name TEXT NOT NULL,
    measure_id TEXT,
    loinc_code TEXT NOT NULL,
    evaluated_value REAL,
    evaluated_unit TEXT,
    is_compliant BOOLEAN NOT NULL,
    status TEXT NOT NULL,
    detail TEXT,
    threshold_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (extraction_id) REFERENCES extractions(id),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Generated FHIR Observation resources
CREATE TABLE IF NOT EXISTS fhir_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    extraction_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    fhir_json TEXT NOT NULL,
    observation_id TEXT,
    is_valid BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (extraction_id) REFERENCES extractions(id),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Human reviewer actions
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    reviewer_action TEXT NOT NULL,
    reviewer_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Pipeline provenance / audit trail
CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    batch_id INTEGER,
    stage_name TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    model_used TEXT,
    error_message TEXT,
    output_summary TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (batch_id) REFERENCES batches(id)
);
"""


def get_connection() -> sqlite3.Connection:
    """Get a SQLite database connection, creating the DB if needed.

    Returns:
        An active sqlite3.Connection with row_factory set to Row.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize_database():
    """Create all tables if they don't already exist."""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        logger.info(f"Database initialized at: {DB_PATH}")
    finally:
        conn.close()
