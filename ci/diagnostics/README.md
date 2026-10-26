# Native dependency diagnostics (fork-only)

For issues #30 (VTK/NumPy) and #31 (Windows QGIS/h5py). These files contain *probes only*, no fixes or test-exemptions. Exclude from the curated external upstream PR unless the maintainer requests the diagnostics.

## Run using an existing interpreter

For #30, run `python ci/diagnostics/vtk_numpy_compat.py` using (a) the affected NumPy 2.5.4 / VTK 9.6.1, (b) a supported NumPy 2.4.x control. Then separately execute the two failing native CATCHJson tests. Preserve full tracebacks and warning-as-error semantics.

For #31, use the **configured OSGeo4W QGIS Python** to run `python -X faulthandler ci/diagnostics/h5py_qgis_imports.py --out native-imports.json` in a real QGIS/MDAL-capable shell. Separate processes compare h5py-only, QGIS-only, both import orders and QGIS before PyTuflow import. Record raw errors and relevant DLL/module paths. Report contents may contain private local paths; sanitise before publication.

## Boundaries

Observed on a non-QGIS Linux control (Python 3.13.5, NumPy 2.3.5, VTK 9.6.2): VTK direct conversion passes; h5py-only passes while all four QGIS cases report missing QGIS. **These are not affected-platform acceptance results.**

Do not silence warning filters, replace OSGeo4W packages, or classify `0xc0000139` as harmless merely because an outer test process returned output. Reproduce against official upstream, exact base and candidate. Any verified fix needs separately reviewed code and full regression checks. See #3 and #20 for the acceptance programme.

## Hosted VTK version matrix

A separate non-required GitHub Actions workflow, `.github/workflows/native-vtk-numpy-diagnostic.yml`, runs a strict direct-conversion test under the following Windows Python 3.12 combinations: NumPy 2.4.6/VTK 9.6.1 (control), NumPy 2.5.4 with VTK 9.6.1, 9.6.2 and 9.7.1. It also runs NumPy 2.5.4 with VTK 9.6.1/9.7.1 on Linux. **Diagnostic failures are deliberately red** and their raw output is uploaded; a failing outdated VTK version does not mean a regression was introduced in PR #33. This isolated test is independent of the repository's required original-library compatibility gates. VTK 9.7 may change other APIs: do not update `pyproject.toml` or CI pins until public PyTuflow reader/geometry suites pass on the proposed version in native QGIS.

The matrix also checks `pv.PolyData(points, legacy_flat_faces)` and `vtkStaticCellLocator` on Windows/Linux for VTK 9.7.1 + NumPy 2.5.4 with both PyVista 0.48.2 and 0.49.1; see `pyvista_geometry_compat.py`. This is a focused geometry compatibility check, *not* a replacement for the native QGIS `CATCHJson` reader suites.
