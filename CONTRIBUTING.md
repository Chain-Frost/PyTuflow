# Contributing to PyTUFLOW

This guide covers the current development setup, tests, documentation build and package build. For usage and installation, see the [README](README.md) and [published documentation](https://docs.tuflow.com/pytuflow/1.2/).

## Development environment

Clone the repository and its submodules:

```bash
git clone --recurse-submodules https://github.com/TUFLOW-Support/PyTuflow.git
cd PyTuflow
python -m pip install -r requirements-dev.txt
```

Some tests require separately installed, compatible GDAL/OGR Python bindings. QGIS-backed mesh tests must run in an initialized QGIS/MDAL Python environment; installing the Python requirements alone does not provide QGIS.

## Tests

From the repository root, run the relevant existing tests:

```bash
python -m unittest tests.test_time_series
python -m pytest tests/tmf
python -m pytest tests/fm_lib/unit_tests tests/fm_lib/integration_tests
```

To run the QGIS-dependent map-output tests, use a QGIS Python environment:

```bash
python -m unittest tests.test_map_output
```

The repository also contains focused regression modules under `tests/`. Some require native providers or sample datasets, so select an appropriate environment for each test suite.

## Documentation

On Windows, from the repository root:

```powershell
cd docs
.\make.bat dirhtml
.\serve.ps1
```

## Building the package

From the repository root:

```bash
python -m build --wheel
```
