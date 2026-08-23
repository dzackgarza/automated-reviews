# Agent instructions

This repository owns the complete LLM review system.

It owns production workflows, prompts, policy inputs, report schemas, the review
runner, validation, delivery, model selection, and frozen replay.
`dzackgarza/ai-review-ci` consumes the published workflow contract.
It remains the owner of deterministic QC, hooks, profiles, and branch protection.

Preserve the model-visible boundary. A replay must use the frozen target source,
reviewer context, prompt inputs, tool permissions, paths, and validator behavior.
Keep adjudication files outside the reviewer filesystem.

Run replays through the targeted pytest surface and a local disposable Docker runner.
Do not move replay execution to GitHub Actions or another remote service.

Do not add evaluation wording to model-visible files or prompts. The reviewer
must see the same CI role and repository state that production supplies.

Use one case manifest as the source of replay identity. Store bespoke
configuration in TOML. Validate it with the package Pydantic models.

`src/automated_reviews/data/reviewer.toml` selects the production model.
Production review commands must read this file. Do not copy the model identifier
into workflows, prompts, OpenCode configuration, or runner scripts.

Publish downstream workflows from `src/automated_reviews/templates/`.
The reusable workflows under `.github/workflows/` execute the same tracked
runtime used by replay.

Use the top-level `justfile` as the project interface.
