# Materials CSV header parsing: implementation scope

Status: planned work only. This PR records a task for a later implementation; it does not fix the parser.

## Observed failure

PyTuflow's materials database reader attempts to convert the CSV heading `Material ID` to an integer:

```text
invalid literal for int() with base 10: 'Material ID'
```

The failed database load subsequently leaves background input checks unresolved:

```text
DeferredDatabaseResolutionError: Expected one cached materials database, found 0
```

In the observed run, TUFLOW 2026.3 successfully read the same file, loaded all 11 materials, and advanced into simulation. Twelve configured runs received checker warnings; this does not establish that all twelve have valid inputs or completed successfully.

## Verified-build follow-up supplied by the owner

The owner reports that installed-distribution verification passed for PyTuflow 1.3.1 from source commit `4ca2dbe35c1d7e6a1c7b7150fbea622b1aa0ddb0`, including the approved wheel SHA-256 and local-wheel provenance. This update records that supplied verification; it has not independently rerun it or reproduced the CSV failure.

The owner reports that this build already contains the materials CSV header fix from [upstream PR #17](https://github.com/TUFLOW-Support/PyTuflow/pull/17). Therefore do not assume the required work is a new header-skipping implementation. If the failing wrapper used this same build and interpreter, investigate a remaining file-specific gap in that existing fix.

## Required investigation before implementation

1. Identify the interpreter and imported PyTuflow module path used by the failing wrapper. Correlate them with the verified installed build; present-day installation alone does not prove historical process identity.
2. Reproduce through the actual materials database reader using the owner's actual Materials_01.csv and the verified installation, without launching the wrapper or solver or changing model inputs. Retain the raw exception and relevant parser context locally.
3. Determine which actual header or file-structure detail is unsupported. If it no longer reproduces, document that result and the remaining uncertainty rather than claiming a demonstrated fix.
4. Add a minimal synthetic regression reproducing the observed unsupported structure without publishing the model file.
5. Coordinate any demonstrated correction with the existing work in upstream PR #17 instead of developing a competing implementation here. Prepare the correction for that work; follow the owner's repository routing and authorisation before any upstream write or submission.
6. Update the ryan-tools dependency only after the corrected build has been tested and a dependency update is separately actioned.

Keep PR #74 open as the investigation scope until the actual CSV is tested. Passing generic header regression tests or finding an existing fix does not alone justify closing it as redundant.

## Implementation, only after reproduction

- Reproduce the failure through the materials database reader and trace the downstream cache-resolution failure.
- Recognise the supported materials CSV column header, including surrounding whitespace, while retaining headerless-file support.
- Preserve quoted multivalue fields for depth-dependent Manning's roughness and rainfall-loss variables.
- Keep malformed material IDs as actionable errors with file and row context. Do not skip arbitrary nonnumeric records.
- Verify the successfully loaded database reaches the cache and resolves dependent input checks.
- Keep the production change limited to materials parsing. Follow repository contribution and validation instructions before implementation.

## Acceptance checks

- Regression: header beginning `Material ID, Manning's n` is accepted.
- Headerless files retain existing behaviour.
- Quoted multivalue roughness and rainfall-loss fields retain their values.
- Invalid data-row material IDs produce a useful error.
- Exercise database loading and downstream resolution, not only a standalone CSV helper.
- Run applicable tests and compatibility checks; report any remaining unresolved checks honestly.

Use a small synthetic fixture in the repository. The model file and logs are local investigation evidence, not attachments authorised for publication by this scope. When available, perform read-only validation against the owner's supplied local Materials_01.csv; record the outcome separately from synthetic coverage. Do not claim native solver or hydraulic acceptance from Python tests.

## Boundaries and owner decisions

- Do not edit model inputs, interrupt or launch simulations, install packages into the active model environment, or change services.
- Material 5 has Manning's n = 0.001 intentionally for water ponds. Preserve it; warning 2218 is not part of this fix.
- For GPU inspection, report: "CodeMeter WebAdmin is not running; GPU availability could not be verified." Take no further service action. GPU behaviour changes are outside this PR.
- Keep this scope PR draft while the investigation remains outstanding. No merge or upstream submission is authorised by this scope update.
