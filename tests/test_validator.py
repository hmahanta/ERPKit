"""Unit tests for erpkit.core.validator.Validator.

Covers every rule builder (required, not_null, currency, duplicate,
balance, foreign_key, date, numeric, regex, range, custom), the shared
execution path (.validate()), and error handling for misconfiguration.
"""

from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from erpkit.core.exceptions import (
    RuleConfigurationError,
    SchemaError,
    ValidationExecutionError,
)
from erpkit.core.result import Severity
from erpkit.core.validator import Validator


# ----------------------------------------------------------------------
# Construction
# ----------------------------------------------------------------------


class TestConstruction:
    def test_rejects_non_dataframe_input(self) -> None:
        with pytest.raises(RuleConfigurationError):
            Validator({"not": "a dataframe"})  # type: ignore[arg-type]

    def test_accepts_polars_dataframe(self, clean_invoice_df: pl.DataFrame) -> None:
        validator = Validator(clean_invoice_df)
        assert validator._df.height == 3

    def test_empty_chain_returns_valid_result(self, clean_invoice_df: pl.DataFrame) -> None:
        result = Validator(clean_invoice_df).validate()
        assert result.is_valid is True
        assert result.row_count == 3


# ----------------------------------------------------------------------
# required
# ----------------------------------------------------------------------


class TestRequired:
    def test_passes_when_all_populated(self, clean_invoice_df: pl.DataFrame) -> None:
        result = Validator(clean_invoice_df).required(["Vendor", "Invoice"]).validate()
        assert result.is_valid is True

    def test_fails_on_null(self, dirty_invoice_df: pl.DataFrame) -> None:
        result = Validator(dirty_invoice_df).required(["Vendor"]).validate()
        assert result.is_valid is False
        assert result.errors[0].rule == "required"
        assert result.errors[0].failing_row_count == 1

    def test_fails_on_empty_string(self) -> None:
        df = pl.DataFrame({"Vendor": ["V-1", "", "  ", "V-4"]})
        result = Validator(df).required(["Vendor"]).validate()
        assert result.error_count == 2

    def test_missing_column_raises_schema_error(self, clean_invoice_df: pl.DataFrame) -> None:
        with pytest.raises(SchemaError):
            Validator(clean_invoice_df).required(["NoSuchColumn"])

    def test_empty_columns_raises_configuration_error(self, clean_invoice_df: pl.DataFrame) -> None:
        with pytest.raises(RuleConfigurationError):
            Validator(clean_invoice_df).required([])

    def test_severity_warning_does_not_fail_validity(self) -> None:
        df = pl.DataFrame({"Notes": [None, "ok"]})
        result = Validator(df).required(["Notes"], severity=Severity.WARNING).validate()
        assert result.is_valid is True
        assert result.warning_count == 1

    def test_required_on_non_string_column_checks_nulls_only(self) -> None:
        df = pl.DataFrame({"Amount": [1.0, None, 3.0]})
        result = Validator(df).required(["Amount"]).validate()
        assert result.error_count == 1


# ----------------------------------------------------------------------
# not_null
# ----------------------------------------------------------------------


class TestNotNull:
    def test_allows_empty_string_but_not_null(self) -> None:
        df = pl.DataFrame({"Code": ["", "A", None]})
        result = Validator(df).not_null(["Code"]).validate()
        assert result.error_count == 1

    def test_empty_columns_raises(self, clean_invoice_df: pl.DataFrame) -> None:
        with pytest.raises(RuleConfigurationError):
            Validator(clean_invoice_df).not_null([])


# ----------------------------------------------------------------------
# currency
# ----------------------------------------------------------------------


class TestCurrency:
    def test_passes_for_allowed_codes(self, clean_invoice_df: pl.DataFrame) -> None:
        result = Validator(clean_invoice_df).currency("Currency", ["USD", "EUR"]).validate()
        assert result.is_valid is True

    def test_fails_for_disallowed_code(self, dirty_invoice_df: pl.DataFrame) -> None:
        result = Validator(dirty_invoice_df).currency("Currency", ["USD", "EUR"]).validate()
        assert result.error_count == 1

    def test_case_insensitive_option(self) -> None:
        df = pl.DataFrame({"Currency": ["usd", "EUR", "gbp"]})
        result = (
            Validator(df)
            .currency("Currency", ["USD", "EUR", "GBP"], case_sensitive=False)
            .validate()
        )
        assert result.is_valid is True

    def test_case_sensitive_by_default_fails_lowercase(self) -> None:
        df = pl.DataFrame({"Currency": ["usd"]})
        result = Validator(df).currency("Currency", ["USD"]).validate()
        assert result.is_valid is False

    def test_empty_allowed_list_raises(self, clean_invoice_df: pl.DataFrame) -> None:
        with pytest.raises(RuleConfigurationError):
            Validator(clean_invoice_df).currency("Currency", [])

    def test_missing_column_raises_schema_error(self, clean_invoice_df: pl.DataFrame) -> None:
        with pytest.raises(SchemaError):
            Validator(clean_invoice_df).currency("NoSuchColumn", ["USD"])


