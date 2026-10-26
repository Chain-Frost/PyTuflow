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
- Curate two external PRs separately: existing-library fixes/improvements first,
  then optional deferred/batch/graph execution on the actual upstream result of
  the first PR. See UPSTREAM_STACK.md for scope and acceptance. Deferred-only
  API/typing work belongs in the second PR. Exclude fork administration/process
  files unless upstream explicitly wants them. Neither submission is authorised
  by this plan.
