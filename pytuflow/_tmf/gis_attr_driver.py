import sqlite3
import typing
from collections import OrderedDict
from collections.abc import Iterable
from pathlib import Path
# noinspection PyProtectedMember
try:
    from dbfread import DBF
    has_dbf_read = True
except ImportError:
    DBF = 'DBF'
    has_dbf_read = False

from .tfpathlib import TuflowPath
from .tmf_types import PathLike

try:
    from osgeo import ogr
    has_gdal = True
except ImportError:
    from .stubs.ogr_ import ogr_ as ogr
    has_gdal = False

if not has_dbf_read and not has_gdal:
    raise ImportError('Requires either GDAL or dbfread library')

T = typing.TypeVar("T")


class GISAttributes(typing.Generic[T], Iterable[T]):
    """Utility class for iterating over a GIS layer to obtain the attributes."""

    def __iter__(self) -> typing.Generator[OrderedDict, None, None]:
        pass

    def __new__(cls, fpath: PathLike) -> object:
        if has_gdal:
            cls = GDALGISAttributes
            return super().__new__(cls)
        fpath = TuflowPath(fpath)
        if '>>' in fpath:
            fpath = fpath.split(' >> ')[0]
        fpath = Path(fpath)
        if fpath.suffix.lower() == '.dbf' or fpath.suffix.lower() == '.shp':
            cls = DBFAttributes
        elif fpath.suffix.lower() == '.mid' or fpath.suffix.lower() == '.mif':
            cls = MIDAttributes
        elif fpath.suffix.lower() == '.gpkg':
            cls = GPKGAttributes
        return super().__new__(cls)

    def __init__(self, fpath: PathLike) -> None:
        """
        Parameters
        ----------
        fpath : PathLike
            The file path to the GIS file.
        """
        self.fpath = TuflowPath(fpath)
        self._db = None
        self.open()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self) -> None:
        """Open the GIS file for reading."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the GIS file."""
        raise NotImplementedError


class GDALGISAttributes(GISAttributes):

    def __init__(self, fpath: PathLike) -> None:
        from .gis import get_driver_name_from_extension
        fpath = TuflowPath(fpath)
        self._driver = get_driver_name_from_extension('vector', fpath.suffix)
        self._lyr = None
        self._ds = None
        super().__init__(fpath)

    def __iter__(self):
        for feat in self._lyr:
            d = OrderedDict()
            for i in range(feat.GetFieldCount()):
                fld = feat.GetFieldDefnRef(i)
                d[fld.GetName()] = feat.GetField(i)
            yield d

    def open(self) -> None:
        self._ds = ogr.Open(str(self.fpath.dbpath))
        self._lyr = self._ds.GetLayer(self.fpath.lyrname)

    def close(self) -> None:
        self._lyr = None
        self._ds = None


class DBFAttributes(GISAttributes):
    """Utility class for iterating over a SHP/DBF file to obtain the attributes."""

    def __init__(self, fpath: PathLike) -> None:
        # docstring inherited
        fpath = TuflowPath(fpath).dbpath
        if fpath.suffix.lower() == '.shp':
            if fpath.with_suffix('.dbf').exists():
                fpath = fpath.with_suffix('.dbf')
            elif fpath.with_suffix('.DBF').exists():
                fpath = fpath.with_suffix('.DBF')
            else:
                raise FileNotFoundError(f'Accompanying DBF file not found for: {self.fpath}')
        super().__init__(fpath)

    def __iter__(self) -> typing.Generator[OrderedDict, None, None]:
        for record in self._db:
            yield record

    def open(self) -> None:
        # docstring inherited
        self._db = DBF(self.fpath)

    def close(self) -> None:
        # docstring inherited
        self._db = None


def mapinfo_companion_path(fpath: PathLike) -> Path:
    """Find the MIF/MID companion under PyTUFLOW's existing naming rules.

    Only the lowercase and uppercase extension forms are accepted, with the
    original filename stem unchanged. This is a path check, not a second
    parser; it is shared with explicit physical input validation.
    """
    path = TuflowPath(fpath).dbpath
    suffix = path.suffix.lower()
    if suffix not in ('.mif', '.mid'):
        raise ValueError(f'Expected a MapInfo MIF or MID file: {path}')
    wanted = '.mid' if suffix == '.mif' else '.mif'
    for candidate in (path.with_suffix(wanted), path.with_suffix(wanted.upper())):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f'Accompanying {wanted[1:].upper()} file not found for: {path}'
    )


class MIDAttributes(GISAttributes):
    """Utility class for iterating over a MIF/MID file to obtain the attributes."""

    def __init__(self, fpath: PathLike) -> None:
        # docstring inherited
        fpath = TuflowPath(fpath).dbpath
        self._col_names = []
        if fpath.suffix.lower() == '.mif':
            self._mif = fpath
            fpath = mapinfo_companion_path(fpath)
        else:
            self._mif = mapinfo_companion_path(fpath)
        super().__init__(fpath)

    def __iter__(self) -> typing.Generator[OrderedDict, None, None]:
        for line in self._db:
            yield OrderedDict(zip(self._col_names, [x.strip(' \t\n"\'') for x in line.split(',')]))

    def open(self) -> None:
        # docstring inherited
        self._db = self.fpath.open()
        ncol = 0
        with self._mif.open() as f:
            for line in f:
                if line.startswith('Columns'):
                    ncol = int(line.split()[1])
                    for i in range(ncol):
                        self._col_names.append(f.readline().split()[0])
                    break
        if not ncol:
            raise Exception(f'MIF file must have at least one attribute column: {self._mif}')

    def close(self) -> None:
        # docstring inherited
        self._db.close()
        self._db = None


