# ==============================================================================
# Module      : erpkit.core.validator
# Package     : erpkit-core
# Purpose     : Metadata-driven, chainable validation engine for enterprise
#               business-transaction data (invoices, journals, vendors, POs).
# Maintainer  : ERPKit Core Team
# Standard    : Follows ERPKit coding standard — PEP 8 formatting, Google-style
#               docstrings on every public symbol, explicit type hints, and
#               ERPKitError-derived exceptions (never a bare Exception) for
#               anything a caller might need to catch.
# ==============================================================================
"""Metadata-driven, chainable validation engine for enterprise transactions.

This module is the heart of ERPKit's Phase 1 core foundation. It provides
:class:`Validator`, a fluent, Polars-native rule builder purpose-built for
business transaction data (invoices, journals, vendors, purchase orders)
rather than generic tabular data.

Why Polars instead of Pandas
-----------------------------
Enterprise reconciliation and invoice-validation workloads routinely deal
with multi-million-row extracts (a mid-size ERP's monthly AP transaction
file alone can exceed 5-10 million rows once line-item detail is included).
Polars was chosen over Pandas for three concrete reasons:

1. **Columnar, Arrow-native memory layout** — validation rules here are
   expressed as vectorized boolean-mask expressions (``pl.col(...).is_null()``,
   ``pl.col(...).is_in(...)``) that Polars executes in parallel across all
   available cores without the GIL contention that plagues Pandas' NumPy
   block manager.
2. **Query optimization** — every rule is expressed as a Polars expression,
   which lets ``.validate()`` execute all rules with Polars' predicate
   pushdown and common-subexpression elimination, rather than N sequential
   Python-level passes over the data.
3. **Lower memory footprint** — Arrow's columnar layout with no per-cell
   Python object overhead means a 10-million-row, 30-column invoice extract
   fits comfortably where a Pandas ``object``-dtype equivalent would not.

Deferred rule execution
------------------------
Calling a rule method (``.required(...)``, ``.currency(...)``, etc.) never
touches the data immediately. It validates its own *configuration*
eagerly (fail fast on typos / bad arguments) and appends a
:class:`_RuleSpec` to an internal queue. Actual execution happens once,
inside ``.validate()``, so that:

* Rule configuration errors surface at the call site where the mistake was
  made, not buried inside a stack trace from deep inside ``.validate()``.
* All engine execution is centralized in one place, which is what makes
  per-rule timing (surfaced in ``ValidationResult.statistics``) possible.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Callable, Iterable, Sequence

import polars as pl

from erpkit.core.exceptions import (
    RuleConfigurationError,
    SchemaError,
    ValidationExecutionError,
)
from erpkit.core.result import Severity, ValidationIssue, ValidationResult

logger = logging.getLogger("erpkit.core.validator")

_MAX_SAMPLE_ROW_INDICES = 25
"""Cap on how many failing row indices are retained per issue.

