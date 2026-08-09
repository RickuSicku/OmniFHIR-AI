"""
HEDIS Comprehensive Diabetes Care (CDC) — HbA1c Testing Rule.

Evaluates Hemoglobin A1c values against the HEDIS compliance threshold.
LOINC Code: 4548-4 (Hemoglobin A1c/Hemoglobin.total in Blood)

Compliance Criteria:
    HbA1c < 8.0%  →  COMPLIANT
    HbA1c >= 8.0% →  NON-COMPLIANT
"""
from src.config import COMPLIANCE_COMPLIANT, COMPLIANCE_NON_COMPLIANT
from src.rules.base_rule import BaseRule, ComplianceResult


# HEDIS threshold for Comprehensive Diabetes Care
HBA1C_THRESHOLD = 8.0


class HbA1cRule(BaseRule):
    """HEDIS rule for Comprehensive Diabetes Care — HbA1c control.

    A patient is considered compliant if their most recent HbA1c
    test result is below 8.0%. Values at or above 8.0% indicate
    poor glycemic control and are flagged as non-compliant.
    """

    @property
    def measure_name(self) -> str:
        return "Comprehensive Diabetes Care — HbA1c Control"

    @property
    def measure_id(self) -> str:
        return "CDC_HBA1C"

    @property
    def loinc_code(self) -> str:
        return "4548-4"

    @property
    def threshold_description(self) -> str:
        return f"HbA1c < {HBA1C_THRESHOLD}%"

    def evaluate(self, value: float, unit: str = "%") -> ComplianceResult:
        """Evaluate HbA1c value against the 8.0% threshold.

        Args:
            value: The HbA1c test result as a percentage.
            unit: Unit of measurement (expected: "%").

        Returns:
            ComplianceResult indicating compliance status.
        """
        is_compliant = value < HBA1C_THRESHOLD

        if is_compliant:
            status = COMPLIANCE_COMPLIANT
            detail = (
                f"HbA1c value of {value}{unit} is below the {HBA1C_THRESHOLD}% threshold. "
                f"Patient demonstrates adequate glycemic control."
            )
        else:
            status = COMPLIANCE_NON_COMPLIANT
            detail = (
                f"HbA1c value of {value}{unit} meets or exceeds the {HBA1C_THRESHOLD}% threshold. "
                f"Patient demonstrates poor glycemic control per HEDIS CDC measure."
            )

        return ComplianceResult(
            measure_name=self.measure_name,
            loinc_code=self.loinc_code,
            is_compliant=is_compliant,
            status=status,
            detail=detail,
            threshold_description=self.threshold_description,
            evaluated_value=value,
            evaluated_unit=unit,
        )
