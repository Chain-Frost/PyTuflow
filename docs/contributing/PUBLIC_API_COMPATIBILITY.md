# Public API compatibility inventory — work package 08B / issue #13

Status: **initial reviewed inventory and executable contracts**; no production API
changes are authorised or introduced here. This is an internal contribution
review document, not an assertion that all incidental Python attributes are
forever supported.

## Revisions and source selection

| Role | Exact revision |
| --- | --- |
| Official original-library comparison | `TUFLOW-Support/PyTuflow@cf908cc922ca8448ed6002834877b0b377329eae` |
| Initial branch base (08A merged) | `Chain-Frost/PyTuflow:contrib/integration@301a1f8f1de9a71bda4423608abe839394a9e325` |
| Previous review base (08A + eager Linux 09 merged) | `Chain-Frost/PyTuflow:contrib/integration@e9d2dcadc69e25d9cc153041230534b827e009ef` |
| Current review base (also includes result-time PR #23) | `Chain-Frost/PyTuflow:contrib/integration@748068b77fa429485fe1df7be21927c64de1123e` |
| Reviewed reference | `phantom-branch/PyTuflow` merged PR #22, source head `3c3385b7dd4464de2355dff81891a520087babc7` |
| Candidate | `contrib/fix-public-api-contracts-13`; obtain and record its full SHA after all commits |

Package 08A / internal PR #27 already integrated the selected import and logging
improvements from phantom #22. Do **not** repeat its production changes in 08B.
Package 08C / #14 owns bounded public typing in separately curated upstream PR B, including any future `py.typed` marker.
Python **3.11 is the minimum**, not the higher minimum advertised by parts of
the reference fork. This package is in **upstream PR A**; upstream PR B is focused public typing and upstream PR C is optional deferred/batch/graph execution.

## Import/export inventory (checked against source)

### A. Root `pytuflow` and TMF model facade

The root package imports the following from `pytuflow._tmf` and exposes their
**same Python objects**, rather than replacement wrappers:

- **Control files:** `TCF`, `ECF`, `TGC`, `TBC`, `TEF`, `QCF`, `TOC`,
  `TRFC`, `TSCF`, `TESF`, `ADCF`, `FVC`, `FVWQ`, `FVSed`, `FVPTM`.
- **Databases:** `BCDatabase`, `MatDatabase`, `PitInletDatabase`,
  `RainfallDatabase`, `SoilDatabase`, `CrossSectionDatabase`.
- **Inputs and context:** `SettingInput`, `FileInput`, `FolderInput`,
  `GisInput`, `GridInput`, `TinInput`, `ControlFileInput`,
  `DatabaseInput`, `CommentInput`, `BlockControlInput`,
  `BCBlockControlInput`, `Context`, `Scope`, `TuflowPath`.
- **Binaries/logging:** `register_tuflow_binary`,
  `register_tuflow_binary_folder`, `tuflow_binaries`,
  `set_logging_level`.

Other concrete symbols such as run states, base classes and FV binary
registration remain imported from `_tmf` by the historical wildcard. They
should be inventoried before *any* future export tightening. The root
`__all__` is currently dynamically built using existing globals and the
result-reader export list; it includes some incidental names. **Do not
replace that list with a restrictive curated `__all__` as a minor fix.**
Both explicit imports and `from pytuflow import *` are used by consumers.

The historical root `ResData` class remains importable; its constructor
emits `DeprecationWarning` directing users to `TPC`/`INFO`. This is a
deprecation, not approval to remove it. The root also exports `GXY` and
`FMDAT` (from `_fm`), `HPCProject`, `FVProject` (from `project`),
`TuflowBinaries` and `pytuflow_logging` (from `util`).
`TemplateManager` remains available from `pytuflow.project`, and
`ResultTypeError` from `pytuflow.results`; neither is newly promised
as a direct root alias.

### B. Complete explicit result-reader facade

All **25** entries below exist at both `pytuflow.<Name>` and
`pytuflow._outputs.<Name>`. The source for each is the existing output module
on the right. Both facade routes must return the **same object**, including
after a lazy import. The canonical definition/module and class identity must
not be replaced to make importing more convenient.

| Public names | Existing `pytuflow._outputs` source modules |
| --- | --- |
| `INFO`, `TPC` | `info`, `tpc` |
| `GPKG1D`, `GPKG2D`, `GPKGRL` | `gpkg_1d`, `gpkg_2d`, `gpkg_rl` |
| `FMTS`, `FVBCTide` | `fm_ts`, `fv_bc_tide` |
| `HydTablesCheck`, `BCTablesCheck` | `hyd_tables_check`, `bc_tables_check` |
| `CrossSections`, `DATCrossSections` | `cross_sections`, `fm_dat` |
| `XMDF`, `NCMesh`, `CATCHJson`, `DAT`, `NCGrid`, `LP2D` | `xmdf`, `nc_mesh`, `catch_json`, `dat`, `nc_grid`, `lp2d` |
| `MapOutput`, `TimeSeries`, `TabularOutput` | `map_output`, `time_series`, `tabular_output` |
| `Mesh`, `Grid`, `GridMesh`, `Output`, `FormatConvention` | `mesh`, `grid`, `grid_mesh`, `output`, `pymesh` |

The original upstream eagerly re-exported these 25 readers from
`_outputs/__init__.py` and mutated `sys.path` at root import.
Merged 08A changed *when* they import and removed the path mutation while
retaining these public routes and their original object identities.
`dir()`, unknown-name `AttributeError` and wildcard imports are covered by
the existing 08A tests as well as focused 08B checks.

### C. Constructor and configuration defaults to retain

These are **existing** default contracts, not proposed signatures or
annotations. `tests/test_public_api_contracts.py` asserts parameter names,
ordering, and defaults independently of interpreter-dependent annotation text.

| Entry point | Existing public call form |
| --- | --- |
| `TCF` | `TCF(fpath=None, *, case_sensitivity=None, **kwargs)` — accepted keyword-only eager Linux `-cs` option from #15 / PR #29 |
| `Context` | `Context(context=(), config=None)` |
| `Scope` | `Scope(type_name, name='', var=None, else_=False)` |
| `TPC` | `TPC(fpath)` |
| `XMDF` | `XMDF(fpath, twodm=None, driver='v1.1')` |
| `NCMesh` | `NCMesh(fpath, driver='v1.1')` |
| `NCGrid` | `NCGrid(fpath)` |
| `ResData` | `ResData(file=None)`, deprecated but retained |
| Root and utility logging | `set_logging_level(level='WARNING', log_to_file=None)` |

Do not silently switch default mesh drivers, alter positional arguments,
change logging handler ownership, change the interpretation of missing paths,
rename the `pytuflow-project` console script, or move defining classes into
new module paths. Actual method return values and error semantics require
focused, data-backed regressions when a particular production fix touches
them; import signatures alone do not establish result parity.

## User-facing examples (supported existing routes)

```python
from pytuflow import TCF, Context, NCMesh, XMDF, TPC
from pytuflow._outputs import NCMesh as ResultNCMesh
from pytuflow.project import HPCProject, FVProject, TemplateManager
from pytuflow.results import ResultTypeError

assert NCMesh is ResultNCMesh
context = Context({"s1": "DEV", "e1": "01.0p"})
# TCF("runs/model.tcf")
# TCF("runs/model.tcf", case_sensitivity=2)  # explicit eager -cs2 policy
# NCMesh("results/model.nc")  # existing default driver="v1.1"
# XMDF("results/model.xmdf", twodm="results/model.2dm")
# TPC("results/model.tpc")
```

The commented examples require real external model/result files.
Driver availability is **separate** from import availability; explicit
QGIS/MDAL or Python backends may require additional compatible native
packages. No example above claims a QGIS runtime is available on CI runners.

## Compatibility review and decisions

| Finding or proposed change | Decision / workstream |
| --- | --- |
| Stable root, `_tmf`, `_outputs`, `project`, `util` imports, 25 outputs | **Preserve**; tested in 08B, implementation already done in 08A |
| Identity, defining module, star imports, unknown-result errors | **Preserve**, including pickled class references where checked; no facades redesigned |
| Existing constructor parameters and `v1.1` mesh defaults | **Preserve**; changing defaults requires explicit owner decision and migration documentation |
| Legacy `ResData` deprecation | Keep class, warning and legacy constructor; removal is **not** approved |
| Missing native backend diagnostics and legacy logging behaviour | 08A / #12; do not reimplement in 08B |
| Public annotations, installed typing consumer, `py.typed` | 08C / #14 after this inventory; no typing rollout here |
| Optional deferred `file_resolution`, batches, graph reuse and deferred-specific controls | **Upstream PR C only** (#16–#21); do not surface or default-enable in PR A; existing eager raster cache correctness remains PR A package 06 |
| Eager Linux filename case policy | **Accepted** package 09 / #15 / merged PR #29; optional keyword-only `TCF(case_sensitivity=0|1|2)` is now a reviewed public extension; omitted/default `None` keeps the configuration path, whose Linux default is strict `-cs0`. See `LINUX_CASE_POLICY.md` |
| `Context` documentation describes list arguments/scopes, but inherited `__init__` only dispatches `dict` and `str` | **Unresolved inherited API/documentation discrepancy**; a functional fix would need separately justified before/after tests and owner review, not an undocumented change in 08B |
| `docs/api.rst` repeats `TSCF` | Minor documentation cleanup candidate; no runtime change |
| Dynamic root `__all__` includes names inherited from wildcard imports and incidental globals | Audit consumer impact before narrowing; do not silently turn it into a strict allowlist |

## Open decisions: significance and recommended disposition

There is **no unapproved breaking change in this test/documentation-only 08B
candidate**. The remaining questions are recorded for deliberate future
changes rather than prerequisites to accepting the inventory:

1. **`Context` input forms — inherited discrepancy (follow-up needed).**
   Its documentation advertises list-of-arguments and list-of-scopes input, but
   the constructor dispatches only dictionaries or strings; a nonempty list
   does not get parsed. Prefer adding an isolated reproduction and deciding
   whether to implement the documented forms in an explicit correctness
   work package, or correct the documentation to describe the actual API.
   Do not freeze silent list-ignoring as a supported contract.
2. **Root export support level — no immediate change.** The root wildcard
   currently exposes more than the curated documentation (roughly 90 named
   `_tmf` imports plus additional convenience globals). Keep them available
   for compatibility. Designating each as explicitly stable vs incidental,
   and tightening `__all__`, requires downstream consumer evidence and
   an agreed migration policy. No narrowing is required for this PR.
3. **Legacy `ResData` deprecation — preserve for PR A.** No removal date
   or breaking-change authorisation exists. The current warning and import
   route are regression-tested; discuss removal only in a future major-version
   policy.
4. **Type surface — assigned to #14.** Introduce only coherent Python 3.11
   compatible annotations, the facade stub and optional `py.typed` in 08C.
   Deferred-only additions remain assigned to upstream PR C; existing public typing is upstream PR B.

Do **not** treat decisions 1–4 as an excuse to combine unrelated runtime
changes into this 08B regression inventory. No owner decision is needed
to retain the present compatible behaviour and merge a validated test-only PR.

## Acceptance and ownership

- 08B changes **only** `docs/contributing/PUBLIC_API_COMPATIBILITY.md`,
  `tests/test_public_api_contracts.py` and the dedicated workflow.
  Production exports, dependencies, project signatures, geometry code and
  parser code stay unchanged.
- Source and wheel contract tests must pass on **Python 3.11, 3.12 and 3.14**.
  A separate Windows workflow installs a wheel outside the checkout and checks
  the console-script entry point. GitHub fast and full gates still require
  their own fresh strict upstream and exact-review-base regression evidence.
- The contract tests are **regression candidates for upstream PR A**; this
  inventory/handover and the CI workflow are **fork-only** by default. The
  source changes in this initial 08B PR are zero.
- Real QGIS/MDAL validation is **not claimed** by these constructor/import
  tests. When a future API adjustment affects native output readers, rerun
  native provider acceptance on its exact head.
- Test coverage is deliberately *representative*: it freezes explicitly
  documented routes, symbols and defaults, not every accidental runtime
  attribute or every function/method. Extend on evidence of actual consumers
  before proposing any compatibility break.

Local focused check (with dependencies in the configured interpreter,
**no virtual environment required**):

```console
python -m pytest -q tests/test_public_api_contracts.py
python ci/python_compatibility.py
```

Do not merge based solely on this initial inventory. Check current-head
reviews/CI and any inherited failure differences before manual integration.
