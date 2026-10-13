# Agent instructions

This repository owns the canonical review skills and the bridge-burning policy index.

The skills live under `src/automated_reviews/resources/skills/`.
The top-level `skills/` directory holds symlinks to them for `just install-skills`.

`skills/policy-index/references/policies.md` owns every `POLICY.*` record.
`skills/style-guide/references/style-guide-index.md` owns every `REMEDIATE.*` construction.
`src/automated_reviews/policy_index.py` parses both files and resolves each policy to its remediation.
`dzackgarza/ai-review-ci` imports that module for its deterministic detectors.
Other repositories link to the policy documents by their path on `main`, so a move or rename breaks those links.

Use the top-level `justfile` as the project interface.
