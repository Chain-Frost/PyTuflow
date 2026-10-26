"""Real filesystem coverage for TUFLOW Classic/HPC Linux -cs0/-cs1/-cs2."""
import os
from pathlib import Path

import pytest

from pytuflow._tmf import TuflowPath
from pytuflow._tmf.cf.tcf import TCF
from pytuflow._tmf.settings import TCFConfig, from_config


linux = pytest.mark.skipif(os.name == "nt", reason="POSIX-only case-sensitive fixture")
windows = pytest.mark.skipif(os.name != "nt", reason="Requires Windows filesystem")


@linux
@pytest.mark.parametrize(
    ("mode", "reference", "expected"),
    [
        (0, "Model/Frame.TIF", "Model/Frame.TIF"),
        (0, "Model/Frame.tif", "Model/Frame.tif"),
        (1, "Model/Frame.tif", "Model/Frame.TIF"),
        (1, "Model/frame.tif", "Model/frame.tif"),
        (2, "Model/frame.tif", "Model/Frame.TIF"),
        (2, "model/Frame.TIF", "model/Frame.TIF"),
    ],
)
def test_linux_literal_modes(tmp_path: Path, mode: int, reference: str, expected: str) -> None:
    (tmp_path / "Model").mkdir()
    (tmp_path / "Model" / "Frame.TIF").write_text("test", encoding="utf-8")
    path = TuflowPath.init_case_policy_path(reference, tmp_path, mode)
    assert str(path) == str(Path(expected))


@linux
@pytest.mark.parametrize("mode", [0, 1, 2])
def test_missing_paths_remain_lexical(tmp_path: Path, mode: int) -> None:
    reference = "Missing/NOFILE.TIF"
    result = TuflowPath.init_case_policy_path(reference, tmp_path, mode)
    assert result == Path(reference)
    assert not (tmp_path / result).exists()


@linux
def test_exact_match_wins_and_nonexact_ambiguity_rejected(tmp_path: Path) -> None:
    (tmp_path / "Material.TIF").touch()
    (tmp_path / "MATERIAL.TIF").touch()
    assert TuflowPath.init_case_policy_path("Material.TIF", tmp_path, 2) == Path("Material.TIF")
    with pytest.raises(ValueError, match="Ambiguous"):
        TuflowPath.init_case_policy_path("material.tif", tmp_path, 2)
    (tmp_path / "Table.shp").touch()
    (tmp_path / "Table.SHP").touch()
    with pytest.raises(ValueError, match="Ambiguous"):
        TuflowPath.init_case_policy_path("Table.ShP", tmp_path, 1)


@linux
def test_gpkg_database_case_without_relaxing_directory_or_layer(tmp_path: Path) -> None:
    (tmp_path / "Model").mkdir()
    (tmp_path / "Model" / "Data.GPKG").touch()
    value = TuflowPath.init_case_policy_path("Model/data.gpkg >> 2d_code", tmp_path, 2)
    assert str(value) == str(TuflowPath("Model/Data.GPKG >> 2d_code"))
    wrong = TuflowPath.init_case_policy_path("model/data.gpkg >> 2d_code", tmp_path, 2)
    assert str(wrong) == str(TuflowPath("model/data.gpkg >> 2d_code"))


@linux
def test_linux_glob_mode_and_directory_boundaries(tmp_path: Path) -> None:
    folder = tmp_path / "Model"
    folder.mkdir()
    source = folder / "Grid_A.TIF"
    source.touch()
    root = TuflowPath(tmp_path)
    assert list(root.glob("Model/Grid_*.tif", case_sensitivity=0)) == []
    assert list(root.glob("Model/Grid_*.tif", case_sensitivity=1)) == [source]
    assert list(root.glob("Model/grid_*.tif", case_sensitivity=1)) == []
    assert list(root.glob("Model/grid_*.tif", case_sensitivity=2)) == [source]
    assert list(root.glob("model/grid_*.tif", case_sensitivity=2)) == []
    assert list(root.glob("Model/Grid_A.TIF", case_sensitivity=0)) == [source]


@linux
def test_linux_glob_ambiguity_and_exact_filename(tmp_path: Path) -> None:
    (tmp_path / "Material.TIF").touch()
    (tmp_path / "MATERIAL.TIF").touch()
    root = TuflowPath(tmp_path)
    assert list(root.glob("Material.TIF", case_sensitivity=2)) == [tmp_path / "Material.TIF"]
    with pytest.raises(ValueError, match="Ambiguous"):
        list(root.glob("material.tif", case_sensitivity=2))


@linux
def test_directory_wildcards_stay_case_strict(tmp_path: Path) -> None:
    folder = tmp_path / "Area_A"
    folder.mkdir()
    source = folder / "Grid_1.TIF"
    source.touch()
    root = TuflowPath(tmp_path)
    assert list(root.glob("area_*/grid_*.tif", case_sensitivity=2)) == []
    assert list(root.glob("Area_*/grid_*.tif", case_sensitivity=2)) == [source]
    assert list(root.glob("Area_*/Grid_*.tif", case_sensitivity=1)) == [source]


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_configuration_snapshot_retains_mode(mode: int) -> None:
    config = TCFConfig(init_from_tcf=False, case_sensitivity=mode)
    assert from_config(config).case_sensitivity == mode


@pytest.mark.parametrize("invalid", [-1, 3, 1.0, True, "2", None])
def test_invalid_mode_rejected(invalid: object) -> None:
    with pytest.raises(ValueError, match="case_sensitivity"):
        TCFConfig(init_from_tcf=False, case_sensitivity=invalid)


@linux
def test_primary_tcf_filename_and_directory_policy(tmp_path: Path) -> None:
    folder = tmp_path / "Runs"
    folder.mkdir()
    (folder / "Main.tcf").write_text("! case policy\n", encoding="utf-8")
    assert TCF(folder / "Main.TCF", case_sensitivity=1).loaded
    assert not TCF(folder / "main.TCF", case_sensitivity=1).loaded
    assert TCF(folder / "main.TCF", case_sensitivity=2).loaded
    assert not TCF(tmp_path / "runs" / "main.tcf", case_sensitivity=2).loaded


@linux
def test_eager_nested_include_resolution_uses_owner_directory(tmp_path: Path) -> None:
    folder = tmp_path / "Runs"
    child = folder / "Child"
    child.mkdir(parents=True)
    (child / "Leaf.TCF").write_text("Set Variable X == NESTED\n", encoding="utf-8")
    (folder / "Includes.TCF").write_text("Read File == Child/leaf.tcf\n", encoding="utf-8")
    tcf = folder / "Main.tcf"
    tcf.write_text("Read File == Includes.TCF\n", encoding="utf-8")
    assert "X" not in TCFConfig(tcf=tcf, case_sensitivity=0).variables
    assert TCFConfig(tcf=tcf, case_sensitivity=2).variables.get("X") == "NESTED"


@linux
def test_spatial_database_physical_case(tmp_path: Path) -> None:
    (tmp_path / "Data.GPKG").touch()
    config = TCFConfig(control_file=tmp_path / "Main.tcf",
                       init_from_tcf=False, case_sensitivity=2)
    config.set_spatial_database("data.gpkg")
    assert config.spatial_database == tmp_path / "Data.GPKG"


@windows
@pytest.mark.parametrize("mode", [0, 1, 2])
def test_windows_host_native_lookup(tmp_path: Path, mode: int) -> None:
    (tmp_path / "Data.TIF").touch()
    result = TuflowPath.init_case_policy_path("data.tif", tmp_path, mode)
    assert result == Path("data.tif")
    assert (tmp_path / result).exists()
