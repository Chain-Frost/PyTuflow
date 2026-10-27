# Compatibility and correctness notes

Python 3.11 is the minimum runtime: the project template engine already uses
`string.Template.get_identifiers()`, introduced in Python 3.11. Runtime
dependencies remain those declared in `pyproject.toml`. QGIS-backed operations
also need a compatible initialized QGIS application with the MDAL provider.

## Model inputs and saves

On Linux, eager filename resolution is case-sensitive by default. Use
`TCF(path, case_sensitivity=1)` for extension-only tolerance or
`case_sensitivity=2` for filename and extension tolerance. Directory components
remain case-sensitive in all modes. Windows uses its native filesystem rules.
An exact match wins; multiple non-exact matches raise an ambiguity error.
The latter is a deliberate deterministic parser policy; equivalence to the
licensed solver's collision handling has not been established.
See the [TUFLOW command-line reference](https://docs.tuflow.com/classic-hpc/manual/2026.3/11-RunningSimulations.html)
and `tests/test_linux_case_policy.py`. Explicit `TuflowPath` case-insensitive
helpers retain their existing behaviour. Classic `Read File` paths remain
relative to the calling control file.

Model saves preserve caller-owned input objects and original text terminators,
stage output before replacement and retain recovery information on failure.
Two competing control-file owners cannot silently write the same destination.
The `tests/tmf/test_safe_model_save*.py` modules cover aliases, inspection,
ownership, rollback and failures. `test_write` and `test_write_trd` in
`tests/tmf/test_control_file.py` expect the input's actual lack of a final
newline; they no longer expect the writer to invent one. The FV project test
replaces its unloaded child placeholder rather than appending a second owner.

A rainfall CSV index is a database; a direct NetCDF rainfall grid is not a
CSV index. `test_load_rainfall_database` now uses an actual CSV fixture, while
`tests/tmf/test_parser_corrections.py` independently checks both cases.
Ordinary Q channels reference curve identifiers, not CSV files. QO operational
CSV and M matrix references retain their separate meanings. The GIS inventory
tests in `test_input.py` and `test_input_context.py` explicitly exclude Q curve
IDs. Material records pad omitted fields with NaN before DataFrame creation;
boundary-condition reads avoid mutating cached frames during index resets.

## Results, cache and imports

Result-time queries use saved timestamps and validated NetCDF time units rather
than assuming uniform output intervals. Grid and map readers construct pandas
objects without deprecated padding or dtype behaviour. Raster caches are
bounded, and NetCDF reader recovery closes invalid state before retrying.
The result-time, pandas compatibility and raster-cache test modules contain
independent expected times, values and failure-injection checks.

Public result-reader imports retain their original objects and names while
loading lazily. Root imports no longer modify `sys.path`. Logging avoids
duplicate library-owned handlers and preserves caller-owned handlers. Existing
constructor defaults, wildcard imports and the deprecated `ResData` API remain
covered by the package-import and public-API regression modules.

## Numerical and QGIS corrections

Depth averages use valid overlapping layer thickness. Missing observations and
their thickness are omitted together; physical zero remains valid. For layer
boundaries `[0,-1,-2]` and values `[10,20]`, the upper 1.5 metres gives
`(1*10 + 0.5*20)/1.5 = 40/3`. Equal-thickness `[10,NaN]` averages to 10,
whereas `[10,0]` averages to 5. Missing physical endpoints cannot be replaced
by interior coordinates. Zero-width or wholly missing intervals return NaN.
The numerical modules use independent rational calculations and check scalar,
vector, activity, masked-data and public-reader shapes.

QGIS face positions use signed-area centroids, not the average of vertices.
The triangle `[(0,0,1),(2,0,2),(0,2,3)]` has centroid `(2/3,2/3,2)`;
the irregular trapezoid `[(10,0),(14,0),(13,2),(10,2)]` has XY centroid
`(10+37/21,20/21)`. Face order, projected offsets, winding, selectors and
independent returned arrays are checked in the centroid and native surface tests.

Face-to-vertex interpolation uses normalized corner-angle weights. Contributions
3 and 9 with angles pi/4 and pi/2 give `(3/3)+(2*9/3) = 7`.
Wetness and validity are evaluated for each requested result and timestep.
Missing vector components invalidate that face's joint interpolated contribution;
valid zero remains valid. The angle-maths and native interpolation tests also
cover isolated vertices, triangle padding and changing wet states.

Point queries distinguish one scalar dataset from one two-component vector
dataset. A vector sample `[3,4]` returns `(3.0,4.0)`, not a scalar conversion
error. Individual components such as `V_x` remain scalar floats. Missing
components remain NaN and valid zeros survive. Noninterpolated point samples
preserve each component independently; they do not apply interpolation's joint
validity rule. Portable extractor-boundary tests and separate real-MDAL tests
cover this distinction, repeated queries and netCDF4/h5py reader paths.

Backend conventions remain distinct: QGIS uses an effective-thickness threshold
of 1e-6; Python uses positive overlap. Zero-thickness ordinal selections,
out-of-range sigma intervals and missing physical endpoints can differ between
providers. These corrections do not promise universal backend or hydraulic
solver equivalence. Native tests require real QGIS/MDAL; simulated boundary
tests cannot establish provider acceptance.

## FM reference and comparison corrections

The Flood Relief Arch ECF reference now registers the already-existing
`1d_nwk_ORIFICE_River_Sections_Flood_Relief_Arch` layer. Without that command,
the ESTRY input omits the relief opening. This is a missing network registration,
not regenerated hydraulic geometry or a new numerical reference. The dedicated
`test_flood_relief_arch_ecf_registers_both_nwk_layers` asserts the independently
specified RIVER, table-link and ORIFICE commands in both generated and reference
files. Comparison helpers match full relative file and layer identities within
the declared CSV/GIS output roots before comparing contents. Text comparison
reads both files and checks every line, including whitespace and final newlines.
`tests/test_fm_comparison.py` protects missing/misnamed files, layer pairing,
nested paths and text differences; numeric and geometry comparators remain intact.
