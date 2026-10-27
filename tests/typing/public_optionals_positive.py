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

    assert_type(Scope("SCENARIO", "DEV", var=None), Scope)
    assert_type(Scope("VARIABLE", "DEV", var="<<VERSION>>"), Scope)
