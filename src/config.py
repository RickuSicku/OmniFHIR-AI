"""
OmniFHIR-AI: Application-wide configuration constants.
"""
import os

# ─── Ollama LLM Configuration ───────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", "mistral")
VISION_MODEL = os.getenv("VISION_MODEL", "llama3.2-vision")

# ─── Pipeline Thresholds ────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
OCR_DISCREPANCY_THRESHOLD = float(os.getenv("OCR_DISCREPANCY_THRESHOLD", "0.80"))

# ─── Database ────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DATA_DIR, "omnifhir.db")

# ─── File Support ────────────────────────────────────────────────────────────
SUPPORTED_TEXT_TYPES = {".txt"}
SUPPORTED_PDF_TYPES = {".pdf"}
SUPPORTED_DOCX_TYPES = {".docx"}
SUPPORTED_IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}
ALL_SUPPORTED_TYPES = SUPPORTED_TEXT_TYPES | SUPPORTED_PDF_TYPES | SUPPORTED_DOCX_TYPES | SUPPORTED_IMAGE_TYPES

# ─── Sample Data ─────────────────────────────────────────────────────────────
SAMPLE_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data")

# ─── Pipeline Stage Names ────────────────────────────────────────────────────
STAGE_INGESTION = "STAGE_1_INGESTION"
STAGE_OCR = "STAGE_2_OCR"
STAGE_EXTRACTION = "STAGE_3_EXTRACTION"
STAGE_VALIDATION = "STAGE_3B_VALIDATION"
STAGE_RULES = "STAGE_4_RULES_ENGINE"
STAGE_FHIR = "STAGE_5_FHIR_OUTPUT"
STAGE_PERSIST = "STAGE_6_PERSISTENCE"

# ─── Status Constants ────────────────────────────────────────────────────────
STATUS_PENDING = "PENDING"
STATUS_PROCESSING = "PROCESSING"
STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"

REVIEW_PENDING = "PENDING_REVIEW"
REVIEW_APPROVED = "APPROVED"
REVIEW_REJECTED = "REJECTED"
REVIEW_FLAGGED = "FLAGGED"

COMPLIANCE_COMPLIANT = "COMPLIANT"
COMPLIANCE_NON_COMPLIANT = "NON-COMPLIANT"
