# Acknowledgements

ERPKit exists because of the foundation laid by the broader Python open-source
ecosystem. This document recognizes the projects that inspired ERPKit's
design and the projects it directly depends on or is designed to complement.

None of the projects mentioned below are affiliated with, endorse, or are
endorsed by ERPKit. They are acknowledged here because ERPKit's architecture
is genuinely built to interoperate with them, as described in the ERPKit
architecture whitepaper, Section 4 ("Why Existing Libraries Are Not
Enough") and Section 6 ("Core Design Principles").

## Direct Dependencies and Execution Layer

- **[Polars](https://www.pola.rs/)** — ERPKit's bulk validation and
  reconciliation paths use Polars as their execution engine. The choice of
  Polars, and the reasoning behind it, is described in the whitepaper,
  Section 11.1.
- **[PyArrow](https://arrow.apache.org/docs/python/)** — Apache Arrow's
  columnar memory format underlies Polars and informs ERPKit's approach to
  efficient, typed data interchange with external systems.

## Design Inspiration

- **[Pydantic](https://docs.pydantic.dev/)** — ERPKit's `TransactionType`
  declaration style and its emphasis on type-driven validation draws
  direct inspiration from Pydantic's developer experience. Where structural
  validation alone is sufficient, ERPKit models are designed to compose
  cleanly with Pydantic rather than duplicate it (whitepaper, Section 4).
- **[SQLAlchemy](https://www.sqlalchemy.org/)** — SQLAlchemy's long-standing
  discipline around separating domain modeling from persistence concerns,
  and its approach to being a foundational library rather than a framework
  that owns the application, directly shaped ERPKit's own architectural
  philosophy (whitepaper, Section 12.2).
- **[FastAPI](https://fastapi.tiangolo.com/)** — FastAPI's approach to
  combining strong typing with excellent developer ergonomics, and its
  success as a library that composes into existing systems rather than
  replacing them, is a model ERPKit aims to follow within its own domain.
- **[Great Expectations](https://greatexpectations.io/)** and
  **[dbt](https://www.getdbt.com/)** — both demonstrated the value of
  declarative, reviewable data-quality and transformation definitions,
  which informed ERPKit's own metadata-driven rule design (whitepaper,
  Section 6.1), even though they operate in the adjacent data-quality and
  warehouse-transformation layers rather than the business-transaction
  layer ERPKit targets.
- **[Apache Airflow](https://airflow.apache.org/)** and
  **[Prefect](https://www.prefect.io/)** — both shaped ERPKit's deliberate
  decision not to own workflow orchestration, and instead to be designed as
  a natural task implementation inside either (whitepaper, Sections 4 and
  12.2).

## Broader Ecosystem

ERPKit's testing, linting, formatting, and type-checking tooling relies on
the following open-source projects, each acknowledged for the standard they
set for Python developer tooling: **pytest**, **Ruff**, **Black**, **MyPy**,
and **pre-commit**.

## A Note on Attribution

If you maintain or contribute to a project listed here and have questions
or concerns about how it is referenced in this document, please open an
issue — we want these acknowledgements to be accurate and to reflect
genuine technical relationships, not implied endorsement.
