# Repository Badges

This snippet is the standard badge block for the top of `README.md`. It is
kept as a separate reference file so the badge set can be reviewed and
updated independently of README prose. Copy the Markdown block below
directly beneath the project title in `README.md`.

Replace `erpkit-project/erpkit` if the repository is hosted under a
different GitHub organization or name, and replace the `readthedocs`
slug/`codecov` token if your documentation or coverage hosting differs.

## Markdown Block

```markdown
[![PyPI version](https://img.shields.io/pypi/v/erpkit.svg?logo=pypi&logoColor=white)](https://pypi.org/project/erpkit/)
[![Python versions](https://img.shields.io/pypi/pyversions/erpkit.svg?logo=python&logoColor=white)](https://pypi.org/project/erpkit/)
[![PyPI downloads](https://img.shields.io/pypi/dm/erpkit.svg?logo=pypi&logoColor=white)](https://pypi.org/project/erpkit/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![CI](https://github.com/erpkit-project/erpkit/actions/workflows/ci.yml/badge.svg)](https://github.com/erpkit-project/erpkit/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/erpkit-project/erpkit/branch/main/graph/badge.svg)](https://codecov.io/gh/erpkit-project/erpkit)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)
[![Documentation](https://readthedocs.org/projects/erpkit/badge/?version=latest)](https://erpkit.readthedocs.io/en/latest/?badge=latest)
```

## Badge Reference Table

| Badge | Purpose | Source |
|---|---|---|
| PyPI version | Latest published version on PyPI | shields.io, reads PyPI metadata |
| Python versions | Supported Python versions (from package classifiers) | shields.io, reads PyPI metadata |
| PyPI downloads | Monthly download count | shields.io, reads PyPI download stats |
| License | Declares the Apache 2.0 license at a glance | Static badge, links to `LICENSE` |
| CI | Status of the most recent `ci.yml` run on `main` | GitHub Actions badge endpoint |
| Coverage | Test coverage percentage | Codecov (requires repository to be connected to Codecov) |
| Code style: black | Signals the formatting convention described in `CONTRIBUTING.md` | Static badge |
| Linting: Ruff | Signals the linting tool in use | Ruff's official badge endpoint |
| Type checked: mypy | Signals that the public API is type-checked | Static badge |
| Documentation | Build status of the latest documentation | Read the Docs badge endpoint |

## Notes

- The **Coverage** badge requires the repository to be connected to
  [Codecov](https://about.codecov.io/) (or an equivalent service) and the
  CI workflow to upload a coverage report — `ci.yml` already produces
  `coverage.xml` as a build artifact; wiring it to a coverage service is a
  one-time setup step outside this file's scope.
- The **Documentation** badge assumes a Read the Docs project named
  `erpkit`; update the slug if documentation is hosted elsewhere (e.g.,
  GitHub Pages via `mkdocs gh-deploy`).
- Badges intentionally avoid unverifiable claims (e.g., no "battle-tested"
  or "production-ready" badges) — each badge here links to a live,
  independently verifiable status.
