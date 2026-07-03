"""ERPKit — the enterprise standard library for business transaction processing.

Phase 1 (Core Foundation Engine) public API:

    from erpkit import Validator, ValidationResult, Severity
    from erpkit import FinancialValidationPipeline

See ``erpkit.core`` for the validation engine and result/exception types,
and ``erpkit.pipeline`` for the metadata-driven end-to-end pipeline.
"""

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
from erpkit.pipeline.financial_pipeline import (
    AuditEntry,
    FinancialValidationPipeline,
    PipelineReport,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
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
    "FinancialValidationPipeline",
    "PipelineReport",
    "AuditEntry",
]
