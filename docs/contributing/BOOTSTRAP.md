# Contribution fork bootstrap and handover

## Strategy review

Keep `master` as an exact official-upstream mirror and integrate internal PRs
into `contrib/integration`. This isolates unfinished phantom work and gives
reviewers a stable original-library comparison. Do not merge phantom/master.
Do not commit fork-only process records, CI administration or benchmark archives
to an external contribution by default.

Prefer independently reviewable correctness changes before the deferred series.
Do not promise one large external PR before the upstream maintainer agrees on
scope: a small ordered series may be easier to review. Prepare a separate
`upstream/<topic>` branch from the then-current official master only when the
selected changes and evidence are ready. No external branch or PR is created
by this bootstrap.

## Internal branch contract

- `contrib/fix-<topic>`: branch from current integration; one correction and its
  regression tests per PR, targeting integration.
- `contrib/deferred-<step>`: declare predecessor and exact base SHA in each PR;
  target the predecessor while stacked, then retarget integration after it lands.
- Squash merging changes ancestry. Rebase remaining unpublished steps onto the
  resulting integration commit. For already published branches, create a new
  successor branch and replacement PR instead of force-pushing shared history.
- Keep merged branches during the dependent series. No automatic merge arming.
- Use explicit file/commit selection when curating upstream; never wholesale merge
  integration into an external branch. Re-run every applicable check on its head.

## Synchronising master

Master protection excludes required fork CI because upstream has no workflows.
Normal changes require PRs; a repository administrator has an explicit bypass
on the master ruleset solely for verified upstream fast-forward synchronisation.
Fetch official master, verify its repository and full SHA, verify old master is
an ancestor, and push that exact commit without force. Re-read both refs after
pushing. Never put fork development commits on master or squash a sync PR,
which would destroy exact upstream identity. Admin bypass is broad in GitHub;
its synchronisation-only purpose is an operator policy, not server enforcement.
Integration has no bypass and requires both verified CI gates.

## Compatibility policy

Minimum runtime and typing language target: Python 3.11. Supported validation
interpreters: 3.11, 3.12, 3.14. Python 3.10 and earlier are unsupported.
Production source is audited against 3.11 grammar; actual 3.11 installed-package
imports and full original suites are required. New annotations must run on 3.11;
use TypeVar rather than PEP 695 declarations. QGIS needs separate real-runtime
validation. No production fixes are transferred by this bootstrap.

## Delivery and remaining verification

The initial 3.10 audit passed grammar and imports but exposed 87 inherited
project failures: `pytuflow/project/template/engine.py:60` calls
`string.Template.get_identifiers()`, introduced in Python 3.11. The owner
therefore superseded the proposed 3.10 minimum: adopt the runtime upstream
actually requires, without adding a backport. Python 3.11 validation is pending. This PR must remain unmerged. No release or upstream PR is authorized.

Before transferring a phantom change, read its current diff and review threads,
check prerequisites, carry only relevant tests, retain failures, record exact
source/base/candidate SHAs and explain its public API impact. Phantom is still
under development; this snapshot is not acceptance of its remaining work.
