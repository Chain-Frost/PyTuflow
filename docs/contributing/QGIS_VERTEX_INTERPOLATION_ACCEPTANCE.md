# QGIS cell-to-vertex interpolation — work package 05/W10

Scope: [issue #9](https://github.com/Chain-Frost/PyTuflow/issues/9). This is the *second* independent reviewable geometry PR after [W9 cell positions](https://github.com/Chain-Frost/PyTuflow/pull/34).

## Provenance and dependency

The exact declared predecessor is `contrib/fix-qgis-cell-positions@a0806656eda615d911809851fe30f7f8b31f8d5e`, which itself is based on numerical PR #26 at `dc9ccded70c5ece73ba8d5b7fdc3e36c37a2f84e`. Both predecessors are separate internal PRs and are **not yet merged**. Do not independently merge this branch into integration and thereby bypass either predecessor. After squash merges, reconstruct successor branches from the resulting integration tree; no force-push on shared published history.

The selected historical reference is [phantom PR #32](https://github.com/phantom-branch/PyTuflow/pull/32), final merged source head `9a00988e1ee0fe2d714524c5c1cecaffbc5f402c`. The selected W10 production paths are `pytuflow/_outputs/pymesh/mesh_geom/qgismesh_geom.py` and `pytuflow/_outputs/pymesh/cell_data_mixin.py`. The previous W9 geometry blob and W8 cell data mixin matched the phantom PR #32 pre-fix implementations; the new files are selected without importing its CI and evidence archive.

## Defect, technical contract and independent expectations

Original QGIS geometry inherits `cell_to_vertex_weights()` as an unimplemented method. Its native MDAL mesh does not populate the base interpolation geometry arrays; consequently `NCMesh(..., driver="qgis geometry ...").surface(..., to_vertex=True)` fails even where face data and positions are valid.

The fix exposes an original-face, N×4 vertex mapping and normalized corner-angle weights, following existing PyNCMesh convention; triangle's padded fourth corner has a valid index with zero weight. It retains isolated vertices, respects native mesh order and maintains correct XYZ ordering for duplicate/reordered selectors. Per-result/time wet/validity masks must not be reused across data/time requests. NaN/masked cell values and incomplete vector components are excluded *jointly*. Valid zero is retained; a wet vertex with no valid contributions is NaN; a dry-only vertex has an inactive/zero placeholder. Scalar, two-component vector and temporal output shapes remain intact.

Provider-independent `tests/test_qgis_vertex_angle_math.py` exercises a mixed triangle/rectangle mesh. For values 3 and 9 at two faces with common vertex, corner angles `π/4` and `π/2` give weights `1/3, 2/3`, shared-vertex output `7`. Its expected output is `[3,7,3,9,9,9]`, plus an isolated dry vertex with zero placeholder. It checks zero triangle padding, changing wet state between frames, missing values, joint vector validity and shape errors. A separate genuine MDAL case tests a non-regular shared corner: weights `0.4149953542513913, 0.5850046457486088`; expected scalar `6.5100278744916515`.

## Test gates and limits

Fast/full host Windows Python 3.11/3.12/3.14 runs W8 numerical, W9 centroids and new W10 angle-contract tests plus the existing immutable-upstream/exact-predecessor comparison and installed-wheel checks.

Native QGIS/MDAL acceptance **must be executed anew on this Chain-Frost candidate** with `tests/test_qgis_cell_to_vertex_interpolation.py`, `tests/test_qgis_surface_cell_positions.py`, W8 provider and public-reader suites, and unchanged map-output/PyMesh suites. Historical phantom W10 acceptance (**19/19** native and **1,157/1,157** affected/analytical tests, QGIS 4.2.3) is reference evidence only; do not claim it was executed here. Compare the original public NotImplementedError and final face-to-vertex results for genuine 2DM/FV3D scalar/vector with independent expected values. No simulated QGIS, no silent skip or changed golden results. Record exact installed QGIS/Python/MDAL details, JUnit failures/skips and capability limits.

Classifications: two production files and two dedicated tests are **upstream candidates**; this issue handover and focused `.github/workflows/original-library-lane.yml` additions are **fork-only coordination/CI**, excluded from curated upstream by default. Do not change W8 numerical averages, W9 centroid algorithms, deferred execution, performance, unrelated geometry APIs or parser behaviour. No virtual environments, worktrees, merge, auto-merge, external PR or release.

## W10 integration successor (28 October 2026)

Original W10 provenance remains `a0806656eda615d911809851fe30f7f8b31f8d5e..fad1d49cb710901b0269b0be7a4231cd99880263` (PR #35). The historical predecessor status above describes that original stack. W8 and W9 are now accepted: W9 successor #42 was squash-merged as `f334cc71bdf36d2e7a93589a7bae092a2139fbc7`, the exact base of this new W10-only successor. Production and regression-test blobs are preserved from original W10; no W11 point delta is included. The original published branches remain unchanged. Fresh successor native and hosted acceptance is required before a manual protected squash; historical counts are not successor acceptance. The integration manager uses a dedicated worktree and external validation artifacts as explicitly authorized by the current task.
