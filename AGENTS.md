# Contribution fork instructions

Read `docs/contributing/BOOTSTRAP.md`, `docs/contributing/FOLLOW_UPS.md` and
`ci/README.md` and `UPSTREAM_STACK.md` before implementation. They define the reviewed integration path.

- Keep `master` identical to official upstream; work through PRs to
  `contrib/integration`. Do not merge phantom/master wholesale.
- Minimum runtime and typing language target: Python 3.11. Validate 3.11, 3.12,
  3.14; real QGIS runs use its own initialized interpreter.
- Use configured interpreters, not local virtual environments.
- Preserve unrelated work. Never force-push, auto-arm a PR, release, or create
  an external upstream PR without explicit authorization.
- Keep production correctness PRs separate from deferred-execution prerequisites.
  Record the predecessor and exact SHA for stacked work; see squash handover rules.
- Run `python ci/python_compatibility.py` and applicable tests. Full CI retains
  raw failures and compares against both immutable official upstream and the
  exact PR base. Preserve accepted fixes and test definitions; do not suppress
  failures/warnings or edit reference outputs simply to obtain green checks.
- For deliberate output corrections or test replacements, follow
  `docs/contributing/INTENTIONAL_CORRECTIONS.md`; provide independent expected
  values and exact affected tests. Review does not override required CI.
- Curate three external PRs separately: **A** existing-library fixes,
  **B** focused public typing, **C** optional deferred/batch/graph execution.
  Both B and C must be curated on the actual accepted upstream A baseline;
  C does not technically depend on B, and whichever lands second must be
  refreshed on the real upstream head. Keep type annotations for *new deferred
  modules* within C. Preserve public compatibility and Python >=3.11.
  Exclude fork administration, CI and internal evidence unless requested.
  Neither upstream submission nor automatic merge is authorised by this plan.

## CI-efficient iteration

- Make focused local commits as useful, then push one coherent, locally checked
  batch at a review or hosted-validation milestone. A push starts CI: do not push
  every edit, formatting correction or work-note update separately.
- Run the applicable lightweight checks before pushing. Use existing failed-job
  reruns for transient infrastructure errors instead of changing source solely
  to start another workflow. Do not use skip-CI markers to bypass required gates.
- Windows Python 3.11, 3.12 and 3.14 remains the acceptance baseline. Ubuntu
  control jobs provide inexpensive early feedback; Linux filename-case tests
  preserve their specific compatibility contract. Neither replaces Windows or
  native QGIS evidence, or changes the declared package dependencies.
- Keep draft PRs subject to applicable checks. Superseded runs may be cancelled
  per workflow and PR; preserve independent focused workflows and stacked PRs.
  Original-library fast/full acceptance is intentionally a single staged workflow:
  full Windows lanes start only after the same candidate's fast gate succeeds.
- For exhaustive focused-matrix diagnostics, re-run all jobs on the same head:
  only the first PR attempt stops sibling lanes on the first failure. Full
  upstream/base/candidate comparisons must still retain complete raw outcomes.

See `ci/README.md` for the current gates and artifact policy.
