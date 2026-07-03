## Summary

<!-- What does this PR do, and why? Link the issue or discussion this
     addresses, if any (e.g. "Closes #123" or "Relates to discussion #45"). -->

## Type of Change

- [ ] `feat` — new feature
- [ ] `fix` — bug fix
- [ ] `docs` — documentation only
- [ ] `refactor` — code change that neither fixes a bug nor adds a feature
- [ ] `perf` — performance improvement
- [ ] `test` — adding or correcting tests
- [ ] `build` / `ci` — build system or CI configuration
- [ ] `chore` — other maintenance

## Does This Change a Core Interface?

- [ ] No — this is scoped to a specific module, adapter, or bug fix.
- [ ] Yes — this changes `TransactionType`, the Validator/MetaFlow rule
      interface, the `Adapter` protocol, or the Transaction Manager
      state-machine contract.

If yes, link the required Design Proposal discussion (see
`CONTRIBUTING.md` → Design Review Process): <!-- link here -->

## Changes

<!-- Bullet list of the concrete changes made. -->

-
-

## Testing

<!-- How was this tested? What test cases were added or updated? -->

- [ ] New and existing unit tests pass locally (`pytest`)
- [ ] Added tests covering the new behavior or reproducing the fixed bug
- [ ] Manually verified against a representative example, where applicable

## Checklist

- [ ] I have read `CONTRIBUTING.md`.
- [ ] My commit messages follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
- [ ] `ruff check .` passes with no new warnings.
- [ ] `black --check .` passes.
- [ ] `mypy src/` passes with no new errors.
- [ ] I have added or updated docstrings for any new or changed public API.
- [ ] I have updated `docs/` if this change affects documented behavior.
- [ ] I have added an entry to `CHANGELOG.md` under `[Unreleased]`.
- [ ] I have added myself to `AUTHORS.md` if this is my first contribution.
- [ ] This PR contains a single, focused logical change.

## Breaking Changes

- [ ] This PR introduces a breaking change.

<!-- If checked, describe the breaking change, the migration path for
     existing users, and confirm the commit message includes a
     `BREAKING CHANGE:` footer or `!` marker per CONTRIBUTING.md. -->

## Additional Notes

<!-- Anything else reviewers should know: alternatives considered,
     follow-up work intentionally left out of scope, etc. -->
