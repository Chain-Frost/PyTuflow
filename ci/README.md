# Contribution CI

The immutable canonical baseline is TUFLOW-Support/PyTuflow commit
`cf908cc922ca8448ed6002834877b0b377329eae`. Each full lane executes it afresh,
then executes the exact candidate and the event-pinned PR target commit in
independent disposable snapshots. Both comparisons must pass. For stacked PRs,
the target is the preceding PR branch, not an assumed integration tip.
When that target SHA equals upstream, the same source report is explicitly
reused; a distinct base always requires its own complete report. Push probes
use their exact `before` commit; a first push uses the immutable upstream SHA.
There is no phantom production baseline, cache trust, or feature-test import.

Adapted from phantom-branch PRs #19, #33 and #38, inspected at
`93d425561ac1995706f95a9c20633d92c4a23fcf`. The regression recorder, comparator,
wheel checker and test-only FM corrections retain their reference contracts.
The two FM test helpers are applied identically to all revisions and hashed.
Before overlays, a committed-source inventory rejects removed/renamed test
definitions, including tests added since upstream. Runtime comparison also
rejects removed collected cases. Intentional test restructuring needs a reviewed
policy change; there is no silent deletion allowlist. Static inventory cannot
prove assertion quality or parameter coverage in overlaid files: changes to
those helpers still require careful review.
No engineering reference data is changed. Raw failures remain failed in reports;
a green comparison means no new regressions, not that all tests passed.

Windows Python 3.11, 3.12 and 3.14 each run fast infrastructure contracts and
full original-library regression plus sdist-to-wheel installation checks.
The wheel check runs with `-I` outside the checkout and verifies package bytes,
RECORD, public imports, resources, generated TCF and CLI entry-point targets.
The OS launcher shim is not tested. Direct dependency pins have interpreter
markers; complete resolved inventories are retained in regression reports.
These pins are validation environments, not a claim about every dependency
version allowed by public metadata. Current/latest and lowest-bound dependency
acceptance remain separate follow-up work.

Only root Markdown/reStructuredText and prose under `docs/` can skip expensive
jobs. All unknown paths, tests, fixtures, CI helpers and workflows require CI.
Classification uses complete Git diffs without rename detection. Both gates
always report; every named lane must be success for code or skipped for prose.
Missing classifier output, missing jobs, failures and cancellation fail closed.
An entirely cancelled workflow cannot satisfy the required success checks.
Artifacts retain raw JSON, JUnit, logs, dependency provenance and wheels for 30
days. Download important release/contribution evidence before it expires.

## Local execution (no virtual environments)

Use a configured interpreter with `ci/requirements-regression.txt` installed.
Run `python ci/python_compatibility.py` and `python -m pytest -q tests/ci`.
Commit the candidate before regression execution: snapshots use committed files.
For each source, run:

```text
python ci/run_regression.py --source . --ref <commit> --label <label> --report-dir <outside-checkout-empty-directory>
python -m ci.accept_regression --root <parent-containing-upstream-base-and-candidate> --upstream cf908cc922ca8448ed6002834877b0b377329eae --base <exact-review-base-sha> --candidate <exact-candidate-sha>
python -m build --no-isolation
```

QGIS is explicitly not selected in standalone lanes. Use the real initialized
QGIS interpreter and `ci/run_regression.py --group qgis` for each revision, then
`ci/compare_regression.py --required-group qgis`. The capability probe requires
an initialized QgsApplication and MDAL; absence fails, never passes as a skip.
Python 3.12 is the reference runtime, not a distribution-wide QGIS assumption.

See [integration handover](../docs/contributing/BOOTSTRAP.md).


## Preventing regression of accepted fixes

An upstream-only comparison can accept a return of an old upstream failure after
integration has fixed it. `accept_regression.py` now requires both comparisons:
upstream preserves the original compatibility boundary, while the exact PR base
protects already accepted fixes and added tests. Missing/wrong-base evidence is
an error. `acceptance.json` records expected SHAs, report reuse and overall status;
`upstream-comparison.json` and `base-comparison.json` retain independent results.
The gate does not fetch a moving branch tip halfway through execution.

`review_base.py` records `test-inventory.json` and fails the job for deleted test
definitions before source overlays can hide them. Its source inventory reads
committed trees, not the working checkout. Scope tests cover the case where
upstream comparison passes but the fixed integration-base comparison fails.
