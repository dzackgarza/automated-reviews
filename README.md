# automated-reviews

`automated-reviews` captures and replays automated code-review environments locally.
It compares model behavior without changing the production review prompt.

The production review contract remains in [`ai-review-ci`](https://github.com/dzackgarza/ai-review-ci).
This repository owns frozen cases, replay control, captured model output, and human adjudication.

## Replay boundary

Each case records the target revision, pull request, review-infrastructure revision, model, tool versions, reviewer context, and observed production run.

A replay uses the same `ai-review-ci` preparation and review commands in a local disposable Docker runner.
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
