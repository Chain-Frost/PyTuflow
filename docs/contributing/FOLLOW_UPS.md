# Follow-up tasks

- [ ] Resolve the original Flood Relief Arch FM output/reference mismatch in a
  dedicated correctness PR, with independent engineering evidence. Never bless
  generated output merely to make comparison green.
- [ ] Establish latest and lowest-supported dependency acceptance separately
  from the pinned regression environment. No claim covers all versions allowed
  by open-ended package metadata.
- [ ] Investigate the native Windows HDF5 DLL loader diagnostic seen during
  QGIS tests (0xc0000139 while importing h5py after QGIS). Both original and
  candidate QGIS suites passed 239 tests, but the diagnostic remains visible;
  do not describe this as a warning-free native environment.
- [ ] Agree the external contribution scope and PR granularity with the upstream
  maintainer before curating production changes from integration.

## Superseded Python 3.10 proposal

The original requested minimum was disproved by full project execution, despite
passing syntax/import/wheel smoke tests. `string.Template.get_identifiers()` in
`pytuflow/project/template/engine.py:60` requires Python 3.11. The owner's revised
policy is to adopt upstream's actual minimum, so no 3.10 production backport is
planned. Issue #2 records the discovery and is closed as superseded by this policy.
