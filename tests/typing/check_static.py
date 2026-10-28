"""Run installed-wheel static consumer and stub/runtime consistency checks.

This executes from an external temporary directory after the source package
has been uninstalled and the distribution wheel installed normally. No venv.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).absolute().parent
VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"


def _invoke(
    label: str,
    arguments: list[str],
    *,
    should_fail: bool = False,
    expected_error_lines: tuple[int, ...] = (),
) -> None:
    command = [sys.executable, "-I", "-m", *arguments]
    result = subprocess.run(
        command, cwd=HERE, capture_output=True, text=True, check=False,
    )
    output = result.stdout + result.stderr
    print(f"\n[{label}] exit={result.returncode}\n{output}", flush=True)
    if should_fail:
        if result.returncode == 0:
            raise AssertionError(f"{label} accepted deliberately invalid public API calls")
        if result.returncode != 1:
            raise AssertionError(f"{label} failed for unexpected tooling reasons")
        target = next(arg for arg in arguments if arg.endswith("_negative.py"))
        diagnostics = re.findall(
            rf"(?im)^.*{re.escape(target)}.*(?:error:| - error:)",
            output,
        )
        if len(diagnostics) < 3:
            raise AssertionError(
                f"{label} did not identify all three deliberately invalid calls"
            )
        # For the inline spatial checks, make sure each public call is rejected;
        # unrelated dictionary construction diagnostics cannot satisfy this.
        for line in expected_error_lines:
            if not re.search(
                rf"(?im)^.*{re.escape(target)}:{line}:\d+ - error:",
                output,
            ):
                raise AssertionError(f"{label} did not reject call on line {line}")
    elif result.returncode != 0:
        raise AssertionError(f"{label} rejected valid public API calls")


def main() -> None:
    _invoke(
        "mypy positive",
        ["mypy", "--strict", "--no-incremental", "resdata_positive.py"],
    )
    _invoke(
        "Pyright positive",
        ["pyright", "--pythonversion", VERSION, "resdata_positive.py"],
    )
    _invoke(
        "mypy negative",
        ["mypy", "--strict", "--no-incremental", "resdata_negative.py"],
        should_fail=True,
    )
    _invoke(
        "Pyright negative",
        ["pyright", "--pythonversion", VERSION, "resdata_negative.py"],
        should_fail=True,
    )
    _invoke(
        "mypy optional contracts positive",
        ["mypy", "--strict", "--no-incremental", "public_optionals_positive.py"],
    )
    _invoke(
        "Pyright optional contracts positive",
        ["pyright", "--pythonversion", VERSION, "public_optionals_positive.py"],
    )
    _invoke(
        "mypy optional contracts negative",
        ["mypy", "--strict", "--no-incremental", "public_optionals_negative.py"],
        should_fail=True,
    )
    _invoke(
        "Pyright optional contracts negative",
        ["pyright", "--pythonversion", VERSION, "public_optionals_negative.py"],
        should_fail=True,
    )
    _invoke(
        "mypy named locations positive",
        ["mypy", "--strict", "--no-incremental", "public_locations_positive.py"],
    )
    _invoke(
        "Pyright named locations positive",
        ["pyright", "--pythonversion", VERSION, "public_locations_positive.py"],
    )
    _invoke(
        "mypy named locations negative",
        ["mypy", "--strict", "--no-incremental", "public_locations_negative.py"],
        should_fail=True,
    )
    _invoke(
        "Pyright named locations negative",
        ["pyright", "--pythonversion", VERSION, "public_locations_negative.py"],
        should_fail=True,
    )
    _invoke(
        "Pyright named inline locations negative",
        ["pyright", "--pythonversion", VERSION, "public_locations_inline_negative.py"],
        should_fail=True,
        expected_error_lines=(9, 10, 11),
    )
    _invoke(
        "mypy stubtest",
        ["mypy.stubtest", "--concise", "pytuflow.TUFLOW"],
    )


if __name__ == "__main__":
    main()
