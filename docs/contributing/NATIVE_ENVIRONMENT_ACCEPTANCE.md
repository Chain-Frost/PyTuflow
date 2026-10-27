# Native Windows QGIS acceptance: issues 30 and 31

Validated 27 October 2026 for [issue 30](https://github.com/Chain-Frost/PyTuflow/issues/30),
[issue 31](https://github.com/Chain-Frost/PyTuflow/issues/31) and
[PR 33](https://github.com/Chain-Frost/PyTuflow/pull/33). This is fork-only
support/diagnostic evidence, excluded from external upstream curation by default.
No production modules, existing assertions, references, project dependency
metadata or system/OSGeo4W packages were changed.

## Frozen revisions and results

| Revision | Exact SHA | Updated profile: QGIS | Updated profile: Python mesh |
| --- | --- | ---: | ---: |
| Official upstream | `cf908cc922ca8448ed6002834877b0b377329eae` | 239 passed | 110 passed |
| PR 23 exact base | `7444bf5abc41cf76f3786fd04e11c26fb9482d4a` | 239 passed | 110 passed |
| PR 23 head | `a858ecd0e90f162f4dde7c2e2392704edc9ac832` | 239 passed | 110 passed |
| PR 33 exact base | `2a516733caec0e7f2ab7c91eef5d5ca3dad6f2eb` | 239 passed | 110 passed |
| PR 33 input head | `aaff74e7a3e65cf7f2a1a50f8463e673b014a8b6` | 239 passed | 110 passed |

All updated-profile raw exits are zero, without errors or skips. Both PRs pass
strict upstream and exact-base comparisons for both groups. The original VTK
profile independently reproduces **237 passed / 2 failed** on upstream, PR 23
base and PR 23 head. All 237 old successes remain successes; the same two
CATCHJson failures become passes, with no new failures:

- `tests/test_map_output.py::TestCATCHJson::test_loading_ontop_netcdf4_driver`
- `tests/test_map_output.py::TestCATCHJson::test_loading_ontop_qgis_driver`

PR 23's unchanged focused time suite passes **108/108** in initialized QGIS.
Existing groups cover geometry, surface, point, time-series and section outputs
against unchanged expectations. This does not fix the separate QGIS-geometry
public `cell_position` limitation in issue 9.

Runs use unchanged `ci/run_regression.py --group qgis` (also `--group python_mesh`
for the updated profile), immutable snapshots and the existing
`ci/compare_regression.py --required-group qgis --required-group python_mesh`.
Every source report records `checkout_unchanged=true`; assertions, warning
policy and references are preserved. The table identifies frozen input
revisions; implementation-head checks are reported separately on PR 33.

## Accepted native profile

The installation supplies QGIS **4.2.3**, Python **3.12.15**, Qt **6.11.0**,
GDAL **3.13.3**, NumPy **2.5.4**, pandas **3.0.6**, netCDF4 **1.7.5** and
operational MDAL. MDAL has no independently exposed version here; QGIS version
and provider DLL hash identify the tested binary. Actual module origins and
loaded HDF5, VTK, GDAL, Qt, Python and MDAL DLLs were recorded and hashed.

| Add-on | Original VTK reproduction | Accepted profile |
| --- | --- | --- |
| PyVista | 0.48.2 | 0.49.1 |
| VTK | 9.6.1 | 9.7.1 |
| Rasterio | 1.5.0 | 1.5.2 |
| h5py for this comparison | 3.14.0 | 3.14.0 |
| HDF5 for this comparison | 1.14.6 | 1.14.6 |

Compatible h5py is held constant to separate issue 30 from issue 31. The original
h5py 3.16 profile is reproduced separately below, not silently accepted.
The complete original native combination also reproduces **237 passed / 2 failed**
on PR 23, with the raw `0xc0000139` diagnostic retained in its native test log.
[Additive constraints](../../ci/diagnostics/requirements-qgis312-additions.txt)
pin the accepted Windows Python 3.12 wheels. In the initialized QGIS shell:

```text
python -m pip install --target <outside-repo-addons> --no-deps -r ci/diagnostics/requirements-qgis312-additions.txt
```

Check missing transitive add-ons separately; preserve bundled NumPy, GDAL, Qt,
netCDF4 and other OSGeo4W libraries. Verify actual imports before accepting a new
installation. This uses ordinary external directories, not virtual environments.

**No global dependency minimum/upper-bound change is justified by this profile
alone.** Keep Python 3.11 support: [NumPy 2.5 supports Python 3.12–3.14](https://numpy.org/doc/stable/release/2.5.0-notes.html)
and [Rasterio 1.5 requires Python 3.12+](https://pypi.org/project/rasterio/1.5.2/).
Do not upgrade VTK 9.7 under PyVista 0.48.2's `vtk<9.7` constraint. The accepted
h5py 3.14 version already satisfies PyTuflow's current requirement.

## HDF5 root cause and remedy

| Independent child | Original h5py 3.16 profile exit | Compatible profile exit |
| --- | ---: | ---: |
| h5py only | 0 | 0 |
| QGIS initialized only | 0 | 0 |
| QGIS initialized, then h5py | 1, `0xc0000139` / ImportError | 0 |
| h5py, then QGIS initialized | 0 | 0 |
| QGIS, then PyTuflow root import only | 0 (insufficient coverage) | 0 |
| Enhanced QGIS, then public readers and HDF5 I/O | 1 | 0 |

Repeated failures show OSGeo4W's **HDF5 1.14.6** `hdf5.dll` loaded before h5py.
The h5py 3.16 wheel bundles **HDF5 2.0.0**, also documented in the
[h5py release notes](https://docs.h5py.org/en/stable/whatsnew/3.16.html).
PE inspection shows the failing `_errors.cp312-win_amd64.pyd` imports
**`H5_libinit_g` and `H5_libterm_g`** from `hdf5.dll`. Both exports are absent
from OSGeo4W's DLL and present in the wheel's DLL. Other extensions require
additional missing exports, including `H5Dread_chunk1` and `H5Tdecode1`.
This establishes an external HDF5 binary/load-order mismatch, not a PR 23
time-selection regression. It does not identify the loader's first attempted
symbol among the missing imports.

The live process confirms the static result: `GetProcAddress` on the already
loaded OSGeo4W HDF5 module returns Windows error **127** for both symbols (and
the other two named exports), while `H5get_libversion` resolves successfully.

**Validated remedy:** use the isolated h5py **3.14.0** wheel built against
HDF5 **1.14.6** with this installation. All inspected direct HDF5 imports exist
in OSGeo4W's DLL. All five import orders repeatedly pass, including an in-memory
dataset write/read, followed by complete native/public-reader regression passes.
No OSGeo4W DLL was swapped, renamed or overwritten.

The old incompatible profile remains broken. Importing h5py 3.16 first loads its
HDF5 2.0 DLL and makes the import-only test pass, but is **not an accepted general
GDAL/MDAL remedy**. Do not prescribe reordering or an untested broad `h5py<3.16`
constraint. Only this exact native wheel/profile was accepted.

## Diagnostic fixes and reproduction

The enhanced probe requires real MDAL registration, public reader imports,
working h5py capability and an HDF5 roundtrip, with warnings as errors. It
rejects incomplete output, swallowed Python errors, timeout or `0xc0000139`,
even if a child exits zero. Lazy root imports previously hid an unavailable
reader backend. Raw exit/unsigned Windows codes, streams, events and search
paths remain in external reports; library optional-backend behavior is unchanged.

Run with the correctly configured OSGeo4W interpreter and the add-ons for each
separate profile:

```text
python -X faulthandler ci/diagnostics/h5py_qgis_imports.py --dependency-path <addons> --source-root <exact-snapshot> --out <outside-repo>/native-imports.json
```

Repeat `--dependency-path` for separate targets. They are appended after bundled
packages and forwarded explicitly to children; the QGIS launcher need not
preserve incoming PYTHONPATH. `--case h5py_only` selects the hosted non-QGIS
control, which cannot establish native QGIS acceptance.

For static comparison, install optional `pefile` into an external target, then:

```text
python ci/diagnostics/hdf5_exports.py --dependency-path <pefile-target> --extension <h5py>/_errors.cp312-win_amd64.pyd --runtime-dll <OSGeo4W>/bin/hdf5.dll --bundled-dll <h5py>/hdf5.dll --out <outside-repo>/exports.json
```

The original extension returns 1 with two missing exports; the compatible
extension reports none. Symbol matching alone does not establish ABI safety.
Raw reports contain private paths and must stay outside the repository.

## Recommendations

- **Issue 30:** native acceptance passes with a dependency-level solution; it can
  close once the owner accepts the supported profile. No production adaptation
  or warning suppression is required.
- **Issue 31:** root cause and exact compatible-profile remediation are verified
  across repeated runs. This does not repair every h5py/QGIS combination or
  alter the user's normal QGIS installation.
- **PR 23:** native acceptance is satisfied on its tested head/base, including
  all 108 time cases. Current-head hosted checks, review and up-to-date rules
  remain separate integration requirements.
- **Upstream PR A:** retain separate numerical/geometry acceptance, obtain
  owner/maintainer scope approval and exclude fork-only records by default.
  Broader dependency metadata changes need the full supported-runtime/platform
  evidence. No merge, auto-merge or external submission is authorized here.

[Sanitized evidence](evidence/native-env-30-31.json) records pinned revisions,
profiles, DLL hashes, exact fixed tests and raw counts. Private JUnit/logs,
module paths, scripts and failed controls remain in the local handoff.
