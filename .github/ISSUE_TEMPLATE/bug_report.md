---
name: "Bug Report"
about: "Report something in ERPKit that is broken or behaves incorrectly"
title: "[Bug]: "
labels: ["bug", "triage"]
assignees: []
---

## Description

A clear, concise description of what the bug is.

## Minimal Reproducible Example

```python
# Paste a minimal, self-contained code sample that reproduces the issue.
# Include any rule/mapping metadata (YAML/JSON) needed to reproduce it.
import erpkit

...
```

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened. Include the full traceback if an exception was
raised:

```
Paste the full traceback here.
```

## Environment

| | |
|---|---|
| ERPKit version | `python -c "import erpkit; print(erpkit.__version__)"` |
| Python version | `python --version` |
| Operating system | e.g. Ubuntu 22.04, macOS 14, Windows 11 |
| Installation method | pip / source checkout / other |
| Relevant optional dependencies | e.g. `erpkit[polars]`, adapter packages in use |

## Additional Context

- Does this happen consistently, or only under certain conditions?
- Is this a regression? If so, which version last worked correctly?
- Any relevant rule-set or mapping metadata files (redact sensitive data)?
- Related issues or discussions, if any.

---

*Before submitting, please confirm:*

- [ ] I searched existing issues and discussions and did not find a duplicate.
- [ ] I can reproduce this with the latest released version of ERPKit.
- [ ] I have included a minimal reproducible example.
