"""Provider registration is separate from importing the QGIS bindings."""

from types import ModuleType, SimpleNamespace
import importlib
from pathlib import Path
from unittest.mock import patch

import pytest

from pytuflow._outputs._backend_capability import require_mesh_backend


@pytest.mark.parametrize("driver", ["v1.0", "qgis geometry netcdf4", "qgis geometry data extractor"])
@pytest.mark.parametrize("state", ["uninitialized", "missing_mdal", "registered"])
def test_explicit_qgis_driver_requires_registered_mdal(driver, state):
    core = ModuleType("qgis.core")
    core.QgsApplication = SimpleNamespace(instance=lambda: None if state == "uninitialized" else object())
    core.QgsProviderRegistry = SimpleNamespace(instance=lambda: SimpleNamespace(
        providerMetadata=lambda name: object() if state == "registered" and name == "mdal" else None,
    ))
    with patch.dict("sys.modules", {"qgis.core": core}):
        arguments = dict(qgis_available=True, h5py_available=True, netcdf4_available=True)
        if state == "uninitialized":
            with pytest.raises(RuntimeError, match="initialized QGIS application"):
                require_mesh_backend(driver, **arguments)
        elif state == "missing_mdal":
            with pytest.raises(ImportError, match="MDAL provider is unavailable"):
                require_mesh_backend(driver, **arguments)
        else:
            require_mesh_backend(driver, **arguments)


def test_default_backend_does_not_require_a_qgis_application():
    with patch.dict("sys.modules", {"qgis": None, "qgis.core": None}):
        require_mesh_backend("v1.1", qgis_available=False, h5py_available=True, netcdf4_available=True)


@pytest.mark.parametrize("module_name,class_name,geometry_name", [
    ("pyxmdf", "PyXMDF", "Py2dm"),
    ("pyncmesh", "PyNCMesh", "PyNCMeshGeometry"),
])
def test_default_qgis_extractor_can_create_layer_for_python_geometry(
    monkeypatch, module_name, class_name, geometry_name,
):
    module = importlib.import_module("pytuflow._outputs.pymesh." + module_name)
    reader = getattr(module, class_name)
    monkeypatch.setattr(reader, "external_engine_available", staticmethod(lambda: False))
    monkeypatch.setattr(reader, "pv_available", staticmethod(lambda: True))
    monkeypatch.setattr(reader, "qgis_available", staticmethod(lambda: True))
    monkeypatch.setattr(reader, "qgis_initialized", staticmethod(lambda: True))
    monkeypatch.setattr(reader, "_preload", lambda self, extractor: None)
    monkeypatch.setattr(module, geometry_name, lambda path: SimpleNamespace())
    created_layer = object()

    def extractor(*args, layer, **kwargs):
        assert layer is None  # Python geometry has no existing QGIS layer to reuse.
        return SimpleNamespace(lyr=created_layer, spherical=lambda: False)

    monkeypatch.setattr(module, "QgisDataExtractor", extractor)
    mesh = reader(Path("result.xmdf" if module_name == "pyxmdf" else "result.nc"))
    assert mesh.geom.lyr is created_layer
    assert mesh.extractors[0].lyr is created_layer
