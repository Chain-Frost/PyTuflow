# Custom 2D vector point extraction — issue #36

The **point-query-only** correction is stacked on QGIS cell-to-vertex [PR #35](https://github.com/Chain-Frost/PyTuflow/pull/35) exact head `fad1d49cb710901b0269b0be7a4231cd99880263`. [Issue #36](https://github.com/Chain-Frost/PyTuflow/issues/36) is in existing-library upstream contribution PR A; geometry/interpolation and deferred work are excluded. Original upstream: `cf908cc922ca8448ed6002834877b0b377329eae`.

## Source defect and contract

The public `PyMesh.data_point()` calls `CellDataMixin.data_point_from_cell_data()`. A QGIS 2D vector dataset yields one result array with **two vector components**. The old return expression tests `len(values)==1` and calls `float(...)`, which attempts to convert an entire component vector into a scalar and raises `TypeError: only 0-dimensional arrays can be converted to Python scalars`. The native QGIS 4.2.3 agent reproduced this for custom group `velocity2d` on W8/W9/W10, and reproduced it on phantom master `fa24498b`. Other extractors with two separate component datasets already return a tuple and remain unchanged.

The correction changes **only** that return/conversion block. Two separate component datasets keep the original tuple path. For one dataset, use `self.is_vector(data_type[0])` (actual extractor metadata) and normalise a point sample of shape `(2,)` or `(1,2)` to exactly two Python float components. Missing/masked components are represented as NaN, never the masked finite backing value, without modifying cached source arrays. Unexpected vector sample shape fails visibly. A scalar dataset still returns a scalar float. Existing cell-centred point returns remain component tuples even when `return_type='scalar'`, as established by the accepted library tests; no magnitude or default API change is made here.

## Focused expected-value checks

- `velocity2d` and `vector velocity`: `[3,4]` or `[[3,4]]` return `(3.0,4.0)`.
- Valid physical zero: `[0,4]` returns `(0.0,4.0)`.
- Missing component: `[3,NaN]` remains `(3.0,NaN)`; do not enforce joint missingness on **noninterpolated face point** results. A masked finite backing 99 returns NaN, not 99.
- Scalar `[7]`, `[0]`, `[NaN]`: scalar float unchanged.
- Inactive and out-of-mesh point: NaN unchanged without reading values.
- Separate `V_x,V_y` source: tuple unchanged.
- Real `netcdf4` FV-3D `velocity` averaging remains `(3,4)` and depth 0–1.5 salinity `40/3`. W8 numerical and W9/W10 geometry public test identities unchanged.

Portable tests `tests/test_cell_point_vector_corrections.py` exercise the public `PyMesh.data_point` dispatch with the extractor **boundary** simulated, plus a real NCMesh/netCDF4 3D averaging call. The first source commit is **tests-only** with an unchanged W10 implementation to preserve failure reproduction. Fast/full hosted CI runs these tests on Python 3.11/3.12/3.14 and retains original upstream/exact W10 predecessor and wheel comparisons.

## Native validation limitation

The hosted workflow is *not* a real-QGIS/MDAL provider. The QGIS-linked local agent **must** run the original custom `velocity2d` point fixture through `qgis geometry data extractor` on W10 and this candidate, compare native netCDF4/h5py, and run the combined existing W8/W9/W10 QGIS suites. Preserve physical scalar/vector component semantics and wet/dry/outside results. Record real native versions, exact SHAs, test IDs, JUnit and dependency/dll limitations. No claim of native acceptance until that run is performed.

Production `cell_data_mixin.py` and the essential regression tests are upstream candidates. Fork-specific CI/handover/metadata are excluded from the external upstream contribution. No solver, private fixture publication, force-push, merge, auto-merge, deferred work or release.
