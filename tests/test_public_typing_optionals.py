"""Focused runtime compatibility checks for narrowly corrected public hints."""

from __future__ import annotations

import inspect
from pathlib import Path

from pytuflow import Scope, TuflowBinaries


def test_binary_lookup_default_and_custom_sentinel_are_unchanged() -> None:
    # Avoid system registries, settings and disk access; exercise existing get().
    registry = object.__new__(TuflowBinaries)
    registry._version2bin = {"2026.1": "C:/TUFLOW/TUFLOW.exe"}

    sentinel = object()
    fallback = Path("fallback-tuflow.exe")

    assert registry.get("2026.1") == "C:/TUFLOW/TUFLOW.exe"
    assert registry.get("missing") is None
    assert registry.get("missing", sentinel) is sentinel
    assert registry.get("missing", fallback) is fallback
    assert registry.get("2026.1", sentinel) == "C:/TUFLOW/TUFLOW.exe"

    signature = inspect.signature(TuflowBinaries.get)
    assert tuple(signature.parameters) == ("self", "item", "default")
    assert signature.parameters["default"].default is None


def test_scope_optional_var_runtime_contract_is_unchanged() -> None:
    absent = Scope("SCENARIO", "DEV", var=None)
    provided = Scope("VARIABLE", "DEV", var="<<VERSION>>")

    assert absent.var is None
    assert provided.var == "<<VERSION>>"

    signature = inspect.signature(Scope)
    assert tuple(signature.parameters) == ("type_name", "name", "var", "else_")
    assert signature.parameters["var"].default is None
    assert signature.parameters["else_"].default is False
