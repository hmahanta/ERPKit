# ==============================================================================
# Module      : erpkit.pipeline.financial_pipeline
# Package     : erpkit-pipeline
# Purpose     : Orchestrates the end-to-end financial validation pipeline —
#               CSV import, MetaFlow schema loading, transformation, rule
#               validation, and audit-trail/report generation.
# Maintainer  : ERPKit Core Team
# Standard    : Follows ERPKit coding standard — PEP 8 formatting, Google-style
#               docstrings on every public symbol, explicit type hints, and
#               ERPKitError-derived exceptions (never a bare Exception) for
#               anything a caller might need to catch.
# ==============================================================================
"""End-to-end, metadata-driven financial validation pipeline.

:class:`FinancialValidationPipeline` wires together every Phase 1 piece —
CSV import, MetaFlow JSON schema loading, schema-driven transformation,
schema-driven validation (built on :class:`erpkit.core.validator.Validator`),
an audit trail, and a final serializable report — into a single ``.run()``
call. It is intentionally a thin *orchestration* layer: none of the
column-level logic lives here. Transformations and validation rules are
data (the JSON schema), not code, so a new rule type or transform can be
added to a dataset without touching this module.

Pipeline stages
----------------
1. ``start``          - run begins, audit trail initialized
2. ``metadata_load``  - schema JSON is read and structurally validated
3. ``import``         - source CSV is read into a Polars DataFrame
4. ``transform``      - schema ``transformation_rules`` are applied
5. ``validate``        - schema ``validation_rules`` are mapped onto a
   :class:`~erpkit.core.validator.Validator` and executed
6. ``complete``        - report is assembled
7. ``failed``          - recorded instead of the remaining stages if any
   prior stage raises; the pipeline still surfaces a full audit trail up
   to the point of failure before re-raising.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

import polars as pl

from erpkit.core.exceptions import MetadataError, PipelineError
from erpkit.core.result import Severity, ValidationResult
from erpkit.core.validator import Validator

logger = logging.getLogger("erpkit.pipeline.financial_pipeline")

_REQUIRED_SCHEMA_KEYS = ("entity", "columns", "validation_rules")
"""Top-level keys every MetaFlow schema document must contain.

``transformation_rules`` is deliberately excluded: a schema with no
transformations at all (pure passthrough validation) is valid.
"""

_REQUIRED_RULE_KEYS: dict[str, tuple[str, ...]] = {
    "required": ("columns",),
    "not_null": ("columns",),
    "currency": ("column", "allowed"),
    "duplicate": ("columns",),
    "balance": ("group_by", "amount_column"),
    "foreign_key": ("column", "reference"),
    "date": ("column",),
    "numeric": ("column",),
    "regex": ("column", "pattern"),
    "range": ("column",),
}
"""Keys required on a ``validation_rules`` entry, keyed by ``rule`` name.

Rule names not present in this mapping are treated as forward-compatible
unknown rules (logged and skipped) rather than a metadata error — see
``ERPKit Design Philosophy #4 (Metadata Driven)`` and the schema-evolution
goal in the project brief: an older pipeline build should not hard-fail
just because a newer schema references a rule type it doesn't know yet.
"""


@dataclass(slots=True)
class AuditEntry:
    """A single timestamped event in a pipeline run's audit trail."""

    stage: str
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }


