"""
Abstract base class for HEDIS compliance rules.

All HEDIS measure rules must subclass BaseRule and implement
the evaluate() method with measure-specific compliance logic.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ComplianceResult:
    """Result from evaluating a HEDIS compliance rule."""

    measure_name: str
    loinc_code: str
    is_compliant: bool
    status: str  # "COMPLIANT" or "NON-COMPLIANT"
    detail: str  # Human-readable explanation
    threshold_description: str  # e.g., "< 8.0%"
    evaluated_value: float
    evaluated_unit: str


class BaseRule(ABC):
    """Abstract base class for all HEDIS compliance rules.

    To add a new HEDIS measure, create a subclass that implements:
    - measure_name: The display name of the HEDIS measure
    - measure_id: A unique identifier for the measure
    - loinc_code: The LOINC code for the clinical test
    - evaluate(): The compliance evaluation logic
    """

    @property
    @abstractmethod
    def measure_name(self) -> str:
        """Human-readable name of the HEDIS measure."""
        ...

    @property
    @abstractmethod
    def measure_id(self) -> str:
        """Unique identifier for the measure (e.g., 'CDC_HBA1C')."""
        ...

    @property
    @abstractmethod
    def loinc_code(self) -> str:
        """LOINC code for the clinical test this rule evaluates."""
        ...

    @property
    @abstractmethod
    def threshold_description(self) -> str:
        """Human-readable description of the compliance threshold."""
        ...

    @abstractmethod
    def evaluate(self, value: float, unit: str = "%") -> ComplianceResult:
        """Evaluate a clinical value against this measure's compliance criteria.

        Args:
            value: The numeric test result.
            unit: The unit of measurement.

        Returns:
            ComplianceResult with compliance determination and explanation.
        """
        ...

    def matches_loinc(self, loinc_code: str) -> bool:
        """Check if this rule applies to the given LOINC code."""
        return self.loinc_code == loinc_code

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.measure_name} (LOINC: {self.loinc_code})>"
