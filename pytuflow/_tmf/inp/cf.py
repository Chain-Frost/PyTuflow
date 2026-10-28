import fnmatch
import logging
import os
import typing
from pathlib import Path

from .file import FileInput
from .inp_run_state import InputRunState
from ..context import Context
from ..abc.bld_state import BuildState
from .. import const



if typing.TYPE_CHECKING:
    # noinspection PyUnusedImports
    from ..cf.cf_run_state import ControlFileRunState

logger = logging.getLogger('pytuflow')



def _cached_filename_matches(
    filename: str, pattern: str, case_sensitivity: int
) -> bool:
    """Match a cached filename with TUFLOW's platform/-cs filename rules."""
    if os.name == 'nt':
        return fnmatch.fnmatchcase(filename.casefold(), pattern.casefold())
    if case_sensitivity == 0:
        return fnmatch.fnmatchcase(filename, pattern)
    if case_sensitivity == 1:
        stem, suffix = os.path.splitext(filename)
        requested_stem, requested_suffix = os.path.splitext(pattern)
        return (fnmatch.fnmatchcase(stem, requested_stem)
                and fnmatch.fnmatchcase(suffix.casefold(),
                                       requested_suffix.casefold()))
    if case_sensitivity == 2:
        return fnmatch.fnmatchcase(filename.casefold(), pattern.casefold())
    raise ValueError(f'Unsupported TUFLOW filename case policy: {case_sensitivity}')


def _cached_path_matches(
    filename: Path, pattern: Path, case_sensitivity: int
) -> bool:
    """Match cached inputs without probing disk; Linux directories stay strict."""
    parts = Path(os.path.normpath(str(filename))).parts
    expected = Path(os.path.normpath(str(pattern))).parts
    if len(parts) != len(expected):
        return False
    for actual_dir, expected_dir in zip(parts[:-1], expected[:-1]):
        if os.name == 'nt':
            actual_dir, expected_dir = actual_dir.casefold(), expected_dir.casefold()
        if not fnmatch.fnmatchcase(actual_dir, expected_dir):
            return False
    return _cached_filename_matches(parts[-1], expected[-1], case_sensitivity)


def select_deferred_children(
    build_input: typing.Any, references: typing.Iterable[typing.Any]
) -> tuple[typing.Any, ...]:
    """Select parsed includes using the model's filename case policy.

    Selection is confined to preloaded child paths: no filesystem or GIS I/O.
    Exact literal spellings take precedence over permitted case-relaxed
    alternatives. Wildcards can intentionally select several children.
    """
    from ..abc.run_state import ResolveError

    children = tuple(build_input.cf)
    loaded_paths = tuple(getattr(build_input, '_cf_loaded_paths', ()))
    if len(children) != len(loaded_paths):
        raise ResolveError(
            f'Cached nested control-file index incomplete: {build_input.lhs}'
        )
    case_sensitivity = getattr(build_input.config, 'case_sensitivity', 0)
    matched: set[int] = set()
    for ref in references:
        if ref.unresolved_variables:
            raise ResolveError(f'Unresolved child control file: {ref.path_pattern}')
        pattern = Path(os.path.normpath(str(ref.path_pattern)))
        literal = not any(char in str(pattern) for char in '*?[')
        selected: list[int] = []
        if literal:
            selected = [
                i for i, original in enumerate(loaded_paths)
                if os.path.normpath(str(original)) == str(pattern)
            ]
        if not selected:
            selected = [
                i for i, original in enumerate(loaded_paths)
                if _cached_path_matches(Path(original), pattern, case_sensitivity)
            ]
        if not selected and os.name == 'nt':
            # Mapped-drive and UNC aliases can name one initially parsed
            # include with different roots. Keep the established directory
            # + filename suffix fallback for Windows only. On Linux it could
            # silently select a different case-sensitive directory.
            for i, original in enumerate(loaded_paths):
                source = Path(os.path.normpath(str(original)))
                if (source.anchor and pattern.anchor
                        and source.anchor.casefold() != pattern.anchor.casefold()
                        and len(source.parts) >= 2 and len(pattern.parts) >= 2
                        and fnmatch.fnmatchcase(
                            source.parts[-2].casefold(), pattern.parts[-2].casefold()
                        ) and _cached_filename_matches(
                            source.name, pattern.name, case_sensitivity
                        )):
                    selected.append(i)
        if not selected:
            raise ResolveError(
                f'No cached nested control file for {ref.path_pattern}'
            )
        if len(selected) > 1 and literal:
            raise ResolveError(
                f'Ambiguous cached child for {ref.path_pattern}'
            )
        matched.update(selected)
    return tuple(children[i] for i in sorted(matched))


