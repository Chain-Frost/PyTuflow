# Upstream contribution stack

Tracking issue: [#3](https://github.com/Chain-Frost/PyTuflow/issues/3).
Bootstrap: [PR #1](https://github.com/Chain-Frost/PyTuflow/pull/1),
squash-merged into `contrib/integration` as `89a43fa5`.

Bootstrap is complete. Python >=3.11 is approved and matches APIs already used
in upstream. Create implementation PRs progressively from the updated
`contrib/integration` branch. Keep `master` as the official-upstream mirror
and integrate internal work separately.
External delivery is **three separately curated upstream PRs**: A fixes,
B public typing, and C opt-in deferred inputs and validation. Internal work packages
remain independently reviewable and continue integrating into
`contrib/integration`. This plan authorises no external submission.

## Three upstream deliverables

| Delivery | Internal packages | Scope | Candidate branch |
| --- | --- | --- | --- |
| **PR A — existing-library fixes and improvements** | 00F, 01–07, 08A, 08B, 09 (exclude 08C) | FM/TMF, results, pandas, numerical/QGIS, cache and save correctness; packaging/import/logging, public API compatibility tests and eager Linux `-cs` handling | `contrib/upstream-fixes` |
| **PR B — public typing and static contracts** | 08C / [#14](https://github.com/Chain-Frost/PyTuflow/issues/14) | Narrowly scoped `py.typed`, `.pyi`, stable existing-library annotations, static/installed-wheel consumer tests, typing documentation | `contrib/upstream-typing` |
| **PR C — deferred input validation** | 10–11 and 14; 12–13 superseded, 15 optional | Opt-in deferred references, immutable fragments, ordered batch provenance, read-only GIS/BC/GPKG input checking, Linux filename parity and inline typing for **new deferred modules** | `contrib/upstream-deferred` |

PR A delivers the corrected existing *eager* library, retaining defaults except
independently justified bug fixes. PR B delivers static typing contracts for
existing public APIs, **without changing runtime behaviour**. PR C adds the
optional deferred fragment/batch-validation pathway with eager still the default. Existing
minor annotations required to implement a real correction in A need not be
artificially extracted into B. Do **not** transfer the legacy `ResData`
typing stub or optional `py.typed` marker with A, and do **not** place typing
for modules first introduced by C in B.

**Dependencies:** PR A comes first. B and C each depend on the *accepted A
baseline* for their external submission; **C does not technically depend on
B** and may be developed/tested internally alongside B once its actual
implementation prerequisites are satisfied. Do not artificially chain C
behind `py.typed`/legacy-stub work. B and C are independently reviewed. For
external submission, curate each branch against the *actual merged upstream A*
and the latest relevant official upstream head. If B lands first, update C
onto that actual head; if C lands first, update B likewise. In either order,
the later PR must not repeat changes from earlier PRs. Do not create a
cumulative B+C diff or assume a future upstream merge order.

**Compatibility:** Public imports, identities, defaults and behaviour remain
protected in A by issue #13's API contract tests. Broad export narrowing,
breaking annotation claims or removing deprecated `ResData` is not implied by
the separate typing PR. Any deliberate compatibility break needs a separately
reviewed owner/maintainer decision and migration guidance. Typing/API changes
needed solely by deferred execution belong in C even if they touch an inherited
module. All three targets support Python **3.11 minimum**, with independent
3.11/3.12/3.14 validation.

Native environment diagnostics [#30](https://github.com/Chain-Frost/PyTuflow/issues/30)
and [#31](https://github.com/Chain-Frost/PyTuflow/issues/31) require a
documented disposition where relevant for A; revisit them for B or C if the
chosen changes affect native imports/providers. External library failures
must not be attributed to a PR without evidence and do not create a fourth
upstream delivery.

### Submission and branch policy

1. Continue small independently validated **internal** PRs into
   `contrib/integration` using reviewed, manually squash-merged changes.
   A/B/C are **external** curation scopes, not changes to existing internal
   PR branches, tests, ownership or integration cadence.
2. Reconstruct A from the **latest official upstream** plus only reviewed A
   production corrections, necessary regression tests and relevant user docs.
   Exclude fork-only workflows, internal records, independent typing work and
   any deferred/batch-validation changes. Run A's own full Windows
   3.11/3.12/3.14, Linux eager, installed-wheel, engineering-reference and
   affected real QGIS/MDAL acceptance before its authorised submission.
3. Reconstruct B from A's **actual accepted upstream result**, not from the
   unaccepted aggregate integration branch. Include only reviewed focused
   public typing changes, a coherent `py.typed`/legacy `.pyi` surface,
   typing tests and necessary consumer docs. Verify stub/runtime consistency,
   mypy/Pyright and `stubtest` where applicable, installed-wheel consumers
   on Python 3.11/3.12/3.14 and the ordinary regression gates. Retain raw
   inherited typing failures without hiding them.
4. Continue C internally against accepted eager policy (#15), deferred
   references (#16) and ordered ownership (#17); general compiled-graph
   work #18/#19 was superseded and is **not** a prerequisite. PR C may
   continue independent of B's acceptance.
   Rebuild the external C candidate on the then-current **actual upstream
   A baseline** (and already merged B if applicable), with *only* deferred,
   immutable fragment/batch validation, justified optimisations and inline
   types for newly added modules. Run cross-platform eager/deferred/batch parity, installed-wheel
   and native provider tests before C submission.
5. If B and C are developed while A is in upstream review, neither may be
   submitted with A's unmerged fixes duplicated in its diff. After either B
   or C lands upstream, rebase/reconstruct the other onto that real head and
   repeat exact-head acceptance. Neither follows the other as a functional
   prerequisite.
6. No force pushes on protected/shared branches, auto-merge, releases or
   external upstream PRs without separate explicit authorisation.

Work package 14 / [#20](https://github.com/Chain-Frost/PyTuflow/issues/20)
remains **PR C's** comprehensive final deferred acceptance gate. A and B have
independent sign-off; unfinished deferred functionality must not hold either
A or B. Optional stage 15 remains deferred-related unless a separate
eager-only improvement is justified for A.

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
| 12 | [General graph compiler — superseded](https://github.com/Chain-Frost/PyTuflow/issues/18) | Closed, not required for PR C |
| 13 | [Mutable graph/prototype reuse — superseded](https://github.com/Chain-Frost/PyTuflow/issues/19) | Closed, not required for PR C |
| 14 | [Complete cross-platform and curated-branch acceptance](https://github.com/Chain-Frost/PyTuflow/issues/20) | [09](https://github.com/Chain-Frost/PyTuflow/issues/15), [10](https://github.com/Chain-Frost/PyTuflow/issues/16), [11](https://github.com/Chain-Frost/PyTuflow/issues/17); includes native QGIS/MDAL and 756-run parity |
| 15 | [Optional additional performance work](https://github.com/Chain-Frost/PyTuflow/issues/21) | Not required for PR C |

All rows begin with source-diff inspection. The selected Phantom MVP is now
merged in [#47](https://github.com/phantom-branch/PyTuflow/pull/47), including
obsolete graph cleanup [#48](https://github.com/phantom-branch/PyTuflow/pull/48). Recheck
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

The required implementation path is 10 -> 11, followed by 14's independent
**PR C** acceptance. Stages 12/13 are superseded, not dependencies. Preserve
real Linux/Windows case-policy, provider, eager/deferred and batch parity. Stage 15 is optional and cannot block a correct core contribution.

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
implementation #16→#17 follows accepted eager Linux case policy (#15);
closed graph issues #18/#19 must not be reintroduced as dependencies. No requirement to finish all PR A work before independent **PR C deferred**
design/research, but do not submit C until an accepted A baseline exists;
keep production implementations and external submission scopes separate. Squash changes ancestry: follow the
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
- Rehearse **PR B (typing)** only against stable existing public APIs;
  reconstruct it from the actual accepted upstream A result. Confirm B's
  diff contains only typing declarations, tests and user-facing type docs,
  without unrelated runtime changes.
- Rehearse **PR C (deferred)** at each feature milestone, first on the
  compatible internal fixes baseline. Reconstruct external C after upstream
  has merged A, plus B only if already accepted. Prove C includes only
  deferred references, immutable fragments, input validation and inline typing
  for *new deferred modules*. Neither rehearsal authorises external submission.
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
The minimum supported Python version is 3.11. This plan targets exactly three
external PRs (A fixes, B public typing, C deferred), each requiring separate
final review/authorisation. No release
or external upstream PR is authorised by this planning update.
