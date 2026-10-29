"""Prototype safety and format parity for PyTuflow's core GeoPackage reader."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from pytuflow._tmf.gis_attr_driver import GISAttributes, GPKGAttributes
from pytuflow._tmf.gpkg_safety import GeoPackageSafetyError, readonly_gpkg
from pytuflow._tmf.tfpathlib import TuflowPath
from pytuflow.validation_gis import inspect_gis_attribute_sources


@pytest.fixture
def gpkg(tmp_path: Path) -> Path:
    """Create the smallest valid attribute-bearing geometry metadata fixture."""
    path = tmp_path / "network.gpkg"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE gpkg_contents (table_name TEXT)")
        db.execute(
            "CREATE TABLE gpkg_geometry_columns ("
            "table_name TEXT, column_name TEXT, geometry_type_name TEXT)"
        )
        db.execute("INSERT INTO gpkg_contents VALUES ('1d_nwk_test')")
        db.execute(
            "INSERT INTO gpkg_geometry_columns VALUES "
            "('1d_nwk_test', 'geom', 'LINESTRING')"
        )
        attrs = ", ".join(f'"attr{i}" TEXT' for i in range(3, 10))
        db.execute(
            "CREATE TABLE \"1d_nwk_test\" ("
            "fid INTEGER PRIMARY KEY, Name TEXT, Type TEXT, "
            f"Ignore TEXT, {attrs}, Inlet_Type TEXT, geom BLOB)"
        )
        db.execute(
            "INSERT INTO \"1d_nwk_test\" "
            "(Name, Type, Ignore, Inlet_Type, geom) VALUES "
            "('link', 'M', '', 'inlet.csv', X'0102')"
        )
    return path


def _source(gpkg: Path) -> TuflowPath:
    """Make an explicit TUFLOW GeoPackage layer reference."""
    return TuflowPath(f"{gpkg} >> 1d_nwk_test")


def test_gpkg_reader_uses_safe_path_with_or_without_gdal(gpkg: Path, monkeypatch) -> None:
    """Route GPKG attribute reads through SQLite even if GDAL is available."""
    import pytuflow._tmf.gis_attr_driver as driver

    for has_gdal in (False, True):
        monkeypatch.setattr(driver, "has_gdal", has_gdal)
        with GISAttributes(_source(gpkg)) as reader:
            assert isinstance(reader, GPKGAttributes)
            fields = reader.field_names
            assert fields[:3] == ("Name", "Type", "Ignore")
            assert fields[-1] == "Inlet_Type"
            record = list(reader)
            assert len(record) == 1
            assert list(record[0].values())[-1] == "inlet.csv"
    assert {p.name for p in gpkg.parent.iterdir()} == {"network.gpkg"}


def test_gpkg_direct_reader_rejects_absent_file_without_creating_it(tmp_path: Path) -> None:
    """Never create a missing main GeoPackage while reading attributes."""
    missing = tmp_path / "absent.gpkg"
    with pytest.raises(FileNotFoundError):
        with GPKGAttributes(TuflowPath(f"{missing} >> 1d_nwk_test")):
            pass
    assert not missing.exists()
    assert list(tmp_path.iterdir()) == []


def test_gpkg_reader_propagates_missing_layer(gpkg: Path) -> None:
    """Report missing layer metadata rather than swallowing SQLite errors."""
    with pytest.raises(ValueError, match="Expected one GeoPackage table"):
        with GPKGAttributes(TuflowPath(f"{gpkg} >> 1d_nwk_absent")):
            pass


def test_gpkg_reader_rejects_uncommitted_wal(gpkg: Path) -> None:
    """Refuse incomplete WAL snapshots without side effects."""
    with sqlite3.connect(gpkg) as editor:
        editor.execute("PRAGMA journal_mode=WAL")
        editor.execute("BEGIN IMMEDIATE")
        editor.execute("INSERT INTO gpkg_contents VALUES ('pending')")
        with pytest.raises(GeoPackageSafetyError, match="wal"):
            with GPKGAttributes(_source(gpkg)) as reader:
                list(reader)
        editor.rollback()


def test_shared_connection_remains_open_and_uses_selected_columns(gpkg: Path) -> None:
    """Reuse the physical validator's pinned connection without closing it."""
    with readonly_gpkg(gpkg) as db:
        with GPKGAttributes(_source(gpkg), connection=db) as reader:
            assert list(reader.iter_selected((1, 10))) == [("M", "inlet.csv")]
        assert db.execute("SELECT COUNT(*) FROM gpkg_contents").fetchone()[0] == 1


def test_validation_reuses_reader_and_keeps_source_attribution(gpkg: Path) -> None:
    """Find network matrix sources using core reader metadata and SQL."""
    key = (gpkg, "1d_nwk_test", True)
    findings, count = inspect_gis_attribute_sources({key})
    assert count == 1
    assert findings[key].status == "present"
    assert findings[key].sources == (gpkg.parent / "inlet.csv",)
