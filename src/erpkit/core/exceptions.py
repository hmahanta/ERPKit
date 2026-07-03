"""Exception hierarchy for ERPKit.

All ERPKit errors derive from :class:`ERPKitError` so calling code can
either catch broadly (``except ERPKitError``) or narrowly (a specific
subclass) depending on how much granularity it needs. Every exception
carries an optional ``context`` mapping of structured, machine-readable
detail (offending column names, rule names, file paths, etc.) in addition
to the human-readable ``message``, so the same exception can drive both a
readable CLI error and a structured log line without re-parsing the
message string.

Hierarchy
---------
ERPKitError
├── RuleConfigurationError   - a validation rule was misconfigured by the caller
├── SchemaError              - data does not match the shape a rule/pipeline expects
├── ValidationExecutionError - a rule failed to execute (engine-level failure)
├── MetadataError            - a metadata document (JSON/YAML schema) is invalid
└── PipelineError            - a pipeline stage failed outside of metadata/validation
"""

from __future__ import annotations

from typing import Any


class ERPKitError(Exception):
    """Base class for every exception raised by ERPKit.

    Attributes:
        message: Human-readable description of what went wrong.
        context: Structured detail about the failure (e.g.
            ``{"missing_columns": [...], "dataset": "invoices"}``). Always
            a ``dict``, defaulting to empty rather than ``None`` so callers
            can safely do ``exc.context.get(...)`` without a null check.
    """

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context: dict[str, Any] = dict(context) if context else {}

    def __str__(self) -> str:  # pragma: no cover - trivial formatting
        if not self.context:
            return self.message
        details = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
        return f"{self.message} ({details})"

    def to_dict(self) -> dict[str, Any]:
        """Structured representation, useful for logging or API error bodies."""
        return {
            "error_type": type(self).__name__,
            "message": self.message,
            "context": self.context,
        }


class RuleConfigurationError(ERPKitError):
    """Raised when a validation rule is called with invalid arguments.

    This is a *caller* mistake (bad rule config), distinct from
    :class:`ValidationExecutionError`, which represents an engine-level
    failure while running an otherwise well-configured rule.
    """


class SchemaError(ERPKitError):
    """Raised when data does not have the columns/shape a rule expects.

    Typically raised eagerly, at rule-declaration time (e.g.
    ``Validator(df).required(["NoSuchColumn"])``), so the mistake surfaces
    at the call site rather than deep inside ``.validate()``.
    """


class ValidationExecutionError(ERPKitError):
    """Raised when a rule raises while actually executing against data.

    Wraps the original exception via ``raise ... from exc`` so the root
    cause is preserved in tracebacks, while giving calling code one
    stable exception type to catch regardless of which underlying engine
    (Polars, a custom rule, etc.) failed.
    """


class MetadataError(ERPKitError):
    """Raised when a metadata document (schema JSON/YAML) is invalid.

    Covers: the file is missing, is not valid JSON/YAML, is missing
    required top-level keys (``entity``, ``columns``, ``validation_rules``),
    or contains a rule/transform definition missing keys required for its
    type (e.g. a ``currency`` rule with no ``column``/``allowed``).
    """


class PipelineError(ERPKitError):
    """Raised when a pipeline stage fails outside of metadata or validation.

    Covers stages like CSV import (missing/unreadable file, parse
    failure) and any unexpected error a pipeline run cannot attribute to
    a more specific ERPKit exception type.
    """
