# ERPKit Roadmap

This roadmap describes the planned evolution of ERPKit, from the current
core library through the longer-term vision described in the ERPKit
architecture whitepaper (Section 13). Phases are sequential in the sense
that later phases build on the interfaces established earlier, but are not
strictly time-boxed — scope and timing depend on maintainer and contributor
bandwidth, and this document will be revised as priorities are validated
against real adopter feedback.

Status legend: :white_check_mark: Shipped &nbsp;·&nbsp; :construction: In
Progress &nbsp;·&nbsp; :calendar: Planned &nbsp;·&nbsp; :bulb: Proposed

## Phase 1 — Core Validator
**Status: :white_check_mark: Shipped in v0.1.0**

The foundation layer: structural and business-rule validation for
individual transaction objects.

- `TransactionType` base class and typed field declarations
- Business Rules primitive library (tolerance comparison, currency-aware
  `Money` arithmetic, date/fiscal-period checks, referential lookups)
- `Validator` engine producing complete, typed `ValidationResult` objects
- Custom validator registration escape hatch for rules metadata cannot
  express declaratively

## Phase 2 — Metadata Engine
**Status: :white_check_mark: Shipped in v0.1.0**

Declarative, versioned rule and schema-mapping definitions, and the
Polars-backed execution layer for bulk operations.

- MetaFlow rule compiler (YAML/JSON → typed, callable rule objects)
- Metadata Loader for rule and mapping source files
- Metadata Engine for source-schema-to-canonical-model field mapping
- Bulk validation and reconciliation execution over Polars `LazyFrame`s,
  including streaming execution for large datasets
- Reconciler with pluggable Matcher strategies (exact, tolerance-based,
  date-window)

## Phase 3 — Transaction Manager
**Status: :white_check_mark: Shipped in v0.1.0**

Multi-step business-process state management.

- Transaction state machine with named states and explicit transitions
- Validation gates enforced between transitions
- Compensating-action support for downstream failure handling
- Audit module: immutable, append-only, queryable action trail

## Phase 4 — Approval Engine
**Status: :white_check_mark: Shipped in v0.1.0**

Declarative approval policy evaluation, integrated with the Transaction
Manager.

- Value-threshold, approver-role, and segregation-of-duties policy rules
- Approval-state tracking across a transaction's lifecycle
- Integration with Transaction Manager transitions as required gates

## Phase 5 — ERP Adapters
**Status: :construction: In Progress**

Officially maintained, separately distributed adapter packages implementing
the `Adapter` protocol for widely used ERP platforms, keeping the core
dependency footprint small (see the whitepaper, Section 12.5).

- [ ] Finalize and stabilize the `Adapter` protocol (v1)
- [ ] `erpkit-adapter-sap` — SAP ECC / S/4HANA
- [ ] `erpkit-adapter-oracle` — Oracle E-Business Suite / Fusion Cloud
- [ ] `erpkit-adapter-dynamics` — Microsoft Dynamics 365
- [ ] `erpkit-adapter-odoo` — Odoo
- [ ] `erpkit-adapter-netsuite` — Oracle NetSuite
- [ ] Adapter development guide and reference implementation template

## Phase 6 — AI Assistant
**Status: :calendar: Planned**

Building on ERPKit's structured, inspectable metadata (validation rules,
mapping definitions, audit records) to add AI-assisted tooling, consistent
with the "AI Readiness" design principle in the whitepaper (Section 6.10).
ERPKit's core will continue to function fully without this module.

- [ ] Natural-language explanation of validation failures for non-technical
      reviewers
- [ ] Assisted first-draft rule-set generation from sample datasets
- [ ] Anomaly surfacing in reconciliation exception reports

## Phase 7 — Workflow Engine
**Status: :calendar: Planned**

An optional, higher-level orchestration layer purpose-built for
business-transaction workflows, for teams that do not already run Airflow
or Prefect — while remaining usable as a task implementation inside either
(see the whitepaper, Section 12.2, on ERPKit's deliberate non-ownership of
general orchestration).

- [ ] Declarative pipeline definitions composing Validator, Reconciler, and
      Transaction Manager steps
- [ ] Native Airflow operator package
- [ ] Native Prefect task/flow integration package

## Phase 8 — Cloud Connectors
**Status: :calendar: Planned**

Adapters and configuration presets simplifying data-migration and
cloud-modernization use cases (whitepaper, Section 9.5–9.6).

- [ ] Cloud object storage connectors (S3-compatible, Azure Blob, GCS) for
      migration source/target staging
- [ ] Cloud data-warehouse connectors for reconciliation source data
- [ ] Managed-identity / secrets-manager integration patterns for adapter
      credentials

## Phase 9 — Low-Code Metadata Designer
**Status: :bulb: Proposed**

A visual authoring tool for rule and mapping metadata, aimed at business
analysts and controllers who need to review or propose rule changes without
writing YAML directly (whitepaper, Section 13).

- [ ] Visual rule-set editor with validation-preview against sample data
- [ ] Change-review workflow integrated with the Design Review Process
      described in `CONTRIBUTING.md`
- [ ] Export/import compatibility with hand-authored MetaFlow YAML

## Phase 10 — Enterprise Platform
**Status: :bulb: Proposed**

A longer-horizon direction: packaging the core library, adapters, workflow
engine, and low-code designer into a cohesive, deployable platform offering
for organizations that want a managed or self-hosted operational surface
around ERPKit, while keeping the underlying library independently usable
and open source. Scope, packaging, and governance implications for this
phase are intentionally undecided and will be shaped by community and
adopter input rather than fixed in advance.

- [ ] Community and adopter input on scope (tracked via GitHub Discussions)
- [ ] Evaluation of deployment/packaging models
- [ ] Governance review to ensure the core library's open-source terms and
      independence are preserved regardless of platform packaging decisions

---

## How This Roadmap Is Maintained

This roadmap is reviewed by the maintainers on a rolling basis and updated
as phases progress or priorities shift based on adopter and contributor
feedback (see `GOVERNANCE.md`). Proposals to reorder, add, or remove roadmap
items are welcome via GitHub Discussions in the **Roadmap** category.
