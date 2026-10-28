"""Incorrect inline named geometry must be rejected through public reader calls."""

# pyright: strict

from pytuflow import Grid, NCMesh


def invalid_inline_calls(grid: Grid, mesh: NCMesh) -> None:
    mesh.time_series({"Bad point": 123}, "water level")
    mesh.section({"Bad line": [1, 2, 3]}, "flow", 1.0)
    grid.data_point({"Bad point": object()}, "water level", 1.0)
