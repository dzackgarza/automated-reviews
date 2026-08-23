set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

control_repo := env_var("GITHUB_WORKSPACE")
infra := justfile_directory() / ".."
reviewer_home := "/home/reviewer"
reviewer_repo := "/home/reviewer/repo"
reviewer_infra := "/home/reviewer/.review/infra"
private_tools := "/opt/automated-reviews/private"

install-tools:
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
    bun add --global opencode-ai
    bun add --global cc-safety-net

fetch-slop-context tool_name pr_number:
    uv run --project {{infra}} automated-reviews fetch-slop-context \
      --repo "${GITHUB_REPOSITORY}" \
      --tool-names "{{tool_name}}" \
      --output "{{control_repo}}/.reviewer-context.md" \
      --alerts-output "{{control_repo}}/.reviewer-alerts.json" \
      --pr-number "{{pr_number}}"

fetch-policy-compliance-context pr_number:
    uv run --project {{infra}} automated-reviews fetch-policy-compliance-context \
      --repo "${GITHUB_REPOSITORY}" \
      --output "{{control_repo}}/.reviewer-context.md" \
      --alerts-output "{{control_repo}}/.reviewer-alerts.json" \
      --pr-number "{{pr_number}}"

create-reviewer:
    if reviewer_entry="$(getent passwd reviewer)"; then \
      IFS=: read -r name _ uid gid gecos home shell <<< "$reviewer_entry"; \
      if [ "$name" != "reviewer" ]; then echo "expected reviewer account, got $name" >&2; exit 1; fi; \
      if [ "$home" != "{{reviewer_home}}" ]; then echo "reviewer home mismatch: $home" >&2; exit 1; fi; \
      if [ "$shell" != "/bin/bash" ]; then echo "reviewer shell mismatch: $shell" >&2; exit 1; fi; \
    else \
      sudo useradd -m -s /bin/bash reviewer; \
    fi
    sudo mkdir -p {{reviewer_home}}/repo
    sudo find {{reviewer_home}}/repo -mindepth 1 -delete
    sudo chown -R reviewer:reviewer {{reviewer_home}}

install-private-tools:
    sudo mkdir -p {{private_tools}}
    sudo find {{private_tools}} -mindepth 1 -delete
    sudo rsync -a --exclude '.venv' {{infra}}/ {{private_tools}}/
    sudo uv sync --project {{private_tools}}
    sudo chown -R root:root {{private_tools}}
    sudo chmod 700 {{private_tools}}
    sudo chmod 500 {{private_tools}}/ci/private/submit-candidate

install-reviewer-home:
    sudo rsync -a --delete {{infra}}/ci/reviewer_home/ {{reviewer_home}}/
    sudo mkdir -p {{reviewer_infra}}
    sudo rsync -a --delete --exclude '.venv' {{infra}}/ {{reviewer_infra}}/
    sudo chown -R reviewer:reviewer {{reviewer_home}}
    sudo chmod 755 {{reviewer_home}}/bin/submit-candidate
    sudo -u reviewer -H uv sync --project {{reviewer_infra}}

install-sudo-rule:
    { echo "reviewer ALL=(root) NOPASSWD: {{private_tools}}/ci/private/submit-candidate"; \
      echo "reviewer ALL=(root) NOPASSWD: {{private_tools}}/ci/private/submit-candidate *"; \
      echo "Defaults!{{private_tools}}/ci/private/submit-candidate env_keep += \"REPORT_TYPE REVIEWER_REPO CONTROL_REPO POLICY_DOCUMENT\""; \
    } | sudo tee /etc/sudoers.d/ai-review-submit >/dev/null
    sudo chmod 0440 /etc/sudoers.d/ai-review-submit
    sudo visudo -c -f /etc/sudoers.d/ai-review-submit

