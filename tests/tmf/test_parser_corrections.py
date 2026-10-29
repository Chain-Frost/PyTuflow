"""Focused regressions for TMF rainfall, BC and free-form material parsing.

Exercises existing parsing APIs using small on-disk fixtures.
"""
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from pytuflow._tmf.cf.tcf import TCF
from pytuflow._tmf.db.bc_dbase import BCDatabase
from pytuflow._tmf.db.mat import MatDatabaseTMF
from pytuflow._tmf.db.rf import RainfallDatabase


def test_direct_netcdf_rainfall_has_no_csv_index(tmp_path: Path) -> None:
    tcf = tmp_path / "direct_rainfall.tcf"
    tcf.write_text("Read Grid RF == rain.nc\n", encoding="utf-8")
    # This public API returns an empty database object when no CSV index
    # exists. A NetCDF raster must not be interpreted as a CSV rainfall index.
    database = TCF(tcf).rainfall_dbase()
    assert isinstance(database, RainfallDatabase)
    assert database.fpath is None
    assert not database.loaded
    assert database.df.empty


def test_rainfall_csv_database_with_native_absolute_path(tmp_path: Path) -> None:
    folder = tmp_path / "model with spaces"
    folder.mkdir()
    tcf = folder / "model.tcf"
    index = folder / "rainfall.csv"
    index.write_text("0,first.flt\n1,second.flt\n", encoding="utf-8")
    tcf.write_text("Read Grid RF == rainfall.csv\n", encoding="utf-8")

    database = TCF(tcf.absolute()).rainfall_dbase()
    assert isinstance(database, RainfallDatabase)
    assert database.fpath == index
    assert database.df.shape == (2, 1)


def test_bc_value_does_not_use_deprecated_inplace_reset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = (
        Path(__file__).parent
        / "test_datasets/models/shp/bc_dbase/bc_dbase_EG00_001.csv"
    )
    reset_index = pd.DataFrame.reset_index

    def reject_inplace(frame, *args, **kwargs):
        if kwargs.get("inplace", False):
            raise AssertionError("BC value must not reset the index in place")
        return reset_index(frame, *args, **kwargs)

    # Independent of whether the installed pandas version emits its
    # deprecation warning: the original implementation must fail this test.
    monkeypatch.setattr(pd.DataFrame, "reset_index", reject_inplace)
    db = BCDatabase(source)
    first = db.value("fc01")
    second = db.value("fc01")
    assert first.index.name == "inflow_time_hr"
    assert first.columns.tolist() == ["inflow_FC01"]
    pd.testing.assert_frame_equal(first, second)


def test_final_boss_material_semantics() -> None:
    source = Path(__file__).parent / "test_datasets/the_final_boss.tmf"
    db = MatDatabaseTMF(source)
    assert db.df.shape == (22, 7)
    assert db.df.index.name == "Material ID"
    assert db.df.index.tolist() == list(range(1, 23))
    assert db.df.columns.tolist() == [
        "Manning's n", "IL", "CL", "y1", "n1", "y2", "n2"
    ]
    assert db.value(6) == 0.03
    assert db.df.loc[1:21, "IL":].isna().all().all()
    pd.testing.assert_frame_equal(
        db.value(22),
        pd.DataFrame({"Depth": [0.65, 0.7], "Manning's n": [0.08, 0.05]}),
    )


@pytest.mark.parametrize(
    "rows",
    [
        "1,0.03\n2,0.04,1,2\n3,0.05\n",
        "2,0.04,1,2\n1,0.03\n3,0.05\n",
    ],
)
def test_material_parser_preserves_uneven_row_values(
    tmp_path: Path, rows: str,
) -> None:
    folder = tmp_path / "materials with spaces"
    folder.mkdir()
    path = folder / "uneven.tmf"
    path.write_text("! Comment, with, commas\n" + rows + "! End\n", encoding="utf-8")

    parser = import_module("pytuflow._tmf.utils.text_to_db_parser")
    actual = parser.text_to_db_parser(path)
    ids = [int(line.split(",")[0]) for line in rows.splitlines()]
    expected = pd.DataFrame(
        [
            [0.04, 1.0, 2.0] if key == 2
            else [0.03 if key == 1 else 0.05, float("nan"), float("nan")]
            for key in ids
        ],
        index=pd.Index(ids, name=0),
        columns=[1, 2, 3],
    )
    pd.testing.assert_frame_equal(actual, expected)


def test_material_parser_pads_before_dataframe_construction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "materials.tmf"
    source.write_bytes(b"1,0.03\r\n2,0.04,1,2\r\n3,0.05\r\n")
    parser = import_module("pytuflow._tmf.utils.text_to_db_parser")

    def require_rectangular(rows):
        assert len({len(row) for row in rows}) <= 1, (
            "Free-form parser passed ragged records to pandas"
        )
        return pd.DataFrame(rows)

    # Test the exact parser-to-pandas boundary, not a version-specific warning.
    # This detects the original bug even when the installed pandas still pads.
    monkeypatch.setattr(
        parser, "pd", SimpleNamespace(DataFrame=require_rectangular)
    )
    actual = parser.text_to_db_parser(source)
    assert actual.shape == (3, 3)
    assert actual.loc[2, 3] == 2
    assert pd.isna(actual.loc[1, 3])
