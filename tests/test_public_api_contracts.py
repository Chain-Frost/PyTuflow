"""Contract tests for established, user-facing PyTUFLOW APIs (08B / #13).

These tests assert existing behaviour. They intentionally do not introduce new
imports, backends, return types, or an expanded public API.
"""

from __future__ import annotations

import importlib
import inspect
import pickle
import warnings

import pytest


# The complete, explicitly maintained result-reader facade introduced in 08A.
# The module is the existing public re-export location, not necessarily the
# object's defining __module__ (for example, FormatConvention).
OUTPUT_EXPORTS: dict[str, str] = {
    "INFO": "info",
    "TPC": "tpc",
    "GPKG1D": "gpkg_1d",
    "GPKG2D": "gpkg_2d",
    "GPKGRL": "gpkg_rl",
    "FMTS": "fm_ts",
    "FVBCTide": "fv_bc_tide",
    "HydTablesCheck": "hyd_tables_check",
    "BCTablesCheck": "bc_tables_check",
    "CrossSections": "cross_sections",
    "DATCrossSections": "fm_dat",
    "XMDF": "xmdf",
    "NCMesh": "nc_mesh",
    "CATCHJson": "catch_json",
    "DAT": "dat",
    "NCGrid": "nc_grid",
    "LP2D": "lp2d",
    "MapOutput": "map_output",
    "TimeSeries": "time_series",
    "TabularOutput": "tabular_output",
    "Mesh": "mesh",
    "Grid": "grid",
    "GridMesh": "grid_mesh",
    "Output": "output",
    "FormatConvention": "pymesh",
}

# Root aliases have existed independently of the 08A lazy output facade.
TMF_PUBLIC_SYMBOLS = (
    "TCF", "ECF", "TGC", "TBC", "TEF", "QCF", "TOC", "TRFC",
    "TSCF", "TESF", "ADCF", "FVC", "FVWQ", "FVSed", "FVPTM",
    "BCDatabase", "MatDatabase", "PitInletDatabase",
    "RainfallDatabase", "SoilDatabase", "CrossSectionDatabase",
    "SettingInput", "FileInput", "FolderInput", "GisInput",
    "GridInput", "TinInput", "ControlFileInput", "DatabaseInput",
    "CommentInput", "BlockControlInput", "BCBlockControlInput",
    "Context", "Scope", "TuflowPath", "set_logging_level",
    "register_tuflow_binary", "register_tuflow_binary_folder",
    "tuflow_binaries",
)


def test_25_result_reader_exports_are_present_and_unique() -> None:
    import pytuflow
    from pytuflow import _outputs

    assert len(OUTPUT_EXPORTS) == 25
    assert len(_outputs.__all__) == len(set(_outputs.__all__))
    assert set(_outputs.__all__) == set(OUTPUT_EXPORTS)
    assert set(OUTPUT_EXPORTS).issubset(set(pytuflow.__all__))

    for name, module_name in OUTPUT_EXPORTS.items():
        implementation = importlib.import_module(
            f"pytuflow._outputs.{module_name}"
        )
        expected = getattr(implementation, name)
        assert getattr(_outputs, name) is expected, name
        assert getattr(pytuflow, name) is expected, name
        assert name in dir(_outputs)
        assert name in dir(pytuflow)


def test_root_tmf_aliases_resolve_to_original_objects() -> None:
    import pytuflow
    from pytuflow import _tmf

    for name in TMF_PUBLIC_SYMBOLS:
        assert name in pytuflow.__all__, name
        assert getattr(pytuflow, name) is getattr(_tmf, name), name


def test_project_fm_and_utility_entry_points_remain_available() -> None:
    import pytuflow
    from pytuflow import _fm, project, results, util

    assert pytuflow.HPCProject is project.HPCProject
    assert pytuflow.FVProject is project.FVProject
    assert callable(project.TemplateManager)
    assert pytuflow.GXY is _fm.GXY
    assert pytuflow.FMDAT is _fm.FMDAT
    assert pytuflow.TuflowBinaries is util.TuflowBinaries
    assert pytuflow.pytuflow_logging is util.pytuflow_logging
    assert issubclass(results.ResultTypeError, ValueError)


def test_legacy_root_star_import_preserves_supported_names() -> None:
    namespace: dict[str, object] = {}
    exec("from pytuflow import *", namespace)
    for name in (
        "TCF", "FVC", "Context", "Scope", "TuflowPath",
        "TPC", "INFO", "XMDF", "NCMesh", "NCGrid",
        "HPCProject", "FVProject", "FMDAT", "ResData",
    ):
        assert callable(namespace[name]), name


@pytest.mark.parametrize(
    ("name", "parameter_names", "defaults"),
    [
        ("TCF", ("fpath", "kwargs"), {"fpath": None}),
        ("Context", ("context", "config"), {"context": (), "config": None}),
        ("Scope", ("type_name", "name", "var", "else_"),
         {"name": "", "var": None, "else_": False}),
        ("TPC", ("fpath",), {}),
        ("XMDF", ("fpath", "twodm", "driver"),
         {"twodm": None, "driver": "v1.1"}),
        ("NCMesh", ("fpath", "driver"), {"driver": "v1.1"}),
        ("NCGrid", ("fpath",), {}),
        ("ResData", ("file",), {"file": None}),
    ],
)
def test_existing_constructor_names_and_defaults(
    name: str,
    parameter_names: tuple[str, ...],
    defaults: dict[str, object],
) -> None:
    import pytuflow

    signature = inspect.signature(getattr(pytuflow, name))
    assert tuple(signature.parameters) == parameter_names, name
    for parameter_name, default in defaults.items():
        assert signature.parameters[parameter_name].default == default, (
            name, parameter_name
        )


def test_logging_configuration_default_remains_warning() -> None:
    import pytuflow

    signature = inspect.signature(pytuflow.set_logging_level)
    assert signature.parameters["level"].default == "WARNING"
    assert signature.parameters["log_to_file"].default is None

    util_signature = inspect.signature(
        pytuflow.pytuflow_logging.set_logging_level
    )
    assert util_signature.parameters["level"].default == "WARNING"
    assert util_signature.parameters["log_to_file"].default is None


def test_legacy_resdata_keeps_deprecation_without_removal() -> None:
    from pytuflow import ResData

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always", DeprecationWarning)
        instance = ResData()
        instance.close()
    assert any(
        issubclass(record.category, DeprecationWarning)
        and "TPC" in str(record.message)
        for record in records
    )


@pytest.mark.parametrize("name", ["TCF", "Context", "TPC", "XMDF", "NCGrid"])
def test_public_class_pickling_references_stable_module(name: str) -> None:
    import pytuflow

    public_class = getattr(pytuflow, name)
    canonical_module = importlib.import_module(public_class.__module__)
    assert getattr(canonical_module, public_class.__name__) is public_class
    assert pickle.loads(pickle.dumps(public_class)) is public_class


def test_unknown_result_reader_does_not_succeed_silently() -> None:
    import pytuflow
    from pytuflow import _outputs

    for namespace in (pytuflow, _outputs):
        with pytest.raises(AttributeError):
            getattr(namespace, "missing_api_contract_08b")


def test_installed_project_cli_target_remains_callable() -> None:
    from importlib.metadata import distribution
    from pytuflow.project.__main__ import main

    candidates = [
        item for item in distribution("pytuflow").entry_points
        if item.group == "console_scripts" and item.name == "pytuflow-project"
    ]
    assert len(candidates) == 1
    assert candidates[0].value == "pytuflow.project.__main__:main"
    assert candidates[0].load() is main
