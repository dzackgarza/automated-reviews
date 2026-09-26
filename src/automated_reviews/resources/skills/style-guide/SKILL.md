---
name: style-guide
description: "Use before implementing or refactoring code in a governed pattern family. Routes by language to the preferred construction."
---

# Implementation Style Guide

Start by selecting the implementation language, then load only the relevant foundation card from the [[style-guide/references/style-guide-index|style-guide index]].

- [[style-guide/style-guide-python/style-guide-python|Python]]

- [[style-guide/style-guide-typescript/style-guide-typescript|TypeScript and Bun]]

- [[style-guide/style-guide-bash/style-guide-bash|Bash]]

- [[style-guide/style-guide-sage/style-guide-sage|SageMath stub]]

Each card is canonical for both paths:

- Before implementation: use its preferred construction and language profile.

- After a `POLICY.*` finding: use its bad-pattern analysis, language-specific rearchitecture, and proof obligation.

Do not maintain a separate remediation interpretation.
[[policy-index/SKILL|policy-index]] maps findings into these cards; [[fixing-slop/SKILL|fixing-slop]] governs the repair process around them.
