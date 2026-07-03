# ==============================================================================
# Script      : run_invoice_pipeline.py
# Purpose     : Runnable, end-to-end demonstration of FinancialValidationPipeline
#               — intended as a copy/paste starting point for integrators.
# Maintainer  : ERPKit Core Team
# ==============================================================================
"""Runnable end-to-end demo: validate the sample invoice extract against
the Supplier master data using ERPKit's FinancialValidationPipeline.

Usage:
    python examples/run_invoice_pipeline.py
"""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

from erpkit.pipeline.financial_pipeline import FinancialValidationPipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

_HERE = Path(__file__).resolve().parent
_DATA_DIR = _HERE / "data"
_SCHEMA_DIR = _HERE.parent / "src" / "erpkit" / "metadata" / "examples"


def main() -> None:
    vendor_master = pl.read_csv(_DATA_DIR / "vendor_master.csv")

    pipeline = FinancialValidationPipeline(dataset_name="invoice_extract_demo")
    report = pipeline.run(
        csv_path=_DATA_DIR / "invoice_extract.csv",
        schema_path=_SCHEMA_DIR / "invoice_schema.json",
        reference_data={"Supplier": vendor_master},
    )

    report.print_summary()

    output_path = _HERE / "invoice_extract_report.json"
    output_path.write_text(report.to_json())
    print(f"\nFull JSON report written to: {output_path}")


if __name__ == "__main__":
    main()
