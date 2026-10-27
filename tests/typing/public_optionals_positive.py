"""Static-only consumers for two corrected, existing public API declarations.

Check against the installed distribution wheel; do not execute this file.
"""

# pyright: strict

from pathlib import Path
from typing import assert_type

from pytuflow import Scope, TuflowBinaries


def use_supported_optionals(binaries: TuflowBinaries) -> None:
    optional_path: str | None = binaries.get("not-registered")
    assert_type(optional_path, str | None)

    custom_default = Path("fallback-tuflow.exe")
    custom_result: str | Path | None = binaries.get("not-registered", custom_default)
    assert_type(custom_result, str | Path | None)

    # Scope.__new__ is an existing factory returning concrete Scope subclasses.
    scenario: Scope = Scope("SCENARIO", "DEV", var=None)
    variable: Scope = Scope("VARIABLE", "DEV", var="<<VERSION>>")
    assert_type(scenario, Scope)
    assert_type(variable, Scope)
