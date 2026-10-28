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

## Check inputs for multiple TUFLOW runs

Use batch input validation to check the files needed by specific scenario and event runs before launching TUFLOW. Pass the simulation flags you intend to run:

```python
from pytuflow import TCF
from pytuflow.batch_validation import validate_batch_inputs

model = TCF("runs/model.tcf")
run_flags = ["-s1 Existing -e1 Q10", "-s1 Proposed -e1 Q100"]
report = validate_batch_inputs(model, run_flags)

if not report.passed:
    for issue in report.issues:
        print(issue.run_index, issue.status, issue.path, issue.detail)
```

Validation checks required input files, supported GIS layers and their companion files, boundary-condition CSV column references, and recognised files linked from GIS attributes. Findings identify the affected run and source. Missing, ambiguous or unsupported inputs are reported rather than assumed valid.

To collect a run's file references **without physically checking those inputs**, use the parsed model:

```python
dependencies = model.collect_file_dependencies(run_flags)
```

Initial model loading still parses control files and may read input databases. Both APIs use only the supplied flags; they do not generate scenario/event combinations or execute TUFLOW. Input validation does not establish hydraulic correctness or validate raster data contents.

See [Validating Inputs for Multiple TUFLOW Runs](docs/examples/validating_batch_inputs.rst) for more examples and inspection options.

## Licence

MIT licence. See [LICENSE.txt](LICENSE.txt).
