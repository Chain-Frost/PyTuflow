"""Real QGIS/MDAL public point regression; run only in initialized QGIS Python.

Missing QGIS/MDAL is an error, never an accepted skip. The tiny FV file is
synthetic and contains two 2D vector groups, a scalar, and a dry second cell.
"""
from pathlib import Path

import numpy as np
from netCDF4 import Dataset
import pytest
from qgis.core import QgsApplication, QgsMeshDatasetIndex, QgsProviderRegistry

from pytuflow import NCMesh


@pytest.fixture(scope="module")
def qapp():
    app = QgsApplication.instance()
    if app is None:
        app = QgsApplication([], False)
        app.initQgis()
    assert QgsProviderRegistry.instance().providerMetadata("mdal") is not None
    yield app


def _write_points(path: Path, sample, scalar=7.) -> None:
    sample = np.ma.asarray(sample, dtype=float).filled(np.nan)
    with Dataset(path, "w") as nc:
        nc.spherical = "false"
        nc.Type = "Cell-centred TUFLOWFV output"
        for name, size in {"Time": 2, "NumCells2D": 2, "NumCells3D": 2,
                           "NumVert2D": 8, "MaxNumCellVert": 4,
                           "NumLayerFaces3D": 4}.items():
            nc.createDimension(name, size)

        def write(name, dimensions, values, *, integer=False, long_name=None):
            variable = nc.createVariable(name, "i4" if integer else "f8", dimensions,
                                         **({} if integer else {"fill_value": np.nan}))
            variable.long_name = long_name or name
            variable[:] = values
            return variable

        write("ResTime", ("Time",), [0., 1.]).units = "hours"
        for name, values in {"cell_Nvert": [4, 4], "NL": [1, 1],
                             "idx2": [1, 2], "idx3": [1, 2]}.items():
            write(name, ("NumCells3D" if name == "idx2" else "NumCells2D",),
                  values, integer=True)
        write("cell_node", ("NumCells2D", "MaxNumCellVert"),
              [[1, 2, 3, 4], [5, 6, 7, 8]], integer=True)
        for name, values in {"node_X": [0, 1, 1, 0, 2, 3, 3, 2],
                             "node_Y": [0, 0, 1, 1, 0, 0, 1, 1],
                             "node_Zb": [-1] * 8}.items():
            write(name, ("NumVert2D",), values)
        for name, values in {"cell_X": [.5, 2.5], "cell_Y": [.5, .5],
                             "cell_Zb": [-1, -1], "cell_A": [1, 1]}.items():
            write(name, ("NumCells2D",), values)
        write("layerface_Z", ("Time", "NumLayerFaces3D"), [[0, -1, 0, -1]] * 2)
        write("stat", ("Time", "NumCells2D"), [[1, 0]] * 2, integer=True)
        write("H", ("Time", "NumCells2D"), [[0, 0]] * 2,
              long_name="water surface elevation")
        write("SAL", ("Time", "NumCells2D"), [[scalar, 19.]] * 2,
              long_name="salinity")
        for prefix, group in [("V2", "velocity2d"), ("V", "velocity")]:
            for component, axis in enumerate("xy"):
                write(prefix + "_" + axis, ("Time", "NumCells2D"),
                      [[sample[component], 17.], [6. if component == 0 else 8., 17.]],
                      long_name=axis + "_" + group)


DRIVERS = ["qgis geometry data extractor", "qgis geometry netcdf4", "qgis geometry h5py"]
SAMPLES = [
    pytest.param([3., 4.], [3., 4.], id="finite"),
    pytest.param([0., 4.], [0., 4.], id="zero-component"),
    pytest.param([0., 0.], [0., 0.], id="zero-vector"),
    pytest.param([3., np.nan], [3., np.nan], id="missing-y"),
    pytest.param([np.nan, 4.], [np.nan, 4.], id="missing-x"),
    pytest.param([np.nan, np.nan], [np.nan, np.nan], id="all-missing"),
    pytest.param(np.ma.array([3., 99.], mask=[False, True]),
                 [3., np.nan], id="masked-backing"),
]


