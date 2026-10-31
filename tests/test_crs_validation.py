"""CRS warnings are read-only, default-on and independent from pass/fail checks."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import rasterio
from pyproj import CRS
from rasterio.transform import from_origin

from pytuflow import TCF
from pytuflow._tmf.dependency_records import BatchDependencyRun, BatchInputReference
from pytuflow._tmf.file_reference import FileReference
from pytuflow.batch_validation import validate_batch_inputs
from pytuflow.validation import ValidationOptions, validate_dependencies


def _raster(path: Path, epsg: int | None) -> None:
    with rasterio.open(
        path, "w", driver="GTiff", width=2, height=2, count=1,
        dtype="float32", crs=f"EPSG:{epsg}" if epsg is not None else None,
        transform=from_origin(300, 500, 1, 1),
    ) as dataset:
        dataset.write(np.zeros((2, 2), dtype="float32"), 1)


def _reference(
    path: Path, *, raster: bool = False, vector: bool = False,
    layer: str | None = None,
) -> FileReference:
    return FileReference(
        base_directory=path.parent, expanded_value=path.name,
        path_pattern=path, layer_pattern=layer,
        origin="Read Grid Zpts" if raster else "Read GIS Code",
        requires_directory_scan=False, requires_layer_scan=layer is not None,
        requires_attribute_scan=False, requires_database_scan=False,
        requires_raster_metadata_scan=raster,
        requires_vector_crs_scan=vector,
    )


def _project(*references: FileReference) -> SimpleNamespace:
    links = tuple(
        BatchInputReference(
            input_uuid=f"source-{i}", command_index=i,
            owner_control_file=reference.base_directory / "model.tcf",
            line_number=i + 1, reference=reference,
        )
        for i, reference in enumerate(references)
    )
    run = BatchDependencyRun(
        index=0, flags="-s1 A", file_references=references,
        database_sources=(), database_activations=(), input_references=links,
    )
    return SimpleNamespace(runs=(run,))


def _options(**changes: object) -> ValidationOptions:
    return ValidationOptions(case_sensitivity=0, **changes)


def _model(tmp_path: Path, gis: str = "", tif: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        fpath=tmp_path / "model.tcf",
        config=SimpleNamespace(projection_wkt=gis, tif_projection=tif),
    )


def _snapshot(tmp_path: Path) -> dict[str, tuple[bytes, int]]:
    return {
        str(p.relative_to(tmp_path)): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in tmp_path.rglob("*") if p.is_file()
    }


def _gpkg(path: Path, layers: dict[str, int]) -> None:
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE gpkg_contents (table_name TEXT PRIMARY KEY)")
        db.execute(
            "CREATE TABLE gpkg_geometry_columns (table_name TEXT, srs_id INTEGER)"
        )
        db.execute(
            "CREATE TABLE gpkg_spatial_ref_sys (srs_id INTEGER, "
            "organization TEXT, organization_coordsys_id TEXT, definition TEXT)"
        )
        for epsg in sorted(set(layers.values())):
            db.execute(
                "INSERT INTO gpkg_spatial_ref_sys VALUES (?, 'EPSG', ?, 'undefined')",
                (epsg, str(epsg)),
            )
        for name, epsg in layers.items():
            db.execute("INSERT INTO gpkg_contents VALUES (?)", (name,))
            db.execute(
                "INSERT INTO gpkg_geometry_columns VALUES (?, ?)",
                (name, epsg),
            )


def test_defaults_are_enabled_and_controls_are_independent() -> None:
    options = ValidationOptions()
    assert options.check_raster_metadata
    assert options.check_crs
    assert not ValidationOptions(
        check_raster_metadata=False, check_crs=False,
    ).check_crs


def test_tcf_projection_is_reference_and_mismatch_only_warns(tmp_path: Path) -> None:
    matching, different = tmp_path / "same.tif", tmp_path / "different.tif"
    _raster(matching, 28350)
    _raster(different, 7850)
    before = _snapshot(tmp_path)
    result = validate_dependencies(
        _project(_reference(matching, raster=True),
                 _reference(different, raster=True)),
        options=_options(),
        model=_model(tmp_path, CRS.from_epsg(28350).to_wkt()),
    )
    assert result.passed
    assert result.raster_sources_examined == 2
    assert result.crs_sources_examined == 2
    assert len(result.warnings) == 1
    warning = result.warnings[0]
    assert warning.kind == "crs" and warning.severity == "warning"
    assert warning.status == "unresolved"
    assert warning.path == different
    assert "EPSG:7850" in warning.detail and "EPSG:28350" in warning.detail
    assert warning.owner_control_file == tmp_path / "model.tcf"
    assert _snapshot(tmp_path) == before


def test_without_tcf_projection_compare_selected_rasters_and_vectors(
    tmp_path: Path,
) -> None:
    reference = tmp_path / "reference.tif"
    different = tmp_path / "different.gpkg"
    _raster(reference, 28350)
    _gpkg(different, {"2d_code": 7850})
    before = _snapshot(tmp_path)
    result = validate_dependencies(
        _project(
            _reference(reference, raster=True),
            _reference(different, vector=True, layer="2d_code"),
        ),
        options=_options(), model=_model(tmp_path),
    )
    assert result.passed
    assert result.crs_sources_examined == 2
    assert len(result.warnings) == 1
    assert result.warnings[0].path == different
    assert result.warnings[0].layer == "2d_code"
    assert _snapshot(tmp_path) == before


def test_gpkg_layer_all_requires_separate_crs_comparison(tmp_path: Path) -> None:
    file = tmp_path / "layers.gpkg"
    _gpkg(file, {"2d_code_A": 28350, "2d_code_B": 7850})
    before = _snapshot(tmp_path)
    result = validate_dependencies(
        _project(_reference(file, vector=True, layer="all")),
        options=_options(), model=_model(tmp_path),
    )
    assert result.passed
    assert result.crs_sources_examined == 1
    assert [(f.layer, f.kind) for f in result.warnings] == [
        ("2d_code_B", "crs"),
    ]
    assert _snapshot(tmp_path) == before


def test_missing_invalid_crs_warn_and_do_not_crash(tmp_path: Path) -> None:
    path = tmp_path / "unprojected.tif"
    _raster(path, None)
    report = validate_dependencies(
        _project(_reference(path, raster=True)),
        options=_options(),
        model=_model(tmp_path, CRS.from_epsg(28350).to_wkt()),
    )
    assert report.passed
    assert len(report.warnings) == 1
    assert "no declared CRS" in report.warnings[0].detail

    # An invalid model CRS is itself a warning, never an uncaught PROJ error.
    invalid = validate_dependencies(
        _project(_reference(path, raster=True)),
        options=_options(), model=_model(tmp_path, "not a valid projection"),
    )
    assert invalid.passed
    assert len(invalid.warnings) >= 1
    assert any("Cannot interpret TCF projection" in f.detail
               for f in invalid.warnings)


def test_crs_can_be_switched_off_without_disabling_raster_headers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "grid.tif"
    _raster(path, 28350)
    original = rasterio.open

    class NoCRS:
        def __init__(self, handle: object) -> None:
            self.handle = handle

        def __enter__(self) -> "NoCRS":
            self.handle.__enter__()
            return self

        def __exit__(self, *args: object) -> None:
            self.handle.__exit__(*args)

        def __getattr__(self, name: str) -> object:
            if name in {"crs", "read", "statistics", "overviews"}:
                raise AssertionError(f"Forbidden metadata/pixel access: {name}")
            return getattr(self.handle, name)

    monkeypatch.setattr(
        rasterio, "open",
        lambda name, mode="r": NoCRS(original(name, mode=mode)),
    )
    report = validate_dependencies(
        _project(_reference(path, raster=True)),
        options=_options(check_crs=False),
    )
    assert report.passed
    assert report.raster_sources_examined == 1
    assert report.crs_sources_examined == 0
    assert not report.warnings


def test_crs_only_still_opens_raster_once(tmp_path: Path) -> None:
    path = tmp_path / "grid.tif"
    _raster(path, 7850)
    report = validate_dependencies(
        _project(_reference(path, raster=True)),
        model=_model(tmp_path, CRS.from_epsg(28350).to_wkt()),
        options=_options(check_raster_metadata=False),
    )
    assert report.passed
    assert report.raster_sources_examined == 1
    assert report.crs_sources_examined == 1
    assert any(f.kind == "crs" for f in report.warnings)
    assert not any(f.kind == "raster_metadata" for f in report.findings)


def test_readonly_vector_information_does_not_enumerate_features(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pyogrio

    path = tmp_path / "clip.shp"
    for suffix in (".shp", ".dbf", ".shx"):
        path.with_suffix(suffix).write_bytes(b"synthetic")
    called: list[Path] = []

    def metadata_only(name: Path, **kwargs: object) -> dict[str, object]:
        called.append(Path(name))
        assert kwargs.get("layer") is None
        return {"crs": "EPSG:28350"}

    monkeypatch.setattr(pyogrio, "read_info", metadata_only)
    report = validate_dependencies(
        _project(_reference(path, vector=True)),
        model=_model(tmp_path, CRS.from_epsg(28350).to_wkt()),
        options=_options(),
    )
    assert report.passed and not report.warnings
    assert called == [path]
    assert report.crs_sources_examined == 1


def test_batch_tcf_projection_warns_and_preserves_errors(tmp_path: Path) -> None:
    raster = tmp_path / "different.tif"
    _raster(raster, 7850)
    (tmp_path / "reference.prj").write_text(
        CRS.from_epsg(28350).to_wkt(), encoding="utf-8",
    )
    control = tmp_path / "model.tcf"
    control.write_text(
        "GIS Projection == reference.prj\nRead Grid Zpts == different.tif\n",
        encoding="utf-8",
    )
    model = TCF(control, case_sensitivity=0)
    result = validate_batch_inputs(model, ["-s1 A", "-s1 B"])
    assert result.passed, result.issues
    assert len([x for x in result.warnings if x.path == raster]) == 2
    assert result.validation.raster_sources_examined == 1
    assert result.validation.crs_sources_examined >= 1
    assert not result.issues


def test_batch_without_projection_warns_on_different_grids(tmp_path: Path) -> None:
    _raster(tmp_path / "one.tif", 28350)
    _raster(tmp_path / "two.tif", 7850)
    control = tmp_path / "model.tcf"
    control.write_text(
        "Read Grid Zpts == one.tif\nRead Grid Zpts == two.tif\n",
        encoding="utf-8",
    )
    model = TCF(control, case_sensitivity=0)
    result = validate_batch_inputs(model, ["-s1 A"])
    assert result.passed, result.issues
    assert len(result.warnings) == 1
    assert result.warnings[0].path == tmp_path / "two.tif"
    assert "selected input" in result.warnings[0].detail


def test_only_one_header_open_for_crs_and_raster_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "grid.tif"
    _raster(path, 28350)
    original = rasterio.open
    calls: list[str] = []

    def counted(name: object, mode: str = "r") -> object:
        calls.append(str(name))
        assert mode == "r"
        return original(name, mode=mode)

    monkeypatch.setattr(rasterio, "open", counted)
    report = validate_dependencies(
        _project(_reference(path, raster=True), _reference(path, raster=True)),
        options=_options(),
    )
    assert report.passed
    assert calls == [str(path)]
    assert report.raster_sources_examined == 1
    assert report.crs_sources_examined == 1
    assert not report.warnings


def test_invalid_tcf_gis_tif_crs_disagreement_is_advisory(tmp_path: Path) -> None:
    path = tmp_path / "terrain.tif"
    _raster(path, 28350)
    report = validate_dependencies(
        _project(_reference(path, raster=True)),
        options=_options(),
        model=_model(
            tmp_path, CRS.from_epsg(28350).to_wkt(),
            CRS.from_epsg(7850).to_wkt(),
        ),
    )
    assert report.passed
    assert any("TIF projection" in w.detail for w in report.warnings)
    assert not any(w.path == path for w in report.warnings)


def test_crs_only_warns_when_existing_raster_header_is_unreadable(
    tmp_path: Path,
) -> None:
    """Disabling blocking headers must not silently certify unreadable CRS."""
    path = tmp_path / "invalid.tif"
    path.write_bytes(b"not a raster")
    report = validate_dependencies(
        _project(_reference(path, raster=True)),
        options=_options(check_raster_metadata=False, check_crs=True),
    )
    assert report.passed
    assert not any(f.kind == "raster_metadata" for f in report.findings)
    assert len(report.warnings) == 1
    assert report.warnings[0].kind == "crs"
    assert "Cannot inspect raster CRS" in report.warnings[0].detail


@pytest.mark.parametrize("flags", [["-s1 A"], ["-s1 B"], ["-s1 A", "-s1 B"]])
def test_projection_reference_uses_each_selected_scenario(tmp_path: Path, flags: list[str]) -> None:
    """Inactive/later projection declarations must not change another run's CRS."""
    for name, epsg in (("A", 28350), ("B", 7850)):
        _raster(tmp_path / f"{name}.tif", epsg)
        (tmp_path / f"{name}.prj").write_text(CRS.from_epsg(epsg).to_wkt(), encoding="utf-8")
    control = tmp_path / "model.tcf"
    control.write_text(
        "If Scenario == A\nGIS Projection == A.prj\nRead Grid Zpts == A.tif\n"
        "Else If Scenario == B\nGIS Projection == B.prj\nRead Grid Zpts == B.tif\nEnd If\n",
        encoding="utf-8",
    )
    model = TCF(control, case_sensitivity=0)
    before = _snapshot(tmp_path)
    result = validate_batch_inputs(model, flags)
    assert result.passed, result.issues
    assert not result.warnings
    assert _snapshot(tmp_path) == before
    # A real mismatch must still be attributed to that run, not the model's
    # last projection (B), whose CRS happens to match this altered input.
    _raster(tmp_path / "A.tif", 7850)
    result = validate_batch_inputs(model, flags)
    expected = [index for index, flag in enumerate(flags) if flag == "-s1 A"]
    assert [w.run_index for w in result.warnings] == expected
    assert all("EPSG:28350" in w.detail and w.path == tmp_path / "A.tif" for w in result.warnings)


