# Native dependency diagnostics (fork-only)

Completed native findings and the exact supported add-on profile are in
[Native environment acceptance](../../docs/contributing/NATIVE_ENVIRONMENT_ACCEPTANCE.md).
Historical limitations below describe the earlier diagnostic checkpoints.

For issues #30 (VTK/NumPy) and #31 (Windows QGIS/h5py). These files contain diagnostics, no production fixes or test-exemptions. Exclude from the curated external upstream PR unless the maintainer requests the diagnostics.

## Run using an existing interpreter

For #30, run `python ci/diagnostics/vtk_numpy_compat.py` using (a) the affected NumPy 2.5.4 / VTK 9.6.1, (b) a supported NumPy 2.4.x control. Then separately execute the two failing native CATCHJson tests. Preserve full tracebacks and warning-as-error semantics.

For #31, use the **configured OSGeo4W QGIS Python** to run `python -X faulthandler ci/diagnostics/h5py_qgis_imports.py --out native-imports.json` in a real QGIS/MDAL-capable shell. Separate processes compare h5py-only, QGIS-only, both import orders and QGIS before PyTuflow import. Record raw errors and relevant DLL/module paths. Report contents may contain private local paths; sanitise before publication.

## Boundaries

Observed on a non-QGIS Linux control (Python 3.13.5, NumPy 2.3.5, VTK 9.6.2): VTK direct conversion passes; h5py-only passes while all four QGIS cases report missing QGIS. **These are not affected-platform acceptance results.**

Do not silence warning filters, replace OSGeo4W packages, or classify `0xc0000139` as harmless merely because an outer test process returned output. Reproduce against official upstream, exact base and candidate. Any verified fix needs separately reviewed code and full regression checks. See #3 and #20 for the acceptance programme.

## Hosted VTK version matrix

A separate GitHub Actions workflow, `.github/workflows/native-vtk-numpy-diagnostic.yml`, runs strict direct-conversion tests under the following Windows Python 3.12 combinations: NumPy 2.4.6/VTK 9.6.1 (passing control), NumPy 2.5.4 with VTK 9.6.1, 9.6.2 and 9.7.1. It also runs NumPy 2.5.4 with VTK 9.6.1/9.7.1 on Linux. The known-broken VTK 9.6.x/NumPy 2.5 jobs use `--expect-shape-deprecation`: they **require the exact observed warning as an exception**, preserve its raw traceback and fail if the warning disappears or another failure occurs. The supported pair must convert correct values/shapes with warnings-as-errors. A green diagnostic matrix therefore means all **specified positive and negative expectations** held, not that the incompatible old versions are safe. The tests are independent of the required original-library gates. Preserve pinned project dependencies until native QGIS/public reader acceptance is established.

The PyVista geometry matrix now tests two **installable**, matched stacks on both Windows and Linux: the original control (PyVista 0.48.2 / VTK 9.6.1 / NumPy 2.4.6), and the verified upgrade (PyVista 0.49.1 / VTK 9.7.1 / NumPy 2.5.4). PyVista 0.48.2 explicitly requires `vtk<9.7`; the previous PyVista 0.48.2 + VTK 9.7.1 job could only fail dependency resolution before exercising geometry. Both valid pairs check `pv.PolyData(points, legacy_flat_faces)` and `vtkStaticCellLocator` with unsuppressed DeprecationWarnings. This is a focused geometry compatibility check, *not* a replacement for native QGIS `CATCHJson` tests.

Finally, `pytuflow_public_readers` in the separate diagnostic workflow upgrades a *hosted test interpreter* from the committed regression environment to NumPy 2.5.4 / VTK 9.7.1 / PyVista 0.49.1 and runs the unchanged `tests/test_map_output_pymesh.py` against the package import from the source checkout. All 110 public non-QGIS reader tests must pass without warning suppression for this narrow test to be accepted. This does not exercise the separate native QGIS-only `tests/test_map_output.py` tests or Windows OSGeo4W DLL loading; retain those limitations.

**Rasterio follow-up:** The first hosted public-reader run with NumPy 2.5.4 / VTK 9.7.1 / PyVista 0.49.1 and regression-pinned Rasterio 1.5.0 returned 108 passed and two Grid tests failing at `rasterio/_io.pyx:660` on NumPy's shape-assignment deprecation. Rasterio upstream issue #3592 documents this and fixed it in release 1.5.1; the next experiment also upgrades Rasterio to 1.5.2. This is an external dependency migration candidate, not accepted PyTuflow production code.

`native-h5py-windows-control.yml` tests the instrumentation in Windows-hosted CPython 3.12 with NumPy 2.5.4 and h5py 3.16.0 **without QGIS/OSGeo4W**; a pass only rules out a generic h5py-only import failure in that interpreter and is not a resolution of issue #31. The native QGIS run must examine `dlls_already_loaded` (before import) versus `dlls` (after import) and on exceptions `dlls_at_failure`. Reproduction of 0xc0000139 is still required on a real OSGeo4W host.
