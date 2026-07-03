"""ERPKit core engine: validation, results, and the exception hierarchy."""

from __future__ import annotations

from erpkit.core.exceptions import (
    ERPKitError,
    MetadataError,
    PipelineError,
    RuleConfigurationError,
    SchemaError,
    ValidationExecutionError,
)
from erpkit.core.result import Severity, ValidationIssue, ValidationResult
from erpkit.core.validator import Validator

__all__ = [
    "Validator",
    "ValidationResult",
    "ValidationIssue",
    "Severity",
    "ERPKitError",
    "RuleConfigurationError",
    "SchemaError",
    "ValidationExecutionError",
    "MetadataError",
    "PipelineError",
]
