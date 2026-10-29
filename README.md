# PyTuflow

![](docs/assets/TUFLOW.png)

**PyTUFLOW** is a library that acts as an API for your TUFLOW model. It allows easy interaction with the model results,
contains a number of useful utilities for building TUFLOW models, and contains some useful parsers for files within the
TUFLOW eco-system.

## Documentation

The documentation for PyTUFLOW can be found at: https://docs.tuflow.com/pytuflow/1.2/

## Installation

PyTUFLOW requires Python 3.11 or newer. You can install it using pip.

```bash
pip install pytuflow
```

## Dependencies

Most Python dependencies, including `netCDF4` and `shapely`, are installed automatically. Some functionality
also requires separately installed native software:

- **GDAL/OGR Python bindings**: Required for GDAL-based GIS input and output operations. The bindings must match
  the installed GDAL library.
- **QGIS/MDAL**: Required for QGIS-backed map and mesh operations. Supported Python-based XMDF and NCMesh
  readers can be used without QGIS.

One of the trickiest libraries to install is GDAL. For Windows, you can download pre-compiled binaries from
here: https://github.com/cgohlke/geospatial-wheels/releases.

For QGIS, there are some broad instructions on how to set up a [QGIS environment](https://docs.tuflow.com/pytuflow/1.2/examples/working_with_tuflow_outputs/) in the output examples.

## Quickstart

The best place to get started is the [Load and Run a TUFLOW Model](https://docs.tuflow.com/pytuflow/1.2/examples/tcf_load_and_run/) example, or to browse through the other
[Examples](https://docs.tuflow.com/pytuflow/1.2/examples/).

## Development

The code base can be cloned from GitHub:

```bash
git clone https://github.com/TUFLOW-Support/PyTuflow.git --recurse-submodules
```

Dependencies can be installed using the `requirements-dev.txt` file:

```bash
pip install -r requirements-dev.txt
```

GDAL python bindings will also need to be installed separately. Version 3.8 or later is preferred.

### Building the Docs

To build the documentation, navigate to the `docs` folder and run:

```bash
# from the pytuflow project root directory
cd docs
.\make.bat dirhtml
```

To serve the documentation locally, you can use (on Windows):

```bash
.\serve.ps1
```

### Running Tests

PyTUFLOW uses `unittest` and `pytest` for testing depending on which module is being tested.

To run tests for the `time series` output classes:

```bash
# from the pytuflow project root directory
python -m unittest tests.test_time_series
```

To run tests for the `map output` classes, you will need to run within a QGIS Python environment:

```bash
# from the pytuflow project root directory
python -m unittest tests.test_map_output
```

To run the `tmf` tests:

```bash
# from the pytuflow project root directory
python -m pytest tests/tmf
```

To run the `fm_to_estry` unit tests:

```bash
# from the pytuflow project root directory
python -m pytest tests/fm_lib/unit_tests
```

To run the `fm_to_estry` integration tests:

```bash
# from the pytuflow project root directory
python -m pytest tests/fm_lib/integration_tests
```

### Building the Package

```bash
# from the pytuflow project root directory
python -m build --wheel
```

## LICENCE

MIT LICENCE (see [LICENSE.txt](LICENSE.txt) for details).