# ----------------------------------------------------------------------
# duplicate
# ----------------------------------------------------------------------


class TestDuplicate:
    def test_passes_when_unique(self, clean_invoice_df: pl.DataFrame) -> None:
        result = Validator(clean_invoice_df).duplicate(["Vendor", "Invoice"]).validate()
        assert result.is_valid is True

    def test_fails_on_duplicate_composite_key(self, dirty_invoice_df: pl.DataFrame) -> None:
        result = Validator(dirty_invoice_df).duplicate(["Vendor", "Invoice"]).validate()
        assert result.is_valid is False
        # both the original and the duplicate row are flagged
        assert result.errors[0].failing_row_count == 2

    def test_single_column_duplicate(self) -> None:
        df = pl.DataFrame({"InvoiceID": ["A", "A", "B"]})
        result = Validator(df).duplicate(["InvoiceID"]).validate()
        assert result.error_count == 2

    def test_empty_columns_raises_configuration_error(self, clean_invoice_df: pl.DataFrame) -> None:
        with pytest.raises(RuleConfigurationError):
            Validator(clean_invoice_df).duplicate([])


# ----------------------------------------------------------------------
# balance
# ----------------------------------------------------------------------


class TestBalance:
    def test_balanced_journal_passes(self, journal_df: pl.DataFrame) -> None:
        balanced_only = journal_df.filter(pl.col("Journal") == "JRN-1")
        result = Validator(balanced_only).balance(["Journal"], "Amount").validate()
        assert result.is_valid is True

    def test_unbalanced_journal_fails(self, journal_df: pl.DataFrame) -> None:
        result = Validator(journal_df).balance(["Journal"], "Amount").validate()
        assert result.is_valid is False
        assert result.errors[0].rule == "balance"
        assert result.errors[0].failing_row_count == 1  # only JRN-2 is out of balance

    def test_within_tolerance_passes(self) -> None:
        df = pl.DataFrame({"Journal": ["J1", "J1"], "Amount": [100.001, -100.0]})
        result = Validator(df).balance(["Journal"], "Amount", tolerance=0.01).validate()
        assert result.is_valid is True

    def test_empty_group_by_raises(self, journal_df: pl.DataFrame) -> None:
        with pytest.raises(RuleConfigurationError):
            Validator(journal_df).balance([], "Amount")


# ----------------------------------------------------------------------
# foreign_key
# ----------------------------------------------------------------------


class TestForeignKey:
    def test_passes_when_all_keys_resolve(
        self, clean_invoice_df: pl.DataFrame, vendor_master_df: pl.DataFrame
    ) -> None:
        result = (
            Validator(clean_invoice_df)
            .foreign_key("Vendor", vendor_master_df["SupplierID"])
            .validate()
        )
        assert result.is_valid is True

    def test_fails_on_unresolvable_key(
        self, dirty_invoice_df: pl.DataFrame, vendor_master_df: pl.DataFrame
    ) -> None:
        result = (
            Validator(dirty_invoice_df)
            .foreign_key("Vendor", vendor_master_df["SupplierID"])
            .validate()
        )
        assert result.is_valid is False

    def test_allow_null_permits_null_values(self, vendor_master_df: pl.DataFrame) -> None:
        df = pl.DataFrame({"Vendor": ["V-1001", None]})
        result = (
            Validator(df)
            .foreign_key("Vendor", vendor_master_df["SupplierID"], allow_null=True)
            .validate()
        )
        assert result.is_valid is True

    def test_disallow_null_by_default(self, vendor_master_df: pl.DataFrame) -> None:
        df = pl.DataFrame({"Vendor": ["V-1001", None]})
        result = Validator(df).foreign_key("Vendor", vendor_master_df["SupplierID"]).validate()
        assert result.is_valid is False

    def test_accepts_plain_list_as_reference(self) -> None:
        df = pl.DataFrame({"Code": ["A", "B", "Z"]})
        result = Validator(df).foreign_key("Code", ["A", "B", "C"]).validate()
        assert result.error_count == 1


# ----------------------------------------------------------------------
# date
# ----------------------------------------------------------------------


