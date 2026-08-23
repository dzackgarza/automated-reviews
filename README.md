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

## Project interface

Run `just` to list the supported operations.
Use the `automated-reviews` CLI for case inspection and replay dispatch.
