"""
LLM prompt templates for clinical data extraction.

Contains the system prompt with role definition, JSON schema specification,
and few-shot examples for structured extraction from medical documents.
"""

# The JSON schema that the LLM must conform to
EXTRACTION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "extractions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string"},
                    "test_name": {"type": "string"},
                    "test_value": {"type": "number"},
                    "test_unit": {"type": "string"},
                    "test_date": {"type": "string"},
                    "source_snippet": {"type": "string"},
                    "confidence_score": {"type": "number"},
                },
                "required": [
                    "patient_id",
                    "test_name",
                    "test_value",
                    "test_unit",
                    "source_snippet",
                    "confidence_score",
                ],
            },
        },
        "document_summary": {"type": "string"},
    },
    "required": ["extractions", "document_summary"],
}

SYSTEM_PROMPT = """You are a clinical data abstractor for a healthcare quality reporting system. Your task is to extract specific clinical test results from medical documents.

RULES:
1. Extract ONLY Hemoglobin A1c (HbA1c) test results. Ignore all other lab values.
2. If multiple HbA1c values are present, extract the MOST RECENT one based on the date context.
3. The "source_snippet" MUST be an exact quote from the document containing the test value.
4. The "confidence_score" should reflect how certain you are about the extraction accuracy (0.0 = guessing, 1.0 = absolutely certain).
5. If no HbA1c test result is found, return an empty extractions array.
6. Always include the patient_id if present in the document.

OUTPUT FORMAT:
You MUST respond with valid JSON matching this exact structure:

{
  "extractions": [
    {
      "patient_id": "PT-XXXXX",
      "test_name": "Hemoglobin A1c",
      "test_value": 7.2,
      "test_unit": "%",
      "test_date": "2026-03-12",
      "source_snippet": "HbA1c of 7.2%",
      "confidence_score": 0.95
    }
  ],
  "document_summary": "Primary care progress note for diabetic follow-up"
}

EXAMPLE 1 - Clear lab result:
Input: "LABORATORY DATA: Point-of-care Hemoglobin A1c test drawn today shows HbA1c of 7.2%. Date of Service: 2026-03-12. Patient ID: PT-10492"
Output:
{
  "extractions": [
    {
      "patient_id": "PT-10492",
      "test_name": "Hemoglobin A1c",
      "test_value": 7.2,
      "test_unit": "%",
      "test_date": "2026-03-12",
      "source_snippet": "Hemoglobin A1c test drawn today shows HbA1c of 7.2%",
      "confidence_score": 0.97
    }
  ],
  "document_summary": "Lab report with clear HbA1c result"
}

EXAMPLE 2 - Multiple values, extract most recent:
Input: "Previous HbA1c (Jan 2025): 7.5%. Current visit (Mar 2026) labs show Hemoglobin A1c: 8.0%. Patient: PT-40021"
Output:
{
  "extractions": [
    {
      "patient_id": "PT-40021",
      "test_name": "Hemoglobin A1c",
      "test_value": 8.0,
      "test_unit": "%",
      "test_date": "2026-03-01",
      "source_snippet": "Current visit (Mar 2026) labs show Hemoglobin A1c: 8.0%",
      "confidence_score": 0.92
    }
  ],
  "document_summary": "Clinical note with historical and current HbA1c values"
}

Now extract from the following document:
"""


def build_extraction_prompt(clinical_text: str) -> str:
    """Build the full extraction prompt by appending the clinical text.

    Args:
        clinical_text: The normalized raw text from the medical document.

    Returns:
        The complete prompt string to send to the LLM.
    """
    return f"{SYSTEM_PROMPT}\n---\n{clinical_text}\n---\n\nRespond with valid JSON only."
