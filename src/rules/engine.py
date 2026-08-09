"""
HEDIS Rules Engine: Auto-discovers and evaluates all registered BaseRule subclasses.

The engine dynamically finds all concrete subclasses of BaseRule and indexes
them by LOINC code for fast lookup during pipeline evaluation.
"""
import logging
from typing import Optional

from src.rules.base_rule import BaseRule, ComplianceResult

# Import all rule implementations so they register as subclasses
from src.rules.hba1c_rule import HbA1cRule  # noqa: F401

logger = logging.getLogger(__name__)


class RulesEngine:
    """HEDIS compliance rules engine.

    Auto-discovers all BaseRule subclasses and provides a unified
    evaluate() interface that routes to the correct rule by LOINC code.

    Usage:
        engine = RulesEngine()
        result = engine.evaluate(loinc_code="4548-4", value=7.2)
    """

    def __init__(self):
        """Initialize the engine and register all discovered rules."""
        self._rules: dict[str, BaseRule] = {}
        self._discover_rules()

    def _discover_rules(self):
        """Find and instantiate all concrete BaseRule subclasses."""
        for rule_class in BaseRule.__subclasses__():
            try:
                instance = rule_class()
                self._rules[instance.loinc_code] = instance
                logger.info(f"Registered rule: {instance}")
            except Exception as e:
                logger.error(f"Failed to register rule {rule_class.__name__}: {e}")

        logger.info(f"Rules engine initialized with {len(self._rules)} rule(s).")

    @property
    def registered_rules(self) -> list[BaseRule]:
        """Return all registered rule instances."""
        return list(self._rules.values())

    @property
    def supported_loinc_codes(self) -> list[str]:
        """Return all LOINC codes that have registered rules."""
        return list(self._rules.keys())

    def get_rule(self, loinc_code: str) -> Optional[BaseRule]:
        """Get the rule instance for a given LOINC code.

        Args:
            loinc_code: The LOINC code to look up.

        Returns:
            The BaseRule instance, or None if no rule matches.
        """
        return self._rules.get(loinc_code)

    def evaluate(
        self,
        loinc_code: str,
        value: float,
        unit: str = "%",
    ) -> Optional[ComplianceResult]:
        """Evaluate a clinical value against the matching HEDIS rule.

        Args:
            loinc_code: The LOINC code of the clinical test.
            value: The numeric test result.
            unit: The unit of measurement.

        Returns:
            ComplianceResult if a matching rule exists, None otherwise.
        """
        rule = self.get_rule(loinc_code)

        if rule is None:
            logger.warning(
                f"No HEDIS rule registered for LOINC code '{loinc_code}'. "
                f"Available codes: {self.supported_loinc_codes}"
            )
            return None

        logger.info(f"Evaluating {rule.measure_name}: value={value}{unit}")
        result = rule.evaluate(value, unit)
        logger.info(f"Result: {result.status} — {result.detail}")

        return result

    def evaluate_by_test_name(
        self,
        test_name: str,
        value: float,
        unit: str = "%",
    ) -> Optional[ComplianceResult]:
        """Evaluate by test name when LOINC code is not available.

        Attempts to match the test name against known measures.

        Args:
            test_name: The clinical test name (e.g., "Hemoglobin A1c").
            value: The numeric test result.
            unit: The unit of measurement.

        Returns:
            ComplianceResult if a matching rule is found, None otherwise.
        """
        test_name_lower = test_name.lower()

        # Known test name → LOINC code mappings
        name_to_loinc = {
            "hemoglobin a1c": "4548-4",
            "hba1c": "4548-4",
            "a1c": "4548-4",
            "glycated hemoglobin": "4548-4",
            "glycosylated hemoglobin": "4548-4",
        }

        for name_pattern, loinc_code in name_to_loinc.items():
            if name_pattern in test_name_lower:
                return self.evaluate(loinc_code, value, unit)

        logger.warning(f"No HEDIS rule matched for test name: '{test_name}'")
        return None
