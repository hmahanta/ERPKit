# ERPKit Governance

This document describes how the ERPKit project is governed: maintainer
roles and responsibilities, how decisions are made, how releases are
managed, and how the broader community participates. It applies to the
core `erpkit` repository; officially recognized adapter and rule-pack
repositories under the `erpkit-project` organization follow the same
governance unless explicitly noted otherwise in their own repositories.

## Project Model

ERPKit follows a **maintainer-led, meritocratic open-source governance
model**, similar in spirit to projects such as SQLAlchemy and Requests:
a small group of maintainers hold merge and release authority, contributor
status is earned through sustained, high-quality contribution, and
significant design decisions are made in the open with community input
rather than unilaterally.

## Roles

### Users

Anyone using ERPKit. Users are encouraged to participate in Discussions,
report issues, and propose improvements. No formal status is required.

### Contributors

Anyone who has had a pull request merged into an `erpkit-project`
repository, or who has made a substantive non-code contribution
(documentation, triage, design review). Contributors are recognized in
`AUTHORS.md`.

### Reviewers

Contributors who have demonstrated sustained, high-quality contribution
and sound judgment in code review, and have been granted review rights by
the maintainers. Reviewers can approve pull requests within their area of
familiarity but rely on a Maintainer for merge on core-interface changes
(see `CONTRIBUTING.md`, Design Review Process).

Reviewer status is proposed by an existing Maintainer or Reviewer and
confirmed by maintainer consensus.

### Maintainers

Maintainers have merge and release authority across the repository, and
collective responsibility for the project's technical direction,
`ROADMAP.md`, and adherence to `CODE_OF_CONDUCT.md`. Maintainers are
listed in `AUTHORS.md`.

Maintainer status is proposed by an existing Maintainer, requires
consensus among current Maintainers (see Decision Making below), and is
based on sustained contribution, demonstrated judgment on design questions,
and alignment with the project's architectural philosophy as described in
the ERPKit whitepaper.

Maintainers who become inactive for an extended period (roughly six months,
used as a guideline rather than an automatic trigger) may be moved to
Emeritus status by consensus of the remaining active Maintainers, with
notice given first. Emeritus maintainers are still recognized in
`AUTHORS.md` and may resume active status by request.

### Founder

The project's original author and initial maintainer, credited in
`AUTHORS.md`. The Founder role carries no special decision-making authority
beyond that of a Maintainer once the project has more than one active
Maintainer — it is a historical/attribution designation, not a permanent
governance tier, consistent with ERPKit's intent to be a community-governed
project rather than one person's tool.

## Decision Making

ERPKit uses **lazy consensus** for most decisions: a proposal is considered
accepted if no Maintainer objects within a reasonable review window
(typically 5 business days for routine changes; see `CONTRIBUTING.md` for
the longer window on core design proposals).

For decisions where consensus cannot be reached through discussion:

1. Any Maintainer may call for an explicit vote among Maintainers.
2. Each Maintainer has one vote.
3. A simple majority of active Maintainers decides the question.
4. In the event of a tie, the decision defaults to **not** making the
   change — preserving the status quo requires less consensus than
   changing it, particularly for core-interface decisions given the
   ecosystem stability concerns described in `CONTRIBUTING.md`.

This process is intentionally reserved for genuine disagreements; the large
majority of day-to-day decisions (routine pull request approval, bug
triage, documentation changes) do not require it.

## Release Management

- ERPKit follows [Semantic Versioning](https://semver.org/).
- Any Maintainer may propose a release by opening a release-preparation
  pull request updating `CHANGELOG.md` per [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
  conventions.
- A release requires sign-off from at least one Maintainer other than the
  one proposing it.
- Patch releases (bug fixes, no interface changes) may be released as
  needed. Minor releases (backward-compatible features) are released on a
  rolling basis as accumulated changes warrant. Major releases (breaking
  changes) require the Design Review Process in `CONTRIBUTING.md` for the
  changes they contain and are announced in advance via GitHub Discussions.
- Published releases are tagged in Git, published to PyPI via the
  `publish.yml` GitHub Actions workflow, and accompanied by GitHub Release
  notes generated from `CHANGELOG.md`.

## Adapter and Rule-Pack Repositories

Officially recognized adapter packages (`erpkit-adapter-*`) and rule packs
maintained under the `erpkit-project` GitHub organization follow this same
governance model, with their own Maintainer sets drawn from contributors
with relevant platform expertise, subject to confirmation by the core
ERPKit Maintainers. Community-maintained adapters and rule packs hosted
outside the `erpkit-project` organization are not governed by this
document and are the responsibility of their own maintainers.

## Amending This Document

Changes to this governance document follow the Decision Making process
above and require Maintainer consensus, given their effect on how the
project is run.
