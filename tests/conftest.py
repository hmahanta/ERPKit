"""Shared pytest fixtures for the ERPKit test suite.

Fixture design notes
---------------------
``clean_invoice_df`` is constructed so that *every* rule exercised
against it in ``test_validator.py`` passes — it deliberately satisfies
required/not-null, currency, duplicate-key, foreign-key, range, and
numeric rules simultaneously, since several tests reuse it across
different rule types.

``dirty_invoice_df`` is constructed so each rule fails for a distinct,
attributable reason:

* Row 0 & 1 share the same (Vendor, Invoice) key -> ``duplicate`` failure.
* Row 2 has a null Vendor -> ``required``/``foreign_key`` failure, an
  out-of-allowed-set Currency ("XXX") -> ``currency`` failure, and a
  negative Amount -> ``range``/``custom`` failure.
* Row 3 references a Vendor ("V-9999") absent from ``vendor_master_df``
  -> ``foreign_key`` failure.

Both fixtures include a ``Journal`` column so ``.balance(...)`` can be
chained onto either without raising ``SchemaError`` for a missing column.
"""

from __future__ import annotations

import polars as pl
import pytest


@pytest.fixture
def clean_invoice_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "Vendor": ["V-1001", "V-1002", "V-1003"],
            "Invoice": ["INV-1", "INV-2", "INV-3"],
            "Currency": ["USD", "EUR", "USD"],
            "Amount": [1000.0, 2500.5, 750.25],
            "Journal": ["J1", "J1", "J2"],
        }
    )


@pytest.fixture
def dirty_invoice_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "Vendor": ["V-1001", "V-1001", None, "V-9999"],
            "Invoice": ["INV-1", "INV-1", "INV-2", "INV-3"],
            "Currency": ["USD", "USD", "XXX", "EUR"],
            "Amount": [500.0, 500.0, -50.0, 200.0],
            "Journal": ["J1", "J1", "J2", "J2"],
        }
    )


@pytest.fixture
def vendor_master_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "SupplierID": ["V-1001", "V-1002", "V-1003", "V-1004", "V-1005"],
            "SupplierName": [
                "Acme Industrial Supply",
                "Nordwind Logistics GmbH",
                "Pacific Rim Components",
                "BlueSky Office Solutions",
                "Meridian Steel Corp",
            ],
        }
    )


@pytest.fixture
def journal_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "Journal": ["JRN-1", "JRN-1", "JRN-2", "JRN-2"],
            "Amount": [100.0, -100.0, 100.0, -50.0],
        }
    )
