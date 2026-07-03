# Changelog

All notable changes to ERPKit are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Nothing yet.

### Changed
- Nothing yet.

### Deprecated
- Nothing yet.

### Removed
- Nothing yet.

### Fixed
- Nothing yet.

### Security
- Nothing yet.

---

## [0.1.0] - 2026-07-03

Initial public release of ERPKit.

### Added
- `TransactionType` base class for declaring typed, metadata-aware business
  transaction models (invoices, journal entries, purchase orders, supplier
  records, and custom types).
- **Validator** module: structural and business-rule validation compiled
  from declarative rule definitions, producing a typed `ValidationResult`
  with a complete list of field-level errors rather than raising on first
  failure.
- **MetaFlow** engine: loads, compiles, and versions declarative YAML/JSON
  rule and mapping definitions into executable, typed rule objects.
- **Business Rules** primitive library: tolerance-based numeric comparison,
  currency-aware fixed-point arithmetic (`Money` value object), date-range
  and fiscal-period checks, and referential lookups against master data.
- **Metadata Loader**: loads and validates rule/mapping metadata from
  YAML and JSON sources.
- **Metadata Engine**: declarative, versioned field-mapping definitions for
  translating source-system schemas into ERPKit's canonical transaction
  model.
- **Audit** module: immutable, append-only, queryable audit trail for
  validation, approval, rejection, and override actions.
- **Reconciler**: configurable reconciliation engine with pluggable
  `Matcher` strategies (exact match, tolerance-based numeric match,
  date-window match), executed over Polars `LazyFrame`s, producing a
  structured match/exception report.
- **Approval Engine**: declarative approval policies (value thresholds,
  approver roles, segregation-of-duties constraints) with lifecycle state
  tracking.
- **Transaction Manager**: multi-step transaction state machine with
  validation and approval gates between transitions, and support for
  compensating actions on downstream failure.
- **Adapter** protocol: the extension interface platform-specific ERP
  adapters implement; no platform-specific adapters are bundled in this
  release (see `ROADMAP.md`, Phase 5).
- **Configuration** module: typed, validated configuration for
  environment- and deployment-specific settings.
- **Logging** module: structured, correlation-aware operational logging,
  kept intentionally distinct from the Audit trail.
- Initial documentation set: architecture whitepaper, API reference stubs,
  and worked examples for supplier onboarding, invoice processing, journal
  validation, and reconciliation workflows.
- Initial test suite covering the Validator, MetaFlow, Business Rules,
  Reconciler, Approval Engine, and Transaction Manager modules.
- Project governance and community infrastructure: `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1), `SECURITY.md`,
  `GOVERNANCE.md`, `SUPPORT.md`, `ROADMAP.md`.
- Continuous integration via GitHub Actions: linting (Ruff), formatting
  checks (Black), static type checking (MyPy), and test execution (pytest)
  across supported Python versions.

### Known Limitations
- No officially maintained ERP-platform adapters are included in this
  release; the Adapter protocol is stable, but SAP/Oracle/Dynamics/Odoo
  adapters are tracked separately (see `ROADMAP.md`, Phase 5).
- The Low-Code Metadata Designer, Workflow Engine, AI Assistant, and Cloud
  Connectors described in the project roadmap are not part of this
  release.

[Unreleased]: https://github.com/erpkit-project/erpkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/erpkit-project/erpkit/releases/tag/v0.1.0
