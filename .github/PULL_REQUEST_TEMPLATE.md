Describe the concrete problem, resulting behavior and why this scope belongs together.

## Base and dependencies

- Target: `contrib/integration` (or name the preceding stacked PR).
- Official upstream baseline and predecessor SHA:
- Work-package issue and verified dependencies:
- Production source/reference PRs and exact SHAs selected (no wholesale phantom merge):

## Validation

Record exact candidate and review-base SHAs, both baseline comparisons,
applicable hosted run links, raw inherited failures,
and any QGIS/native validation required by the change. A passing regression
comparison does not mean the inherited suite is failure-free.

For intentional output or test changes, follow the
[correction policy](https://github.com/Chain-Frost/PyTuflow/blob/contrib/integration/docs/contributing/INTENTIONAL_CORRECTIONS.md): identify the
old defect, independent expected-value evidence, affected test node IDs and
fixtures, and any old-to-new test mapping. Explain compatibility impact. Test
replacement requires explicit review and passing gates; no blanket exemptions.

## Upstream curation

Identify files/commits intended for upstream and fork-only infrastructure to omit.
State public API or compatibility impact and any prerequisite correctness PRs.
Classify each changed file as upstream implementation/test/docs or fork-only.
Record any Linux/QGIS evidence and the last upstream-curation rehearsal.
Leave auto-merge off; the owner decides when to merge.
