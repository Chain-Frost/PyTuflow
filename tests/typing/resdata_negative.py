"""Deliberately invalid legacy calls: both static checkers must reject them.

Do not run this file as Python; it is a negative type-check fixture.
"""

# pyright: strict
from pytuflow import ResData


def invalid_calls(reader: ResData) -> None:
    reader.load(123)                  # invalid: requires str or path-like
    reader.channels().append(123)    # invalid: channel identifiers are str
    reader.maximum("node")           # invalid: resultType is mandatory
