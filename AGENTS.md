# Agent instructions

This repository owns faithful capture and replay of automated review runs.
It does not own production review prompts, policy definitions, report schemas,
or remediation rules. Those remain in `dzackgarza/ai-review-ci`.

Preserve the model-visible boundary. A replay must use the frozen target source,
reviewer context, prompt inputs, tool permissions, paths, and validator behavior.
Keep adjudication files outside the reviewer filesystem.

Do not add evaluation wording to model-visible files or prompts. The reviewer
must see the same CI role and repository state that production supplies.

Use one case manifest as the source of replay identity. Store bespoke
configuration in TOML. Validate it with the package Pydantic models.

Use the top-level `justfile` as the project interface. Global QC remains owned by
`ai-review-ci`.

