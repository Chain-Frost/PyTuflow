# Contribution fork bootstrap and handover

## Strategy review

Keep `master` as an exact official-upstream mirror and integrate internal PRs
into `contrib/integration`. This isolates unfinished phantom work and gives
reviewers a stable original-library comparison. Do not merge phantom/master.
Do not commit fork-only process records, CI administration or benchmark archives
to an external contribution by default.

Keep independently reviewable internal work packages. The revised plan has
**three externally curated PRs**: **A** existing-library fixes, **B** focused
public typing, **C** optional deferred/batch/graph execution. Reconstruct
`contrib/upstream-fixes` from actual official upstream; curate
`contrib/upstream-typing` and `contrib/upstream-deferred` independently after A
has been accepted upstream. Both use the accepted A baseline, but **C does not
depend on B**. If either B or C has already landed, the other is reconstructed
on the latest real upstream head. Typing for new deferred modules belongs in C.
See [UPSTREAM_STACK.md](../../UPSTREAM_STACK.md) for curation and separate
acceptance. No external submission or auto-merge is authorised by the plan.

## Internal branch contract

- `contrib/fix-<topic>`: branch from current integration; one correction and its
  regression tests per PR, targeting integration.
- `contrib/deferred-<step>`: declare predecessor and exact base SHA in each PR;
  target the predecessor while stacked, then retarget integration after it lands.
- Squash merging changes ancestry. Rebase remaining unpublished steps onto the
  resulting integration commit. For already published branches, create a new
  successor branch and replacement PR when rebuilding stacked ancestry instead
  of force-pushing shared history. Independent published PRs can merge current
  integration into their branch and push normally without replacing the PR.
  Every candidate must satisfy strict up-to-date checks on its refreshed base.
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
A separate non-bypassable master ruleset enforces deletion, force-push and linear-
history restrictions even for administrators.
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
actually requires, without adding a backport. Python 3.11.16 passed the grammar audit, 121 infrastructure tests plus 10
subtests, and all 23 installed-wheel checks. Hosted fast run **40330148824**
passed all 3.11/3.12/3.14 lanes. Full final-head hosted acceptance is required
before handover. This historical checkpoint was superseded by final validation
and the authorised squash merge of bootstrap PR #1 as `89a43fa5`. No release or
upstream PR is authorised by that merge.

Before transferring a phantom change, read its current diff and review threads,
check prerequisites, carry only relevant tests, retain failures, record exact
source/base/candidate SHAs and explain its public API impact. Phantom is still
under development; this snapshot is not acceptance of its remaining work.


## Repository configuration

Exact snapshots: [before](bootstrap-before.json), [after](bootstrap-after.json).
Squash only; zero required approvals; PRs and resolved review threads required;
linear history, no force pushes or branch deletion. Automatic merge and automatic
merged-branch deletion are disabled. Issues were enabled to record compatibility
follow-up #2 (now superseded by the owner's 3.11 minimum policy).

- Integration ruleset **25880728**: no bypass, strict up-to-date checks
  `Fast contracts gate` and `Original library acceptance`, bound to GitHub Actions
  app **15368**. Names were observed on real hosted runs before activation.
- Master PR ruleset **25880727**: admin bypass for exact upstream fast-forwards.
- Master immutable-history ruleset **25881302**: no bypass. Master deliberately
  has no fork CI requirements, because official upstream has no such workflows.

The initial hosted 3.10 fast run **40329310658** failed on the runner's older
3.10.11 tarfile API (`extractall(filter=...)`); the gate correctly failed. Local
3.10.21 had that backport. This infrastructure failure is distinct from the 87
production project failures. Initial raw evidence is retained; it is superseded
by 3.11/3.12/3.14 acceptance, not relabelled as a pass.

Real hosted prose-only push runs **40329606617** and **40329606735** passed both
gates with all three substantive lanes skipped. Superseded runs **40329533268**
and **40329533338** were cancelled and their gates failed. These exercised the
same gate code; complete three-dot PR classification (including source-to-docs
renames) is separately exercised by hosted tests. No second PR was created for
these probes. Synthetic missing/failed/skipped/cancelled-result contracts run
in every fast lane; missing jobs are rejected by exact expected-name comparison.


## Retained local evidence

[Local validation summary](evidence/local-validation.json) and
[sanitised native QGIS reports](evidence/qgis-d025029.zip) retain exact tested
revisions. QGIS 4.2.3 / Python 3.12.15 passed all 239 tests on upstream and
candidate with no skips; MDAL was present. Production and QGIS tests have not
changed since that candidate. The DLL diagnostic remains an explicit limitation.
The local exploratory 3.10 full comparison was rejected because files changed
while it ran; its group outcomes informed the minimum-runtime investigation but
are not an accepted baseline. Hosted evidence remains authoritative for the
final committed candidate.

## Next agent checklist

1. Fetch integration and verify this bootstrap has been reviewed and merged;
   until then branch from its exact head only with an explicit dependency.
2. Inspect current phantom changes individually; record the selected source SHA,
   rationale and prerequisites. Start independent correctness PRs first.
3. Keep raw failure evidence. The initial FM comparison finds three differing
   cases locally (Flood Relief Arch, culvert inlet/outlet, river junctions).
   Investigate engineering correctness separately from CI infrastructure.
4. Use the PR template and real-runtime QGIS testing where applicable. Do not
   mistake a green inherited-failure comparison for hydraulic acceptance.
5. Before external curation, fetch official upstream again, agree scope, and
   reconstruct only accepted production/test commits on a separate branch.
   Re-run CI there; no upstream PR or release is authorized by this bootstrap.


## Roadmap and strengthened acceptance

See [UPSTREAM_STACK.md](../../UPSTREAM_STACK.md) for work-package issues,
provisional dependencies, source SHAs and the three upstream curation scopes.
Bootstrap is merged and internal implementation is underway. Each subsequent
merge still needs accepted evidence and owner authorisation. Python >=3.11 is
settled; no 3.10 backport is planned.

The follow-up strengthens CI to compare the candidate with both immutable
upstream and its exact event-pinned PR base. This prevents a fixed upstream bug
from returning unnoticed and protects tests added after upstream. A committed
pre-overlay inventory also guards the FM helper boundary. See ci/README.md for
report names and the updated reproduction command. The earlier run IDs above
remain historical bootstrap evidence; PR #1 records current-head validation.
