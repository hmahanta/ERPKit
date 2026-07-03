"""Unit tests for erpkit.core.result (ValidationResult, ValidationIssue, Severity)."""

from __future__ import annotations

from erpkit.core.result import Severity, ValidationIssue, ValidationResult


def _issue(
    rule: str = "required",
    column: str | None = "Vendor",
    severity: Severity = Severity.ERROR,
    failing_row_count: int = 1,
) -> ValidationIssue:
    return ValidationIssue(
        rule=rule,
        column=column,
        severity=severity,
        message=f"'{column}' failed rule '{rule}'.",
        failing_row_count=failing_row_count,
        row_indices=[0],
        details={},
    )


class TestSeverity:
    def test_is_string_valued(self) -> None:
        assert Severity.ERROR == "error"
        assert Severity.WARNING == "warning"
        assert Severity.INFO == "info"

    def test_constructible_from_raw_string(self) -> None:
        assert Severity("error") is Severity.ERROR
        assert Severity("warning") is Severity.WARNING


class TestValidationIssue:
    def test_to_dict_structure(self) -> None:
        issue = _issue()
        payload = issue.to_dict()
        assert payload["rule"] == "required"
        assert payload["column"] == "Vendor"
        assert payload["severity"] == "error"
        assert payload["failing_row_count"] == 1
        assert payload["row_indices"] == [0]

    def test_details_default_to_empty_dict(self) -> None:
        issue = ValidationIssue(
            rule="required",
            column="Vendor",
            severity=Severity.ERROR,
            message="msg",
            failing_row_count=1,
        )
        assert issue.details == {}
        assert issue.row_indices == []


class TestValidationResultBuild:
    def test_no_issues_is_valid(self) -> None:
        result = ValidationResult.build(
            issues=[], row_count=10, execution_time=0.01, rule_timings={}
        )
        assert result.is_valid is True
        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.errors == []
        assert result.warnings == []

    def test_error_issue_makes_result_invalid(self) -> None:
        result = ValidationResult.build(
            issues=[_issue(severity=Severity.ERROR)],
            row_count=5,
            execution_time=0.01,
            rule_timings={"required": 0.001},
        )
        assert result.is_valid is False
        assert result.error_count == 1
        assert result.warning_count == 0

    def test_warning_only_issue_keeps_result_valid(self) -> None:
        result = ValidationResult.build(
            issues=[_issue(severity=Severity.WARNING)],
            row_count=5,
            execution_time=0.01,
            rule_timings={"required": 0.001},
        )
        assert result.is_valid is True
        assert result.error_count == 0
        assert result.warning_count == 1

    def test_mixed_severities_partition_correctly(self) -> None:
        issues = [
            _issue(rule="required", severity=Severity.ERROR),
            _issue(rule="date_range", severity=Severity.WARNING),
            _issue(rule="currency", severity=Severity.ERROR),
        ]
        result = ValidationResult.build(
            issues=issues, row_count=5, execution_time=0.02, rule_timings={}
        )
        assert result.error_count == 2
        assert result.warning_count == 1
        assert {i.rule for i in result.errors} == {"required", "currency"}
        assert {i.rule for i in result.warnings} == {"date_range"}

    def test_statistics_contains_rule_timings(self) -> None:
        timings = {"required": 0.001, "currency": 0.002}
        result = ValidationResult.build(
            issues=[], row_count=5, execution_time=0.05, rule_timings=timings
        )
        assert result.statistics["rule_timings_seconds"] == timings
        assert result.statistics["rules_executed"] == 2

    def test_summary_is_a_nonempty_string(self) -> None:
        result = ValidationResult.build(
            issues=[_issue()], row_count=3, execution_time=0.01, rule_timings={"required": 0.001}
        )
        assert isinstance(result.summary, str)
        assert "3" in result.summary

    def test_row_count_and_execution_time_passthrough(self) -> None:
        result = ValidationResult.build(
            issues=[], row_count=42, execution_time=1.234, rule_timings={}
        )
        assert result.row_count == 42
        assert result.execution_time == 1.234

    def test_to_dict_round_trips_key_fields(self) -> None:
        result = ValidationResult.build(
            issues=[_issue(severity=Severity.ERROR)],
            row_count=3,
            execution_time=0.01,
            rule_timings={"required": 0.001},
        )
        payload = result.to_dict()
        assert payload["is_valid"] is False
        assert payload["error_count"] == 1
        assert payload["row_count"] == 3
        assert len(payload["errors"]) == 1
        assert payload["errors"][0]["rule"] == "required"
