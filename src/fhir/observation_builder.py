"""
FHIR R4 Observation resource builder using the fhir.resources library.

Constructs validated HL7 FHIR Observation resources from extracted clinical
data, including custom extensions for HEDIS compliance status, AI confidence,
and provenance metadata.
"""
import logging
from datetime import datetime, date
from typing import Optional
from uuid import uuid4

from fhir.resources.observation import Observation
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.quantity import Quantity
from fhir.resources.reference import Reference
from fhir.resources.extension import Extension
from fhir.resources.meta import Meta

from src.extraction.schema import ClinicalExtraction
from src.rules.base_rule import ComplianceResult

logger = logging.getLogger(__name__)

# LOINC system URI
LOINC_SYSTEM = "http://loinc.org"

# Custom extension URIs for OmniFHIR-AI metadata
EXT_BASE = "http://omnifhir-ai.cotiviti.com/fhir/extensions"
EXT_HEDIS_COMPLIANCE = f"{EXT_BASE}/hedis-compliance-status"
EXT_HEDIS_DETAIL = f"{EXT_BASE}/hedis-compliance-detail"
EXT_AI_CONFIDENCE = f"{EXT_BASE}/ai-confidence-score"
EXT_SOURCE_SNIPPET = f"{EXT_BASE}/source-evidence-snippet"
EXT_PROCESSING_TIMESTAMP = f"{EXT_BASE}/processing-timestamp"


def build_observation(
    extraction: ClinicalExtraction,
    compliance: Optional[ComplianceResult] = None,
    source_file: Optional[str] = None,
) -> Observation:
    """Build a validated FHIR R4 Observation resource from extracted data.

    Maps the extraction to standard FHIR fields and adds custom extensions
    for HEDIS compliance, AI confidence, and audit metadata.

    Args:
        extraction: The validated clinical data extraction.
        compliance: The HEDIS compliance evaluation result (if available).
        source_file: The original source file name (for provenance).

    Returns:
        A validated FHIR R4 Observation resource.

    Raises:
        ValueError: If the observation cannot be constructed.
    """
    observation_id = str(uuid4())

    # Determine LOINC code — default to HbA1c
    loinc_code = "4548-4"
    loinc_display = "Hemoglobin A1c/Hemoglobin.total in Blood"
    if compliance:
        loinc_code = compliance.loinc_code
        loinc_display = compliance.measure_name

    # Build extensions
    extensions = _build_extensions(extraction, compliance, source_file)

    # Determine effective date
    effective_date = None
    if extraction.test_date:
        try:
            effective_date = extraction.test_date
        except Exception:
            effective_date = None

    # Build the Observation resource
    obs_data = {
        "resourceType": "Observation",
        "id": observation_id,
        "meta": Meta(
            profile=["http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-lab"],
        ),
        "status": "final",
        "category": [
            CodeableConcept(
                coding=[
                    Coding(
                        system="http://terminology.hl7.org/CodeSystem/observation-category",
                        code="laboratory",
                        display="Laboratory",
                    )
                ]
            )
        ],
        "code": CodeableConcept(
            coding=[
                Coding(
                    system=LOINC_SYSTEM,
                    code=loinc_code,
                    display=loinc_display,
                )
            ],
            text=extraction.test_name,
        ),
        "subject": Reference(
            reference=f"Patient/{extraction.patient_id}",
            display=f"Patient {extraction.patient_id}",
        ),
        "valueQuantity": Quantity(
            value=extraction.test_value,
            unit=extraction.test_unit,
            system="http://unitsofmeasure.org",
            code=extraction.test_unit,
        ),
        "extension": extensions,
    }

    # Add effective date if available
    if effective_date:
        obs_data["effectiveDateTime"] = effective_date

    # Add interpretation based on compliance
    if compliance:
        interp_code = "N" if compliance.is_compliant else "H"
        interp_display = "Normal" if compliance.is_compliant else "High"
        obs_data["interpretation"] = [
            CodeableConcept(
                coding=[
                    Coding(
                        system="http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        code=interp_code,
                        display=interp_display,
                    )
                ],
                text=compliance.status,
            )
        ]

    try:
        observation = Observation(**obs_data)
        logger.info(f"Built FHIR Observation: id={observation_id}, LOINC={loinc_code}")
        return observation
    except Exception as e:
        logger.error(f"Failed to build FHIR Observation: {e}")
        raise ValueError(f"Invalid FHIR Observation: {e}")


def _build_extensions(
    extraction: ClinicalExtraction,
    compliance: Optional[ComplianceResult],
    source_file: Optional[str],
) -> list[Extension]:
    """Build custom FHIR extensions for OmniFHIR-AI metadata.

    Args:
        extraction: The clinical extraction data.
        compliance: The compliance evaluation result.
        source_file: The source file name.

    Returns:
        List of FHIR Extension objects.
    """
    extensions = []

    # AI Confidence Score
    extensions.append(
        Extension(
            url=EXT_AI_CONFIDENCE,
            valueDecimal=extraction.confidence_score,
        )
    )

    # Source Evidence Snippet
    extensions.append(
        Extension(
            url=EXT_SOURCE_SNIPPET,
            valueString=extraction.source_snippet,
        )
    )

    # Processing Timestamp
    extensions.append(
        Extension(
            url=EXT_PROCESSING_TIMESTAMP,
            valueDateTime=datetime.utcnow().isoformat(),
        )
    )

    # HEDIS Compliance Status
    if compliance:
        extensions.append(
            Extension(
                url=EXT_HEDIS_COMPLIANCE,
                valueString=compliance.status,
            )
        )
        extensions.append(
            Extension(
                url=EXT_HEDIS_DETAIL,
                valueString=compliance.detail,
            )
        )

    return extensions


def observation_to_dict(observation: Observation) -> dict:
    """Convert a FHIR Observation to a JSON-serializable dictionary.

    Args:
        observation: The FHIR Observation resource.

    Returns:
        A dictionary representation of the observation.
    """
    return json.loads(observation.model_dump_json(exclude_none=True))


# Need json import for observation_to_dict
import json
