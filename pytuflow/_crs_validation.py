"""Read-only CRS metadata inspection and comparison for selected spatial inputs.

This module performs no geometry or pixel reads. GeoPackages use PyTUFLOW's
pinned immutable SQLite reader; other vector formats use the Pyogrio provider
already required by GeoPandas. There is no persistent file metadata cache.
"""

from __future__ import annotations

import fnmatch
import sqlite3
from collections.abc import Collection
from pathlib import Path

from pyproj import CRS

from ._tmf.gpkg_safety import readonly_gpkg

# One result per resolved layer: (layer name, CRS description, inspection error).
CRSLayer = tuple[str | None, str | None, str]
VectorCRSResult = dict[tuple[str | None, bool], tuple[CRSLayer, ...]]
_VECTOR_SUFFIXES = frozenset({".gpkg", ".shp", ".mif", ".mid", ".tab"})


def is_vector_source(path: Path) -> bool:
    """Recognise a selected GIS attribute-linked vector source by its suffix."""
    return path.suffix.casefold() in _VECTOR_SUFFIXES


def parse_crs(value: object) -> CRS:
    """Normalise WKT, EPSG strings, Rasterio CRS and other PROJ inputs."""
    try:
        return CRS.from_user_input(value)
    except (TypeError, ValueError, RuntimeError) as exc:
        raise ValueError(f"Invalid CRS metadata: {exc}") from exc


def same_crs(left: CRS, right: CRS) -> bool:
    """Compare coordinate systems semantically, ignoring axis-order spelling."""
    return left.equals(right, ignore_axis_order=True)


def crs_label(value: CRS) -> str:
    """Use a concise authority identifier where one is available."""
    authority = value.to_authority()
    if authority:
        return f"{authority[0]}:{authority[1]}"
    return value.name or "unnamed CRS"


def _selected_layers(
    names: tuple[str, ...], selector: str | None, implicit: bool, stem: str,
) -> tuple[str, ...]:
    """Match the same literal/default and wildcard selectors as the validator."""
    if selector is None:
        selector = stem
        implicit = True
    if implicit:
        return tuple(name for name in names if name.casefold() == stem.casefold())
    pattern = selector.strip().casefold()
    if pattern == "all":
        return names
    if any(symbol in pattern for symbol in "*?["):
        return tuple(name for name in names if fnmatch.fnmatchcase(name.casefold(), pattern))
    return tuple(name for name in names if name.casefold() == pattern)


def _gpkg_crs(
    path: Path, selectors: Collection[tuple[str | None, bool]],
) -> VectorCRSResult:
    """Read only selected vector-layer CRS records using safe immutable SQLite."""
    output: VectorCRSResult = {}
    try:
        with readonly_gpkg(path) as database:
            # The metadata tables may be missing in a malformed or simplified
            # fixture: a CRS warning should not itself fail file validation.
            names = tuple(
                str(row[0]) for row in database.execute(
                    "SELECT table_name FROM gpkg_contents ORDER BY table_name"
                )
            )
            try:
                spatial = {
                    str(table).casefold(): int(srid)
                    for table, srid in database.execute(
                        "SELECT table_name, srs_id FROM gpkg_geometry_columns"
                    )
                }
            except sqlite3.DatabaseError:
                spatial = {}
            try:
                definitions = {
                    int(row[0]): (str(row[1]), str(row[2]), str(row[3]))
                    for row in database.execute(
                        "SELECT srs_id, organization, organization_coordsys_id, "
                        "definition FROM gpkg_spatial_ref_sys"
                    )
                }
            except sqlite3.DatabaseError:
                definitions = {}

            for request in selectors:
                selector, implicit = request
                matched = _selected_layers(names, selector, implicit, path.stem)
                if not matched:
                    output[request] = (
                        (selector, None, "Selected GeoPackage vector layer was not found"),
                    )
                    continue
                layers: list[CRSLayer] = []
                for name in matched:
                    srid = spatial.get(name.casefold())
                    if srid is None:
                        layers.append(
                            (name, None, "GeoPackage layer lacks spatial CRS metadata")
                        )
                        continue
                    definition = definitions.get(srid)
                    if definition is None:
                        layers.append(
                            (name, None, f"GeoPackage spatial reference {srid} is undefined")
                        )
                        continue
                    organisation, code, wkt = definition
                    # EPSG and other authority codes may be more useful than a
                    # placeholder/invalid WKT. The comparison layer parses both.
                    if organisation.upper() != "NONE" and code not in {"0", "-1"}:
                        crs = f"{organisation}:{code}"
                    elif wkt and wkt.casefold() != "undefined":
                        crs = wkt
                    else:
                        crs = None
                    layers.append(
                        (name, crs, "" if crs else "GeoPackage layer has no defined CRS")
                    )
                output[request] = tuple(layers)
    except (OSError, sqlite3.DatabaseError, RuntimeError, ValueError) as exc:
        return {
            request: ((request[0], None, f"Cannot inspect vector CRS: {exc}"),)
            for request in selectors
        }
    return output


def inspect_vector_crs(
    path: Path, selectors: Collection[tuple[str | None, bool]],
) -> VectorCRSResult:
    """Inspect selected layers of one existing vector source, without features."""
    selected = frozenset(selectors)
    if not selected:
        return {}
    if path.suffix.casefold() == ".gpkg":
        return _gpkg_crs(path, selected)
    if not is_vector_source(path):
        return {
            selector: ((selector[0], None, "Unsupported vector CRS source format"),)
            for selector in selected
        }

    # GeoPandas >=1.0.1 requires Pyogrio; importing it here adds no dependency.
    # read_info() extracts driver and CRS metadata but never loads features.
    import pyogrio
    import rasterio

    output: VectorCRSResult = {}
    with rasterio.Env(GDAL_PAM_ENABLED="NO"):
        for request in selected:
            selector, _implicit = request
            try:
                metadata = pyogrio.read_info(path, layer=selector)
                value = metadata.get("crs")
                output[request] = (
                    (selector, str(value) if value else None,
                     "" if value else "Vector layer has no declared CRS"),
                )
            except (OSError, RuntimeError, ValueError, TypeError) as exc:
                output[request] = (
                    (selector, None, f"Cannot inspect vector CRS: {exc}"),
                )
    return output
