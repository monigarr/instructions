# File Header Template

| Primary Source | [ClientRequirement.md](ClientRequirement.md) |
| Derived Spec | [PRD.md](PRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) |
| Client Deliverable | GitHub repository (code quality and organization) |

Use this header on production modules per [ARCHITECTURE.md](ARCHITECTURE.md) §15 and M.O.M. file standards. Test modules may use minimal headers.

## Python (LabelForge `app/`)

```python
"""
===============================================================================
FILE: example_module.py
AUTHOR: MoniGarr (Monica Peters)
CREATED: 2026-06-09
UPDATED: 2026-06-09
CLASSIFICATION: Internal

PURPOSE:
One-line description of module responsibility.

DEPENDENCIES:
  - domain.interfaces — abstractions this module implements or consumes

SECURITY:
  - No logging of full label/application text in production mode

PERFORMANCE:
  - Target budget and hot-path notes

OPERATIONAL:
  - Feature flags or rollback notes
===============================================================================
"""
```

## C# / general (Echelon template)

```
// =============================================================================
// FILE: FileName.cs
// NAMESPACE: FileName.Gameplay.Conjugation
// ASSEMBLY: FileName.Gameplay
// AUTHOR: MoniGarr (Monica Peters)
// CREATED:
// UPDATED:
// LICENSE:
// CLASSIFICATION: Internal | Public (select one)
//
// PURPOSE:
// Description here
//
// USAGE:
//   usage examples here
//
// DEPENDENCIES:
//   - dependency one
//
// SECURITY:
//   - security details here
//
// PERFORMANCE:
//   - performance details here
//
// OPERATIONAL:
//   - Feature flag: details here
//   - Rollback: details here
//
// =============================================================================
```

## Classification Guide

| Label | Use When |
|-------|----------|
| **Internal** | Prototype and interview codebase; not for public distribution |
| **Public** | Open-source modules intended for external reuse |

## Minimal Header

For small helpers or tests, a single-line module docstring with PURPOSE is acceptable. Production agents, rules, graph nodes, and API entrypoints should use the full block.
