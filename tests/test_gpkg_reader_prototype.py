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
        with GPKGAttributes(_source(gpkg), read_only=True) as reader:
            assert isinstance(reader, GPKGAttributes)
            fields = reader.field_names
            assert fields[:3] == ("Name", "Type", "Ignore")
            assert fields[-1] == "Inlet_Type"
            record = list(reader)
            assert len(record) == 1
            assert list(record[0].values())[-1] == "inlet.csv"
    assert {p.name for p in gpkg.parent.iterdir()} == {"network.gpkg"}


def test_default_gpkg_reader_keeps_original_provider_dispatch(gpkg: Path, monkeypatch) -> None:
    """Keep GDAL precedence and the original SQLite fallback by default."""
    import pytuflow._tmf.gis_attr_driver as driver

    for enabled in (False, True):
        monkeypatch.setattr(driver, "has_gdal", enabled)
        instance = GISAttributes.__new__(GISAttributes, _source(gpkg))
        expected = driver.GDALGISAttributes if enabled else GPKGAttributes
        assert type(instance) is expected

    monkeypatch.setattr(driver, "has_gdal", False)
    with GISAttributes(_source(gpkg)) as reader:
        assert isinstance(reader, GPKGAttributes)
        assert next(iter(reader))["Inlet_Type"] == "inlet.csv"
    with GPKGAttributes(_source(gpkg)) as reader:
        assert next(iter(reader))["Inlet_Type"] == "inlet.csv"


def test_strict_gpkg_reader_requires_explicit_read_only_for_shared_connection(gpkg: Path) -> None:
    """Never reuse a pinned connection through the legacy mutable mode."""
    with readonly_gpkg(gpkg) as db:
        with pytest.raises(ValueError, match="read_only=True"):
            GPKGAttributes(_source(gpkg), connection=db)


def test_gpkg_direct_reader_rejects_absent_file_without_creating_it(tmp_path: Path) -> None:
    """Never create a missing main GeoPackage while reading attributes."""
    missing = tmp_path / "absent.gpkg"
    with pytest.raises(FileNotFoundError):
        with GPKGAttributes(TuflowPath(f"{missing} >> 1d_nwk_test"), read_only=True):
            pass
    assert not missing.exists()
    assert list(tmp_path.iterdir()) == []


def test_gpkg_reader_propagates_missing_layer(gpkg: Path) -> None:
    """Report missing layer metadata rather than swallowing SQLite errors."""
    with pytest.raises(ValueError, match="Expected one GeoPackage table"):
        with GPKGAttributes(TuflowPath(f"{gpkg} >> 1d_nwk_absent"), read_only=True):
            pass


def test_gpkg_reader_rejects_uncheckpointed_wal(gpkg: Path) -> None:
    """Reject nonempty committed WAL snapshots without changing sidecars."""
    from contextlib import closing

    with closing(sqlite3.connect(gpkg)) as editor:
        editor.execute("PRAGMA journal_mode=WAL")
        editor.execute("INSERT INTO gpkg_contents VALUES ('committed_in_wal')")
        editor.commit()
        wal = gpkg.with_name(gpkg.name + "-wal")
        assert wal.is_file() and wal.stat().st_size > 0
        with pytest.raises(GeoPackageSafetyError, match="wal"):
            with GPKGAttributes(_source(gpkg), read_only=True) as reader:
                list(reader)


def test_shared_connection_remains_open_and_uses_selected_columns(gpkg: Path) -> None:
    """Reuse the physical validator's pinned connection without closing it."""
    with readonly_gpkg(gpkg) as db:
        with GPKGAttributes(_source(gpkg), read_only=True, connection=db) as reader:
            assert list(reader.iter_selected((1, 10))) == [("M", "inlet.csv")]
        assert db.execute("SELECT COUNT(*) FROM gpkg_contents").fetchone()[0] == 1


def test_validation_reuses_reader_and_keeps_source_attribution(gpkg: Path) -> None:
    """Find network matrix sources using core reader metadata and SQL."""
    key = (gpkg, "1d_nwk_test", True)
    findings, count = inspect_gis_attribute_sources({key})
    assert count == 1
    assert findings[key].status == "present"
    assert findings[key].sources == (gpkg.parent / "inlet.csv",)


def test_nonspatial_attribute_table_remains_readable(tmp_path: Path) -> None:
    """Keep existing ordinary attribute-table reads without geometry metadata."""
    gpkg = tmp_path / "attributes.gpkg"
    with sqlite3.connect(gpkg) as db:
        db.execute(
            "CREATE TABLE gpkg_contents (table_name TEXT, data_type TEXT)"
        )
        db.execute(
            "INSERT INTO gpkg_contents VALUES ('lookup', 'attributes')"
        )
        db.execute(
            "CREATE TABLE lookup (fid INTEGER PRIMARY KEY, value TEXT, code TEXT)"
        )
        db.execute(
            "INSERT INTO lookup (value, code) VALUES ('alpha', 'one')"
        )

    with GPKGAttributes(TuflowPath(f"{gpkg} >> lookup"), read_only=True) as reader:
        assert isinstance(reader, GPKGAttributes)
        assert reader.field_names == ("value", "code")
        assert list(reader) == [{"value": "alpha", "code": "one"}]
    assert {p.name for p in tmp_path.iterdir()} == {"attributes.gpkg"}



def test_geometry_only_layer_yields_one_empty_record_per_feature(tmp_path: Path) -> None:
    """Keep feature counts even when a GeoPackage has no user attribute fields."""
    gpkg = tmp_path / "geometry_only.gpkg"
    with sqlite3.connect(gpkg) as db:
        db.execute("CREATE TABLE gpkg_contents (table_name TEXT)")
        db.execute(
            "CREATE TABLE gpkg_geometry_columns "
            "(table_name TEXT, column_name TEXT, geometry_type_name TEXT)"
        )
        db.execute("INSERT INTO gpkg_contents VALUES ('2d_empty')")
        db.execute(
            "INSERT INTO gpkg_geometry_columns VALUES "
            "('2d_empty', 'geom', 'POLYGON')"
        )
        db.execute(
            "CREATE TABLE \"2d_empty\" (fid INTEGER PRIMARY KEY, geom BLOB)"
        )
        db.executemany(
            "INSERT INTO \"2d_empty\" (geom) VALUES (?)",
            [(b"a",), (b"b",)],
        )

    with GPKGAttributes(TuflowPath(f"{gpkg} >> 2d_empty"), read_only=True) as reader:
        assert reader.field_names == ()
        assert list(reader) == [{}, {}]
    assert {item.name for item in tmp_path.iterdir()} == {"geometry_only.gpkg"}
