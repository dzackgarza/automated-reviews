# automated-reviews

`automated-reviews` captures and replays automated code-review environments.
It compares model behavior without changing the production review prompt.

The production review contract remains in [`ai-review-ci`](https://github.com/dzackgarza/ai-review-ci).
This repository owns frozen cases, replay control, captured model output, and human adjudication.

## Replay boundary

Each case records the target revision, pull request, review-infrastructure revision, model, tool versions, reviewer context, and observed production run.

A replay uses the same `ai-review-ci` preparation and review commands on a new GitHub Actions runner.
The selected model is an outer workflow input.
The model does not receive evaluation labels or adjudication data.

The first case freezes the `sage-categories` PR 3 run that produced issue 5.
GitHub retained the job log and review comments.
The original runner did not retain its prompt file.
The frozen reviewer context uses GitHub state from the original run boundary.
Its manifest records this reconstruction and all artifact digests.

## Project interface

Run `just` to list the supported operations.
Use the `automated-reviews` CLI for case inspection and replay dispatch.

```console
uv run automated-reviews inspect cases/sage-categories-pr3-run32660872242
uv run automated-reviews dispatch cases/sage-categories-pr3-run32660872242 --model opencode/nemotron-3-ultra-free
```