class ControlFileInputRunState(InputRunState):

    @property
    def files(self) -> list[Path]:
        """Include the CSV index and its referenced grids in eager file inputs.

        Secondary grid references come from the already-parsed database
        and active run context, without reopening the index or raster files.
        """
        primary = InputRunState.files.fget(self)
        if (getattr(self.ctx, 'file_resolution', 'eager') != 'eager'
                or not self._command.is_rainfall_grid_csv()):
            return primary
        secondary = [ref.path_pattern for ref in self.database_source_references]
        return list(dict.fromkeys([*primary, *secondary]))


    def _resolve_scope_in_context(self):
        super()._resolve_scope_in_context()
        deferred = getattr(self.ctx, 'file_resolution', 'eager') == 'deferred'
        if deferred and not isinstance(self.bs, ControlFileInput):
            # DatabaseInput shares this run-state class, but its cached .cf
            # entries are tables, not recursively parsed control files.
            # The explicit deferred_database_sources API handles database
            # contents; do not apply nested-control coverage checks here.
            return
        if deferred:
            # Use the paths captured when cached child control files were
            # loaded in the initial TCF parse. cf.fpath may be canonicalised
            # to a different UNC/mapped-drive spelling, and must not become
            # the only key for matching run-specific references.
            for child in select_deferred_children(self.bs, self.file_references):
                self.cf.append(child.context(context=self.ctx, parent=self.parent))
        else:
            for cf in self.bs.cf:
                # A direct NetCDF rainfall input exposes an empty database
                # object for compatibility; it has no database file to enter.
                if cf.fpath is not None and cf.fpath.resolve() == self.value.resolve():
                    self.cf.append(cf.context(context=self.ctx, parent=self.parent))


class ControlFileInput(FileInput):
    """
    Class for control files.Includes TRD, TEF

    | e.g.
    | :code:`Geometry Control File == geometry_control_file.tgc`
    """
    TUFLOW_TYPE = const.INPUT.CF

    @property
    def dirty(self) -> bool:
        return self._dirty or any(cf.dirty for cf in self.cf)

    @dirty.setter
    def dirty(self, value: bool):
        BuildState.dirty.fset(self, value)

    def _load(self, load_control_files: bool):
        super()._load(load_control_files)
        if load_control_files:
            self._load_control_files()

    def _load_files(self):
        super()._load_files()
        self._files_loaded = True

    def _load_control_files(self):
        from ..cf.get_control_file_class import get_control_file_class
        self._cf_loaded_paths = []
        for file in self.files:
            try:
                cf = get_control_file_class(file)(file, self._command.config, self.parent)
                self.cf.append(cf)
                self._cf_loaded_paths.append(Path(file))
            except Exception as e:
                logger.error(f'Error loading control file {file}. Command: {self._command}. Error: {e}')

    def context(self,
                run_context: str | dict[str, str] = '',
                context: Context | None = None,
                parent: 'ControlFileRunState | None' = None) -> ControlFileInputRunState:
        # docstring inherited
        ctx = context if context else Context(run_context, config=self.config)
        return ControlFileInputRunState(self, ctx, parent)


# Retain the original constructor before an extension can replace the method.
_CONTROL_FILE_INPUT_CONTEXT = ControlFileInput.context
