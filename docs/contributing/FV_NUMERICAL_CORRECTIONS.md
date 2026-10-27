# FV averaging and numerical reductions — correctness record

Tracked by [issue #8](https://github.com/Chain-Frost/PyTuflow/issues/8), [tracker #3](https://github.com/Chain-Frost/PyTuflow/issues/3), and [draft PR #26](https://github.com/Chain-Frost/PyTuflow/pull/26).

## Exact sources and reproduction

- Immutable official upstream: `TUFLOW-Support/PyTuflow@cf908cc922ca8448ed6002834877b0b377329eae`.
- Exact independent integration review base: `Chain-Frost/PyTuflow@0b6e2bc77ec9bb22254e88e54a466f4cd3fb6ff4`.
- Historical numerical reference: `phantom-branch/PyTuflow@4fdcde77c2b86f14b19c96f97c2b8328d60e998c`, PR #23.
- The five affected production files were byte-for-byte identical across upstream, integration and PR #23's pre-fix base `e162c04330d24c37bee3ade94479cc4602651060`.
- Test-only reproduction commit `9228b930f84b3051fc823155d67c4f6690b3cda1`, [Actions run 40354102277](https://github.com/Chain-Frost/PyTuflow/actions/runs/40354102277): each of Python 3.11/3.12/3.14 on Windows reports **356 failed / 243 passed / 0 collection or test errors** across 599 focused cases. These are uncensored, intentional old-code failure reports. XML is in the corresponding contract artifacts; the production code at that commit was unchanged.
- This change applies only the five numerical production modules from the historical tested implementation. Its one source-code difference is a documentation-link correction in the depth-averaging module docstring. The four numerical test modules retain the original independent oracles and public-reader fixtures. The unrelated historical workflow, geometry changes, performance changes and evidence archive are not imported.

## Independent expectations and intentional output corrections

Physical cell layers are constant over their own thickness. For each requested interval, intersect its vertical extent with each physical layer, omit missing/invalid observations **and their corresponding thickness**, then divide the sum of value × valid overlapping thickness by total valid overlapping thickness. Missing observations are **not zeros**. Missing physical boundaries cannot be replaced by an interior coordinate; padding is distinct from a physical layer with missing geometry or observations. No positive valid overlap returns NaN.

The tests use exact rational antiderivatives independently of production overlap calculations (`Fraction` and `rtol=atol=1e-12`). For physical boundaries `[0,-1,-2]` and values `[10,20]`:

| Interval measured below surface | Explicit calculation | Correct result |
| --- | --- | --- |
| 0–0.5 m | 0.5 × 10 / 0.5 | 10 |
| 0.2–0.8 m | 0.6 × 10 / 0.6 | 10 |
| 0–1.0 m | 1 × 10 / 1 | 10 |
| 0–1.5 m | (1 × 10 + 0.5 × 20) / 1.5 | 40/3 |

For equal-thickness `[10, NaN]`, omit missing thickness: result **10**, rather than the incorrectly diluted **5**. For `[10, 0]`, zero is valid and the result is **5**. Masked finite backing values are omitted; caller-owned arrays are not mutated. Zero-width, wholly outside or fully missing intervals return NaN.

For a nonuniform physical column with boundaries `[-1,-2,-2.5,-4,-5]` and values `[1,2,NaN,4]`: full column is `(1×1 + 0.5×2 + 1×4)/(1+0.5+1) = 2.4`; the first three ordinal layers give `(1+1)/1.5 = 4/3`; the 1.25–3.5 m top-depth interval gives `(0.25×2 + 0.5×4)/(0.25+0.5) = 10/3`. Physical ordinal indices must remain fixed when a prior layer is missing. Depth/height/sigma origins require the corresponding physical surface/bed coordinates, even if bounded interior layers remain numerically usable by known-origin or absolute-elevation requests.

**Vectors:** for `(3,4)` and `(6,8)`, magnitude minimum/maximum are scalar **5 / 10**. With split components the result is the tuple `(3,4) / (6,8)`. Vector averaging excludes a layer for *both* components when either is missing. Active NaNs, inactive entries, valid physical zeros and entirely inactive extrema retain their prior distinct contracts.

**Public shape/activity:** a scalar column average produces one scalar per requested column, retaining row/time/section/surface dimensions defined by the public reader. Two-component vector surfaces retain both components and do not collapse them into an unintended scalar. Existing inactive surface flag/zero placeholders remain unchanged; dry point/time-series/section outputs remain NaN; a wet cell with all missing observations remains active with a NaN observation. A single physical layer must still honour a requested partial interval instead of bypassing averaging.

## Provider boundary and limitations

QGIS/MDAL is **not** installed or initialised by the standard hosted Windows Python regression. `tests/test_numerical_qgis_reductions.py` is a separately selected native-provider suite requiring real `QgsApplication` and MDAL blocks; it must not be reported as passing until executed with an installed QGIS interpreter. Independent source and historical QGIS 4.2.3 acceptance are evidence from phantom PR #23, not a new native run on this fork.

Known differences are intentional and characterised, not silently corrected: QGIS's effective-thickness threshold is 1e-6 whereas Python uses strictly positive overlap; QGIS can accept a zero-thickness selected ordinal that Python returns NaN; QGIS rejects sigma fractions beyond [0,1] where Python intersects/clips. For missing surface/bed endpoints QGIS 4.2.3 may reject the entire physical face, while the Python path still permits a fully bounded layer for absolute elevations or a known opposite origin. Finite sentinels not normalised by the source reader are not assumed missing. The inherited QGIS public-surface `cell_position` geometry limitation belongs to issue #9, not this correction.

## Executed and required validation

The test-only baseline reproductions ran on Windows Python 3.11/3.12/3.14 and retained raw failures. The amended hosted workflow runs the three standalone numerical modules on each interpreter in addition to `ci/python_compatibility.py` and the original-library acceptance gate. It retains the existing original upstream and exact-review-base comparisons, the unchanged FM reference results and test-identity protections. Candidate pass/fail and native QGIS status must be recorded in PR #26; a historical success is not treated as a current-run success.

Production/test files are candidates for an external upstream contribution. This explanatory document is user/developer documentation. The change to `.github/workflows/original-library-lane.yml` is **fork-only CI infrastructure** and must be omitted by default from any curated upstream patch. No virtual environment, benchmark, solver, external release or upstream PR is part of this work.
