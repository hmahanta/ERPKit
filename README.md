# ERPKit

**A metadata-driven data integration framework for enterprise ERP ecosystems.**

[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue)](#)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](#)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](#)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](#)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000)](#)
[![Type Checked](https://img.shields.io/badge/mypy-checked-blue)](#)

ERPKit is a Python framework for building reliable, auditable, metadata-driven data pipelines between flat files, APIs, and enterprise ERP systems — Oracle ERP, SAP, PeopleSoft, Microsoft Dynamics, Workday, Coupa, Odoo, ERPNext, and custom-built systems alike.

Instead of writing bespoke integration code for every source format and every target system, you describe *what* your data looks like and *what rules it must satisfy* in metadata (YAML or JSON). ERPKit's engine handles the *how*: parsing, validation, transformation, transaction management, auditing, and loading.

> **Status:** ERPKit is under active development. Interfaces may change prior to a 1.0 release. See the [Roadmap](#roadmap) for current maturity by module.

---

## Table of Contents

- [Why ERPKit](#why-erpkit)
- [Philosophy](#philosophy)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Supported Platforms](#supported-platforms)
- [Performance](#performance)
- [Example](#example)
- [Comparison to Other Tools](#comparison-to-other-tools)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Community](#community)

---

## Why ERPKit

Enterprise ERP integration work tends to fall into a predictable pattern: a supplier sends a CSV, a bank sends a fixed-width file, a legacy system exports pipe-delimited text — and each one needs to be parsed, validated against business rules, transformed into a target schema, loaded into staging or production tables, and audited end-to-end for compliance.

Most teams solve this by writing one-off scripts per feed. The scripts accumulate, business rules get duplicated across them, and nobody can answer "which fields are validated, and how?" without reading code.

ERPKit exists to make that answerable by reading a metadata file instead.

It does not replace your ETL orchestrator, your dataframe library, or your ORM. It sits at the layer above raw parsing and below orchestration: **the layer that turns "here is a file and here are the rules" into a validated, audited, loaded dataset**, with the same guarantees every time regardless of source format or target system.

## Philosophy

1. **Metadata over code.** The shape of your data and the rules it must satisfy are configuration, not logic. Changing a validation rule should mean editing a YAML file, not shipping a code change.
2. **Auditability is not optional.** Every record that fails validation, every transformation applied, and every row loaded should be traceable after the fact — not just logged, but queryable.
3. **ERP-neutral by design.** A supplier import looks structurally the same whether the target is Oracle, SAP, or PeopleSoft. ERPKit models the integration pattern once and lets adapters handle system-specific details.
4. **Fail loud, fail early, fail per-record.** A malformed row should not silently corrupt a load or abort an entire batch. ERPKit isolates failures to the record level wherever possible and reports them precisely.
5. **Extensibility through plugins, not forks.** Readers, validators, transformers, and loaders are pluggable adapters behind stable interfaces, so custom logic never requires touching the core engine.

## Features

- **Multi-format ingestion** — CSV, TXT, fixed-width, pipe- and tab-delimited files, with a common internal record representation.
- **Metadata-driven schema definition** — Describe field positions, types, constraints, and transformations declaratively in YAML or JSON.
- **Composable validation pipeline** — Chain field-level, record-level, and cross-record validators; write custom validators against a simple interface.
- **Transformation engine** — Declarative field mapping, type coercion, lookups, and derived fields, with room for custom transform plugins.
- **Transaction-safe loading** — Batched, transactional loads to relational targets (Oracle first-class; extensible to other RDBMS via adapters), with rollback semantics on failure.
- **Built-in audit trail** — Every processing run, validation failure, and load outcome is captured for compliance and troubleshooting.
- **Plugin registry** — Reader, validator, transformer, and loader adapters are registered and resolved by name, so extending ERPKit to a new format or target doesn't require modifying the core.
- **Clean, layered architecture** — A hexagonal (ports-and-adapters) design keeps business rules independent of file formats, database drivers, and I/O concerns, so the same core logic works whether you're reading a CSV or a fixed-width mainframe extract.
- **Approval workflow hooks** — Optional integration points for human-in-the-loop review of records that fail soft validation thresholds.

## Installation

```bash
pip install erpkit
```

For Oracle target support:

```bash
pip install "erpkit[oracle]"
```

Requires Python 3.11 or later.

## Quick Start

**1. Describe your data in metadata (`suppliers.yaml`):**

```yaml
source:
  format: csv
  delimiter: ","
  has_header: true

fields:
  - name: supplier_id
    type: string
    required: true
    max_length: 10
  - name: supplier_name
    type: string
    required: true
    max_length: 100
  - name: tax_id
    type: string
    validators:
      - type: regex
        pattern: "^[A-Z0-9]{9,12}$"
  - name: payment_terms_days
    type: integer
    default: 30

target:
  table: STAGING.SUPPLIERS
  mode: upsert
  key_fields: [supplier_id]
```

**2. Run the pipeline:**

```python
from erpkit import Pipeline

pipeline = Pipeline.from_metadata("suppliers.yaml")
result = pipeline.run(source_path="incoming/suppliers_20260703.csv")

print(f"Processed: {result.total_records}")
print(f"Loaded:    {result.loaded_records}")
print(f"Rejected:  {result.rejected_records}")

for failure in result.validation_failures:
    print(failure.record_number, failure.field, failure.reason)
```

That's the whole integration: no bespoke parser, no hand-written validation code, and a full audit trail generated automatically.

## Architecture

ERPKit follows a **hexagonal (ports-and-adapters) architecture**. The core domain — metadata interpretation, validation orchestration, transformation logic — has no knowledge of *which* file format it's reading or *which* database it's writing to. Those concerns live in adapters behind well-defined ports:

```
                         ┌─────────────────────────┐
                         │      Metadata Layer      │
                         │   (YAML / JSON schemas)  │
                         └────────────┬─────────────┘
                                      │
 ┌───────────┐     ┌──────────────┐  │  ┌──────────────┐     ┌────────────┐
 │  Readers  │────▶│              │◀─┴─▶│              │────▶│  Loaders   │
 │  (CSV,    │     │  Core Domain │     │  Validation  │     │ (Oracle,   │
 │  fixed-   │────▶│    Engine    │────▶│  & Transform │────▶│  extensible│
 │  width,…) │     │              │     │   Pipeline   │     │  targets)  │
 └───────────┘     └──────┬───────┘     └──────────────┘     └────────────┘
                          │
                   ┌──────▼───────┐
                   │  Audit Sink  │
                   └──────────────┘
```

- **Ports** define the contracts (`Reader`, `Validator`, `Transformer`, `Loader`, `AuditSink`).
- **Adapters** implement those contracts for specific technologies (a `FixedWidthReader`, an `OracleLoader`, a `RegexValidator`).
- **The Plugin Registry** resolves adapters by name at runtime from metadata, so adding support for a new format or target is a matter of registering a new adapter class — not modifying the engine.

This separation is what makes ERPKit ERP-neutral: the validation and transformation pipeline is identical whether the eventual target is Oracle, SAP, or a custom system; only the loader adapter changes.

## Supported Platforms

| Category | Support |
|---|---|
| Python | 3.11+ |
| Source formats | CSV, TXT, fixed-width, pipe-delimited, tab-delimited |
| First-class database target | Oracle |
| Extensible targets | Any RDBMS reachable via a custom `Loader` adapter (SAP, PeopleSoft, Dynamics, Workday, Coupa, Odoo, ERPNext staging tables, etc.) |
| Metadata formats | YAML, JSON |

ERPKit does not ship pre-built connectors for every ERP vendor's API surface. It ships the integration *pipeline*, and a stable adapter interface for connecting to whichever target your organization uses.

## Performance

ERPKit is designed around these performance principles:

- **Streaming record processing** — files are processed record-by-record rather than loaded wholesale into memory, so large files don't require large RAM footprints.
- **Batched transactional loads** — records are grouped into configurable batch sizes for database loads, balancing transaction overhead against rollback granularity.
- **Metadata compiled once per run** — schema and validation rules are parsed and compiled at pipeline start, not re-evaluated per record.
- **Validation short-circuiting** — record-level validation stops at the first hard failure for that record by default, avoiding wasted work on already-rejected data.

We have not yet published formal benchmarks. A benchmark suite comparing throughput across file sizes, formats, and target databases is on the [Roadmap](#roadmap); we'd rather publish real, reproducible numbers than estimates.

## Example

A slightly larger look at validation and transformation together:

```yaml
fields:
  - name: invoice_amount
    type: decimal
    required: true
    validators:
      - type: range
        min: 0.01
        max: 10000000

  - name: currency_code
    type: string
    validators:
      - type: enum
        values: [USD, EUR, GBP, INR, JPY]

  - name: invoice_date
    type: date
    format: "%Y-%m-%d"
    transformers:
      - type: derive_field
        target: fiscal_period
        function: fiscal_period_from_date
```

Custom validators and transformers implement a small interface and register themselves with the plugin registry:

```python
from erpkit.plugins import validator

@validator("fiscal_period_from_date")
def fiscal_period_from_date(value, context):
    # context gives access to org-specific fiscal calendar config
    return context.fiscal_calendar.period_for(value)
```

## Comparison to Other Tools

ERPKit is not a replacement for the general-purpose data tools you already use — it's a layer that sits alongside them for a specific job: turning heterogeneous ERP-bound files into validated, audited, loaded records via declarative metadata.

| Tool | What it's for | Where ERPKit differs |
|---|---|---|
| **Pandas / Polars** | General-purpose dataframe manipulation and analysis | ERPKit is not a dataframe library; it's a pipeline framework. You can use Polars *inside* a custom ERPKit transformer if you want vectorized operations on a batch. |
| **Pydantic** | Data validation and settings management via Python models | ERPKit's validation is metadata-driven (YAML/JSON) rather than code-defined models, and is oriented around per-record pass/fail auditing across a batch, not a single object's validity. |
| **SQLAlchemy** | ORM and SQL toolkit | ERPKit's `Loader` adapters can use SQLAlchemy under the hood for the actual database interaction; ERPKit adds the metadata-driven mapping and transaction orchestration on top. |
| **Great Expectations** | Data quality assertions, typically over already-loaded datasets | Conceptually adjacent — both validate data against declarative rules — but ERPKit validates inline during ingestion/load, not as a separate post-hoc quality check step. |
| **dbt** | SQL-based transformation of data already in a warehouse | ERPKit operates *before* data reaches that stage: parsing and loading raw files into staging tables. The two compose well — ERPKit lands clean data, dbt transforms it further downstream. |
| **Apache Airflow / Prefect** | Workflow orchestration and scheduling | ERPKit is not an orchestrator. An Airflow or Prefect task can invoke an ERPKit `Pipeline.run()` as one step in a larger DAG. |

## Roadmap

- [x] Core metadata schema (v1) and pipeline engine
- [x] CSV, fixed-width, and delimited file readers
- [x] Oracle loader adapter with transactional batching
- [x] Plugin registry for readers/validators/transformers/loaders
- [x] Audit sink for run-level and record-level events
- [ ] Formal benchmark suite (published with real numbers, not estimates)
- [ ] Reference adapters for additional RDBMS targets
- [ ] Approval-engine reference implementation (human-in-the-loop review UI)
- [ ] MetaFlow visual pipeline builder
- [ ] 1.0 API stability guarantee

## Contributing

Contributions are welcome — from bug reports to new adapters. See `CONTRIBUTING.md` for setup instructions, coding standards, and the pull request process. Please read `CODE_OF_CONDUCT.md` before participating.

If you're building a custom `Reader`, `Validator`, `Transformer`, or `Loader` for a format or system not yet supported, consider contributing it back as a reference adapter.

## License

ERPKit is released under the Apache 2.0 License. See `LICENSE` for details.

## Community

- **Issues & feature requests:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Security reports:** see `SECURITY.md` for responsible disclosure instructions

---

*ERPKit is an independent open-source project and is not affiliated with, endorsed by, or sponsored by Oracle, SAP, Workday, Microsoft, Coupa, Odoo, or any ERP vendor named in this document. Vendor names are used solely to describe interoperability.*
