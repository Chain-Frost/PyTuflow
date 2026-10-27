# QGIS cell-surface geometry — work package 05/W9

Tracker: [issue #9](https://github.com/Chain-Frost/PyTuflow/issues/9). Migration source: [phantom PR #26](https://github.com/phantom-branch/PyTuflow/pull/26).

## Scope and exact predecessor

This **first geometry correction** is independently reviewed on top of [numerical issue #8/PR #26](https://github.com/Chain-Frost/PyTuflow/pull/26) at `dc9ccded70c5ece73ba8d5b7fdc3e36c37a2f84e`. That predecessor has been reviewed and passed native QGIS numerical validation but is **not merged**; after upstream squash merging, restack on the new integration head without force-pushing. Its production/tests already match the prior numerical source. Current upstream source for this work: `phantom-branch/PyTuflow@fd151d50fef2dbe98c27382fa9ac82b35838b027` (W9 PR #26); exact selected implementation: `pytuflow/_outputs/pymesh/mesh_geom/qgismesh_geom.py`. W10 interpolation is separate.

## Actual defect and expected result

The original QGIS-backed geometry delegates `cell_position()` to a base method that raises `NotImplementedError`. Thus public `NCMesh(..., driver="qgis geometry ...").surface(..., to_vertex=False)` cannot return face positions even when result reduction succeeded. The correction obtains native QGIS/MDAL mesh-face centroids, preserving 3D bed Z where present, face ordering and independent returned arrays. It uses signed area instead of arithmetic mean of vertex coordinates.

Independent references for triangle `[[0,0,1],[2,0,2],[0,2,3]]`: centroid `(2/3,2/3,2)`. Irregular trapezoid `[[10,0,0],[14,0,0],[13,2,0],[10,2,0]]`: centroid `(10+37/21,20/21,0)`, not its vertex mean. Winding reversal and projected coordinate offsets preserve results. Degenerate/non-finite XY fails. Missing Z stays NaN. Tests check duplicate and sliced face positions, local/global coordinate transforms, cache non-aliasing, bounds and real 2D/FV-3D scalar/vector surfaces.

## Validation contract

Standalone host Windows Python 3.11/3.12/3.14 must run the provider-independent `tests/test_qgis_centroid_math.py` in addition to the original-library regression and installed-wheel checks. `tests/test_qgis_surface_cell_positions.py` imports *real* QGIS at collection and **must run only under a genuine initialized QGIS/MDAL runtime**. No fake provider or allowed skip. Native baseline must reproduce the original public `cell_position` error and candidate must pass provider cases; compare existing `tests/test_map_output.py`, `tests/test_map_output_pymesh.py`, numerical cases against immutable official upstream `cf908cc922ca8448ed6002834877b0b377329eae` and the exact PR base. A historical phantom report is reference evidence, not a new fork-run pass. Record JUnit, version/provenance, raw failures/skips and differences.

Source and focused tests are **upstream candidates**; this work-package note and `.github/workflows/original-library-lane.yml` extension are **fork process/CI** and should be omitted by default from external curation. No deferred execution, interpolation, numerical policy change, reference regeneration, venv/worktree, merge, release or external upstream PR.
