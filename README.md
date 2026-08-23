# automated-reviews

`automated-reviews` runs production LLM code reviews and replays captured CI environments locally.
It publishes reusable GitHub workflows and keeps the active reviewer model in one metadata file.

Use a frozen case to compare model behavior against the same repository, prompt, tools, and reviewer context.

## Requirements

- Linux on x86-64
- [Git](https://git-scm.com/)
- [uv](https://docs.astral.sh/uv/)
- [Docker Engine](https://docs.docker.com/engine/)
- Outbound HTTPS access for image downloads and model requests

The project requires Python 3.14 or later. `uv` installs the required Python version when needed.

## Installation

```bash
git clone https://github.com/dzackgarza/automated-reviews.git
cd automated-reviews
uv sync
```

Verify the installation:

```console
$ uv run automated-reviews active-model
opencode-go/ox-alpha-free
```

Run `uv run automated-reviews --help` for the complete command list.

## Replay a frozen review

Inspect the included case:

```bash
uv run automated-reviews inspect \
  cases/sage-categories-pr3-run32660872242
```

Replay the case with the active model:

```bash
uv run automated-reviews replay \
  cases/sage-categories-pr3-run32660872242 \
  opencode-go/ox-alpha-free
```

The first replay builds the pinned runner image. Later replays use the cached image.
The command streams the model session and ends with an artifact path:

```text
Replay artifacts: .git/automated-reviews/artifacts/sage-categories-pr3-run32660872242/opencode-go--ox-alpha-free/<run-id>
```

The artifact directory contains the model prompt, submitted candidates, validation feedback, OpenCode state, and logs.
A successful validation adds the final report.

The case supplies the exact target checkout, review infrastructure, tool versions, and reconstructed GitHub reviewer context.
The reviewer cannot fetch source or review infrastructure during replay.
OpenCode still contacts the selected model provider.

## Publish review workflows

Write the review triggers into a target repository:

```bash
uv run automated-reviews publish-workflows \
  /path/to/repository \
  --profile python \
  --review-ref main \
  --qc-ref main
```

The command creates:

- `.github/workflows/review-pr.yml`
- `.github/workflows/review-slop.yml`

It stops if either file already exists.

Available profiles are `python`, `bun`, `bun-playwright`, `bun-python`, `docs-and-configs`, `rust`, and `sage`.
The generated workflows call this repository for LLM reviews.
They call [`ai-review-ci`](https://github.com/dzackgarza/ai-review-ci) for deterministic QC.

The GitHub workflows require read access to repository contents.
They also require write access to pull requests, issues, and code-scanning results.

## Select the production model

[`src/automated_reviews/data/reviewer.toml`](src/automated_reviews/data/reviewer.toml) contains the active model identifier.
Production workflows read this file before each review.
Change this value when the provider retires the model.

## Current limits

The included replay corpus contains one diff-scoped slop-review case from `dzackgarza/sage-categories` pull request 3.
The production review schema currently supports slop reviews.
Replay output stays under `.git/automated-reviews/artifacts/` and can contain complete model transcripts.

## Reference

- [Frozen case manifest](cases/sage-categories-pr3-run32660872242/case.toml)
- [Reusable review workflow](.github/workflows/_review.yml)
- [Reusable issue-alignment workflow](.github/workflows/_issue-alignment.yml)
- [`ai-review-ci`](https://github.com/dzackgarza/ai-review-ci) deterministic QC

## License

This repository has no license file.
