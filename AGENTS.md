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
  **B** focused public typing, **C** optional deferred fragment-based input validation.
  Both B and C must be curated on the actual accepted upstream A baseline;
  C does not technically depend on B, and whichever lands second must be
  refreshed on the real upstream head. Keep type annotations for *new deferred
  modules* within C. Preserve public compatibility and Python >=3.11.
  General compiled control trees and mutable input-group prototype reuse have
  been superseded ([#18](https://github.com/Chain-Frost/PyTuflow/issues/18),
  [#19](https://github.com/Chain-Frost/PyTuflow/issues/19)); do not recreate
  them as PR C prerequisites. Stage #20 requires native QGIS/MDAL and
  M480/M36/M240 run/source/physical parity and matched timing.
  Exclude fork administration, CI and internal evidence unless requested.
  Neither upstream submission nor automatic merge is authorised by this plan.
