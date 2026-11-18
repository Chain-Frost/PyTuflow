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

## Implementation

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
- Keep this PR draft until implemented and validated. No merge or upstream submission is authorised.
