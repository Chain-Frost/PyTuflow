"""Static-only example of supported, typed legacy public API calls.

Run under both mypy --strict and Pyright strict against the installed wheel.
Do not execute: the example demonstrates signatures, not real result files.
"""

# pyright: strict
from datetime import datetime
from os import PathLike
from pathlib import Path
from typing import assert_type

from pytuflow import ResData
from pytuflow.TUFLOW import ResData as LegacyResData


def consume_public_resdata(reader: ResData, path: Path, when: datetime) -> None:
    assert_type(reader, LegacyResData)
    assert_type(reader.format(), str)
    assert_type(reader.name(), str)
    assert_type(reader.source(), str | PathLike[str])
    assert_type(reader.load(path), tuple[bool, str])
    assert_type(reader.channels(), list[str])
    assert_type(reader.channelCount(), int)
    assert_type(reader.nodeDownstream("C01"), str)
    assert_type(reader.referenceTime(), datetime | None)
    assert_type(reader.units(), str | None)

    reader.setReferenceTime(when)
    assert_type(reader.timesteps(), list[float | None] | list[datetime])
    series = reader.getTimeSeriesData("C01", "Q")
    assert_type(series[0], bool)
    assert_type(series[1], str)
    assert_type(
        series[2][1],
        list[float | str | None] | list[list[float | str | None]],
    )
    assert_type(reader.maximum("C01", "Q"), tuple[bool, str, float])

    profile = reader.getLongProfileData("max", "H", "C01")[2]
    if isinstance(profile, tuple):
        x_coordinates, y_coordinates = profile
        # No false guarantee that all profile coordinates are plain floats.
        assert x_coordinates is not None and y_coordinates is not None
    else:
        polygons: list[list[tuple[float, float]]] = profile
        assert_type(polygons, list[list[tuple[float, float]]])

    pipes: list[list[tuple[float, float] | tuple[()]]] = reader.getPipes()
    assert_type(pipes, list[list[tuple[float, float] | tuple[()]]])
