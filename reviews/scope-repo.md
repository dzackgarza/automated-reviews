# Slop Review Scope: Repository-Wide Sweep

Perform a fresh repository-wide slop review.
Inspect the source tree only for specific violations of the loaded `POLICY.*` records.

Coverage strategy:

1. Run `tree -L 3` to understand the directory layout.

2. Identify source, test, workflow, configuration, and documentation surfaces covered by the policy index.

3. Inspect candidate red flags against their complete local control flow.

4. Report only violations supported by a specific policy code and repository evidence.

EXCEPTION: the reviewer context above lists findings already tracked for this repository.
Open code scanning alerts are carried forward into the next SARIF upload by automation.
Do NOT duplicate them in your report unless you have new evidence, the problem reappears in a materially different form, or the previous resolution is directly contradicted by the current code.

Submit only specific `POLICY.*` slop violations.
Otherwise, submit an empty findings array.
