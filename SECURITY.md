# Security Policy

ERPKit is used to validate, reconcile, and process financial and
operational transaction data. Security issues in this project can have
outsized downstream impact, and we take reports seriously. Thank you for
helping keep ERPKit and its users safe.

## Supported Versions

ERPKit follows Semantic Versioning. Security fixes are backported according
to the table below. Versions not listed do not receive security updates —
please upgrade before reporting an issue against an unsupported version.

| Version | Supported |
|---------|-----------|
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x: (pre-release, not supported) |

Once ERPKit reaches 1.0, this table will be updated to reflect a standard
policy of supporting the latest major version with security patches, and
the previous major version for twelve months following a new major release.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub
issues, discussions, or pull requests.**

Instead, report vulnerabilities using one of the following private channels:

1. **Preferred: GitHub Security Advisories.** Use the
   ["Report a vulnerability"](https://github.com/erpkit-project/erpkit/security/advisories/new)
   button under the repository's Security tab. This creates a private
   advisory visible only to maintainers until a fix is ready.
2. **Email:** **security@erpkit-project.org**. If the report contains
   sensitive details, you may request our PGP key in advance by emailing
   the same address.

Please include as much of the following as you can:

- A description of the vulnerability and its potential impact
- Steps to reproduce, or a minimal proof-of-concept
- The affected version(s) of ERPKit
- Any known mitigations or workarounds
- Whether the vulnerability has been disclosed elsewhere

### What to Expect

| Stage | Target Timeline |
|---|---|
| Acknowledgement of your report | Within 3 business days |
| Initial assessment and severity triage | Within 7 business days |
| Status updates while a fix is developed | At least every 14 days |
| Coordinated disclosure and patch release | Target within 90 days of report, sooner for critical severity |

We use [CVSS v3.1](https://www.first.org/cvss/v3-1/) to assess severity and
will share our assessment with you as part of triage.

## Responsible Disclosure

We ask that you:

- Give us a reasonable opportunity to investigate and address a
  vulnerability before any public disclosure.
- Make a good-faith effort to avoid privacy violations, data destruction,
  and service disruption to any systems while investigating.
- Only interact with test accounts, test data, or your own deployments when
  demonstrating a proof-of-concept — never with production data or systems
  belonging to others.
- Give us the details necessary to reproduce and fix the issue.

In return, we commit to:

- Respond promptly and keep you informed of progress.
- Credit you (unless you prefer to remain anonymous) in the security
  advisory and `CHANGELOG.md` entry for the fix.
- Not pursue legal action against researchers who report vulnerabilities in
  good faith and in accordance with this policy.

Once a fix is released, we will publish a GitHub Security Advisory with an
assigned CVE (where applicable), a description of the issue, affected
versions, and upgrade guidance.

## Security Expectations for Deployments

ERPKit is a library, not a hosted service, and its security posture depends
partly on how it is deployed. Adopting organizations should be aware of the
following:

- **Rule and mapping metadata is executable configuration.** MetaFlow
  compiles YAML/JSON rule definitions into executable rule objects (see the
  ERPKit whitepaper, Section 7.2). Treat rule-set sources with the same
  access-control discipline as application code — do not load rule
  definitions from untrusted or unauthenticated sources.
- **Custom validator registration executes arbitrary code you register.**
  The escape hatch described in the whitepaper (Section 12.1) that allows a
  metadata rule to invoke a registered custom validator function will
  execute whatever function is registered; only register functions from
  trusted sources.
- **Audit records are compliance-sensitive data.** The Audit module
  (Section 8.3 of the whitepaper) is designed to produce an immutable,
  queryable record of financial-transaction decisions. Secure the audit
  storage backend with the same rigor as the underlying transactional data.
- **Adapters may hold ERP credentials.** Platform-specific Adapter packages
  (Section 8.8) are the boundary at which ERPKit typically handles
  connection credentials for source ERP systems. Follow your organization's
  secrets-management practices for any adapter configuration.
- **Keep dependencies current.** ERPKit's dependency versions are pinned
  with security patching in mind; run `pip list --outdated` or your
  organization's dependency-scanning tooling regularly against your
  deployment.

## Security Tooling in CI

Every pull request runs automated dependency and static-analysis scanning
as part of continuous integration (see `.github/workflows/ci.yml`),
including `pip-audit` for known-vulnerable dependencies and Ruff's
security-oriented lint rules (`S` rule set, based on `bandit`). Findings
that affect released versions are handled through the private reporting
channels above, not through public CI logs.

## Questions

For questions about this policy that are not themselves a vulnerability
report, please use [GitHub Discussions](SUPPORT.md) rather than the
security email address.
