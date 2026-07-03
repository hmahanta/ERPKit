# Support

This document explains where to get help with ERPKit, and which channel to
use for which kind of request.

## Quick Guide

| I want to... | Use |
|---|---|
| Ask a usage question | [GitHub Discussions → Q&A](https://github.com/erpkit-project/erpkit/discussions/categories/q-a) |
| Report a bug | [GitHub Issues → Bug Report](https://github.com/erpkit-project/erpkit/issues/new?template=bug_report.md) |
| Request a feature | [GitHub Issues → Feature Request](https://github.com/erpkit-project/erpkit/issues/new?template=feature_request.md) |
| Propose a core design change | [GitHub Discussions → Design Proposals](https://github.com/erpkit-project/erpkit/discussions/categories/design-proposals) |
| Report a security vulnerability | See [`SECURITY.md`](SECURITY.md) — do **not** use public issues |
| Read the docs | [ERPKit Documentation](https://erpkit.readthedocs.io) |
| Share something you built with ERPKit | [GitHub Discussions → Show and Tell](https://github.com/erpkit-project/erpkit/discussions/categories/show-and-tell) |

## GitHub Discussions

[GitHub Discussions](https://github.com/erpkit-project/erpkit/discussions) is
the primary community hub for anything that isn't a confirmed bug or a
concrete, scoped feature request:

- **Q&A** — "How do I express a cross-field rule that depends on fiscal
  period?", "What's the recommended pattern for X?"
- **Design Proposals** — proposed changes to core interfaces, following the
  [Design Review Process](CONTRIBUTING.md#design-review-process) in
  `CONTRIBUTING.md`.
- **Roadmap** — discussion of `ROADMAP.md` priorities and sequencing.
- **Show and Tell** — share adapters, rule packs, or integrations you've
  built on top of ERPKit.
- **General** — anything else community-related.

Discussions are searchable and browsable by everyone, so a good question
asked once often saves the next person from asking it again.

## Issues

[GitHub Issues](https://github.com/erpkit-project/erpkit/issues) is reserved
for actionable engineering work:

- **Bugs** — something in ERPKit does not behave as documented.
- **Feature requests** — a specific, scoped enhancement proposal.

Please do not use Issues for open-ended usage questions — they get lost
among actionable engineering items and are harder for maintainers to
triage. Use Discussions instead, and a maintainer will convert a discussion
into an issue if it turns out to be a confirmed bug or an accepted feature.

## Questions

Before asking, please:

1. Check the [documentation](https://erpkit.readthedocs.io), including the
   architecture whitepaper and worked examples.
2. Search existing [Discussions](https://github.com/erpkit-project/erpkit/discussions)
   and [Issues](https://github.com/erpkit-project/erpkit/issues) for the
   same question.
3. If nothing matches, open a new Q&A discussion with:
   - What you are trying to accomplish
   - What you have tried
   - A minimal, reproducible code example if applicable
   - Your ERPKit and Python version

## Community

ERPKit's community lives primarily on GitHub. There is no separate chat
server at this time; consolidating discussion on GitHub keeps it searchable
and keeps the project's history in one place. If that changes, this
document will be updated with the relevant links.

## Documentation

- **Architecture Whitepaper** — design philosophy, module responsibilities,
  and architectural rationale.
- **API Reference** — generated from docstrings, published at
  [erpkit.readthedocs.io](https://erpkit.readthedocs.io).
- **Worked Examples** — supplier onboarding, invoice processing, journal
  validation, reconciliation, and migration workflows, under `docs/examples/`.
- **`CONTRIBUTING.md`** — development setup and contribution workflow.

If documentation is unclear or missing something you needed, please open a
documentation issue — documentation gaps are treated as bugs.

## Commercial and Enterprise Support

ERPKit does not currently offer a paid support or services tier. If your
organization needs commercial support (SLA-backed response times,
implementation assistance, or custom adapter development), please open a
discussion describing your needs — this helps the maintainers gauge
demand and is one of the inputs into the Phase 10 roadmap item in
`ROADMAP.md`.
