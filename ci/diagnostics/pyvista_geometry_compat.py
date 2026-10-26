"""Issue #30: check the exact PyVista/VTK geometry path used by PyTuflow.

Use Python 3.12+ with specified external dependency versions.
All DeprecationWarnings become failures; do not mute library warnings.
"""
from __future__ import annotations

import importlib.metadata
import json
import sys
import traceback
import warnings


def main() -> int:
    names = ("numpy", "vtk", "pyvista")
    print(json.dumps({
        "python": sys.version, "executable": sys.executable,
        "versions": {name: importlib.metadata.version(name) for name in names},
    }, indent=2), flush=True)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            import numpy as np
            import pyvista as pv
            import vtk

            points = np.array(
                [[0., 0., 0.], [1., 0., 0.], [1., 1., 0.],
                 [0., 1., 0.], [2., 1., 0.]], dtype=float,
            )
            # The same legacy flat-face representation PyTuflow passes to
            # pv.PolyData: one triangle plus one quad.
            faces = np.array([3, 0, 1, 3, 4, 1, 2, 4, 3], dtype=np.int64)
            mesh = pv.PolyData(points, faces)
            if mesh.n_points != 5 or mesh.n_cells != 2:
                raise AssertionError(
                    f"wrong geometry sizes: {mesh.n_points} points, {mesh.n_cells} cells"
                )
            if not np.array_equal(np.asarray(mesh.faces), faces):
                raise AssertionError("PyVista changed the face connectivity/order")
            if not np.array_equal(np.asarray(mesh.points), points):
                raise AssertionError("PyVista changed the coordinates")

            locator = vtk.vtkStaticCellLocator()
            locator.SetDataSet(mesh)
            locator.BuildLocator()
            if locator.GetDataSet().GetNumberOfCells() != 2:
                raise AssertionError("VTK cell locator lost geometry")
    except Exception:
        traceback.print_exc()
        return 1
    print("PASS: mixed faces, coordinates, and native VTK geometry locator")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
