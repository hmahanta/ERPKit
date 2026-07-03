"""Integration tests for erpkit.pipeline.FinancialValidationPipeline.

Uses small on-disk CSV/JSON fixtures generated per-test (rather than the
larger ``examples/data`` demo files) so each test is self-contained and
fast, and exercises every pipeline stage: import, metadata loading,
transformation, validation, audit trail, and error handling.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest

from erpkit.core.exceptions import MetadataError, PipelineError
from erpkit.pipeline.financial_pipeline import FinancialValidationPipeline


SCHEMA = {
    "entity": "Invoice",
    "version": "1.0.0",
    "columns": [
        {"name": "InvoiceID", "dtype": "string"},
        {"name": "Vendor", "dtype": "string"},
        {"name": "Currency", "dtype": "string"},
        {"name": "Amount", "dtype": "float"},
    ],
    "validation_rules": [
        {"rule": "required", "columns": ["InvoiceID", "Vendor", "Currency"], "severity": "error"},
        {"rule": "currency", "column": "Currency", "allowed": ["USD", "EUR"], "severity": "error"},
        {"rule": "range", "column": "Amount", "minimum": 0, "maximum": 100000, "severity": "error"},
        {
            "rule": "foreign_key",
            "column": "Vendor",
            "reference": {"entity": "Supplier", "column": "SupplierID"},
            "severity": "error",
        },
    ],
    "transformation_rules": [
        {"op": "trim", "columns": ["Vendor", "Currency"]},
        {"op": "uppercase", "columns": ["Currency"]},
        {"op": "round", "columns": ["Amount"], "precision": 2},
    ],
}


@pytest.fixture
def workdir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def schema_path(workdir: Path) -> Path:
    path = workdir / "invoice_schema.json"
    path.write_text(json.dumps(SCHEMA))
    return path


@pytest.fixture
def clean_csv(workdir: Path) -> Path:
    path = workdir / "invoices.csv"
    path.write_text(
        "InvoiceID,Vendor,Currency,Amount\n"
        "INV-1,V-1, usd ,100.005\n"
        "INV-2,V-2,EUR,250.129\n"
    )
    return path


@pytest.fixture
def dirty_csv(workdir: Path) -> Path:
    path = workdir / "invoices_dirty.csv"
    path.write_text(
        "InvoiceID,Vendor,Currency,Amount\n"
        "INV-1,V-1,USD,100.0\n"
        "INV-2,,ZZZ,-5.0\n"
        "INV-3,V-99,USD,999999.0\n"
    )
    return path


@pytest.fixture
def vendor_master() -> pl.DataFrame:
    return pl.DataFrame({"SupplierID": ["V-1", "V-2"]})


class TestPipelineHappyPath:
    def test_clean_data_passes_validation(
        self, clean_csv: Path, schema_path: Path, vendor_master: pl.DataFrame
    ) -> None:
        pipeline = FinancialValidationPipeline(dataset_name="test_invoices")
        report = pipeline.run(
            csv_path=clean_csv, schema_path=schema_path, reference_data={"Supplier": vendor_master}
        )
        assert report.validation_result.is_valid is True
        assert report.transformed_row_count == 2

    def test_transformations_applied_before_validation(
        self, clean_csv: Path, schema_path: Path, vendor_master: pl.DataFrame
    ) -> None:
        # "usd" with whitespace would fail the currency rule if not
        # trimmed+uppercased by the transformation stage first.
        pipeline = FinancialValidationPipeline(dataset_name="test_invoices")
        report = pipeline.run(
            csv_path=clean_csv, schema_path=schema_path, reference_data={"Supplier": vendor_master}
        )
        assert report.validation_result.is_valid is True

    def test_audit_trail_records_every_stage(
        self, clean_csv: Path, schema_path: Path, vendor_master: pl.DataFrame
    ) -> None:
        pipeline = FinancialValidationPipeline(dataset_name="test_invoices")
        report = pipeline.run(
            csv_path=clean_csv, schema_path=schema_path, reference_data={"Supplier": vendor_master}
        )
        stages = [e.stage for e in report.audit_trail]
        assert "start" in stages
        assert "import" in stages
        assert "metadata_load" in stages
        assert "transform" in stages
        assert "validate" in stages
        assert "complete" in stages

    def test_report_to_dict_and_json_serializable(
        self, clean_csv: Path, schema_path: Path, vendor_master: pl.DataFrame
    ) -> None:
        pipeline = FinancialValidationPipeline(dataset_name="test_invoices")
        report = pipeline.run(
            csv_path=clean_csv, schema_path=schema_path, reference_data={"Supplier": vendor_master}
        )
        as_json = report.to_json()
        parsed = json.loads(as_json)
        assert parsed["dataset"] == "test_invoices"
        assert "validation" in parsed


class TestPipelineDirtyData:
    def test_dirty_data_fails_validation(
        self, dirty_csv: Path, schema_path: Path, vendor_master: pl.DataFrame
    ) -> None:
        pipeline = FinancialValidationPipeline(dataset_name="test_invoices_dirty")
        report = pipeline.run(
            csv_path=dirty_csv, schema_path=schema_path, reference_data={"Supplier": vendor_master}
        )
        assert report.validation_result.is_valid is False
        rule_names = {e.rule for e in report.validation_result.errors}
        assert "required" in rule_names
        assert "currency" in rule_names
        assert "range" in rule_names
        assert "foreign_key" in rule_names

    def test_missing_reference_data_skips_foreign_key_gracefully(
        self, dirty_csv: Path, schema_path: Path
    ) -> None:
        pipeline = FinancialValidationPipeline(dataset_name="no_reference_data")
        # Should not raise even though "Supplier" reference data was never provided.
        report = pipeline.run(csv_path=dirty_csv, schema_path=schema_path, reference_data=None)
        rule_names = {e.rule for e in report.validation_result.errors}
        assert "foreign_key" not in rule_names


class TestPipelineErrorHandling:
    def test_missing_csv_raises_pipeline_error(
        self, workdir: Path, schema_path: Path
    ) -> None:
        pipeline = FinancialValidationPipeline(dataset_name="missing_csv")
        with pytest.raises(PipelineError):
            pipeline.run(csv_path=workdir / "does_not_exist.csv", schema_path=schema_path)

    def test_missing_schema_raises_metadata_error(
        self, clean_csv: Path, workdir: Path
    ) -> None:
        pipeline = FinancialValidationPipeline(dataset_name="missing_schema")
        with pytest.raises(MetadataError):
            pipeline.run(csv_path=clean_csv, schema_path=workdir / "no_schema.json")

    def test_malformed_json_schema_raises_metadata_error(
        self, clean_csv: Path, workdir: Path
    ) -> None:
        bad_schema = workdir / "bad_schema.json"
        bad_schema.write_text("{not valid json")
        pipeline = FinancialValidationPipeline(dataset_name="bad_schema")
        with pytest.raises(MetadataError):
            pipeline.run(csv_path=clean_csv, schema_path=bad_schema)

    def test_schema_missing_required_keys_raises_metadata_error(
        self, clean_csv: Path, workdir: Path
    ) -> None:
        incomplete = workdir / "incomplete_schema.json"
        incomplete.write_text(json.dumps({"entity": "Invoice"}))
        pipeline = FinancialValidationPipeline(dataset_name="incomplete_schema")
        with pytest.raises(MetadataError):
            pipeline.run(csv_path=clean_csv, schema_path=incomplete)

    def test_failed_run_still_records_audit_trail_up_to_failure(
        self, workdir: Path, schema_path: Path
    ) -> None:
        pipeline = FinancialValidationPipeline(dataset_name="failure_audit")
        with pytest.raises(PipelineError):
            pipeline.run(csv_path=workdir / "nope.csv", schema_path=schema_path)
        stages = [e.stage for e in pipeline._audit_trail]
        assert "start" in stages
        assert "failed" in stages


class TestSchemaRuleMappingCoverage:
    """Exercises the metadata -> Validator mapping for rule kinds not
    covered by the primary SCHEMA fixture (not_null, duplicate, balance,
    regex, date, mask transform, and unknown rule/transform handling).
    """

    def test_not_null_duplicate_balance_regex_date_rules_via_metadata(
        self, workdir: Path
    ) -> None:
        schema = {
            "entity": "Journal",
            "columns": [],
            "validation_rules": [
                {"rule": "not_null", "columns": ["LineNumber"], "severity": "error"},
                {"rule": "duplicate", "columns": ["Journal", "LineNumber"], "severity": "error"},
                {
                    "rule": "balance",
                    "group_by": ["Journal"],
                    "amount_column": "Amount",
                    "tolerance": 0.01,
                    "severity": "error",
                },
                {"rule": "regex", "column": "Journal", "pattern": "JRN-\\d+", "severity": "error"},
                {
                    "rule": "date",
                    "column": "PostedDate",
                    "format": "%Y-%m-%d",
                    "min_date": "2020-01-01",
                    "max_date": "today",
                    "severity": "warning",
                },
                {"rule": "unknown_future_rule", "severity": "warning"},
            ],
            "transformation_rules": [
                {"op": "mask", "columns": ["BankAccountNumber"]},
                {"op": "some_future_transform", "columns": ["Journal"]},
            ],
        }
        schema_path = workdir / "journal_schema.json"
        schema_path.write_text(json.dumps(schema))

        csv_path = workdir / "journal.csv"
        csv_path.write_text(
            "Journal,LineNumber,Amount,PostedDate,BankAccountNumber\n"
            "JRN-1,1,100.0,2026-01-01,ACCT123456789012\n"
            "JRN-1,2,-100.0,2026-01-02,ACCT123456789012\n"
        )

        pipeline = FinancialValidationPipeline(dataset_name="journal_metadata_coverage")
        report = pipeline.run(csv_path=csv_path, schema_path=schema_path)
        assert report.validation_result.row_count == 2
        # Masking should have rewritten the bank account column.
        rule_names = {e.rule for e in report.validation_result.errors}
        assert "not_null" not in rule_names  # LineNumber is populated
        assert "balance" not in rule_names  # 100 + -100 == 0

    def test_rule_missing_required_key_raises_metadata_error(self, workdir: Path) -> None:
        schema = {
            "entity": "Invoice",
            "columns": [],
            "validation_rules": [{"rule": "currency", "severity": "error"}],  # missing "column"/"allowed"
        }
        schema_path = workdir / "broken_schema.json"
        schema_path.write_text(json.dumps(schema))
        csv_path = workdir / "invoices.csv"
        csv_path.write_text("Currency\nUSD\n")

        pipeline = FinancialValidationPipeline(dataset_name="broken_rule")
        with pytest.raises(MetadataError):
            pipeline.run(csv_path=csv_path, schema_path=schema_path)


class TestReportSummary:
    def test_print_summary_does_not_raise(
        self, clean_csv: Path, schema_path: Path, vendor_master: pl.DataFrame, capsys
    ) -> None:
        pipeline = FinancialValidationPipeline(dataset_name="printable")
        report = pipeline.run(
            csv_path=clean_csv, schema_path=schema_path, reference_data={"Supplier": vendor_master}
        )
        report.print_summary()
        captured = capsys.readouterr()
        assert "ERPKit Financial Validation Report" in captured.out
