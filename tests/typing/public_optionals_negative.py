"""Incorrect public API uses that mypy and Pyright must independently reject."""

# pyright: strict

from typing import assert_type

from pytuflow import Scope, TuflowBinaries


def reject_incorrect_contracts(binaries: TuflowBinaries) -> None:
    assert_type(binaries.get("unknown-version"), str)
    assert_type(binaries.get("unknown-version", 123), int)
    Scope("SCENARIO", "DEV", var=123)
