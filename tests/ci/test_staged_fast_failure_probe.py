"""Deliberate temporary CI probe; never merge or reuse as acceptance evidence."""


def test_staged_fast_gate_failure_probe() -> None:
    raise AssertionError("Intentional fast-contract failure; full Windows lanes must not start")
