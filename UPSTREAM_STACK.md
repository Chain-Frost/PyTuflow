# Upstream contribution stack

Tracking issue: [#3](https://github.com/Chain-Frost/PyTuflow/issues/3).
Bootstrap: [PR #1](https://github.com/Chain-Frost/PyTuflow/pull/1).

Plan all work now; create implementation PRs progressively after bootstrap is
reviewed and merged with owner authorization. Python >=3.11 is settled. Keep
master as the official-upstream mirror and integrate internal work separately.
The intended external delivery is one curated PR with logical reviewable commits;
confirm its scope with the maintainer before creating it. No external PR is
created or authorized by this plan.

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

All rows begin with source-diff inspection. Open phantom PRs #4 and #39 are
unfinished; their recorded heads are provisional references, not accepted inputs.
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

## First implementation wave

After bootstrap review and an authorized merge, start a small wave: 01 (TMF),
02 (time correctness), and 07 (safe saves/ownership). They have no assumed
inter-package prerequisites; still record exact touched files and coordinate
actual overlap. 00F, 04 and 08A can start as capacity allows after the same
preflight. Keep broad typing work away from modules undergoing feature edits.
No agents or implementation branches are launched by this planning change.

Open a draft PR when implementation begins, link its issue and exact predecessor,
and keep auto-merge off. Branch dependent work once its parent implementation is
stable. Squash changes ancestry: follow BOOTSTRAP.md's restacking instructions
and never force-push published shared history.

## Acceptance and upstream curation

- Record upstream, exact target/base, selected source and candidate SHAs.
- Pass both upstream and review-base comparisons. Preserve tests and accepted
  fixes; inherited failures are not permission to reintroduce them.
- Numerical/geometry fixes need independent expected values. Do not regenerate
  references to manufacture agreement.
- Classify every changed file/commit as upstream production, essential regression
  test, user documentation, or fork-only process/CI/evidence. Fork-only material
  is omitted by default from the external branch.
- After the correctness wave and each deferred milestone, rehearse reconstruction
  from pinned official upstream in a disposable checkout. Run applicable tests
  and record selected commits, omissions, prerequisites and API impact. Do not
  publish an external PR during rehearsal.
- Recheck upstream before final curation; any intended behavior change needs
  explicit review. Use one clear rationale per logical upstream commit, without
  importing the fork's administrative merge history.
- Before performance work, define the measurement protocol and useful improvement
  threshold. Preserve correctness parity and unsuccessful trial results.

## Status ownership

Issues hold live implementation status and PR links; this file holds stable
scope and ordering rules. Update dependencies when actual code proves them.
The source inventory is dated; refresh it when implementation starts.
Bootstrap remains unmerged until reviewed and explicitly authorized. No release,
external upstream PR or production transfer is part of this scaffolding.
