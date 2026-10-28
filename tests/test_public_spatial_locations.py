"""Verify named spatial dictionary handling without opening results or GIS files."""

from __future__ import annotations

from pytuflow import Grid


def test_named_point_dictionary_preserves_location_labels() -> None:
    # The translation method does not require Grid.__init__ or any data file.
    grid = object.__new__(Grid)
    points = {
        "Upstream": (100.0, 200.0),
        "Downstream": (300.0, 400.0),
    }
    assert grid._translate_point_location(points) == points


def test_named_line_dictionary_preserves_location_labels() -> None:
    grid = object.__new__(Grid)
    lines = {
        "Reach": [(100.0, 200.0), (300.0, 400.0)],
    }
    assert grid._translate_line_string_location(lines) == lines