@dataclass(slots=True)
class PipelineReport:
    """Final, serializable output of a ``FinancialValidationPipeline.run()`` call."""

    dataset: str
    validation_result: ValidationResult
    transformed_row_count: int
    audit_trail: list[AuditEntry]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "transformed_row_count": self.transformed_row_count,
            "validation": self.validation_result.to_dict(),
            "audit_trail": [entry.to_dict() for entry in self.audit_trail],
        }

    def to_json(self, *, indent: int = 2) -> str:
        """Return the report as a JSON string, safe for files/API bodies."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def print_summary(self) -> None:
        """Print a short, human-readable console summary of the report."""
        result = self.validation_result
        status = "PASSED" if result.is_valid else "FAILED"
        lines = [
            "=" * 60,
            "ERPKit Financial Validation Report",
            "=" * 60,
            f"Dataset:            {self.dataset}",
            f"Status:             {status}",
            f"Rows validated:     {result.row_count}",
            f"Errors:             {result.error_count}",
            f"Warnings:           {result.warning_count}",
            f"Execution time:     {result.execution_time:.4f}s",
            "-" * 60,
        ]
        for issue in result.errors + result.warnings:
            lines.append(f"[{issue.severity.value.upper():7s}] {issue.rule:15s} {issue.message}")
        lines.append("=" * 60)
        print("\n".join(lines))


class FinancialValidationPipeline:
    """Metadata-driven pipeline: CSV -> transform -> validate -> report.

    Example:
        >>> pipeline = FinancialValidationPipeline(dataset_name="ap_invoices")
        >>> report = pipeline.run(
        ...     csv_path="invoices.csv",
        ...     schema_path="invoice_schema.json",
        ...     reference_data={"Supplier": vendor_master_df},
        ... )
        >>> report.validation_result.is_valid
        True
    """

    def __init__(self, dataset_name: str = "unnamed") -> None:
        """Initialize a pipeline.

        Args:
            dataset_name: Logical name for the dataset being processed,
                used in logs, the audit trail, and the final report.
        """
        self.dataset_name = dataset_name
        self._audit_trail: list[AuditEntry] = []

    # ------------------------------------------------------------------
    # Audit trail
    # ------------------------------------------------------------------

    def _audit(self, stage: str, message: str, **details: Any) -> None:
        entry = AuditEntry(stage=stage, message=message, details=details)
        self._audit_trail.append(entry)
        logger.info("pipeline.%s", stage, extra={"dataset": self.dataset_name, **details})

    # ------------------------------------------------------------------
    # Stage: metadata_load
    # ------------------------------------------------------------------

    def _load_schema(self, schema_path: str | Path) -> dict[str, Any]:
        path = Path(schema_path)
        if not path.exists():
            raise MetadataError(
                "Schema file not found.", context={"schema_path": str(path)}
            )
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise MetadataError(
                "Schema file could not be read.", context={"schema_path": str(path)}
            ) from exc
        try:
            schema = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MetadataError(
                "Schema file is not valid JSON.",
                context={"schema_path": str(path), "json_error": str(exc)},
            ) from exc
        if not isinstance(schema, dict):
            raise MetadataError(
                "Schema document must be a JSON object.", context={"schema_path": str(path)}
            )
        missing = [k for k in _REQUIRED_SCHEMA_KEYS if k not in schema]
        if missing:
            raise MetadataError(
                "Schema document is missing required key(s).",
                context={"missing_keys": missing, "schema_path": str(path)},
            )
        return schema

    # ------------------------------------------------------------------
    # Stage: import
    # ------------------------------------------------------------------

    def _import_csv(self, csv_path: str | Path) -> pl.DataFrame:
        path = Path(csv_path)
        if not path.exists():
            raise PipelineError("CSV source file not found.", context={"csv_path": str(path)})
        try:
            return pl.read_csv(path, try_parse_dates=False)
        except Exception as exc:  # noqa: BLE001 - normalize to ERPKit error
            raise PipelineError(
                "Failed to read CSV source file.", context={"csv_path": str(path)}
            ) from exc

    # ------------------------------------------------------------------
    # Stage: transform
    # ------------------------------------------------------------------

    @staticmethod
    def _mask_value(value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) <= 4:
            return "*" * len(value)
        return "*" * (len(value) - 4) + value[-4:]

    def _apply_transformations(
        self, df: pl.DataFrame, transformation_rules: list[dict[str, Any]]
    ) -> pl.DataFrame:
        # Transformation rules are applied sequentially, in schema-declared order,
        # so a later rule always sees the output of every earlier rule (e.g. a
        # "trim" rule can run before a "uppercase" rule on the same column).
        for rule in transformation_rules:
            op = rule.get("op")
            columns = rule.get("columns", [])
            # Only touch columns that actually exist on this DataFrame — a schema
            # may target optional columns that are absent from a given extract.
            present = [c for c in columns if c in df.columns]

            if op == "trim":
                string_cols = [c for c in present if df.schema[c] == pl.Utf8]
                if string_cols:
                    df = df.with_columns(
                        [pl.col(c).str.strip_chars().alias(c) for c in string_cols]
                    )
            elif op == "uppercase":
                string_cols = [c for c in present if df.schema[c] == pl.Utf8]
                if string_cols:
                    df = df.with_columns(
                        [pl.col(c).str.to_uppercase().alias(c) for c in string_cols]
                    )
            elif op == "round":
                precision = rule.get("precision", 2)
                numeric_cols = [c for c in present if df.schema[c].is_numeric()]
                if numeric_cols:
                    df = df.with_columns(
                        [pl.col(c).round(precision).alias(c) for c in numeric_cols]
                    )
            elif op == "mask":
                string_cols = [c for c in present if df.schema[c] == pl.Utf8]
                for c in string_cols:
                    df = df.with_columns(
                        pl.col(c)
                        .map_elements(self._mask_value, return_dtype=pl.Utf8)
                        .alias(c)
                    )
            else:
                logger.warning(
                    "pipeline.transform.unknown_op",
                    extra={"op": op, "dataset": self.dataset_name},
                )
        return df

    # ------------------------------------------------------------------
    # Stage: validate
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_bound_date(value: Any) -> date | None:
        if value is None:
            return None
        if value == "today":
            return datetime.now(timezone.utc).date()
        if isinstance(value, date):
            return value
        return datetime.strptime(str(value), "%Y-%m-%d").date()

    def _check_required_keys(self, rule_def: dict[str, Any]) -> None:
        rule = rule_def.get("rule")
        required_keys = _REQUIRED_RULE_KEYS.get(rule)
        if required_keys is None:
            return
        missing = [k for k in required_keys if k not in rule_def]
        if missing:
            raise MetadataError(
                f"Validation rule '{rule}' is missing required key(s).",
                context={"missing_keys": missing, "rule_definition": rule_def},
            )

    def _build_validator(
        self,
        df: pl.DataFrame,
        schema: dict[str, Any],
        reference_data: dict[str, pl.DataFrame] | None,
    ) -> Validator:
        validator = Validator(df, name=self.dataset_name)

        # Walk every rule declared in the schema and map it onto the matching
        # Validator builder method. This loop is the single translation point
        # between "metadata" (JSON rule definitions) and "code" (Validator
        # calls) — keeping it here means Validator itself never needs to know
        # that schemas or JSON exist (see module docstring, "Framework Agnostic").
        for rule_def in schema.get("validation_rules", []):
            rule = rule_def.get("rule")
            severity = Severity(rule_def.get("severity", "error"))
            self._check_required_keys(rule_def)

            if rule == "required":
                validator.required(rule_def["columns"], severity=severity)
            elif rule == "not_null":
                validator.not_null(rule_def["columns"], severity=severity)
            elif rule == "currency":
                validator.currency(
                    rule_def["column"],
                    rule_def["allowed"],
                    case_sensitive=rule_def.get("case_sensitive", True),
                    severity=severity,
                )
            elif rule == "duplicate":
                validator.duplicate(rule_def["columns"], severity=severity)
            elif rule == "balance":
                validator.balance(
                    rule_def["group_by"],
                    rule_def["amount_column"],
                    tolerance=rule_def.get("tolerance", 0.005),
                    severity=severity,
                )
            elif rule == "foreign_key":
                reference = rule_def["reference"]
                entity = reference.get("entity")
                ref_column = reference.get("column")
                if not entity or not ref_column:
                    raise MetadataError(
                        "'foreign_key' rule reference must include 'entity' and 'column'.",
                        context={"rule_definition": rule_def},
                    )
                if reference_data is None or entity not in reference_data:
                    self._audit(
                        "validate",
                        f"Skipped foreign_key rule for '{rule_def['column']}': "
                        f"no reference data supplied for entity '{entity}'.",
                    )
                    continue
                ref_df = reference_data[entity]
                if ref_column not in ref_df.columns:
                    raise MetadataError(
                        "Foreign key reference column not found in reference data.",
                        context={"entity": entity, "column": ref_column},
                    )
                validator.foreign_key(
                    rule_def["column"],
                    ref_df[ref_column],
                    allow_null=rule_def.get("allow_null", False),
                    severity=severity,
                )
            elif rule == "date":
                validator.date(
                    rule_def["column"],
                    fmt=rule_def.get("format"),
                    min_date=self._parse_bound_date(rule_def.get("min_date")),
                    max_date=self._parse_bound_date(rule_def.get("max_date")),
                    severity=severity,
                )
            elif rule == "numeric":
                validator.numeric(
                    rule_def["column"],
                    allow_null=rule_def.get("allow_null", False),
                    severity=severity,
                )
            elif rule == "regex":
                validator.regex(rule_def["column"], rule_def["pattern"], severity=severity)
            elif rule == "range":
                validator.range(
                    rule_def["column"],
                    minimum=rule_def.get("minimum"),
                    maximum=rule_def.get("maximum"),
                    inclusive=rule_def.get("inclusive", True),
                    severity=severity,
                )
            else:
                logger.warning(
                    "pipeline.validate.unknown_rule",
                    extra={"rule": rule, "dataset": self.dataset_name},
                )
                self._audit("validate", f"Skipped unknown validation rule '{rule}'.")

        return validator

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def run(
        self,
        *,
        csv_path: str | Path,
        schema_path: str | Path,
        reference_data: dict[str, pl.DataFrame] | None = None,
    ) -> PipelineReport:
        """Execute the full import -> transform -> validate pipeline.

        Args:
            csv_path: Path to the source CSV extract.
            schema_path: Path to the MetaFlow JSON schema describing
                columns, transformation rules, and validation rules.
            reference_data: Optional mapping of entity name (as referenced
                by a schema's ``foreign_key`` rules, e.g. ``"Supplier"``)
                to a Polars DataFrame holding that entity's master data.
                Any ``foreign_key`` rule whose entity is absent here is
                skipped gracefully rather than failing the run.

        Returns:
            A :class:`PipelineReport` with the validation result, row
            count after transformation, and the full audit trail.

        Raises:
            MetadataError: if the schema file is missing, malformed, or
                structurally invalid.
            PipelineError: if the CSV file is missing/unreadable, or an
                unexpected error occurs outside of metadata/validation.
        """
        self._audit_trail = []
        self._audit("start", f"Pipeline '{self.dataset_name}' started.")

        try:
            schema = self._load_schema(schema_path)
            self._audit(
                "metadata_load", f"Loaded schema for entity '{schema.get('entity')}'."
            )

            df = self._import_csv(csv_path)
            self._audit("import", f"Imported {df.height} row(s) from '{csv_path}'.")

            transformed = self._apply_transformations(
                df, schema.get("transformation_rules", [])
            )
            self._audit(
                "transform",
                f"Applied {len(schema.get('transformation_rules', []))} "
                f"transformation rule(s); {transformed.height} row(s) remain.",
            )

            validator = self._build_validator(transformed, schema, reference_data)
            result = validator.validate()
            self._audit(
                "validate",
                f"Validation complete: is_valid={result.is_valid}, "
                f"errors={result.error_count}, warnings={result.warning_count}.",
            )

            self._audit("complete", "Pipeline completed successfully.")
            return PipelineReport(
                dataset=self.dataset_name,
                validation_result=result,
                transformed_row_count=transformed.height,
                audit_trail=list(self._audit_trail),
            )
        except (MetadataError, PipelineError) as exc:
            self._audit("failed", f"Pipeline failed: {exc.message}")
            raise
        except Exception as exc:  # noqa: BLE001 - normalize to ERPKit error
            self._audit("failed", f"Pipeline failed with an unexpected error: {exc}")
            raise PipelineError(
                "Pipeline failed due to an unexpected error.",
                context={"dataset": self.dataset_name, "original_error": str(exc)},
            ) from exc
