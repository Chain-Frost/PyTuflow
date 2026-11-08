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
policy change; follow the [intentional-correction policy](../docs/contributing/INTENTIONAL_CORRECTIONS.md).
There is no silent deletion allowlist. Static inventory cannot
prove assertion quality or parameter coverage in overlaid files: changes to
those helpers still require careful review.
No engineering reference data is changed. Raw failures remain failed in reports;
a green comparison means no new regressions, not that all tests passed.

Windows Python 3.11, 3.12 and 3.14 each run fast infrastructure contracts and
full original-library regression plus sdist-to-wheel installation checks.
Windows remains the acceptance baseline. Ubuntu runs inexpensive scope, grammar
and final-gate checks; Linux filename-case lanes retain their distinct filesystem
contract. A successful Linux job does not replace Windows or native QGIS evidence.
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
Both scope jobs now audit Python grammar before their Windows lanes start. Grammar
also runs before dependency installation in each reusable or focused lane.
The original quick and full workflows still execute independently.

## Iteration, cancellation and retained evidence

Push a locally checked batch at a review or validation milestone. Multiple local
commits can share one push; pushing each small correction separately starts more
hosted work. Required workflows continue to run for draft PRs. Do not use skip-CI
markers to obtain missing or misleading acceptance checks.

All focused workflows cancel older runs for the same workflow and PR, while
keeping other workflows and stacked PRs independent. Their matrices stop sibling
lanes after the first failure on the first PR attempt. Re-run all jobs on the
same head for exhaustive diagnostics: subsequent attempts do not fail fast.
This path works without adding fork workflows to the upstream-mirror `master`.
The original full comparison still gathers every required raw test outcome.

Focused lanes cache downloaded pip packages, not installed environments, source,
regression results or acceptance reports. Every job installs its declared
dependencies and every full lane reruns upstream, exact base and candidate.
Dependency declarations and the three Windows interpreter versions are unchanged.

Artifact retention is now:

| Evidence | Retention |
| --- | --- |
| Fast/full infrastructure contract reports | 14 days |
| Every interpreter's built wheel, provenance and complete smoke JSON | 14 days |
| Original regression raw JSON, JUnit, logs and comparison evidence | 21 days |
| Reference Python 3.12 source distribution and any failing lane's available sdist | 14 days |
| Focused pandas/TMF/raster evidence | 30 days |

Every full interpreter still builds an sdist and builds and tests its own wheel
from that sdist. Each provenance JSON records the source archive name and SHA-256.
Successful runs retain one source archive, from reference Python 3.12, instead
of storing three large archives for the same source revision. Each interpreter's
wheel and its validation evidence are retained separately. Failed lanes retain
their available source archive for diagnosis. `outside/` is only the isolated
working directory; the wheel is installed into the configured interpreter.
Download important contribution evidence before it expires. Previously uploaded
artifacts retain their original expiry; this change does not delete them.

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