copy-reviewer-repo:
    sudo rsync -a --delete \
      --exclude '.git' \
      --exclude '.github' \
      --exclude '.agents' \
      --exclude '.hermes' \
      --exclude '.review-report-artifact.json' \
      --exclude '.review-report.sarif' \
      {{control_repo}}/ {{reviewer_repo}}/
    sudo mkdir -p {{reviewer_repo}}/.agents/review-runner/candidates
    sudo cp {{control_repo}}/.reviewer-context.md {{reviewer_repo}}/.reviewer-context.md
    # cc-safety-net loads custom rulebooks from the *project* scope (cwd);
    # user-scope placement under $HOME does not activate them. The reviewer
    # runs with cwd={{reviewer_repo}}, so the rulebook must live there.
    sudo mkdir -p {{reviewer_repo}}/.cc-safety-net
    sudo cp -r {{reviewer_home}}/.config/cc-safety-net/rules {{reviewer_repo}}/.cc-safety-net/rules
    sudo chown -R reviewer:reviewer {{reviewer_repo}}

prepare:
    just -f {{infra}}/ci/runner.just create-reviewer
    just -f {{infra}}/ci/runner.just install-private-tools
    just -f {{infra}}/ci/runner.just install-reviewer-home
    just -f {{infra}}/ci/runner.just install-sudo-rule
    just -f {{infra}}/ci/runner.just copy-reviewer-repo

check-reviewer-model:
    #!/usr/bin/env bash
    set -euo pipefail
    configured_model="$(uv run --project {{infra}} automated-reviews active-model)"
    provider="${configured_model%%/*}"
    available_models="$(cd "{{reviewer_home}}" && sudo -u reviewer -H env \
      PATH="{{reviewer_home}}/bin:/usr/bin:/bin" \
      HOME="{{reviewer_home}}" \
      XDG_CONFIG_HOME="{{reviewer_home}}/.config" \
      /usr/local/bin/opencode models "$provider")"
    if ! grep -Fxq "$configured_model" <<<"$available_models"; then
      echo "FATAL: configured reviewer model is unavailable: $configured_model" >&2
      printf '%s\n' "$available_models" >&2
      exit 1
    fi
    echo "Reviewer model available: $configured_model"

stage-context-packet archive:
    #!/usr/bin/env bash
    set -euo pipefail
    packet="{{control_repo}}/{{archive}}"
    if [ ! -f "$packet" ]; then
      echo "FATAL: review context packet not found: {{archive}}" >&2
      exit 1
    fi
    sudo mkdir -p {{reviewer_repo}}/.review-context
    sudo find {{reviewer_repo}}/.review-context -mindepth 1 -delete
    sudo tar -xf "$packet" -C {{reviewer_repo}}/.review-context
    sudo chown -R reviewer:reviewer {{reviewer_repo}}/.review-context

stage-pr-diff base_ref:
    git -C {{control_repo}} diff "origin/{{base_ref}}...HEAD" > "${RUNNER_TEMP}/reviewer-diff.patch"
    test -s "${RUNNER_TEMP}/reviewer-diff.patch"
    if [ -d "{{reviewer_repo}}" ]; then \
      sudo cp "${RUNNER_TEMP}/reviewer-diff.patch" {{reviewer_repo}}/.reviewer-diff.patch; \
      sudo chown reviewer:reviewer {{reviewer_repo}}/.reviewer-diff.patch; \
    fi

run-slop-review scope:
    sudo -u reviewer -H env \
      PATH="{{reviewer_home}}/bin:/usr/bin:/bin" \
      HOME="{{reviewer_home}}" \
      XDG_CONFIG_HOME="{{reviewer_home}}/.config" \
      XDG_DATA_HOME="{{reviewer_home}}/.local/share" \
      XDG_STATE_HOME="{{reviewer_home}}/.local/state" \
      XDG_CACHE_HOME="{{reviewer_home}}/.cache" \
      REPORT_TYPE="slop" \
      REVIEWER_REPO="{{reviewer_repo}}" \
      CONTROL_REPO="{{control_repo}}" \
      AI_REVIEW_OPENCODE_BIN="/usr/local/bin/opencode" \
      AI_REVIEW_OPENCODE_TIMEOUT="600" \
      AI_REVIEW_MAX_ATTEMPTS="5" \
      AI_REVIEW_BACKOFF="5" \
      AI_REVIEW_POLICY_PATHS="${REVIEW_POLICY_PATHS:-}" \
      AI_SLOP_REVIEW_FOCUS="${SLOP_REVIEW_FOCUS:-}" \
      bash -lc 'cd {{reviewer_repo}} && /usr/local/bin/opencode --version && /usr/local/bin/uv run --project {{reviewer_infra}} automated-reviews run-slop-review \
        --template "{{reviewer_infra}}/reviews/slop/template.md" \
        --scope "{{reviewer_infra}}/reviews/scope-{{scope}}.md" \
        --manifest "{{reviewer_infra}}/reviews/slop/manifest.txt" \
        --reviewer-context .reviewer-context.md \
        --policy-paths "$AI_REVIEW_POLICY_PATHS" \
        --slop-focus "$AI_SLOP_REVIEW_FOCUS"'

