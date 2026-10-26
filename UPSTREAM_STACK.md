# Upstream contribution stack

Tracking issue: [#3](https://github.com/Chain-Frost/PyTuflow/issues/3).
Bootstrap: [PR #1](https://github.com/Chain-Frost/PyTuflow/pull/1),
squash-merged into `contrib/integration` as `89a43fa5`.

Bootstrap is complete. Python >=3.11 is approved and matches APIs already used
in upstream. Create implementation PRs progressively from the updated
`contrib/integration` branch. Keep `master` as the official-upstream mirror
and integrate internal work separately.
External delivery is **two separate upstream PRs**, not one consolidated PR:
first existing-library fixes/improvements, then optional deferred/batch/graph
execution. Internal package PRs remain independently reviewable. Neither
external PR is created or authorised by this plan.

## Two upstream deliverables

| Delivery | Internal work packages | Scope | Proposed export branch |
| --- | --- | --- | --- |
| **Upstream PR A — correctness and improvements** | 00F, 01–09, including 08A/08B/08C | Inherited FM/TMF defects; output/numerical/QGIS corrections; pandas/NetCDF, safe saves, package/import/logging/API/typing improvements; eager Linux `-cs` policy; verified non-deferred fixes | `contrib/upstream-fixes` |
| **Upstream PR B — deferred execution and related architecture** | 10–15 | Optional deferred file references, ordered batch dependencies, compiled graphs, conservative cross-run reuse, deferred Linux parity and strictly justified deferred-related performance | `contrib/upstream-deferred` |

PR A is the **complete existing-functionality improvement contribution**, with
the eager parser still the only execution mode. PR B adds the **optional**
deferred execution pathway and preserves eager as the default. Any non-deferred
bug found during development of PR B should normally be fixed and validated
in PR A before PR A is finalised; once PR A is merged upstream, avoid silently
folding unrelated fixes into PR B. If additional unexpected defects are found
after that point, record them and obtain a scope decision rather than expanding
PR B without review.

Classify changes by purpose, not just their module or source PR. API changes,
typing and optimisations needed only by deferred execution belong in PR B even
when they touch existing modules. PR A preserves existing defaults except for
independently justified, documented bug fixes; any deliberate compatibility
break needs an explicit scope decision and migration guidance.

ENV-A [#30](https://github.com/Chain-Frost/PyTuflow/issues/30) and ENV-B
[#31](https://github.com/Chain-Frost/PyTuflow/issues/31) are parallel native
runtime diagnostics. Include proven PyTUFLOW fixes in PR A if applicable;
external environment issues should be documented, not falsely attributed
to a candidate regression. Unresolved relevant native limitations require
an explicit acceptance decision. They do not automatically create a third
upstream PR.

### Submission and branch policy

1. Continue using small **internal** PRs into `contrib/integration` with manual
   squash merges and review/CI evidence.
2. Reconstruct `contrib/upstream-fixes` from the **latest official upstream**
   head plus only reviewed PR A production fixes, essential regression tests
   and appropriate user-facing documentation. Exclude fork-only CI,
   coordination records, internal evidence and deferred features.
3. Validate PR A independently on Windows Python 3.11/3.12/3.14, Linux eager
   path semantics, installed wheels and native QGIS/MDAL where affected.
   Submit **upstream PR A first**, with a maintainable series of logical commits.
4. Develop PR B internally against the accepted fixes baseline when safe, but
   **do not open upstream PR B with PR A's changes in its diff**. Once PR A is
   accepted/merged upstream, rebuild/rebase PR B onto that actual upstream
   result, test eager/deferred/batch parity and submit the **second** upstream PR.
   If PR A has not landed, keep PR B's upstream submission pending.
5. Do not force-push protected/shared branches, enable auto-merge, publish a
   release or open either external PR without explicit authorisation.

The final acceptance in work package 14 is **PR B's** cross-platform deferred
gate. PR A has its own standalone release/curation acceptance, including
all relevant existing-library tests, reference-change justifications and
native environment outcomes. Do not hold PR A merely because PR B's
architecture or performance work is unfinished. Optional stage 15 is
deferred-related unless an independently justified eager-only optimisation
is expressly included in PR A.

## Work packages

Numbers identify scope, not automatic merge order or one PR per package.
There are 18 packages: the original 15, the package/API/typing split adds two,
and the inherited FM mismatch adds one. Issues record exact source heads,
merge SHAs, owned areas, acceptance requirements and exclusions.

| Package | Scope / issue | Planned contract prerequisites |
| --- | --- | --- |
| 00F | [Investigate inherited Flood Relief Arch reference mismatch](https://github.com/Chain-Frost/PyTuflow/issues/4) | Bootstrap; verify extraction prerequisites |
| 01 | [Correct TMF rainfall, GIS inventory and material parsing](https://github.com/Chain-Frost/PyTuflow/issues/5) | Bootstrap; verify extraction prerequisites |
| 02 | [Correct result timestep selection and NetCDF time units](https://github.com/Chain-Frost/PyTuflow/issues/6) | Bootstrap; verify extraction prerequisites |
| 03 | [Restore pandas result-reader compatibility](https://github.com/Chain-Frost/PyTuflow/issues/7) | Bootstrap; verify extraction prerequisites |
| 04 | [Correct FV averaging and numerical reductions](https://github.com/Chain-Frost/PyTuflow/issues/8) | Bootstrap; verify extraction prerequisites |
| 05 | [Correct QGIS geometry and interpolation](https://github.com/Chain-Frost/PyTuflow/issues/9) | Bootstrap; verify extraction prerequisites |
| 06 | [Bound raster caches and recover NetCDF readers](https://github.com/Chain-Frost/PyTuflow/issues/10) | Bootstrap; verify extraction prerequisites |
| 07 | [Make model saves recoverable and preserve input ownership](https://github.com/Chain-Frost/PyTuflow/issues/11) | Bootstrap; verify extraction prerequisites |
| 08A | [Harden package imports and installed resources](https://github.com/Chain-Frost/PyTuflow/issues/12) | Bootstrap; verify extraction prerequisites |
| 08B | [Review public API contracts and changes](https://github.com/Chain-Frost/PyTuflow/issues/13) | Bootstrap; verify extraction prerequisites |
| 08C | [Add focused typing after affected APIs stabilize](https://github.com/Chain-Frost/PyTuflow/issues/14) | [08A](https://github.com/Chain-Frost/PyTuflow/issues/12), [08B](https://github.com/Chain-Frost/PyTuflow/issues/13) |
| 09 | [Establish Linux filename case-resolution policy](https://github.com/Chain-Frost/PyTuflow/issues/15) | Bootstrap; verify extraction prerequisites |
| 10 | [Introduce optional deferred file resolution](https://github.com/Chain-Frost/PyTuflow/issues/16) | [09](https://github.com/Chain-Frost/PyTuflow/issues/15) |
| 11 | [Add ordered batch dependency indexing](https://github.com/Chain-Frost/PyTuflow/issues/17) | [10](https://github.com/Chain-Frost/PyTuflow/issues/16) |
| 12 | [Compile and validate shared dependency graphs](https://github.com/Chain-Frost/PyTuflow/issues/18) | [11](https://github.com/Chain-Frost/PyTuflow/issues/17) |
| 13 | [Add conservative invariant graph reuse](https://github.com/Chain-Frost/PyTuflow/issues/19) | [12](https://github.com/Chain-Frost/PyTuflow/issues/18) |
| 14 | [Complete cross-platform and curated-branch acceptance](https://github.com/Chain-Frost/PyTuflow/issues/20) | [09](https://github.com/Chain-Frost/PyTuflow/issues/15), [10](https://github.com/Chain-Frost/PyTuflow/issues/16), [11](https://github.com/Chain-Frost/PyTuflow/issues/17), [12](https://github.com/Chain-Frost/PyTuflow/issues/18), [13](https://github.com/Chain-Frost/PyTuflow/issues/19) |
| 15 | [Evaluate optional additional performance work](https://github.com/Chain-Frost/PyTuflow/issues/21) | [13](https://github.com/Chain-Frost/PyTuflow/issues/19), [14](https://github.com/Chain-Frost/PyTuflow/issues/20) |

All rows begin with source-diff inspection. Phantom PR #4 has merged (merge
commit `fa24498b`); phantom PR #39 remains open and provisional. Recheck
source revisions and review findings before selecting changes.
See [the inspected source inventory](docs/contributing/migration-sources.json).
Do not import an entire historical PR just because it is listed here.

## Dependency evidence and coordination

The suggested arrows below are not confirmed code prerequisites. Changed-file
inventories establish coordination needs; implementation must establish semantic
prerequisites before stacking branches.

| Suggested dependency | Inspected evidence | Planning decision |
| --- | --- | --- |
| 03 needs 02 | #16/#30 share grid.py and map_output.py | Coordinate edits; independent until code proves otherwise |
| 06 needs 03 | #30/#20 share grid.py | Coordinate edits; no automatic hard dependency |
| 05 needs 04 | #23/#26 share no production files; #23/#32 share cell_data_mixin.py | Assess the two QGIS corrections separately |
| 09 needs 01 | #27/#4 share no production files | Verify parser semantics; historical order is insufficient |
| 07 combines #17/#18 | Both modify cf_build_state.py | One ownership area; split coherent fixes if useful |

The 10 -> 11 -> 12 -> 13 chain expresses intended API/ownership contracts and
must be confirmed during extraction. Stage 14 is final consolidated acceptance;
Linux tests accompany stage 09 and every deferred/batch/graph stage from the
start. Stage 15 is optional and cannot block a correct core contribution.

## Internal implementation, integration and merge cadence

The first wave (01 / 02 / 07) and follow-up independent workstreams
(00F / 04 / 08A / 09) already have implementation PRs; use their issue/PR
threads for live status. Continue branching independent corrections from the
latest `contrib/integration`, confirm touched-file ownership and keep broad
typing work away from modules undergoing changes. This document does not
itself authorise agent assignments, merges or new implementation branches.

Open a draft internal PR when implementation begins, link its issue and exact
predecessor, and keep auto-merge off. **Prefer integrating the small validated
fixes before opening more overlapping PRs:** consider #28 (reference and test),
then #23 (time), #27 (package), and #26 (FV numerical) after exact-head review,
applicable native tests and both required CI gates. These are review priorities,
not a hard dependency ordering: another independent fix, including #25 (TMF),
can integrate when ready. Read current checks and review threads rather than
using a historical green/red list in this document. Resolve failed acceptance
and substantive review findings before merging any candidate.
Never merge red CI or use the fast gate alone as acceptance. No merge is
authorised by this planning document.

After each internal squash merge, every remaining PR must satisfy the strict
up-to-date rule before its own merge, even if its files do not overlap. Refresh
the branch and exact review-base evidence, rerun applicable checks and review
conflicts; old green checks are insufficient for a changed base. For an existing
independent published branch, merge current integration into it and push normally
to preserve the PR and shared history. For a published dependent stack whose
parent was squash-merged, follow BOOTSTRAP.md's successor-branch guidance when
ancestry needs rebuilding. Do not force-push or weaken branch protection.
Issue #7 (pandas readers) overlaps #23; issue #9 (QGIS geometry) overlaps
#26; issue #10 (raster recovery) overlaps #7/#23. Start those implementations
only with coordinated file ownership and a stable predecessor. The deferred
chain #16→#17→#18→#19 must not enter integration before the accepted eager
Linux policy (#15). No requirement to finish all PR A work before undertaking
independent PR B design/research, but keep production implementations and
upstream submission scopes separate. Squash changes ancestry: follow the
repository's restacking guidance and never force-push shared history.

## Acceptance and upstream curation

- Record upstream, exact target/base, selected source and candidate SHAs.
- Pass both upstream and review-base comparisons. Preserve tests and accepted
  fixes; inherited failures are not permission to reintroduce them.
- Numerical/geometry fixes need independent expected values. Do not regenerate
  references to manufacture agreement.
- Follow the [intentional-correction policy](docs/contributing/INTENTIONAL_CORRECTIONS.md)
  for changed outputs, fixtures or test identities; review cannot bypass CI.
- Classify every changed file/commit as upstream production, essential regression
  test, user documentation, or fork-only process/CI/evidence. Fork-only material
  is omitted by default from the external branch.
- Rehearse **PR A** reconstruction from current official upstream after the
  existing-functionality work converges. Record selected fixes and excluded
  fork-only material; independently test the curated result.
- Rehearse **PR B** reconstruction at each deferred milestone, initially on
  the accepted PR A integration baseline. Before external submission rebuild
  from PR A's actual merged upstream result and independently verify that
  the PR B diff contains only deferred/batch/graph-related changes. Do not
  publish an external PR during rehearsal.
- Recheck upstream before **each** external PR; intentional behaviour changes
  need explicit review. Use one rationale per logical upstream commit without
  importing the fork's administrative merge history.
- Before performance work, define the measurement protocol and useful improvement
  threshold. Preserve correctness parity and unsuccessful trial results.

## Status ownership

Issues hold live implementation status and PR links; this file holds stable
scope and ordering rules. Update dependencies when actual code proves them.
The source inventory is dated; refresh it when implementation starts.
Bootstrap PR #1 was squash-merged into `contrib/integration` as `89a43fa5`.
The minimum supported Python version is 3.11. This plan targets exactly two
external PRs, both requiring separate final review/authorisation. No release
or external upstream PR is authorised by this planning update.
