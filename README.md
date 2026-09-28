# automated-reviews

`automated-reviews` holds the canonical skills that agents load to review code, tests, and documentation.
It also holds the bridge-burning policy index and a Python parser for it.

## Contents

| Path | Purpose |
| --- | --- |
| `src/automated_reviews/resources/skills/` | The review skills: `anti-slop`, `bespoke-software-policy`, `policy-index`, `reviewing-llm-code`, `style-guide`, `test-guidelines` |
| `skills/` | Symlinks to the skill directories |
| `src/automated_reviews/policy_index.py` | Loads `POLICY.*` records and their `REMEDIATE.*` constructions |

## Requirements

- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just)

The project requires Python 3.14 or later.

## Install the skills

Link every skill into a skill directory:

```bash
AI_SKILLS_DIR=~/path/to/skills just install-skills
```

The recipe replaces existing symlinks and stops at any existing non-symlink entry.

## Use the policy index

```python
from automated_reviews.policy_index import load_policy_index

index = load_policy_index()
remediation = index.remediation_for_policy("POLICY.NO_HIDDEN_CONFIG")
```

A policy record names exactly one remediation code.
The loader raises `PolicyIndexError` when a record is malformed or names a missing remediation.

[`ai-review-ci`](https://github.com/dzackgarza/ai-review-ci) depends on this package for its deterministic policy detectors.

## License

This repository has no license file.