@pytest.mark.parametrize("driver", DRIVERS)
@pytest.mark.parametrize("data_type", ["velocity2d", "velocity"])
@pytest.mark.parametrize("sample,expected", SAMPLES)
def test_public_real_mdal_vector_points(qapp, tmp_path, driver, data_type, sample, expected):
    path = tmp_path / "vector-points.nc"
    _write_points(path, sample)
    reader = NCMesh(path, driver=driver)
    first = reader.data_point((.5, .5), data_type, 0.)
    assert isinstance(first, tuple) and len(first) == 2
    if driver == "qgis geometry data extractor":
        assert all(type(component) is float for component in first)
    np.testing.assert_allclose(first, expected, rtol=0, atol=0, equal_nan=True)
    np.testing.assert_allclose(reader.data_point((.5, .5), data_type, 1.), [6., 8.],
                               rtol=0, atol=0)
    np.testing.assert_allclose(reader.data_point((.5, .5), data_type, 0.), expected,
                               rtol=0, atol=0, equal_nan=True)
    # Preserve the public PyMesh cell-point tuple even with return_type omitted.
    default = reader._driver.data_point((.5, .5), data_type, 0.)
    explicit = reader._driver.data_point((.5, .5), data_type, 0., return_type="vector")
    assert isinstance(default, tuple) and isinstance(explicit, tuple)
    np.testing.assert_allclose(default, expected, rtol=0, atol=0, equal_nan=True)
    np.testing.assert_allclose(explicit, expected, rtol=0, atol=0, equal_nan=True)


@pytest.mark.parametrize("driver", DRIVERS)
@pytest.mark.parametrize("value", [7., 0., np.nan])
def test_public_real_mdal_scalar_points(qapp, tmp_path, driver, value):
    path = tmp_path / "scalar-points.nc"
    _write_points(path, [3., 4.], scalar=value)
    reader = NCMesh(path, driver=driver)
    result = reader.data_point((.5, .5), "salinity", 0.)
    assert type(result) is float
    np.testing.assert_allclose(result, value, rtol=0, atol=0, equal_nan=True)


@pytest.mark.parametrize("driver", DRIVERS)
@pytest.mark.parametrize("data_type", ["velocity2d", "velocity"])
def test_public_real_mdal_dry_and_outside(qapp, tmp_path, driver, data_type):
    path = tmp_path / "inactive-points.nc"
    _write_points(path, [3., 4.])
    reader = NCMesh(path, driver=driver)
    for point in [(2.5, .5), (-1., -1.)]:
        result = reader.data_point(point, data_type, 0.)
        assert isinstance(result, float) and np.isnan(result)


def test_real_mdal_combined_vector_metadata_and_shape(qapp, tmp_path):
    path = tmp_path / "metadata-points.nc"
    _write_points(path, [3., 4.])
    reader = NCMesh(path, driver="qgis geometry data extractor")
    reader._load()
    provider = reader._driver.extractors[0].lyr.dataProvider()
    assert provider.faceCount() == 2
    for data_type in ["velocity2d", "velocity"]:
        assert reader._driver.is_vector(data_type)
        assert not reader._driver.is_3d(data_type)
        group = next(i for i in range(provider.datasetGroupCount())
                     if provider.datasetGroupMetadata(i).name() == data_type)
        assert not provider.datasetGroupMetadata(group).isScalar()
        block = provider.datasetValues(QgsMeshDatasetIndex(group, 0), 0, 1)
        assert block.isValid()
        np.testing.assert_allclose(block.values(), [3., 4.], rtol=0, atol=0)
        values = reader._driver.data(data_type, (0, 0))
        assert values.shape == (1, 2)
