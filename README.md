# PyTuflow

![TUFLOW](docs/assets/TUFLOW.png)

**PyTUFLOW** is a Python library for working with TUFLOW models and results. It provides APIs for loading and inspecting model inputs, editing supported model data, extracting time-series and map results, and using TUFLOW model-building utilities.

## Documentation

Documentation and examples are available at https://docs.tuflow.com/pytuflow/1.2/.

## Installation

PyTUFLOW requires **Python 3.11 or newer**. Install it with pip:

```bash
python -m pip install pytuflow
```

The installation includes PyTUFLOW's declared Python dependencies. Some features also require separately installed native software:

- **GDAL/OGR Python bindings** are required for GDAL-based GIS functionality, including selected `GisInput` operations. The bindings must be compatible with the installed native GDAL library.
- **QGIS/MDAL** is required for QGIS-backed map and mesh operations. Supported Python-based XMDF and NCMesh readers can be used without QGIS.

For QGIS-backed operations, use a compatible QGIS Python environment.

## Quickstart

Start with [Load and Run a TUFLOW Model](https://docs.tuflow.com/pytuflow/1.2/examples/tcf_load_and_run/) or browse the [other examples](https://docs.tuflow.com/pytuflow/1.2/examples/).

## Contributing

Contributor setup, testing and documentation-build instructions are in [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MIT licence. See [LICENSE.txt](LICENSE.txt).
