"""Issue #30: reproduce VTK / NumPy 2.5 conversion deprecation.

Use an existing Python interpreter; do not create an environment:
  python ci/diagnostics/vtk_numpy_compat.py

The optional negative control requires the *specific* inherited deprecation.
Different failures and an unexpected success both fail the control.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
import traceback
import warnings


SHAPE_DEPRECATION = "Setting the shape on a NumPy array has been deprecated in NumPy 2.5."


def version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "NOT INSTALLED"


def is_expected_shape_deprecation(error: BaseException) -> bool:
    """Accept only the observed NumPy 2.5 VTK array-shape deprecation."""
    return type(error) is DeprecationWarning and str(error).startswith(SHAPE_DEPRECATION)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expect-shape-deprecation",
        action="store_true",
        help="Require the known VTK 9.6.x / NumPy 2.5 warning as an exception",
    )
    args = parser.parse_args(argv)
    print(json.dumps({
        "python": sys.version, "executable": sys.executable,
        "expect_shape_deprecation": args.expect_shape_deprecation,
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
    except DeprecationWarning as error:
        # Preserve the full traceback, even in an expected negative control.
        # Warnings remain errors; only the exact observed cause is accepted.
        traceback.print_exc()
        if args.expect_shape_deprecation and is_expected_shape_deprecation(error):
            print("PASS: expected NumPy 2.5 / VTK 9.6.x shape deprecation reproduced")
            return 0
        print("FAIL: unexpected deprecation")
        return 1
    except Exception:
        traceback.print_exc()
        return 1
    if args.expect_shape_deprecation:
        print("FAIL: expected NumPy 2.5 / VTK 9.6.x deprecation did not occur")
        return 1
    print("PASS: no deprecation, expected values and dimensions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
