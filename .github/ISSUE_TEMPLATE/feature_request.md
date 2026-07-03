---
name: "Feature Request"
about: "Propose new functionality or an enhancement to ERPKit"
title: "[Feature]: "
labels: ["enhancement", "triage"]
assignees: []
---

## Problem Statement

Describe the problem you're trying to solve — not the solution yet. What
are you unable to do with ERPKit today? What workaround, if any, are you
currently using?

> Example: "Validating a purchase order requires checking that the
> requested delivery date falls within the supplier's committed lead time,
> but there's no Business Rules primitive for a lookup that depends on a
> related record's field, so I have to write a custom validator for
> something that feels like it should be declarative."

## Proposed Solution

Describe the functionality you'd like to see. If you have a specific API
shape in mind, sketch it — this is not binding, but it helps ground the
discussion.

```python
# Optional: sketch the API you have in mind
```

## Which Module Does This Affect?

- [ ] Validator
- [ ] MetaFlow
- [ ] Business Rules
- [ ] Metadata Engine / Metadata Loader
- [ ] Transaction Manager
- [ ] Approval Engine
- [ ] Audit
- [ ] Reconciler
- [ ] Adapter protocol
- [ ] Configuration / Logging
- [ ] Documentation
- [ ] Other (describe above)

## Alternatives Considered

What other approaches did you consider (including existing extension
points, such as a custom validator or a custom matcher)? Why don't they
fully solve the problem?

## Is This a Core-Interface Change?

If this proposal would change `TransactionType`, the Validator/MetaFlow
rule interface, or the `Adapter` protocol, please also open a Design
Proposal discussion per the process in `CONTRIBUTING.md`, and link it here.

## Additional Context

Any related issues, discussions, prior art in other libraries, or
real-world scenarios that motivate this request.

---

*Before submitting, please confirm:*

- [ ] I searched existing issues and discussions and did not find a duplicate.
- [ ] I've described the underlying problem, not only the proposed solution.
