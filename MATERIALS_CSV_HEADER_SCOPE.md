# Materials CSV parsing investigation and correction

Status: reproduced on the actual owner-supplied file; correction delivered in the existing [upstream PR #17](https://github.com/TUFLOW-Support/PyTuflow/pull/17). This PR retains the investigation record only. No competing production implementation is introduced here.

## Reproduction and cause

The installed Python 3.14 environment reports PyTuflow 1.3.1 from the approved local wheel for source commit `4ca2dbe35c1d7e6a1c7b7150fbea622b1aa0ddb0`. All 579 wheel package members match the installed files byte for byte. Upstream PR #17 was verified at that same source revision before modification.

Reading the actual Materials_01.csv with that installation reproduces:

```text
ValueError: invalid literal for int() with base 10: 'Material ID'
```

The existing header detection is present. Spaces before quoted multivalue fields and extra commas in trailing comments cause the shared CSV driver to use its fallback parser. That fallback ignores headers and quote grouping, reintroducing the header as a material record.

The original wrapper process was previously observed using the same Python 3.14 executable. Its historical in-memory package contents cannot be reconstructed from today's installed provenance alone; direct reproduction on the verified installation independently establishes the remaining defect.

## Correction and routing

Commit `0121101` on `contrib/upstream-batch-validation-final` corrects the existing implementation behind upstream PR #17, based directly on `4ca2dbe35c1d7e6a1c7b7150fbea622b1aa0ddb0`.

Materials CSV parsing now recognises spaces before quoted fields. Where the header declares a trailing `!` comment column, parsing is bounded through that column so extra comment commas do not trigger fallback. Quoted Manning's and rainfall-loss fields remain intact. Nonempty invalid material IDs still raise errors. The shared CSV driver and TMF header override are unchanged.

## Validation

- The actual file fails on the installed baseline and loads all 11 expected materials from the newly built candidate wheel.
- Material dependency resolution succeeds in both eager and deferred modes for all 12 configured AEP/scenario selections: 24 checks. This is materials-specific coverage, not complete model-input or hydraulic acceptance.
- The actual materials file has identical SHA-256 before and after validation. No model files were published.
- New synthetic regressions exercise spaced quoted values, trailing comment commas, blank/comment preambles, BOM, headerless input, malformed IDs, and database-context/dependency resolution. The three headered regression variants fail on the baseline with the original exception and pass on the correction.
- Focused database/deferred suites: 102 passed, 4 skipped on Python 3.11 and Python 3.14. The four skips are Linux filename-case checks on Windows.
- Broader TMF suite on Python 3.14: 587 passed, 1 skipped.
- Python 3.11 grammar audit: 641 tracked files, zero errors. Wheel build and diff whitespace checks pass.
- Python 3.12 and fresh native TUFLOW execution were not performed. Existing broad lint findings were not treated as a clean lint pass. Hosted CI is separate from these local results.

The initial direct pytest invocation emitted the existing Windows HDF5 loader diagnostic (0xc0000139). Subsequent local runs preload h5py before pytest and complete successfully; no installed dependency was changed to obtain these results.

## Owner decisions and boundaries

Material 5 has Manning's n = 0.001 intentionally for water ponds; preserve it. For GPU inspection report: "CodeMeter WebAdmin is not running; GPU availability could not be verified." Take no service action.

No simulations were launched or interrupted, no model inputs or services were changed, and no wheel was installed into the model environment. The ryan-tools dependency and installed distribution remain unchanged. No merge or new upstream PR was performed. Keep this record available for review and any separately actioned dependency rollout.
