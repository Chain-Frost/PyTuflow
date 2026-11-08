# Follow-up: stage original-library acceptance after fast contracts

Status: implementation from PR #66 refreshed for integration after its predecessor merged.
Accepted predecessor: [PR #65](https://github.com/Chain-Frost/PyTuflow/pull/65),
squash-merged into `contrib/integration` at
`8505817380a6250d074f9a84d3c21a4cf85946a5`. Its tree exactly matches the reviewed
parent `d10fa694568e504f13b556a097d43dd3c609fb4b`.
The successor preserves the implementation from [PR #66](https://github.com/Chain-Frost/PyTuflow/pull/66)
head `b738a2e8d5a5b0b991d10deecf38dedc0ad7282b` on that actual accepted base,
without rewriting either published branch. Its PR description records final
candidate checks and integration state. Keep `master` as the upstream mirror;
do not enable auto-merge or scheduled testing.

The original quick/full triggers did not match the stacked base
`ci/resource-efficiency-20261108`. PR #66 now adds that explicit pull-request
base to the single staged workflow, while preserving `contrib/integration`,
`contrib/**`, `master` and `ci-validation/**` push probes. Its fast and full
protected gates must both appear and pass on the actual candidate before
acceptance. Preserve the `master` upstream mirror; missing checks are never
acceptance.

## Evidence and objective

At audited head `7890a51d494f6b41118aff51cfe67c24f079c94b`,
[fast run 42449677851](https://github.com/Chain-Frost/PyTuflow/actions/runs/42449677851)
used 7 minutes of Windows runner time across Python 3.11, 3.12 and 3.14.
[Full run 42449677849](https://github.com/Chain-Frost/PyTuflow/actions/runs/42449677849)
used 61 minutes 41 seconds. Both workflows started independently and each full
lane repeated the same infrastructure/numerical contracts: 225 seconds of test
steps in total. These are observed runner times, not a billed-cost estimate.

The predecessor PR #65 added grammar checks before Windows fan-out and bounded
focused work. PR #66 stages full regression behind the successful fast gate;
the [isolated intentional fast-failure probe](https://github.com/Chain-Frost/PyTuflow/actions/runs/42458071902)
failed all three fast lanes and both gates while all three full lanes remained
skipped. The probe code is not part of the implementation.

## Integration checkpoint (2026-11-08)

- [Ready-mode run 42463921576](https://github.com/Chain-Frost/PyTuflow/actions/runs/42463921576)
  passed all three Windows fast and full lanes and both protected gates on
  `b738a2e8d5a5b0b991d10deecf38dedc0ad7282b`, against review base
  `d10fa694568e504f13b556a097d43dd3c609fb4b`. Each retained regression archive
  contains 52 evidence files and passed both exact-source comparisons. Every
  installed wheel passed all 23 smoke checks with matching provenance and hash.
- The earlier draft run was superseded when the PR became ready; its Python
  3.12 lanes were intentionally skipped and its running full lanes cancelled.
  The ready event restored all three versions on the same candidate.
- The successor targets `contrib/integration` so the pandas-reader, raster-
  recovery and TMF/pandas workflows, previously excluded by the stacked base,
  also run. Require their applicable ready-mode matrices and both protected
  gates on the successor's exact head and accepted base before integration.
- Record final run URLs, candidate/base SHAs and merge outcome in the successor
  PR description; do not push another source commit solely to record CI results.
- [Weekly-validation issue #67](https://github.com/Chain-Frost/PyTuflow/issues/67)
  is closed as not planned. No recurring workflow or scheduler is configured.

## Bounded implementation

1. Read `AGENTS.md`, `ci/README.md`, the current PR checks and the exact branch
   protection requirements. Preserve the required check names `Fast contracts
   gate` and `Original library acceptance`, both bound to GitHub Actions.
2. Consolidate quick and full orchestration into one PR-triggered workflow with
   one scope classifier. Retain the existing pull-request base branches and
   `ci-validation/**` push-probe behaviour, and explicitly cover the chosen stacked
   base when it falls outside those filters. Retire the old automatic quick trigger
   only when the replacement reports both required check names without prefixes
   or duplicate contexts. Do not use `workflow_run` on untrusted PR code or reuse
   a result from a previous head.
3. Run the same three Windows fast lanes, then report `Fast contracts gate`.
   Start the three full lanes only when that gate has succeeded for the same
   event-pinned candidate. Keep the full lanes' upstream, exact-base and exact-
   candidate snapshots, removed-test inventory, both comparisons, and every
   per-interpreter sdist-to-wheel and installed-wheel check unchanged.
4. Avoid repeating infrastructure/numerical contracts inside full lanes only
   after the dependency graph guarantees their successful fast counterparts.
   Standalone reusable-lane calls must still run their own contracts by default.
   Both gates must use `always()` and reject missing, failed, cancelled or
   unexpectedly skipped prerequisite jobs. Explicit prose-only classification
   remains the only successful substantive-job skip.
5. Keep full comparison outcome collection exhaustive. Do not add pytest
   `--maxfail`, suppress inherited failures, cache baseline results, alter
   reference data, remove interpreter coverage or change public dependencies.
   Pushing a draft PR must still produce applicable acceptance checks.

Primary files: `.github/workflows/original-library-quick.yml`,
`.github/workflows/original-library-regression.yml`,
`.github/workflows/original-library-lane.yml`, `ci/pr_gate.py`, and relevant
`tests/ci/` gate contracts. Coordinate any overlapping workflow changes.

## Acceptance before handoff

- Verify the actual stacked PR base triggers both protected checks on the exact
  candidate. Neither a missing workflow nor an absent check is a successful gate.
- Validate workflow syntax and fail-closed gate behaviour for classifier failure,
  missing output, fast failure, cancellation, skipped lanes and documentation-
  only changes. Preserve source-to-prose rename coverage and unknown-path safety.
- Show on hosted evidence that a deliberate cheap/fast failure starts no full
  Windows regression lanes, and that the full acceptance gate reports failure.
  Keep such probes separate from the final candidate and its protected checks.
- On the stable final head, require both protected gates and all three complete
  Windows upstream/base/candidate comparisons, packaging and installed-wheel
  checks. Record candidate/base/upstream SHAs and retain raw failures honestly.
- Compare runner minutes and time to first failure with the measured runs above.
  Expect a longer successful critical path because fast contracts now precede
  full regression. Claim only measured savings; dependency installation still
  occurs in separate Windows jobs and is not eliminated by this design.
- Push one tested implementation batch and rerun only the validation that needs
  it. No branch-protection changes, release or merge is authorised by this handoff.

## Python 3.12 draft/pre-merge policy adjustment (2026-11-08)

The same conditional matrix and readiness event are also applied to all six
path-filtered focused workflows (Linux case policy, imports/logging, pandas
readers, public API, raster recovery, TMF/pandas). For matrix workflows with
multiple pandas versions or operating systems, every combination retains the
3.12 pre-merge lane. Their narrow path/base filters remain unchanged.

The original handoff's unconditional three-version PR matrix is superseded by
an approved resource-efficiency policy: run Python 3.11 and 3.14 on draft PRs,
then require Python 3.12 as well when a PR becomes ready for review. Ready PRs
rerun 3.12 on subsequent candidate changes; `ci-validation/**` push probes
retain the complete three-version matrix. The classifier supplies an explicit
fail-closed Python 3.12 decision, and both pre-existing protected gates verify
that decision. The workflow reacts to `ready_for_review`, so the three-version
acceptance is a pre-merge requirement without changing branch protection. Real native QGIS validation remains a separate acceptance boundary.

A subsequent Codex review identified stale draft-rerun risk: rerunning an old
draft workflow after marking the PR ready could cancel fresh full validation and
publish green gates with only 3.11/3.14. Both gates now re-query the current PR
from GitHub using read-only token permission and require an open PR with the
same draft/ready state, head and exact review-base revision as the original
event. This executes during partial reruns too. The original event-pinned
upstream/base/candidate snapshots are unchanged; API failure fails closed.

A hosted draft run on `bbc610d84bafa316a4d655aba5ab0577501865c7`
passed the fast gate but correctly failed final acceptance when GitHub
implicitly skipped 3.11/3.14 full lanes due to the optional skipped 3.12 fast
job in the transitive prerequisite graph. The follow-up fix adds explicit
`always()` to each full-lane job **together with** positive checks for
classifier success, substantive scope, successful fast gate and the per-lane
3.12 decision. No failed/cancelled gate can start full regression; missing
required full jobs still fail final acceptance. The ready-mode run recorded
above subsequently passed all three full lanes.

A later Codex review identified a test assertion counting compound `always()`
conditions, and full jobs preventing cancellation of superseded runs. The test
now counts exact unconditional gate lines. All three full jobs require
`always() && !cancelled()` plus successful scope and fast-gate prerequisites.
The stacked candidate's ready-mode validation is recorded above. The refreshed
successor still requires complete acceptance against its actual integration base.
