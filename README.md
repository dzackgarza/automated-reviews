# automated-reviews

`automated-reviews` is the canonical source for LLM reviews.

It owns the production workflows, prompts, policy inputs, report schemas, runner, validation, delivery, model selection, frozen cases, and local replay.
[`ai-review-ci`](https://github.com/dzackgarza/ai-review-ci) consumes the published workflow contract.
It owns deterministic QC, hooks, profiles, gates, and branch protection.

## Production model

[`src/automated_reviews/data/reviewer.toml`](src/automated_reviews/data/reviewer.toml) selects the active model.
Production passes this value to OpenCode for each run.
Change this metadata when the provider retires the model.

The current model is Ox Alpha: `opencode-go/ox-alpha-free`.

## Published workflows

- `.github/workflows/_review.yml` runs slop reviews.

- `.github/workflows/_issue-alignment.yml` checks policy-owning issues.

- `src/automated_reviews/templates/` contains downstream trigger workflows.

The pull-request template calls deterministic workflows from `ai-review-ci`. It calls the LLM reviewer from this repository.

The package exposes `publish-workflows` for downstream installation.

## Replay boundary

Each case records the target revision, pull request, review-infrastructure revision, model, tool versions, reviewer context, and observed production run.

A replay uses the frozen production preparation and review commands in a local disposable Docker runner.
The selected model is an outer test input.
The model does not receive evaluation labels or adjudication data.

The first case freezes the `sage-categories` PR 3 run that produced issue 5. GitHub retained the job log and review comments.
The original runner did not retain its prompt file.
The frozen reviewer context uses GitHub state from the original run boundary.
Its manifest records this reconstruction and all artifact digests.

## Project interface

Run `just` to list the supported operations.
Use the `automated-reviews` CLI for case inspection and local replay.

```console
uv run automated-reviews inspect cases/sage-categories-pr3-run32660872242
just replay cases/sage-categories-pr3-run32660872242 opencode/nemotron-3-ultra-free
```

The replay is a targeted pytest test.
Docker caches the frozen runner image after its first build.
Each run streams the model transcript to the terminal.
It writes prompts, every submitted candidate, validation feedback, and OpenCode state under `.git/automated-reviews/artifacts/`. It also writes the final report when a candidate passes production validation.

The frozen case contains a Git bundle for the exact merge checkout.
It also contains the exact `ai-review-ci` archive and the reconstructed reviewer context.
The replay does not fetch source or review infrastructure from the network.
