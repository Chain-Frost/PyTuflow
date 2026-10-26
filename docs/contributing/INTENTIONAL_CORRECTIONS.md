# Intentional output corrections and test replacements

A correctness PR may deliberately change an incorrect output. The regression
gate already permits an inherited failure to become a pass and does not compare
every output byte between revisions. Passing comparisons alone cannot establish
that new expected values are correct.

For an intentional correction, include the following evidence in the PR:

1. Reproduce the old defect on the exact review-base SHA. Identify affected test
   node IDs, inputs and observed output, retaining the original failure evidence.
2. Justify the corrected expectation independently: cite an applicable documented
   contract, an analytical calculation or a verified reference implementation and
   its version. Candidate-generated output alone is not an oracle. Explain any
   numerical tolerance and public API or compatibility impact.
3. Make focused production, test and fixture changes together. List each changed
   expected value or fixture and why it changes; show the regression test exposes
   the old defect and passes with the correction. Preserve unrelated coverage.
4. Record exact candidate/base/source SHAs and applicable test results, including
   both upstream and review-base comparisons. Retain raw failures and limitations.

Do not blanket-exempt a suite, suppress a failure, weaken assertions or regenerate
golden files merely to obtain green checks. Keep the immutable upstream baseline
and comparison requirements intact. Shared FM overlays run on every revision, so
changes there also need explicit evidence that the old defect remains observable
and that assertions and parameter coverage have not been lost.

## Replacing or restructuring tests

The committed test inventory rejects removed or renamed test definitions; runtime
comparison also rejects removed collected cases. A legitimate rename or parameter
restructure can therefore fail CI even when its replacement is better.

Prefer preserving existing test identities while strengthening their assertions
or adding focused cases. When replacement is necessary, explain why and provide
an explicit old-to-new mapping of test node IDs, parameter cases and assertions,
including proof that the replacement still detects the original defect. Request
review of this evidence in the PR. Review approval alone does not override CI.

If existing gates cannot represent the justified replacement, stop that change
from merging until a narrowly scoped handling mechanism has itself been reviewed,
implemented and tested for missing evidence, lost coverage and unintended
exceptions. This policy supplies no deletion allowlist or generic gate bypass.
Do not disable required checks or change reference results to hide the conflict.
