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

import re

_VALID_IDENTIFIER = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_\s\\-]*$")

def _safe_identifier(name: str) -> str:
    if not _VALID_IDENTIFIER.match(name):
        raise ValueError(f"Invalid SQL identifier: {name}")
    return '"' + name.replace('"', '""') + '"'


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
    """Read GeoPackage attributes using the existing stable, read-only opener.

    Ordinary reads preserve the previous SQLite behaviour. Setting
    ``read_only=True`` opts into pinned immutable inspection: an absent
    database is never created, SQL errors propagate, and unsaved WAL/rollback
    journals are rejected. Validation can reuse an existing pinned connection.
    """

    def __new__(
        cls, fpath: PathLike, *, read_only: bool = False,
        connection: sqlite3.Connection | None = None,
    ) -> "GPKGAttributes":
        """Construct a direct SQLite reader without switching to the GDAL factory."""
        return object.__new__(cls)

    def __init__(
        self, fpath: PathLike, *, read_only: bool = False,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        """Use legacy SQLite reads by default, or opt into strict read-only."""
        if connection is not None and not read_only:
            raise ValueError("connection requires read_only=True")
        self._read_only = read_only
        self._connection = connection
        self._owned_context = None
        self._db = None
        self._tname = ""
        self.field_names: tuple[str, ...] = ()
        if not read_only:
            # Preserve the previous direct-GPKGAttributes construction path,
            # including its metadata lookups and existing error policy.
            fpath = TuflowPath(fpath)
            self._tname = fpath.lyrname
            dbpath = fpath.dbpath
            self._tname = self._get_case_insensitive_table_name(dbpath, self._tname)
            self._geom_col = self._get_geom_col(dbpath, self._tname)
            self._fid_col = self._get_fid_col(dbpath, self._tname)
            super().__init__(dbpath)
            return
        super().__init__(fpath)

    def open(self) -> None:
        """Open SQLite using the selected legacy or strict inspection policy."""
        if not self._read_only:
            return
        from .gpkg_safety import readonly_gpkg

        try:
            if self._connection is None:
                self._owned_context = readonly_gpkg(self.fpath.dbpath)
                self._db = self._owned_context.__enter__()
            else:
                self._db = self._connection

            requested = self.fpath.lyrname or self.fpath.stem
            # Avoid SQLite's ASCII-only NOCASE rules when matching Unicode
            # layer names; ambiguous case-folded matches must not be guessed.
            matches = [
                str(row[0])
                for row in self._db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                if str(row[0]).casefold() == requested.casefold()
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"Expected one GeoPackage table {requested!r}, found {len(matches)}"
                )
            self._tname = matches[0]
            quoted = _quote_gpkg_identifier(self._tname)
            try:
                geometry_columns = {
                    str(row[0]).casefold()
                    for row in self._db.execute(
                        "SELECT column_name FROM gpkg_geometry_columns "
                        "WHERE lower(table_name) = lower(?)",
                        (self._tname,),
                    )
                }
            except sqlite3.OperationalError as exc:
                if "no such table" not in str(exc).lower():
                    raise
                # A GeoPackage containing only attribute tables need not
                # provide vector geometry metadata.
                geometry_columns = set()
            if not geometry_columns:
                # A valid nonspatial GeoPackage table has no geometry column.
                # Do not certify malformed spatial tables as attribute data.
                kind = self._db.execute(
                    "SELECT data_type FROM gpkg_contents "
                    "WHERE lower(table_name) = lower(?)",
                    (self._tname,),
                ).fetchone()
                if kind is None or str(kind[0]).casefold() != "attributes":
                    raise ValueError(
                        f"GeoPackage layer has no geometry column: {self._tname}"
                    )
            columns = self._db.execute(f"PRAGMA table_info({quoted})")
            self.field_names = tuple(
                str(name)
                for _, name, _, _, _, primary_key in columns
                if not primary_key and str(name).casefold() not in geometry_columns
            )
        except BaseException:
            self.close()
            raise

    def iter_selected(self, positions: tuple[int, ...]) -> typing.Iterator[tuple[object, ...]]:
        """Stream only selected fields without decoding GIS geometry blobs."""
        if self._db is None:
            raise RuntimeError("GeoPackage attributes reader is closed")
        if not positions:
            # Preserve one empty attribute mapping per feature even when a
            # geometry-only layer has no non-FID attribute fields.
            quoted = _quote_gpkg_identifier(self._tname)
            cursor = self._db.execute(f"SELECT 1 FROM {quoted}")
            try:
                for _ in cursor:
                    yield ()
            finally:
                cursor.close()
            return
        if any(index < 0 or index >= len(self.field_names) for index in positions):
            raise ValueError(f"Attribute index out of range for {self._tname}")
        fields = ", ".join(
            _quote_gpkg_identifier(self.field_names[index]) for index in positions
        )
        quoted = _quote_gpkg_identifier(self._tname)
        cursor = self._db.execute(f"SELECT {fields} FROM {quoted}")
        try:
            yield from cursor
        finally:
            cursor.close()

    def _iter_legacy(self) -> typing.Generator[OrderedDict, None, None]:
        import sqlite3
        try:
            self._db = sqlite3.connect(self.fpath)
            self._cursor = self._db.cursor()
            tname_quoted = _safe_identifier(self._tname)
            self._cursor.execute(f'SELECT * FROM {tname_quoted};')  # nosec B608
            for row in self._cursor:
                inds = [i for i, x in enumerate(self._cursor.description) if x[0] not in (self._fid_col, self._geom_col)]
                yield OrderedDict([(self._cursor.description[i][0], row[i]) for i in inds])
        except sqlite3.Error:
            pass
        finally:
            if self._db is not None:
                self._db.close()
            self._cursor = None
            self._db = None

    def __iter__(self) -> typing.Iterator[OrderedDict]:
        """Yield attributes using legacy or strict read-only mode."""
        if not self._read_only:
            yield from self._iter_legacy()
            return
        names = self.field_names
        for row in self.iter_selected(tuple(range(len(names)))):
            yield OrderedDict(zip(names, row, strict=True))

    def close(self) -> None:
        """Close an owned strict connection; legacy iteration owns its cursor."""
        if not self._read_only:
            return
        owned = self._owned_context
        self._owned_context = None
        self._db = None
        if owned is not None:
            owned.__exit__(None, None, None)

    @staticmethod
    def _get_case_insensitive_table_name(fpath: PathLike, tname: str) -> str:
        import sqlite3
        db = None
        try:
            db = sqlite3.connect(fpath)
            cursor = db.cursor()
            cursor.execute(
                'SELECT name FROM sqlite_master WHERE type="table" AND name=? COLLATE NOCASE;',
                (tname,)
            )
            tname = cursor.fetchone()[0]
        except sqlite3.Error:
            tname = tname
        finally:
            if db is not None:
                db.close()
        return tname

    @staticmethod
    def _get_geom_col(fpath: PathLike, tname: str) -> str:
        import sqlite3
        db = None
        try:
            db = sqlite3.connect(fpath)
            cursor = db.cursor()
            cursor.execute(
                'SELECT column_name FROM gpkg_geometry_columns WHERE table_name=?;',
                (tname,)
            )
            geom_col = cursor.fetchone()[0]
        except sqlite3.Error:
            geom_col = 'geometry'
        finally:
            if db is not None:
                db.close()
        return geom_col

    @staticmethod
    def _get_fid_col(fpath: PathLike, tname: str) -> str:
        import sqlite3
        db = None
        try:
            db = sqlite3.connect(fpath)
            cursor = db.cursor()
            cursor.execute('SELECT name FROM PRAGMA_TABLE_INFO(?) WHERE pk = 1;', (tname,))
            fid_col = cursor.fetchone()[0]
        except sqlite3.Error:
            fid_col = 'fid'
        finally:
            if db is not None:
                db.close()
        return fid_col


def _quote_gpkg_identifier(value: str) -> str:
    """Quote a trusted SQLite metadata identifier, preserving Unicode names."""
    return '"' + value.replace('"', '""') + '"'