run-policy-compliance-review scope policy_document:
    sudo -u reviewer -H env \
      PATH="{{reviewer_home}}/bin:/usr/bin:/bin" \
      HOME="{{reviewer_home}}" \
      XDG_CONFIG_HOME="{{reviewer_home}}/.config" \
      XDG_DATA_HOME="{{reviewer_home}}/.local/share" \
      XDG_STATE_HOME="{{reviewer_home}}/.local/state" \
      XDG_CACHE_HOME="{{reviewer_home}}/.cache" \
      REPORT_TYPE="compliance" \
      POLICY_DOCUMENT="{{policy_document}}" \
      REVIEWER_REPO="{{reviewer_repo}}" \
      CONTROL_REPO="{{control_repo}}" \
      AI_REVIEW_OPENCODE_BIN="/usr/local/bin/opencode" \
      AI_REVIEW_OPENCODE_TIMEOUT="600" \
      AI_REVIEW_MAX_ATTEMPTS="5" \
      AI_REVIEW_BACKOFF="5" \
      bash -lc 'cd {{reviewer_repo}} && /usr/local/bin/opencode --version && /usr/local/bin/uv run --project {{reviewer_infra}} automated-reviews run-policy-compliance-review \
        --template "{{reviewer_infra}}/reviews/compliance/template.md" \
        --scope "{{reviewer_infra}}/reviews/compliance/scope-{{scope}}.md" \
        --reviewer-context .reviewer-context.md \
        --policy-document "$POLICY_DOCUMENT"'

collect-output:
    cp {{reviewer_repo}}/.review-report-artifact.json {{control_repo}}/.review-report-artifact.json

write-review-state:
    uv run --project {{infra}} automated-reviews report-metadata \
      --path "{{control_repo}}/.review-report-artifact.json" \
      > "{{control_repo}}/.review-findings.json"

enforce-review-status:
    uv run --project {{infra}} automated-reviews enforce-report-status \
      --path "{{control_repo}}/.review-report-artifact.json"

convert-sarif category:
    uv run --project {{infra}} automated-reviews to-sarif \
      --artifact "{{control_repo}}/.review-report-artifact.json" \
      --output "{{control_repo}}/.review-report.sarif" \
      --carry-forward-alerts "{{control_repo}}/.reviewer-alerts.json" \
      --category "{{category}}" \
      --sha "${GITHUB_SHA}" \
      --server-url "${GITHUB_SERVER_URL}" \
      --repository "${GITHUB_REPOSITORY}"

publish-issues parent_issue:
    uv run --project {{infra}} automated-reviews publish-issues \
      --artifact "{{control_repo}}/.review-report-artifact.json" \
      --repo "${GITHUB_REPOSITORY}" \
      --parent-issue "{{parent_issue}}" \
      --sha "${GITHUB_SHA}"

post-threads pr_number:
    uv run --project {{infra}} automated-reviews post-threads \
      --artifact "{{control_repo}}/.review-report-artifact.json" \
      --diff "${RUNNER_TEMP}/reviewer-diff.patch" \
      --repo "${GITHUB_REPOSITORY}" \
      --pr-number "{{pr_number}}"
