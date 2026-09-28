# ai-review-ci Python QC delegation justfile.
# The central implementation lives in ~/ai-review-ci/justfiles/python.just.
# Public recipes delegate to that central justfile while preserving this repo as the caller root.

# ai-review-ci contract variables consumed by doctor and workflow installers.
ai_review_ci_schema_version := "1"
ai_review_ci_profile := "python"
ai_review_ci_ref := "main"
ai_review_ci_release_channel := "main"
ai_review_ci_workflow_template_version := "1"
ai_review_ci_local_delegation := "global-justfile"
ai_review_ci_default_branch := "main"
# List available recipes.
default:
    @just --list

# Run commit-tier Python QC through the central implementation.
test-commit:
    @just -f ~/ai-review-ci/justfiles/python.just -d . test-commit

# Run the full Python test suite before pushing.
test-push:
    @just -f ~/ai-review-ci/justfiles/python.just -d . test-push

# Run CI acceptance QC through the central implementation.
test-ci:
    @just -f ~/ai-review-ci/justfiles/python.just -d . test-ci

# Link the review-facing skills into the configured skill vault.
install-skills:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ "${AI_SKILLS_DIR+x}" != x ]]; then
        echo "ERROR: AI_SKILLS_DIR must be set."
        exit 1
    fi
    mkdir -p "$AI_SKILLS_DIR"
    for skill in "{{ justfile_directory() }}"/skills/*; do
        name="$(basename "$skill")"
        target="$AI_SKILLS_DIR/$name"
        if [[ -e "$target" && ! -L "$target" ]]; then
            echo "ERROR: refusing to replace non-symlink skill: $target"
            exit 1
        fi
        ln -snf "$skill" "$target"
    done