class TestDate:
    def test_valid_string_dates_pass(self) -> None:
        df = pl.DataFrame({"InvoiceDate": ["2026-01-01", "2026-02-15"]})
        result = Validator(df).date("InvoiceDate", fmt="%Y-%m-%d").validate()
        assert result.is_valid is True

    def test_unparseable_date_fails(self) -> None:
        df = pl.DataFrame({"InvoiceDate": ["2026-01-01", "not-a-date"]})
        result = Validator(df).date("InvoiceDate", fmt="%Y-%m-%d").validate()
        assert result.error_count == 1

    def test_min_max_bounds_enforced(self) -> None:
        df = pl.DataFrame({"InvoiceDate": ["2019-01-01", "2026-01-01"]})
        result = (
            Validator(df)
            .date(
                "InvoiceDate",
                fmt="%Y-%m-%d",
                min_date=date(2020, 1, 1),
                max_date=date(2030, 1, 1),
            )
            .validate()
        )
        assert result.error_count == 1

    def test_native_date_dtype_supported(self) -> None:
        df = pl.DataFrame({"InvoiceDate": [date(2026, 1, 1), date(2026, 2, 1)]})
        result = Validator(df).date("InvoiceDate").validate()
        assert result.is_valid is True


# ----------------------------------------------------------------------
# numeric
# ----------------------------------------------------------------------


class TestNumeric:
    def test_numeric_dtype_passes(self, clean_invoice_df: pl.DataFrame) -> None:
        result = Validator(clean_invoice_df).numeric("Amount").validate()
        assert result.is_valid is True

    def test_string_castable_to_float_passes(self) -> None:
        df = pl.DataFrame({"Amount": ["100.5", "200.25"]})
        result = Validator(df).numeric("Amount").validate()
        assert result.is_valid is True

    def test_non_numeric_string_fails(self) -> None:
        df = pl.DataFrame({"Amount": ["100.5", "abc"]})
        result = Validator(df).numeric("Amount").validate()
        assert result.error_count == 1

    def test_null_fails_by_default(self) -> None:
        df = pl.DataFrame({"Amount": [1.0, None]})
        result = Validator(df).numeric("Amount").validate()
        assert result.error_count == 1

    def test_allow_null_true_permits_nulls(self) -> None:
        df = pl.DataFrame({"Amount": [1.0, None]})
        result = Validator(df).numeric("Amount", allow_null=True).validate()
        assert result.is_valid is True


# ----------------------------------------------------------------------
# regex
# ----------------------------------------------------------------------


class TestRegex:
    def test_matching_values_pass(self) -> None:
        df = pl.DataFrame({"Code": ["AB12", "CD34"]})
        result = Validator(df).regex("Code", r"[A-Z]{2}\d{2}").validate()
        assert result.is_valid is True

    def test_non_matching_values_fail(self) -> None:
        df = pl.DataFrame({"Code": ["AB12", "bad!"]})
        result = Validator(df).regex("Code", r"[A-Z]{2}\d{2}").validate()
        assert result.error_count == 1

    def test_pattern_is_fully_anchored(self) -> None:
        # Without anchoring, "AB1234" would partially match [A-Z]{2}\d{2}
        df = pl.DataFrame({"Code": ["AB1234"]})
        result = Validator(df).regex("Code", r"[A-Z]{2}\d{2}").validate()
        assert result.is_valid is False

    def test_invalid_pattern_raises_configuration_error(self, clean_invoice_df: pl.DataFrame) -> None:
        with pytest.raises(RuleConfigurationError):
            Validator(clean_invoice_df).regex("Currency", "[unterminated")

    def test_null_values_fail_regex(self) -> None:
        df = pl.DataFrame({"Code": ["AB12", None]})
        result = Validator(df).regex("Code", r"[A-Z]{2}\d{2}").validate()
        assert result.error_count == 1


# ----------------------------------------------------------------------
# range
# ----------------------------------------------------------------------


class TestRange:
    def test_within_bounds_passes(self, clean_invoice_df: pl.DataFrame) -> None:
        result = Validator(clean_invoice_df).range("Amount", minimum=0, maximum=10000).validate()
        assert result.is_valid is True

    def test_below_minimum_fails(self, dirty_invoice_df: pl.DataFrame) -> None:
        result = Validator(dirty_invoice_df).range("Amount", minimum=0).validate()
        assert result.error_count == 1

    def test_above_maximum_fails(self) -> None:
        df = pl.DataFrame({"Amount": [5.0, 1_000_000.0]})
        result = Validator(df).range("Amount", minimum=0, maximum=100).validate()
        assert result.error_count == 1

    def test_no_bounds_raises_configuration_error(self, clean_invoice_df: pl.DataFrame) -> None:
        with pytest.raises(RuleConfigurationError):
            Validator(clean_invoice_df).range("Amount")

    def test_minimum_greater_than_maximum_raises(self, clean_invoice_df: pl.DataFrame) -> None:
        with pytest.raises(RuleConfigurationError):
            Validator(clean_invoice_df).range("Amount", minimum=100, maximum=10)

    def test_exclusive_bounds(self) -> None:
        df = pl.DataFrame({"Amount": [100.0]})
        result = (
            Validator(df).range("Amount", minimum=100, maximum=200, inclusive=False).validate()
        )
        assert result.error_count == 1


