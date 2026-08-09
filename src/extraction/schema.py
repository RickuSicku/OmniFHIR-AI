"""
Pydantic models for structured clinical data extraction.

Defines the expected output schema from the LLM and provides
post-extraction validation to catch hallucinations.
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ClinicalExtraction(BaseModel):
    """A single clinical data point extracted from a medical document."""

    patient_id: str = Field(
        ...,
        description="Patient identifier (e.g., PT-10492)",
    )
    test_name: str = Field(
        ...,
        description="Name of the clinical test (e.g., Hemoglobin A1c)",
    )
    test_value: float = Field(
        ...,
        description="Numeric test result value",
    )
    test_unit: str = Field(
        default="%",
        description="Unit of measurement (e.g., %, mg/dL)",
    )
    test_date: Optional[str] = Field(
        default=None,
        description="Date the test was performed (YYYY-MM-DD format)",
    )
    source_snippet: str = Field(
        ...,
        description="Exact quote from the document that contains the test value",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI confidence in the extraction accuracy (0.0 to 1.0)",
    )

    @field_validator("test_value")
    @classmethod
    def validate_test_value(cls, v: float) -> float:
        """Catch obvious hallucinations — HbA1c values must be physiologically plausible."""
        if v < 0:
            raise ValueError(f"Test value cannot be negative: {v}")
        if v > 20:
            raise ValueError(
                f"Test value {v} is physiologically implausible for HbA1c "
                "(normal range 4.0-14.0%, extreme cases up to ~20%)."
            )
        return v

    @field_validator("confidence_score")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        """Ensure confidence is within valid range."""
        return max(0.0, min(1.0, v))


class ExtractionResult(BaseModel):
    """Wrapper for the full extraction output from a single document."""

    extractions: list[ClinicalExtraction] = Field(
        default_factory=list,
        description="List of clinical data points extracted from the document",
    )
    document_summary: Optional[str] = Field(
        default=None,
        description="Brief summary of the document type and content",
    )
    raw_llm_response: Optional[str] = Field(
        default=None,
        description="The raw JSON string returned by the LLM (for audit)",
    )

    @property
    def has_extractions(self) -> bool:
        """Check if any clinical data was successfully extracted."""
        return len(self.extractions) > 0

    @property
    def primary_extraction(self) -> Optional[ClinicalExtraction]:
        """Return the highest-confidence extraction, if any."""
        if not self.extractions:
            return None
        return max(self.extractions, key=lambda e: e.confidence_score)
