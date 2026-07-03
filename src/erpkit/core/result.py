"""Result data structures produced by :class:`erpkit.core.validator.Validator`.

Kept dependency-free (no Polars imports) and JSON-serializable by
construction, so a :class:`ValidationResult` can be logged, persisted to
an audit table, or returned from a FastAPI endpoint without any adapter
layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Severity of a validation issue.

    A subclass of ``str`` so severities compare and JSON-serialize as
    plain strings (``Severity.ERROR == "error"``) while still being a
    real enum for IDE autocomplete and exhaustiveness checks.
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(slots=True)
class ValidationIssue:
    """A single rule failure surfaced by ``Validator.validate()``.

    Attributes:
        rule: Rule name that produced this issue (e.g. ``"required"``,
            or a caller-supplied name for ``.custom()`` rules).
        column: Primary column the issue relates to, or ``None`` for
            rules that span multiple columns (e.g. ``duplicate`` reports
            the joined key column list here as a display string).
        severity: How serious the issue is. Only ``Severity.ERROR``
            issues affect ``ValidationResult.is_valid``.
        message: Human-readable description of the failure.
        failing_row_count: Total number of rows (or, for ``balance``,
            groups) that failed this rule.
        row_indices: A capped sample of failing row indices, for quick
            inspection without re-scanning the full dataset. See
            ``erpkit.core.validator._MAX_SAMPLE_ROW_INDICES``.
        details: Rule-specific structured extras (e.g. ``{"allowed": [...]}``
            for ``currency``, or out-of-balance group summaries for
            ``balance``).
    """

    rule: str
    column: str | None
    severity: Severity
    message: str
    failing_row_count: int
    row_indices: list[int] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable representation of this issue."""
        return {
            "rule": self.rule,
            "column": self.column,
            "severity": self.severity.value,
            "message": self.message,
            "failing_row_count": self.failing_row_count,
            "row_indices": list(self.row_indices),
            "details": self.details,
        }


@dataclass(slots=True)
class ValidationResult:
    """Aggregate outcome of running every rule queued on a ``Validator``.

    Construct via :meth:`build` rather than the constructor directly, so
    ``is_valid``, ``error_count``, ``warning_count`` and ``statistics``
    stay derived from — and therefore always consistent with —
    ``errors``/``warnings``.
    """

    is_valid: bool
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
    row_count: int
    execution_time: float
    error_count: int
    warning_count: int
    statistics: dict[str, Any]
    summary: str

    @classmethod
    def build(
        cls,
        *,
        issues: list[ValidationIssue],
        row_count: int,
        execution_time: float,
        rule_timings: dict[str, float],
    ) -> "ValidationResult":
        """Assemble a ``ValidationResult`` from raw issues + run metadata.

        Args:
            issues: Every issue produced across all executed rules, in
                execution order.
            row_count: Number of rows in the DataFrame that was validated.
            execution_time: Total wall-clock seconds spent in ``.validate()``.
            rule_timings: Per-rule elapsed seconds, keyed by rule name
                (disambiguated with a ``#N`` suffix for repeated rule
                names — see ``Validator.validate``).

        Returns:
            A fully populated, internally consistent ``ValidationResult``.
        """
        errors = [i for i in issues if i.severity == Severity.ERROR]
        other = [i for i in issues if i.severity != Severity.ERROR]
        # "warnings" is the historical/public name for every non-error
        # issue (WARNING and INFO alike) surfaced outside of `errors`.
        warnings = other

        # error_count / warning_count are counted in *failing rows*, not
        # in ValidationIssue objects: a single rule invocation (e.g.
        # `.required(["Vendor"])`) may bundle many failing rows into one
        # ValidationIssue, and callers reasonably expect error_count to
        # reflect how many rows are actually bad, matching the
        # `failing_row_count` reported on each issue.
        error_count = sum(i.failing_row_count for i in errors)
        warning_count = sum(i.failing_row_count for i in warnings)
        total_failing_rows = error_count + warning_count

        statistics: dict[str, Any] = {
            "rule_timings_seconds": dict(rule_timings),
            "rules_executed": len(rule_timings),
            "total_issues": len(issues),
            "total_failing_rows": total_failing_rows,
        }

        is_valid = error_count == 0
        summary = (
            f"Validated {row_count} row(s): {error_count} error(s), "
            f"{warning_count} warning(s) across {len(rule_timings)} rule(s) "
            f"in {execution_time:.4f}s."
        )

        return cls(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            row_count=row_count,
            execution_time=execution_time,
            error_count=error_count,
            warning_count=warning_count,
            statistics=statistics,
            summary=summary,
        )

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable representation of the full result."""
        return {
            "is_valid": self.is_valid,
            "row_count": self.row_count,
            "execution_time": self.execution_time,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "summary": self.summary,
            "statistics": self.statistics,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
        }
