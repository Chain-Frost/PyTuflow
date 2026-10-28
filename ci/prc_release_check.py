"""Validate PR C release metadata and packaged user documentation.

This check belongs to the validation branch, not the upstream contribution.
"""

from __future__ import annotations

import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXPECTED = "1.2.9"

source = (ROOT / "pytuflow" / "__init__.py").read_text(encoding="utf-8")
assert f"__version__ = '{EXPECTED}'" in source

readme = (ROOT / "README.md").read_text(encoding="utf-8")
assert "## Check inputs for multiple TUFLOW runs" in readme
assert "from pytuflow.batch_validation import validate_batch_inputs" in readme
assert "model.collect_file_dependencies(run_flags)" in readme
assert (ROOT / "docs" / "examples" / "validating_batch_inputs.rst").is_file()

changelog = (ROOT / "docs" / "changelog" / "1.2.rst").read_text(encoding="utf-8")
assert changelog.startswith("Changelog for 1.2\n=================\n\n1.2.9\n-----\n")
assert (chr(96) * 2 + "TCF.collect_file_dependencies()" + chr(96) * 2) in changelog

wheels = list((ROOT / "dist").glob("*.whl"))
sdists = list((ROOT / "dist").glob("*.tar.gz"))
assert len(wheels) == len(sdists) == 1, (wheels, sdists)
wheel, sdist = wheels[0], sdists[0]
assert f"-{EXPECTED}-" in wheel.name, wheel.name
assert sdist.name.endswith(f"-{EXPECTED}.tar.gz"), sdist.name

with zipfile.ZipFile(wheel) as archive:
    names = set(archive.namelist())
    metadata_file = next(name for name in names if name.endswith(".dist-info/METADATA"))
    contents = archive.read(metadata_file).decode("utf-8")
    assert f"Version: {EXPECTED}" in contents
    assert "## Check inputs for multiple TUFLOW runs" in contents
    for name in (
        "pytuflow/py.typed",
        "pytuflow/batch_validation.py",
        "pytuflow/validation.py",
        "pytuflow/_tmf/fragment_dependencies.py",
    ):
        assert name in names, name

with tarfile.open(sdist) as archive:
    names = archive.getnames()
    for suffix in (
        "/README.md",
        "/docs/changelog/1.2.rst",
        "/docs/examples/validating_batch_inputs.rst",
    ):
        assert any(name.endswith(suffix) for name in names), suffix

subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "pytuflow"], check=True)
subprocess.run(
    [sys.executable, "-m", "pip", "install", "--no-deps", str(wheel)], check=True
)
code = (
    "from importlib.metadata import version;"
    "from pathlib import Path;"
    "import pytuflow;"
    f"assert version('pytuflow') == pytuflow.__version__ == {EXPECTED!r};"
    f"assert not Path(pytuflow.__file__).resolve().is_relative_to({str(ROOT)!r});"
    "from pytuflow.batch_validation import validate_batch_inputs;"
    "assert callable(validate_batch_inputs);"
    "print('Installed wheel and source metadata match')"
)
with tempfile.TemporaryDirectory() as outside:
    subprocess.run([sys.executable, "-I", "-c", code], cwd=outside, check=True)

print(f"PR C source, wheel, sdist and README validated at {EXPECTED}")
