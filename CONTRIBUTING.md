# Contributing to ERPKit

Thank you for considering a contribution to ERPKit. This document describes
how to set up a development environment, the branching and pull-request
workflow, coding standards, testing expectations, documentation
conventions, commit message format, and how to report issues or propose
features.

ERPKit's core domain model (transaction types, the Validator/MetaFlow
interface, the Adapter protocol) is deliberately conservative about change,
since adapter packages and rule packs across the ecosystem depend on these
interfaces remaining stable. Please read [Design Review Process](#design-review-process)
before starting work on a core interface change.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Local Development Setup](#local-development-setup)
- [Branch Strategy](#branch-strategy)
- [Commit Message Conventions](#commit-message-conventions)
- [Pull Request Process](#pull-request-process)
- [Design Review Process](#design-review-process)
- [Coding Standards](#coding-standards)
- [Unit Testing](#unit-testing)
- [Documentation](#documentation)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)
- [Bug Reports](#bug-reports)

## Code of Conduct

This project and everyone participating in it is governed by the
[Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to
uphold it. Please report unacceptable behavior as described in that
document.

## Local Development Setup

ERPKit targets Python 3.10+. Development dependencies are managed with
`pip` and an editable install.

```bash
# 1. Fork the repository on GitHub, then clone your fork
git clone https://github.com/<your-username>/erpkit.git
cd erpkit

# 2. Add the upstream remote
git remote add upstream https://github.com/erpkit-project/erpkit.git

# 3. Create an isolated virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 4. Install ERPKit in editable mode with development dependencies
pip install -e ".[dev]"

# 5. Install pre-commit hooks (runs Ruff, Black, and MyPy on every commit)
pre-commit install

# 6. Verify your environment
pytest
ruff check .
black --check .
mypy src/
```

If any of these commands fail on a clean checkout, please open an issue —
that is itself a bug in our onboarding process.

### Keeping Your Fork Up to Date

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

## Branch Strategy

ERPKit uses a simple trunk-based workflow:

| Branch | Purpose |
|---|---|
| `main` | Always releasable. Protected; merges only via reviewed pull request. |
| `feature/<short-description>` | New functionality, branched from `main`. |
| `fix/<short-description>` | Bug fixes, branched from `main`. |
| `docs/<short-description>` | Documentation-only changes. |
| `release/vX.Y.Z` | Cut by maintainers when preparing a release; used for release-stabilization fixes only. |

Guidelines:

- Branch from an up-to-date `main`.
- Keep branches focused on a single logical change; large, unrelated changes
  bundled into one branch are harder to review and more likely to be
  rejected.
- Rebase onto `main` before opening a pull request if your branch has
  drifted significantly; avoid merge commits from `main` into your feature
  branch when a rebase is feasible.
- Delete your branch after it has been merged.

## Commit Message Conventions

ERPKit follows [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
This format is used to generate `CHANGELOG.md` entries and to determine
semantic version bumps.

```
<type>(<optional scope>): <short summary>

<optional longer body>

<optional footer(s)>
```

**Types:**

| Type | Use for |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Formatting changes that do not affect code meaning |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | A performance improvement |
| `test` | Adding or correcting tests |
| `build` | Changes to the build system or dependencies |
| `ci` | Changes to CI configuration |
| `chore` | Other changes that don't modify source or test files |

**Examples:**

```
feat(validator): support cross-field tolerance rules

fix(reconciler): correct date-window matcher off-by-one at window boundary

docs(contributing): clarify pre-commit hook installation step

feat(transaction-manager)!: rename `advance()` parameter `target` to `to_state`

BREAKING CHANGE: `TransactionManager.advance()` now requires `to_state`
instead of `target`. Update call sites accordingly.
```

A `!` after the type/scope, or a `BREAKING CHANGE:` footer, marks a breaking
change and triggers a major-version bump per Semantic Versioning.

## Pull Request Process

1. **Open an issue first for non-trivial changes.** For anything beyond a
   small fix or documentation correction, open an issue describing the
   problem or proposal before writing code. This avoids wasted effort on
   approaches that won't be accepted.
2. **Write tests.** New behavior needs new tests; bug fixes need a
   regression test that fails before the fix and passes after it.
3. **Keep the diff focused.** One logical change per pull request.
4. **Update documentation and `CHANGELOG.md`.** Add an entry under
   `[Unreleased]` following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
   conventions.
5. **Ensure CI is green.** Ruff, Black, MyPy, and pytest must all pass
   across supported Python versions before review will begin.
6. **Fill out the pull request template completely.** Incomplete templates
   will be sent back before review.
7. **Respond to review feedback.** At least one maintainer approval is
   required before merge; core-interface changes require two (see
   [Design Review Process](#design-review-process)).
8. **Squash-merge is the default merge strategy**, producing one commit per
   pull request on `main` with a Conventional Commit message.

## Design Review Process

Changes to ERPKit's core domain model — the `TransactionType` base class,
the Validator/MetaFlow rule interface, the `Adapter` protocol, or the
Transaction Manager's state-machine contract — require a written design
proposal before implementation begins, because adapter packages and rule
packs across the ecosystem depend on these interfaces remaining stable.

To propose a core design change:

1. Open a GitHub Discussion in the **Design Proposals** category.
2. Describe the problem, the proposed interface change, backward
   compatibility implications, and at least one alternative considered.
3. Allow at least five business days for maintainer and community feedback
   before opening an implementing pull request.
4. Reference the discussion from the pull request.

Changes scoped to a specific adapter package, a specific rule pack, or an
isolated bug fix do not require this process — open a pull request directly.

## Coding Standards

ERPKit's coding standards are enforced automatically via pre-commit hooks
and CI; the descriptions below explain the *why* behind each tool.

### Ruff — Linting

Ruff is used for linting (import sorting, unused variables, common bug
patterns, and style rules). Configuration lives in `pyproject.toml` under
`[tool.ruff]`.

```bash
ruff check .          # lint
ruff check . --fix    # auto-fix what can be auto-fixed
```

### Black — Formatting

Black is the canonical formatter; formatting is not up for debate in code
review. Configuration lives in `pyproject.toml` under `[tool.black]`
(line length 88, the Black default).

```bash
black .                # format in place
black --check .        # verify formatting without modifying files
```

### MyPy — Static Type Checking

All public APIs must be fully type-annotated. ERPKit's domain model relies
on type hints for both correctness and developer experience (see the
whitepaper, Section 10), so MyPy runs in strict mode against `src/erpkit`.

```bash
mypy src/
```

New code should introduce zero new MyPy errors. `# type: ignore` is
permitted only with an inline comment explaining why, and is reviewed
critically in pull requests.

### General Style Expectations

- Public functions, classes, and methods require docstrings (Google style).
- Prefer explicit, typed exceptions over silent failure (see the
  whitepaper, Section 10.5, on ERPKit's error-design philosophy).
- Avoid introducing new runtime dependencies without discussion — ERPKit's
  core dependency footprint is a deliberate design constraint (see
  `ACKNOWLEDGEMENTS.md` and the whitepaper, Section 12.5).
- Business rules and validation logic belong in metadata-driven definitions
  or the `erpkit.rules` primitive library, not hardcoded into pipeline or
  application code — this mirrors ERPKit's own architectural philosophy.

## Unit Testing

ERPKit uses `pytest`.

```bash
pytest                          # run the full suite
pytest tests/test_validator.py  # run a single test module
pytest -k "reconcile"           # run tests matching a keyword
pytest --cov=erpkit --cov-report=term-missing   # with coverage
```

Guidelines:

- Every new module or public function requires corresponding tests under
  `tests/`, mirroring the `src/erpkit/` package structure.
- Prefer small, focused unit tests over broad integration tests where the
  behavior under test can be isolated.
- Tests for metadata-driven rules should include at least one fixture rule
  set under `tests/fixtures/rules/` rather than constructing rule metadata
  inline, so fixtures can be reused across tests.
- Bug fixes must include a regression test reproducing the original issue.
- Target coverage for new code is 90% or higher; CI will report coverage
  deltas on the pull request.

## Documentation

- Public API changes require corresponding updates to the API reference
  documentation under `docs/`.
- New modules should include a short architecture note in `docs/architecture/`
  describing the module's responsibility and its relationship to other
  modules, consistent with the whitepaper's module descriptions.
- Code examples in documentation are tested via `pytest --doctest-glob`
  where feasible, so they do not silently drift out of date.
- Prefer clear, complete prose over terse fragments — documentation is
  reviewed with the same rigor as code.

## Reporting Issues

Please use the appropriate issue template:

- **Bug Report** — something is broken or behaves incorrectly.
- **Feature Request** — propose new functionality or an enhancement.
- **Question** — usage questions not clearly a bug or feature request
  (consider [GitHub Discussions](SUPPORT.md) for open-ended questions).

Search existing issues before opening a new one to avoid duplicates.

## Feature Requests

Feature requests should describe the problem being solved, not only the
proposed solution — this helps maintainers evaluate whether the proposal
fits ERPKit's scope (see the whitepaper, Section 12.2, on what ERPKit
deliberately does not try to be) or whether an existing extension point
(a custom validator, a custom matcher, a plugin adapter) already covers the
need. Use the **Feature Request** issue template.

## Bug Reports

A useful bug report includes:

- ERPKit version (`python -c "import erpkit; print(erpkit.__version__)"`)
- Python version and operating system
- A minimal, reproducible example
- The full traceback, if applicable
- Expected behavior versus actual behavior

Use the **Bug Report** issue template, which structures this information.

---

Thank you again for contributing. ERPKit exists because enough people were
tired of solving the same enterprise-integration problems in isolation —
your contribution helps make the shared solution better.
