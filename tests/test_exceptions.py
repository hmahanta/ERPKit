"""Unit tests for erpkit.core.exceptions."""

from __future__ import annotations

import pytest

from erpkit.core.exceptions import (
    ERPKitError,
    MetadataError,
    PipelineError,
    RuleConfigurationError,
    SchemaError,
    ValidationExecutionError,
)


class TestERPKitErrorBase:
    def test_stores_message(self) -> None:
        exc = ERPKitError("something went wrong")
        assert exc.message == "something went wrong"
        assert str(exc) == "something went wrong"

    def test_defaults_to_empty_context(self) -> None:
        exc = ERPKitError("boom")
        assert exc.context == {}

    def test_stores_context(self) -> None:
        exc = ERPKitError("boom", context={"column": "Vendor"})
        assert exc.context == {"column": "Vendor"}

    def test_str_includes_context(self) -> None:
        exc = ERPKitError("boom", context={"column": "Vendor"})
        assert "boom" in str(exc)
        assert "column" in str(exc)
        assert "Vendor" in str(exc)

    def test_context_is_copied_not_aliased(self) -> None:
        original = {"column": "Vendor"}
        exc = ERPKitError("boom", context=original)
        original["column"] = "mutated"
        assert exc.context == {"column": "Vendor"}

    def test_is_a_real_exception(self) -> None:
        with pytest.raises(ERPKitError):
            raise ERPKitError("boom")

    def test_to_dict_structure(self) -> None:
        exc = ERPKitError("boom", context={"column": "Vendor"})
        payload = exc.to_dict()
        assert payload == {
            "error_type": "ERPKitError",
            "message": "boom",
            "context": {"column": "Vendor"},
        }

    def test_to_dict_uses_subclass_name(self) -> None:
        exc = SchemaError("missing column")
        assert exc.to_dict()["error_type"] == "SchemaError"


class TestExceptionHierarchy:
    @pytest.mark.parametrize(
        "exc_type",
        [
            RuleConfigurationError,
            SchemaError,
            ValidationExecutionError,
            MetadataError,
            PipelineError,
        ],
    )
    def test_all_subclasses_derive_from_erpkit_error(self, exc_type: type) -> None:
        assert issubclass(exc_type, ERPKitError)

    @pytest.mark.parametrize(
        "exc_type",
        [
            RuleConfigurationError,
            SchemaError,
            ValidationExecutionError,
            MetadataError,
            PipelineError,
        ],
    )
    def test_all_subclasses_are_catchable_as_base(self, exc_type: type) -> None:
        with pytest.raises(ERPKitError):
            raise exc_type("boom")

    def test_subclasses_are_distinct_types(self) -> None:
        assert RuleConfigurationError is not SchemaError
        assert not issubclass(RuleConfigurationError, SchemaError)

    def test_chained_exception_preserves_cause(self) -> None:
        try:
            try:
                raise ValueError("root cause")
            except ValueError as exc:
                raise ValidationExecutionError("wrapped") from exc
        except ValidationExecutionError as wrapped:
            assert isinstance(wrapped.__cause__, ValueError)
            assert str(wrapped.__cause__) == "root cause"