class GPKGAttributes(GISAttributes):
    """Read GeoPackage attributes with optional strict read-only inspection.

    Normal reads retain the existing SQLite behaviour, including the
    GDAL-first selection in GISAttributes. Setting read_only=True uses a
    pinned read-only database, rejects unsafe journals, and propagates
    inspection errors. A caller-supplied connection must already be pinned.
    """

    def __new__(
        cls, fpath: PathLike, *, read_only: bool = False,
        connection: sqlite3.Connection | None = None,
    ) -> "GPKGAttributes":
        """Construct the selected SQLite attribute reader directly."""
        return object.__new__(cls)

    def __init__(
        self, fpath: PathLike, *, read_only: bool = False,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        """Prepare attribute metadata with a shared read-only option."""
        if connection is not None and not read_only:
            raise ValueError("connection requires read_only=True")
        self._read_only = read_only
        self._connection = connection
        self._owned_context = None
        self._db = None
        self._tname = ""
        self.field_names: tuple[str, ...] = ()
        super().__init__(fpath)

    def open(self) -> None:
        """Read layer metadata once, using the selected SQLite access mode."""
        from contextlib import closing

        from .gpkg_safety import readonly_gpkg

        try:
            if self._read_only:
                if self._connection is None:
                    self._owned_context = readonly_gpkg(self.fpath.dbpath)
                    self._db = self._owned_context.__enter__()
                else:
                    self._db = self._connection
                self._read_metadata(self._db)
            else:
                # Legacy mode remains independent of immutable WAL checks.
                # Metadata and feature rows share the same query logic.
                with closing(sqlite3.connect(self.fpath.dbpath)) as connection:
                    self._read_metadata(connection)
        except BaseException:
            self.close()
            raise

    def _read_metadata(self, connection: sqlite3.Connection) -> None:
        """Identify the selected table, geometry and ordered attribute fields."""
        wanted = self.fpath.lyrname or self.fpath.stem
        matches = [
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
            if str(row[0]).casefold() == wanted.casefold()
        ]
        if not matches or (self._read_only and len(matches) != 1):
            raise ValueError(
                f"Expected one GeoPackage table {wanted!r}, found {len(matches)}"
            )
        self._tname = matches[0]
        quoted = _quote_gpkg_identifier(self._tname)
        geometry: set[str] = set()
        try:
            geometry = {
                str(row[0]).casefold()
                for row in connection.execute(
                    "SELECT column_name FROM gpkg_geometry_columns "
                    "WHERE lower(table_name) = lower(?)",
                    (self._tname,),
                )
            }
        except sqlite3.OperationalError as exc:
            if "no such table" not in str(exc).lower():
                raise
        if not geometry:
            if self._read_only:
                # Valid nonspatial tables have no geometry column; malformed
                # spatial tables must not silently pass strict validation.
                kind = connection.execute(
                    "SELECT data_type FROM gpkg_contents "
                    "WHERE lower(table_name) = lower(?)",
                    (self._tname,),
                ).fetchone()
                if kind is None or str(kind[0]).casefold() != "attributes":
                    raise ValueError(
                        f"GeoPackage layer has no geometry column: {self._tname}"
                    )
            else:
                geometry.add("geometry")
        columns = tuple(connection.execute(f"PRAGMA table_info({quoted})"))
        identifiers = {
            str(name).casefold()
            for _, name, _, _, _, primary_key in columns
            if primary_key
        }
        if not identifiers and not self._read_only:
            identifiers.add("fid")
        self.field_names = tuple(
            str(name)
            for _, name, _, _, _, _ in columns
            if str(name).casefold() not in identifiers
            and str(name).casefold() not in geometry
        )

    def _rows(
        self, connection: sqlite3.Connection, positions: tuple[int, ...],
    ) -> typing.Iterator[tuple[object, ...]]:
        """Select only requested fields without reading geometry blobs."""
        if any(index < 0 or index >= len(self.field_names) for index in positions):
            raise ValueError(f"Attribute index out of range for {self._tname}")
        columns = (
            ", ".join(
                _quote_gpkg_identifier(self.field_names[index])
                for index in positions
            )
            if positions else "1"
        )
        quoted = _quote_gpkg_identifier(self._tname)
        cursor = connection.execute(f"SELECT {columns} FROM {quoted}")
        try:
            for row in cursor:
                yield tuple(row) if positions else ()
        finally:
            cursor.close()

    def iter_selected(
        self, positions: tuple[int, ...],
    ) -> typing.Iterator[tuple[object, ...]]:
        """Stream selected attributes under the chosen SQLite error policy."""
        if self._read_only:
            if self._db is None:
                raise RuntimeError("GeoPackage attributes reader is closed")
            yield from self._rows(self._db, positions)
        else:
            from contextlib import closing

            try:
                with closing(sqlite3.connect(self.fpath.dbpath)) as database:
                    yield from self._rows(database, positions)
            except sqlite3.Error:
                # Match the existing eager reader's permissive SQL policy.
                return

    def __iter__(self) -> typing.Iterator[OrderedDict]:
        """Yield attribute mappings in their original GeoPackage field order."""
        names = self.field_names
        for row in self.iter_selected(tuple(range(len(names)))):
            yield OrderedDict(zip(names, row, strict=True))

    def close(self) -> None:
        """Close the pinned reader only when this instance owns it."""
        owned = self._owned_context
        self._owned_context = None
        self._db = None
        if owned is not None:
            owned.__exit__(None, None, None)


def _quote_gpkg_identifier(value: str) -> str:
    """Quote a SQLite metadata identifier, preserving Unicode names."""
    return '"' + value.replace('"', '""') + '"'
