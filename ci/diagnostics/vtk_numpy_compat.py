"""Issue #30: reproduce VTK / NumPy 2.5 conversion deprecation.

Use an existing Python interpreter; do not create an environment:
  python ci/diagnostics/vtk_numpy_compat.py
"""
from __future__ import annotations

import importlib.metadata
import json
import sys
import traceback
import warnings


def version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "NOT INSTALLED"


def main() -> int:
    print(json.dumps({
        "python": sys.version, "executable": sys.executable,
        **{name: version(name) for name in ("numpy", "vtk", "pyvista")},
    }, indent=2), flush=True)
    try:
        import numpy as np
        from vtkmodules.vtkCommonCore import vtkFloatArray
        from vtkmodules.util.numpy_support import vtk_to_numpy

        data = vtkFloatArray()
        data.SetNumberOfComponents(2)
        data.InsertNextTuple2(1.0, 2.0)
        data.InsertNextTuple2(3.0, 4.0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            result = vtk_to_numpy(data)
        if result.shape != (2, 2) or not np.array_equal(
            result, [[1.0, 2.0], [3.0, 4.0]]
        ):
            print("FAIL: unexpected VTK conversion values/shape")
            return 1
    except Exception:
        traceback.print_exc()
        return 1
    print("PASS: no deprecation, expected values and dimensions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
