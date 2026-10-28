"""Invalid named-location values: concrete dictionaries retain useful mypy checks.

Inherited untyped third-party geometry alternatives can weaken mypy's direct
inline-call checks. Pyright additionally detects the invalid inline arguments.
"""

# pyright: strict

from pytuflow import Grid, NCMesh


def reject_invalid_locations(grid: Grid, mesh: NCMesh) -> None:
    # Precise user-supplied dictionary annotations reject incorrect geometry.
    bad_points: dict[str, tuple[float, float]] = {"Bad point": 123}
    bad_lines: dict[str, list[tuple[float, float]]] = {"Bad line": [1, 2, 3]}
    bad_object: dict[str, tuple[float, float]] = {"Bad point": object()}

    mesh.time_series(bad_points, "water level")
    mesh.section(bad_lines, "flow", 1.0)
    grid.data_point(bad_object, "water level", 1.0)

    # Exercise the direct-call form as well; strict Pyright sees these mistakes,
    # while mypy currently loses precision through inherited geometry imports.
    mesh.time_series({"Bad point": 123}, "water level")
    mesh.section({"Bad line": [1, 2, 3]}, "flow", 1.0)
    grid.data_point({"Bad point": object()}, "water level", 1.0)
