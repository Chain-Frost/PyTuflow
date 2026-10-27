# Linux filename case policy: TUFLOW Classic/HPC `-cs`

Scope: eager parser only. The official solver documentation is the policy
authority, not the implementation in phantom-branch PR #4.

## Authoritative sources

- [2026.3 command-line `-cs` reference](https://docs.tuflow.com/classic-hpc/manual/2026.3/11-RunningSimulations.html)
- [2026.0.0 `-cs` introduction](https://docs.tuflow.com/classic-hpc/changelog/2026.0.0/)
- [2026.3 file-path conventions](https://docs.tuflow.com/classic-hpc/manual/2026.3/04-ControlFiles-and-Inputs.html)

| Scenario | Linux omitted/`-cs0` | Linux `-cs1` | Linux `-cs2` | Windows, any level |
|---|---|---|---|---|
| Exactly matching path | Match | Match | Match | Native filesystem |
| Extension case differs | Missing | Match | Match | Native filesystem |
| Basename case differs | Missing | Missing | Match | Native filesystem |
| Directory component case differs | Missing | Missing | Missing | Native filesystem |
| Missing filename/parent | Unresolved | Unresolved | Unresolved | Unresolved |
| Casefold collision, exact match exists | Exact match | Exact match | Exact match | Not normally available on default Windows volumes |
| Casefold collision, no exact match | Unresolved | Raise ambiguity | Raise ambiguity | Native filesystem |

**Documented**: -cs0 strict on Linux and default when omitted; -cs1
extension-only insensitivity; -cs2 filename+extension insensitivity, **not**
directories. TUFLOW automatically interprets backslashes as forward slashes
in Linux control-file paths. Windows commonly uses a case-insensitive volume.

**Not independently established**: collision tie-break behaviour of the
licensed TUFLOW 2026.3 Linux executable. Official documentation does not
state which of two non-exact case-insensitive matches wins, or whether TUFLOW
rejects them. The PyTUFLOW parser deliberately fails closed rather than
selecting by filesystem enumeration order. **Do not claim reference solver
equivalence for this ambiguity case** without a reproducible native TUFLOW run.

Missing inputs retain lexical paths for existing eager-parser missing-file
reporting. A constructed TCF does not guarantee complete input validation.

## Compatibility correction

The inherited eager expansion used `init_case_insensitive_path()` and
the `//` operator on Linux; this could resolve case-mismatched directories
and files, despite the TUFLOW -cs0 default. The eager parser now uses the
strict default and offers `TCF(..., case_sensitivity=1|2)` or
`TCFConfig(case_sensitivity=...)` for opt-in TUFLOW-compatible filename
tolerance. This is an **intentional Linux behaviour correction**.
The public explicit `init_case_insensitive_path()` and `//` helpers are
preserved, without a silent API behaviour change.

The config snapshots, primary TCF name, nested includes, event files,
spatial databases, GeoPackage filename references, and filesystem wildcard
materialisation use the chosen mode. No deferred, batch or graph APIs
are included. Folder paths retain exact spelling.

## Pinned provenance, coordination and transfer selection

- Clean fork review base: `0b6e2bc77ec9bb22254e88e54a466f4cd3fb6ff4`
- Immutable upstream: `TUFLOW-Support/PyTuflow@cf908cc922ca8448ed6002834877b0b377329eae`
- Selected source: [phantom-branch PR #4](https://github.com/phantom-branch/PyTuflow/pull/4),
  merged source head `c09d8a624e3f0282afabbb790303c1ae95c4c5cb`.
- Upstream production candidates: five eager modules in `pytuflow/_tmf/`:
  `settings.py`, `tfpathlib/file.py`, `parsers/expand_tuflow_value.py`,
  `parsers/line.py`, `cf/tcf.py`.
- Essential upstream regression: `tests/test_linux_case_policy.py`.
- Documentation candidate: this file, pending maintainer choice.
- Fork-only CI: `.github/workflows/linux-case-policy.yml`.
- Excluded: all phantom deferred, batch, graph, benchmark and consumer
  parity code; historical commits and generated fixtures.

PR #24 owns `parsers/non_recursive_basic_parser.py`: no modifications
to it here. PR #25 changes different production modules. Existing full
3.11/3.12/3.14 Windows acceptance and both immutable-upstream and
exact-base comparisons remain mandatory; a focused workflow cannot
replace them.

## Regression collection boundary

The platform-specific tests are kept in `tests/test_linux_case_policy.py`,
outside `tests/tmf/`, because the original-library comparator requires an
explicit per-node skip contract and does not silently approve platform skips.
The dedicated six-lane Linux/Windows workflow exercises them on actual target
filesystems, while the original TMF regression collection remains strictly
comparable with official upstream and the review base. Do not weaken skip
validation in the production acceptance gate.

Classic `Read File` content retains paths relative to the *calling* control
file (documented by `docs/examples/working_with_fv.rst`), rather than
relative to the read file. The preliminary scans apply the filename case policy
without changing that reference base. FV's different include-file convention
is outside this change.
