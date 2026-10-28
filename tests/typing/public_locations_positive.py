"""Static-only consumers for named point and line result-extraction locations.

Run under strict mypy and Pyright against the separately installed PyTUFLOW wheel.
Do not execute these examples: readers are supplied, not constructed.
"""

# pyright: strict

from pytuflow import Grid, NCMesh


def consume_named_locations(grid: Grid, mesh: NCMesh) -> None:
    # Predeclared dictionaries matter: dict value parameters are invariant.
    points: dict[str, tuple[float, float]] = {
        "Upstream": (100.0, 200.0),
        "Downstream": (300.0, 400.0),
    }
    lines: dict[str, list[tuple[float, float]]] = {
        "Reach": [(100.0, 200.0), (300.0, 400.0)],
    }

    grid_series = grid.time_series(points, "water level")
    mesh_series = mesh.time_series(points, "water level")
    grid_section = grid.section(lines, "flow", 1.0)
    mesh_section = mesh.section(lines, "flow", 1.0)

    # Also accept dictionaries authored directly at the call site.
    inline_grid = grid.time_series(
        {"Point A": (120.0, 220.0)}, "water level"
    )
    inline_mesh = mesh.section(
        {"Cross Section": [(100.0, 200.0), (150.0, 250.0)]},
        "velocity",
        1.0,
    )

    # Keep the existing scalar/vector/DataFrame return contract unchanged.
    result = grid.data_point(
        points, "water level", 1.0
    )
    _ = (grid_series, mesh_series, grid_section, mesh_section, inline_grid,
         inline_mesh, result)
