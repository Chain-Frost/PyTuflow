# Focused public typing — work package 08C / issue #14

This contribution adds a **bounded** typing contract for the existing,
deprecated `pytuflow.ResData` / `pytuflow.TUFLOW.ResData` facade, without
modifying any `.py` implementation or its public imports, defaults, errors,
identity or results. The approved minimum remains **Python 3.11**. The changes
belong to external upstream **PR B**, not PR A (existing-library fixes) or
PR C (optional deferred/batch/graph functionality).

## Source and classification

- Internal PR B base: `contrib/integration@251387feeae0e53e48fddae762d59b13b2a8f525`.
- Immutable comparison reference: `TUFLOW-Support/PyTuflow@cf908cc922ca8448ed6002834877b0b377329eae`.
- Reviewed historical reference: `phantom-branch/PyTuflow` merged PR #35,
  candidate `e46cb7bfe3cfa14f5cc28503dc7c7792f6a4cfef`. Its runtime
  method audit and synthetic regressions informed this small adoption.
  Historical PR #22's package marker and PR #37's deferred-module annotations
  are *not* blanket-transferred. PR #37 belongs to deferred PR C.

| Files | External PR B classification |
| --- | --- |
| `pytuflow/py.typed` and `pytuflow/TUFLOW.pyi` | Include; distributed typing artifacts |
| Two resource entries in `pyproject.toml` | Include; wheel packaging only |
| `tests/test_legacy_resdata_stub.py` | Include; signature, sentinel, return-shape and legacy compatibility regressions |
| `tests/typing/resdata_positive.py`, `resdata_negative.py` | Include; source files for external type consumers |
| `tests/typing/check_static.py` | Include as test harness or omit if upstream CI directly executes equivalent commands |
| This internal review record and `.github/workflows/public-typing-08c.yml` | Fork-only by default; curate necessary public usage instructions separately |

## Coverage and limitations

`TUFLOW.pyi` describes all **41 inherited ResData methods** and restores the
otherwise implicit runtime `os`, `warnings` and `ResData_GPKG` exports.
A `ResData` imported from the root is still the **same runtime class** from
`pytuflow.TUFLOW`. Constructor and method arguments/defaults are checked
against the real implementation. The stub makes no runtime imports.

- Time series may have **flat or nested** numeric, string or missing values;
  masked values may become `None` after `.tolist()`.
- Long profiles may contain XY pairs with NumPy/masked scalars **or** polygon
  lists for pipes and culverts. The existing `getPipes()` sentinel is
  `[[()]]` for unavailable results.
- `timesteps()` can return numbers, masked `None` entries or datetimes.
  `source()` may retain an `os.PathLike[str]` object; `units()` can be
  `None` for a GPKG reader.
- INFO and GPKG readers retain inherited format-specific exceptions for
  unsupported operations. Static declarations do **not** assert those calls
  are universally implemented or never raise.
- `py.typed` advertises the **partially annotated existing package** to type
  checkers; it is not a promise of complete or globally strict typing.
  Unannotated inherited modules may still be inferred incompletely. No
  broad strict typing migration is included.

We deliberately do not create literal-dependent overloads for free-form
result names or replace heterogeneous results with an unsound float-only
signature. No implicit numeric operations on string/masked series are promised.
No annotations for deferred execution modules are included.

## Validation

The dedicated fork-only Windows 3.11 / 3.12 / 3.14 workflow builds **sdist
and wheel**, checks marker/stub inclusion, then uninstalls the editable source
and installs the wheel. From outside the checkout with Python `-I`, it checks
package origin, synthetic facade regressions, strict **mypy** and strict
**Pyright** valid and deliberately-invalid consumers, and
`python -m mypy.stubtest pytuflow.TUFLOW`. It also executes the existing
`tests/test_public_api_contracts.py` unchanged.

The ordinary fast/full exact-head CI gates must additionally pass both the
immutable-upstream and exact-review-base comparisons. No static result or
QGIS/MDAL claim is made until independently executed and recorded. Since this
change contains no implementation, dynamic annotation or QGIS-backed import
changes, it does not by itself require a fresh native QGIS run; any discovered
import/provider regression will reopen that requirement.

## Reproduction

With the repository's existing configured interpreters, **without creating a
virtual environment**, install requirements and run:

```powershell
python -m pytest -q tests/test_legacy_resdata_stub.py tests/test_public_api_contracts.py
python -m build --sdist --wheel --no-isolation
# Install built wheel normally, change to a directory outside the checkout,
# copy tests/typing/*.py there, then:
python -I check_static.py
```

The external `contrib/upstream-typing` export must **not** be created from this
provisional integration base. It must be rebuilt after PR A is accepted on its
actual merged upstream commit and separately authorised by the owner.
