# Why ERPKit Uses the Apache License 2.0

This note documents the licensing decision for maintainers, contributors, and
adopting organizations evaluating ERPKit for enterprise use. It is a
supporting rationale document, not a substitute for the `LICENSE` file itself.

## Recommendation

**ERPKit is licensed under the Apache License, Version 2.0.**

## Why Apache 2.0 Over the Alternatives

ERPKit's primary audience is enterprise engineering teams integrating with
ERP systems and handling financial data. That audience, and the nature of
the problem domain, drove the license choice more than general open-source
convention.

### Compared to MIT (used by Pydantic, SQLAlchemy, Requests, Polars)

MIT is simpler and equally permissive with respect to use and modification,
but it does not include an explicit patent grant or patent-retaliation
clause. For a library that enterprises will embed directly into financial
and transactional systems, the absence of an explicit patent grant is a real
adoption friction point: many corporate legal and open-source-compliance
review processes specifically favor licenses with explicit patent terms for
dependencies used in production financial infrastructure, precisely to avoid
ambiguity about patent rights when multiple contributors are involved.
Apache 2.0 removes that ambiguity.

### Compared to BSD-3-Clause

Similar reasoning applies as with MIT: BSD-3-Clause is permissive but
silent on patents. It is a fine license for many projects, but it does not
give ERPKit the same clarity that Apache 2.0 provides for enterprise legal
review.

### Compared to GPL / AGPL

Copyleft licenses would materially reduce ERPKit's adoption inside
proprietary enterprise codebases, which is the primary deployment context
the project targets. Requiring downstream proprietary applications to
release their source, or requiring network-triggered source disclosure in
AGPL's case, is inconsistent with the goal of ERPKit being adopted as a
foundational library the way SQLAlchemy or Pydantic are.

### Compared to a source-available or "fair source" license (BSL, SSPL, etc.)

These licenses restrict commercial use in ways that would work against
ERPKit's explicit goal of becoming a shared, freely adoptable standard
library for the ERP integration problem space (see the ERPKit whitepaper,
Section 2). They are more common for products with a commercial hosted
offering to protect; ERPKit does not currently have one, and adopting a
restrictive license preemptively would work against community adoption.

## What Apache 2.0 Provides ERPKit Specifically

- **An explicit, perpetual, royalty-free patent grant** from every
  contributor to every user — directly relevant for a library that touches
  financial-transaction processing, where patent exposure is a genuine
  enterprise legal concern.
- **A patent-retaliation clause** (Section 3): a party that sues over patent
  infringement related to the Work loses its patent license under the
  project. This discourages patent-based attacks on the project and its
  users.
- **Permissive commercial and proprietary use**, consistent with the
  project's goal of broad enterprise adoption, including inside closed-source
  adapters and rule packs (see `CONTRIBUTING.md` and the plugin architecture
  described in the ERPKit whitepaper, Section 6.6).
- **Precedent among comparable enterprise-oriented open-source
  infrastructure projects** — Apache 2.0 is the license used by Apache
  Airflow, Kubernetes, and a substantial share of the Apache Software
  Foundation's data-infrastructure portfolio, which gives enterprise legal
  reviewers a familiar, well-understood license to evaluate rather than a
  novel one.

## Interoperability With ERPKit's Dependencies

ERPKit depends on and complements MIT-licensed projects (Polars, Pydantic,
SQLAlchemy, FastAPI) and BSD-licensed projects (PyArrow). Apache 2.0 is
compatible with both: it permits combining and redistributing MIT/BSD-licensed
code inside an Apache 2.0 project (and vice versa), so this choice creates no
license-compatibility friction with ERPKit's core dependency stack.