# ----------------------------------------------------------------------
# custom
# ----------------------------------------------------------------------


class TestCustom:
    def test_custom_rule_passes(self, clean_invoice_df: pl.DataFrame) -> None:
        result = (
            Validator(clean_invoice_df)
            .custom(lambda df: df["Amount"] < 0, name="no_negative_amounts")
            .validate()
        )
        assert result.is_valid is True

    def test_custom_rule_fails(self, dirty_invoice_df: pl.DataFrame) -> None:
        result = (
            Validator(dirty_invoice_df)
            .custom(lambda df: df["Amount"] < 0, name="no_negative_amounts")
            .validate()
        )
        assert result.error_count == 1
        assert result.errors[0].rule == "no_negative_amounts"

    def test_custom_rule_wrong_return_type_raises(self, clean_invoice_df: pl.DataFrame) -> None:
        with pytest.raises(ValidationExecutionError):
            Validator(clean_invoice_df).custom(
                lambda df: [True, False, True], name="bad_rule"
            ).validate()

    def test_custom_rule_wrong_length_raises(self, clean_invoice_df: pl.DataFrame) -> None:
        with pytest.raises(ValidationExecutionError):
            Validator(clean_invoice_df).custom(
                lambda df: pl.Series([True, False]), name="wrong_length"
            ).validate()

    def test_custom_rule_exception_wrapped(self, clean_invoice_df: pl.DataFrame) -> None:
        def _boom(df: pl.DataFrame) -> pl.Series:
            raise ValueError("kaboom")

        with pytest.raises(ValidationExecutionError):
            Validator(clean_invoice_df).custom(_boom, name="boom_rule").validate()

    def test_empty_name_raises_configuration_error(self, clean_invoice_df: pl.DataFrame) -> None:
        with pytest.raises(RuleConfigurationError):
            Validator(clean_invoice_df).custom(lambda df: df["Amount"] < 0, name="")


# ----------------------------------------------------------------------
# Chaining / execution semantics
# ----------------------------------------------------------------------


class TestChainingAndExecution:
    def test_full_chain_matches_readme_example(self, dirty_invoice_df: pl.DataFrame) -> None:
        result = (
            Validator(dirty_invoice_df)
            .required(["Vendor", "Invoice"])
            .currency("Currency", ["USD", "EUR"])
            .duplicate(["Vendor", "Invoice"])
            .balance(group_by=["Journal"], amount_column="Amount")
            .validate()
        )
        assert result.is_valid is False
        rule_names = {issue.rule for issue in result.errors}
        assert "required" in rule_names
        assert "currency" in rule_names
        assert "duplicate" in rule_names

    def test_result_has_execution_metadata(self, clean_invoice_df: pl.DataFrame) -> None:
        result = Validator(clean_invoice_df).required(["Vendor"]).validate()
        assert result.execution_time >= 0
        assert result.row_count == 3
        assert "required" in result.statistics["rule_timings_seconds"]

    def test_rules_execute_in_declared_order(self, clean_invoice_df: pl.DataFrame) -> None:
        order: list[str] = []

        def _track(name: str):
            def _fn(df: pl.DataFrame) -> pl.Series:
                order.append(name)
                return pl.Series([False] * df.height)

            return _fn

        Validator(clean_invoice_df).custom(_track("first"), name="first").custom(
            _track("second"), name="second"
        ).validate()
        assert order == ["first", "second"]

    def test_each_rule_returns_self_for_chaining(self, clean_invoice_df: pl.DataFrame) -> None:
        validator = Validator(clean_invoice_df)
        assert validator.required(["Vendor"]) is validator

    def test_unexpected_rule_exception_is_normalized(self, clean_invoice_df: pl.DataFrame) -> None:
        validator = Validator(clean_invoice_df)
        # Inject a rule whose closure raises a plain (non-ERPKit) exception,
        # simulating an unforeseen engine-level failure.
        validator._add_rule(
            "broken_rule",
            None,
            Severity.ERROR,
            lambda: (_ for _ in ()).throw(RuntimeError("engine exploded")),
        )
        with pytest.raises(ValidationExecutionError):
            validator.validate()

    def test_duplicate_rule_names_get_disambiguated_timing_keys(
        self, clean_invoice_df: pl.DataFrame
    ) -> None:
        result = (
            Validator(clean_invoice_df)
            .required(["Vendor"])
            .required(["Invoice"])
            .validate()
        )
        timing_keys = result.statistics["rule_timings_seconds"].keys()
        assert "required" in timing_keys
        assert any(k.startswith("required#") for k in timing_keys)
