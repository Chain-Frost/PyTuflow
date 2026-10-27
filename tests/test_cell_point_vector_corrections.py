"""Public PyMesh point regression for one dataset containing two vector components.

Only the extractor is simulated: public dispatch, result metadata, masks, cache
and the cell point reduction use real PyTUFLOW production code. The matching
native-QGIS MDAL case must also be run in the installed QGIS environment.
"""
from unittest.mock import MagicMock

import numpy as np
import pytest

from pytuflow._outputs.pymesh import PyMesh
from tests.test_numerical_fv_reader import _write_fv
from pytuflow import NCMesh


def _reader(*, dtype="velocity2d", vector=True, values=None, wet=True, cell_id=0, name="QgisDataExtractor"):
    mesh = PyMesh()
    mesh.geom.data_type = ""
    mesh.geom.find_containing_cell = lambda point, scope="local": cell_id
    extractor = MagicMock()
    extractor.NAME = name
    extractor.data_types.return_value = [dtype]
    extractor.is_vector.return_value = vector
    extractor.is_3d.return_value = False
    extractor.is_static.return_value = True
    extractor.on_vertex.return_value = False
    extractor.zlevel_count.return_value = np.array([1])
    extractor.wd_flag.return_value = np.array([wet])
    extractor.data.return_value = np.asarray([3., 4.]) if values is None else values
    mesh.extractors = [extractor]
    return mesh, extractor


@pytest.mark.parametrize("dtype", ["velocity2d", "vector velocity"])
@pytest.mark.parametrize("values", [
    np.array([3., 4.]),
    np.array([[3., 4.]]),
    np.array([[0., 4.]]),
    np.array([[3., np.nan]]),
    np.array([[np.nan, 4.]]),
    np.array([[np.nan, np.nan]]),
], ids=["flat", "single-row", "zero", "missing-y", "missing-x", "all-missing"])
def test_public_cell_point_combined_vector_uses_metadata(dtype, values):
    mesh, extractor = _reader(dtype=dtype, values=values)
    expected = tuple(float(x) for x in values.ravel())
    result = mesh.data_point((.5, .5), dtype, 0.)
    assert isinstance(result, tuple) and len(result) == 2
    assert all(type(component) is float for component in result)
    np.testing.assert_allclose(result, expected, rtol=0, atol=0, equal_nan=True)
    # Existing cell-centred public behavior is a component tuple even with
    # return_type="scalar", unlike vertex-centred magnitude interpolation.
    assert mesh.data_point((.5, .5), dtype, 0., return_type="vector") == result or (
        np.isnan(result).any() and np.allclose(
            mesh.data_point((.5, .5), dtype, 0., return_type="vector"), result, equal_nan=True
        )
    )
    assert extractor.is_vector.call_count >= 1


@pytest.mark.parametrize("values,expected", [
    (np.array([[3., 99.]]), [3., np.nan]),
    (np.array([[99., 4.]]), [np.nan, 4.]),
])
def test_masked_vector_components_do_not_expose_finite_backing(values, expected):
    mask = np.isnan(expected)
    data = np.ma.array(values, mask=mask.reshape(values.shape))
    mesh, _ = _reader(values=data)
    got = mesh.data_point((.5, .5), "velocity2d")
    np.testing.assert_allclose(got, expected, rtol=0, atol=0, equal_nan=True)


@pytest.mark.parametrize("value", [0., 7., np.nan])
def test_scalar_single_dataset_remains_float(value):
    mesh, _ = _reader(dtype="water level", vector=False, values=np.array([value]))
    result = mesh.data_point((.5, .5), "water level")
    assert type(result) is float
    np.testing.assert_allclose(result, value, equal_nan=True)


@pytest.mark.parametrize("wet,cell_id", [(False, 0), (True, -1)])
def test_dry_and_outside_point_remain_nan_and_do_not_read_values(wet, cell_id):
    mesh, extractor = _reader(wet=wet, cell_id=cell_id)
    result = mesh.data_point((.5, .5), "velocity2d")
    assert isinstance(result, float) and np.isnan(result)
    extractor.data.assert_not_called()


def test_separate_vector_components_still_return_tuple():
    mesh, extractor = _reader(dtype="velocity", name="PyNCMeshDataExtractor")
    mesh.translate_data_type = lambda name: ("V_x", "V_y") if name == "velocity" else (name,)
    extractor.data.side_effect = lambda dtype, index: np.array([3.]) if dtype == "V_x" else np.array([4.])
    got = mesh.data_point((.5, .5), "velocity")
    assert got == (3., 4.)


def test_real_public_3d_averaging_is_unchanged(tmp_path):
    path = tmp_path / "existing-fv.nc"
    _write_fv(path)
    reader = NCMesh(path, driver="netcdf4")
    np.testing.assert_allclose(reader.data_point((.5, .5), "velocity", 0.), (3., 4.))
    np.testing.assert_allclose(
        reader.data_point((.5, .5), "salinity", 0., averaging_method="depth&0&1.5"),
        40. / 3., rtol=1e-12, atol=1e-12,
    )