def test_unselected_projection_does_not_become_no_projection_reference(tmp_path: Path) -> None:
    """Each simulation without a projection chooses its own selected baseline."""
    _raster(tmp_path / "A.tif", 28350)
    _raster(tmp_path / "B.tif", 7850)
    (tmp_path / "reference.prj").write_text(CRS.from_epsg(7850).to_wkt(), encoding="utf-8")
    control = tmp_path / "model.tcf"
    control.write_text(
        "If Scenario == A\nRead Grid Zpts == A.tif\n"
        "Else If Scenario == B\nRead Grid Zpts == B.tif\n"
        "Else If Scenario == C\nGIS Projection == reference.prj\nEnd If\n",
        encoding="utf-8",
    )
    result = validate_batch_inputs(TCF(control, case_sensitivity=0), ["-s1 A", "-s1 B"])
    assert result.passed and not result.warnings


def test_selected_gis_projection_overrides_conflicting_tif_projection(tmp_path: Path) -> None:
    """Name both references once, and prefer the active GIS projection."""
    _raster(tmp_path / "projection.tif", 7850)
    _raster(tmp_path / "grid.tif", 28350)
    (tmp_path / "reference.prj").write_text(
        CRS.from_epsg(28350).to_wkt(), encoding="utf-8",
    )
    control = tmp_path / "model.tcf"
    control.write_text(
        "GIS Projection == reference.prj\nTIF Projection == projection.tif\nRead Grid Zpts == grid.tif\n",
        encoding="utf-8",
    )
    result = validate_batch_inputs(TCF(control, case_sensitivity=0), ["-s1 A"])
    assert result.passed
    assert len(result.warnings) == 1
    assert "TCF GIS projection EPSG:28350 and TIF projection EPSG:7850 differ" in result.warnings[0].detail