Retaining every failing index for a rule that fails on 2 million rows would
make ``ValidationResult`` itself a multi-million-element object, defeating
the purpose of keeping the result cheap to hold and serialize. Callers who
need the full failing set should re-run the rule's underlying boolean mask
against the DataFrame directly (each rule's mask logic is a small pure
function, exposed via ``Validator._rule_mask`` for exactly this purpose).
"""


@dataclass(slots=True)
class _RuleSpec:
    """Internal descriptor for a single queued rule.

    Attributes:
        name: Rule name, used in ``ValidationIssue.rule`` and timings.
        column: Primary column the rule targets, or ``None``.
        severity: Severity assigned to issues this rule produces.
        run: Zero-argument callable (closure over the rule's own args and
            the Validator's DataFrame) that executes the rule and returns
            a list of ``ValidationIssue``. Deferring to a closure keeps
            each rule builder method self-contained and independently
            testable without a large ``if rule.name == ...`` dispatch table.
    """

    name: str
    column: str | None
    severity: Severity
    run: Callable[[], list[ValidationIssue]]


class Validator:
    """Fluent, metadata-friendly validator over a Polars DataFrame.

    Example:
        >>> result = (
        ...     Validator(df)
        ...     .required(["Vendor", "Invoice"])
        ...     .currency("Currency", ["USD", "EUR"])
        ...     .duplicate(["Invoice"])
        ...     .balance(group_by=["Journal"], amount_column="Amount")
        ...     .validate()
        ... )
        >>> result.is_valid
        False

    The same rules can be constructed from metadata (see
    ``erpkit.metadata.examples``) by mapping a YAML/JSON rule list onto
    these method calls; that mapping layer is intentionally kept out of
    this module so ``Validator`` has zero knowledge of any serialization
    format, per the metadata-driven / clean-architecture design goal.
    """

    def __init__(self, df: pl.DataFrame, *, name: str = "unnamed") -> None:
        """Initialize a Validator.

        Args:
            df: The Polars DataFrame to validate. Not copied or mutated;
                ERPKit never transforms data as a side effect of validation.
            name: Optional logical name for the dataset, used only in log
                messages (e.g. ``"invoice_extract_2026_07"``).

        Raises:
            RuleConfigurationError: if ``df`` is not a ``polars.DataFrame``.
        """
        if not isinstance(df, pl.DataFrame):
            raise RuleConfigurationError(
                "Validator requires a polars.DataFrame instance.",
                context={"received_type": type(df).__name__},
            )
        self._df = df
        self._name = name
        self._rules: list[_RuleSpec] = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_columns(self, columns: Iterable[str], rule: str) -> None:
        """Fail fast with SchemaError if any column is absent from the df."""
        missing = [c for c in columns if c not in self._df.columns]
        if missing:
            raise SchemaError(
                f"Rule '{rule}' references column(s) not present in the DataFrame.",
                context={"missing_columns": missing, "dataset": self._name},
            )

    def _mask_to_issue(
        self,
        *,
        mask: pl.Series,
        rule: str,
        column: str | None,
        severity: Severity,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> ValidationIssue | None:
        """Convert a boolean failure-mask into a ValidationIssue, or None if clean.

        ``mask`` must be ``True`` for rows that FAIL the rule.
        """
        failing_count = int(mask.sum())
        if failing_count == 0:
            return None
        indices = (
            pl.arange(0, mask.len(), eager=True)
            .filter(mask)
            .head(_MAX_SAMPLE_ROW_INDICES)
            .to_list()
        )
        return ValidationIssue(
            rule=rule,
            column=column,
            severity=severity,
            message=message,
            failing_row_count=failing_count,
            row_indices=indices,
            details=details or {},
        )

    def _add_rule(
        self,
        name: str,
        column: str | None,
        severity: Severity,
        run: Callable[[], list[ValidationIssue]],
    ) -> "Validator":
        self._rules.append(_RuleSpec(name=name, column=column, severity=severity, run=run))
        return self

    # ------------------------------------------------------------------
    # Rule builders
    # ------------------------------------------------------------------

    def required(
        self, columns: Sequence[str], *, severity: Severity = Severity.ERROR
    ) -> "Validator":
        """Require that columns exist and contain no null / empty-string values.

        Args:
            columns: Column names that must be present and populated on
                every row.
            severity: Severity of raised issues. Defaults to ERROR.

        Returns:
            self, for chaining.

        Raises:
            SchemaError: if any column is missing from the DataFrame.
            RuleConfigurationError: if ``columns`` is empty.
        """
        if not columns:
            raise RuleConfigurationError("'required' needs at least one column.")
        self._require_columns(columns, "required")

        def _run() -> list[ValidationIssue]:
            issues: list[ValidationIssue] = []
            # Each column gets its own independent failure mask (and therefore
            # its own ValidationIssue), so a report can say precisely which
            # column(s) failed rather than lumping every column into one issue.
            for col in columns:
                dtype = self._df.schema[col]
                if dtype == pl.Utf8:
                    mask = self._df[col].is_null() | (self._df[col].str.strip_chars() == "")
                else:
                    mask = self._df[col].is_null()
                issue = self._mask_to_issue(
                    mask=mask,
                    rule="required",
                    column=col,
                    severity=severity,
                    message=f"'{col}' must not be null or empty.",
                )
                if issue:
                    issues.append(issue)
            return issues

        return self._add_rule("required", None, severity, _run)

    def not_null(
        self, columns: Sequence[str], *, severity: Severity = Severity.ERROR
    ) -> "Validator":
        """Require that columns contain no nulls (unlike ``required``, empty
        strings are allowed — useful for optional-but-present text fields).

        Args:
            columns: Columns that must not contain nulls.
            severity: Severity of raised issues.

        Returns:
            self, for chaining.
        """
        if not columns:
            raise RuleConfigurationError("'not_null' needs at least one column.")
        self._require_columns(columns, "not_null")

        def _run() -> list[ValidationIssue]:
            issues = []
            # Same one-issue-per-column pattern as `required` above, but the
            # per-column mask here is simpler: nulls only (empty strings pass).
            for col in columns:
                mask = self._df[col].is_null()
                issue = self._mask_to_issue(
                    mask=mask,
                    rule="not_null",
                    column=col,
                    severity=severity,
                    message=f"'{col}' must not be null.",
                )
                if issue:
                    issues.append(issue)
            return issues

        return self._add_rule("not_null", None, severity, _run)

    def currency(
        self,
        column: str,
        allowed: Sequence[str],
        *,
        case_sensitive: bool = True,
        severity: Severity = Severity.ERROR,
    ) -> "Validator":
        """Require a column's values to be within an allowed ISO currency set.

        Args:
            column: Column holding currency codes (e.g. ``"Currency"``).
            allowed: Allowed currency codes, e.g. ``["USD", "EUR", "GBP"]``.
            case_sensitive: If False, comparison is case-insensitive
                (values are upper-cased before comparison).
            severity: Severity of raised issues.

        Returns:
            self, for chaining.

        Raises:
            SchemaError: if ``column`` is missing.
            RuleConfigurationError: if ``allowed`` is empty.
        """
        if not allowed:
            raise RuleConfigurationError("'currency' needs a non-empty allowed list.")
        self._require_columns([column], "currency")
        allowed_set = list(allowed) if case_sensitive else [a.upper() for a in allowed]

        def _run() -> list[ValidationIssue]:
            series = self._df[column]
            compare = series if case_sensitive else series.str.to_uppercase()
            mask = (~compare.is_in(allowed_set)) | series.is_null()
            issue = self._mask_to_issue(
                mask=mask,
                rule="currency",
                column=column,
                severity=severity,
                message=f"'{column}' must be one of {allowed_set}.",
                details={"allowed": allowed_set},
            )
            return [issue] if issue else []

        return self._add_rule("currency", column, severity, _run)

    def duplicate(
        self, columns: Sequence[str], *, severity: Severity = Severity.ERROR
    ) -> "Validator":
        """Flag rows whose combination of ``columns`` is not unique.

        Args:
            columns: Column(s) forming the uniqueness key, e.g.
                ``["Invoice", "Vendor"]`` for a per-vendor invoice number.
            severity: Severity of raised issues.

        Returns:
            self, for chaining.
        """
        if not columns:
            raise RuleConfigurationError("'duplicate' needs at least one column.")
        self._require_columns(columns, "duplicate")

        def _run() -> list[ValidationIssue]:
            mask = self._df.select(pl.struct(columns).is_duplicated().alias("_dup"))["_dup"]
            issue = self._mask_to_issue(
                mask=mask,
                rule="duplicate",
                column=", ".join(columns),
                severity=severity,
                message=f"Duplicate values found for key {list(columns)}.",
                details={"key_columns": list(columns)},
            )
            return [issue] if issue else []

        return self._add_rule("duplicate", ", ".join(columns), severity, _run)

    def balance(
        self,
        group_by: Sequence[str],
        amount_column: str,
        *,
        tolerance: float = 0.005,
        severity: Severity = Severity.ERROR,
    ) -> "Validator":
        """Require that ``amount_column`` sums to (approximately) zero within
        each ``group_by`` group — the classic double-entry journal-balance
        check (debits net to zero against credits per journal/batch).

        Args:
            group_by: Grouping columns, e.g. ``["Journal"]`` or
                ``["Journal", "FiscalPeriod"]``.
            amount_column: Signed amount column (debits positive, credits
                negative, or vice versa, per the source system's convention).
            tolerance: Absolute rounding tolerance for the group sum to
                still be considered balanced. Defaults to 0.005 to absorb
                floating-point / currency-rounding noise.
            severity: Severity of raised issues.

        Returns:
            self, for chaining.
        """
        if not group_by:
            raise RuleConfigurationError("'balance' needs at least one group_by column.")
        self._require_columns([*group_by, amount_column], "balance")

        def _run() -> list[ValidationIssue]:
            grouped = (
                self._df.group_by(group_by, maintain_order=True)
                .agg(pl.col(amount_column).sum().alias("_group_sum"))
                .with_columns(pl.col("_group_sum").abs().gt(tolerance).alias("_out_of_balance"))
            )
            out_of_balance = grouped.filter(pl.col("_out_of_balance"))
            failing_count = out_of_balance.height
            if failing_count == 0:
                return []
            sample = out_of_balance.head(_MAX_SAMPLE_ROW_INDICES).to_dicts()
            issue = ValidationIssue(
                rule="balance",
                column=amount_column,
                severity=severity,
                message=(
                    f"{failing_count} group(s) of {list(group_by)} do not net to zero "
                    f"within tolerance {tolerance}."
                ),
                failing_row_count=failing_count,
                row_indices=[],
                details={"out_of_balance_groups": sample, "tolerance": tolerance},
            )
            return [issue]

        return self._add_rule("balance", amount_column, severity, _run)

    def foreign_key(
        self,
        column: str,
        valid_values: Sequence[Any] | pl.Series,
        *,
        allow_null: bool = False,
        severity: Severity = Severity.ERROR,
    ) -> "Validator":
        """Require every value in ``column`` to exist in a reference set.

        Args:
            column: Column holding the referencing key, e.g. ``"VendorID"``
                on an invoice extract.
            valid_values: The reference/master set of valid keys — typically
                the primary-key column pulled from a vendor/customer/GL
                master table extract.
            allow_null: If True, null values pass (useful for optional
                references such as an optional cost-center override).
            severity: Severity of raised issues.

        Returns:
            self, for chaining.
        """
        self._require_columns([column], "foreign_key")
        ref = pl.Series(valid_values) if not isinstance(valid_values, pl.Series) else valid_values
        # `.implode()` wraps the reference Series as a single list-typed value so
        # `.is_in()` compares element-wise against a *set* of allowed values rather
        # than doing a same-dtype elementwise comparison (which Polars now flags as
        # ambiguous/deprecated for this use case — see polars issue #22149).
        ref_list = ref.implode()

        def _run() -> list[ValidationIssue]:
            series = self._df[column]
            not_in_ref = series.is_not_null() & (~series.is_in(ref_list).fill_null(False))
            mask = not_in_ref if allow_null else (not_in_ref | series.is_null())
            issue = self._mask_to_issue(
                mask=mask,
                rule="foreign_key",
                column=column,
                severity=severity,
                message=f"'{column}' contains values not present in the reference set.",
                details={"reference_size": ref.len()},
            )
            return [issue] if issue else []

        return self._add_rule("foreign_key", column, severity, _run)

    def date(
        self,
        column: str,
        *,
        fmt: str | None = None,
        min_date: date | None = None,
        max_date: date | None = None,
        severity: Severity = Severity.ERROR,
    ) -> "Validator":
        """Validate a column parses as a date and optionally falls within bounds.

        Args:
            column: Target column. May already be a ``pl.Date``/``pl.Datetime``
                dtype, or a string column to be parsed using ``fmt``.
            fmt: strptime-style format string (e.g. ``"%Y-%m-%d"``) used only
                when ``column`` is a string dtype. Ignored for native date
                dtypes.
            min_date: Optional inclusive lower bound (e.g. fiscal year start).
            max_date: Optional inclusive upper bound (e.g. today, or period
                close date).
            severity: Severity of raised issues.

        Returns:
            self, for chaining.
        """
        self._require_columns([column], "date")

        def _run() -> list[ValidationIssue]:
            dtype = self._df.schema[column]
            if dtype in (pl.Date, pl.Datetime):
                parsed = self._df[column]
                unparseable_mask = parsed.is_null() & self._df[column].is_null()
            else:
                try:
                    parsed = self._df[column].str.strptime(pl.Date, fmt, strict=False)
                except Exception as exc:  # noqa: BLE001 - surfaced as ERPKit error
                    raise ValidationExecutionError(
                        f"Failed to parse '{column}' as date with format {fmt!r}.",
                        context={"column": column, "format": fmt},
                    ) from exc
                unparseable_mask = parsed.is_null() & self._df[column].is_not_null()

            issues: list[ValidationIssue] = []
            unparseable_issue = self._mask_to_issue(
                mask=unparseable_mask,
                rule="date",
                column=column,
                severity=severity,
                message=f"'{column}' contains value(s) that are not valid dates.",
            )
            if unparseable_issue:
                issues.append(unparseable_issue)

            if min_date is not None or max_date is not None:
                out_of_range = parsed.is_not_null() & (
                    (parsed < min_date if min_date else pl.lit(False))
                    | (parsed > max_date if max_date else pl.lit(False))
                )
                range_issue = self._mask_to_issue(
                    mask=out_of_range,
                    rule="date_range",
                    column=column,
                    severity=severity,
                    message=(
                        f"'{column}' contains date(s) outside "
                        f"[{min_date or '-inf'}, {max_date or '+inf'}]."
                    ),
                    details={"min_date": str(min_date), "max_date": str(max_date)},
                )
                if range_issue:
                    issues.append(range_issue)
            return issues

        return self._add_rule("date", column, severity, _run)

    def numeric(
        self, column: str, *, allow_null: bool = False, severity: Severity = Severity.ERROR
    ) -> "Validator":
        """Require a column to hold numeric (non-NaN) values.

        Args:
            column: Target column.
            allow_null: If True, nulls are treated as passing; otherwise
                nulls fail the rule alongside non-numeric values.
            severity: Severity of raised issues.

        Returns:
            self, for chaining.
        """
        self._require_columns([column], "numeric")

        def _run() -> list[ValidationIssue]:
            dtype = self._df.schema[column]
            if dtype.is_numeric():
                nan_mask = self._df[column].is_nan() if dtype.is_float() else pl.Series(
                    [False] * self._df.height
                )
                null_mask = self._df[column].is_null()
                mask = nan_mask | (null_mask if not allow_null else pl.Series([False] * self._df.height))
            else:
                cast = self._df[column].cast(pl.Float64, strict=False)
                failed_cast = cast.is_null() & self._df[column].is_not_null()
                null_mask = self._df[column].is_null() & (not allow_null)
                mask = failed_cast | pl.Series([null_mask] if isinstance(null_mask, bool) else null_mask)
            issue = self._mask_to_issue(
                mask=mask,
                rule="numeric",
                column=column,
                severity=severity,
                message=f"'{column}' must contain numeric values.",
            )
            return [issue] if issue else []

        return self._add_rule("numeric", column, severity, _run)

    def regex(
        self, column: str, pattern: str, *, severity: Severity = Severity.ERROR
    ) -> "Validator":
        """Require every non-null value in ``column`` to fully match ``pattern``.

        Args:
            column: Target string column.
            pattern: A Python-flavored regular expression. Anchored
                automatically (``^`` / ``$`` added if absent) so partial
                matches are not silently accepted.
            severity: Severity of raised issues.

        Returns:
            self, for chaining.

        Raises:
            RuleConfigurationError: if ``pattern`` does not compile.
        """
        self._require_columns([column], "regex")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise RuleConfigurationError(
                f"Invalid regex pattern for column '{column}': {exc}",
                context={"pattern": pattern},
            ) from exc
        anchored = pattern if pattern.startswith("^") else f"^{pattern}"
        anchored = anchored if anchored.endswith("$") else f"{anchored}$"

        def _run() -> list[ValidationIssue]:
            series = self._df[column]
            matches = series.str.contains(anchored)
            mask = (~matches).fill_null(True)
            issue = self._mask_to_issue(
                mask=mask,
                rule="regex",
                column=column,
                severity=severity,
                message=f"'{column}' must match pattern {pattern!r}.",
                details={"pattern": pattern},
            )
            return [issue] if issue else []

        return self._add_rule("regex", column, severity, _run)

    def range(
        self,
        column: str,
        *,
        minimum: float | None = None,
        maximum: float | None = None,
        inclusive: bool = True,
        severity: Severity = Severity.ERROR,
    ) -> "Validator":
        """Require a numeric column's values to fall within ``[minimum, maximum]``.

        Args:
            column: Target numeric column.
            minimum: Lower bound, or ``None`` for no lower bound.
            maximum: Upper bound, or ``None`` for no upper bound.
            inclusive: Whether bounds are inclusive (default) or exclusive.
            severity: Severity of raised issues.

        Returns:
            self, for chaining.

        Raises:
            RuleConfigurationError: if both bounds are ``None``, or
                ``minimum > maximum``.
        """
        if minimum is None and maximum is None:
            raise RuleConfigurationError("'range' needs at least one of minimum/maximum.")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise RuleConfigurationError(
                "'range' minimum must not exceed maximum.",
                context={"minimum": minimum, "maximum": maximum},
            )
        self._require_columns([column], "range")

        def _run() -> list[ValidationIssue]:
            series = self._df[column]
            if inclusive:
                below = series < minimum if minimum is not None else pl.Series([False] * series.len())
                above = series > maximum if maximum is not None else pl.Series([False] * series.len())
            else:
                below = series <= minimum if minimum is not None else pl.Series([False] * series.len())
                above = series >= maximum if maximum is not None else pl.Series([False] * series.len())
            mask = (below | above) & series.is_not_null()
            issue = self._mask_to_issue(
                mask=mask,
                rule="range",
                column=column,
                severity=severity,
                message=f"'{column}' must be within [{minimum}, {maximum}] (inclusive={inclusive}).",
                details={"minimum": minimum, "maximum": maximum},
            )
            return [issue] if issue else []

        return self._add_rule("range", column, severity, _run)

    def custom(
        self,
        fn: Callable[[pl.DataFrame], pl.Series],
        *,
        name: str,
        column: str | None = None,
        message: str | None = None,
        severity: Severity = Severity.ERROR,
    ) -> "Validator":
        """Register a caller-defined rule for business logic ERPKit can't
        anticipate (e.g. ERP-specific approval-hierarchy checks).

        Args:
            fn: Callable that receives the full DataFrame and returns a
                boolean ``pl.Series`` of the same length, ``True`` marking
                FAILING rows (mirrors every built-in rule's convention).
            name: Rule name used in the result/report.
            column: Optional column label for reporting purposes only.
            message: Optional custom failure message.
            severity: Severity of raised issues.

        Returns:
            self, for chaining.

        Raises:
            RuleConfigurationError: if ``name`` is empty.
        """
        if not name:
            raise RuleConfigurationError("'custom' rules require a non-empty name.")

        def _run() -> list[ValidationIssue]:
            try:
                mask = fn(self._df)
            except Exception as exc:  # noqa: BLE001 - re-raised as ERPKit error
                raise ValidationExecutionError(
                    f"Custom rule '{name}' raised an exception during execution.",
                    context={"rule": name},
                ) from exc
            if not isinstance(mask, pl.Series) or mask.dtype != pl.Boolean:
                raise ValidationExecutionError(
                    f"Custom rule '{name}' must return a boolean polars.Series.",
                    context={"rule": name, "returned_type": type(mask).__name__},
                )
            if mask.len() != self._df.height:
                raise ValidationExecutionError(
                    f"Custom rule '{name}' returned a Series of mismatched length.",
                    context={"expected": self._df.height, "received": mask.len()},
                )
            issue = self._mask_to_issue(
                mask=mask,
                rule=name,
                column=column,
                severity=severity,
                message=message or f"Custom rule '{name}' failed.",
            )
            return [issue] if issue else []

        return self._add_rule(name, column, severity, _run)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def validate(self) -> ValidationResult:
        """Execute every queued rule and return the aggregate result.

        Rules execute in the order they were declared. A failure in one
        rule's *execution* (as opposed to a data validation failure, which
        is expected and captured as a ``ValidationIssue``) aborts the whole
        run with a wrapped :class:`ValidationExecutionError`, since a
        rule that cannot execute means the result set can no longer be
        trusted as complete.

        Returns:
            A fully populated :class:`ValidationResult`.

        Raises:
            ValidationExecutionError: if any rule raises during execution.
        """
        started = time.perf_counter()
        all_issues: list[ValidationIssue] = []
        rule_timings: dict[str, float] = {}

        logger.info(
            "validator.start",
            extra={"dataset": self._name, "rule_count": len(self._rules), "row_count": self._df.height},
        )

        # Rules run strictly in declaration order (see class docstring). Each
        # rule is timed individually so `ValidationResult.statistics` can show
        # callers which rule is the slow one on large extracts.
        for spec in self._rules:
            rule_started = time.perf_counter()
            try:
                issues = spec.run()
            except (SchemaError, RuleConfigurationError, ValidationExecutionError):
                raise
            except Exception as exc:  # noqa: BLE001 - normalize to ERPKit error
                raise ValidationExecutionError(
                    f"Rule '{spec.name}' failed during execution.",
                    context={"rule": spec.name, "dataset": self._name},
                ) from exc
            elapsed = time.perf_counter() - rule_started
            key = spec.name if spec.name not in rule_timings else f"{spec.name}#{len(rule_timings)}"
            rule_timings[key] = round(elapsed, 6)
            all_issues.extend(issues)
            logger.debug(
                "validator.rule_complete",
                extra={"rule": spec.name, "issues": len(issues), "elapsed_seconds": elapsed},
            )

        total_elapsed = round(time.perf_counter() - started, 6)
        result = ValidationResult.build(
            issues=all_issues,
            row_count=self._df.height,
            execution_time=total_elapsed,
            rule_timings=rule_timings,
        )
        logger.info(
            "validator.complete",
            extra={
                "dataset": self._name,
                "is_valid": result.is_valid,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "execution_time": total_elapsed,
            },
        )
        return result
