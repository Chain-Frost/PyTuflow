"""Compare a Windows extension's HDF5 imports with two DLL export tables.

Optional diagnostic dependency: pefile. No DLL is loaded or replaced.
Matching symbol names alone do not establish ABI or runtime compatibility.
Reports contain private paths; redact them before publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def inspect(extension: Path, runtime: Path, bundled: Path) -> dict[str, object]:
    import pefile

    def exports(path: Path) -> set[str]:
        with pefile.PE(str(path)) as image:
            return {symbol.name.decode("ascii") for symbol in image.DIRECTORY_ENTRY_EXPORT.symbols
                    if symbol.name is not None}

    with pefile.PE(str(extension)) as image:
        dependencies = [entry for entry in getattr(image, "DIRECTORY_ENTRY_IMPORT", [])
                        if entry.dll.decode("ascii").lower() == runtime.name.lower()]
        if not dependencies:
            raise ValueError(f"Extension has no direct import of {runtime.name}")
        imports = [symbol for entry in dependencies for symbol in entry.imports]
        if any(symbol.name is None for symbol in imports):
            raise ValueError("Ordinal imports require a separate ordinal-aware comparison")
        required = {symbol.name.decode("ascii") for symbol in imports}
    missing_runtime = sorted(required - exports(runtime))
    missing_bundled = sorted(required - exports(bundled))
    return {
        "status": "missing_runtime_exports" if missing_runtime else "no_missing_runtime_exports",
        "required_symbols": sorted(required), "missing_runtime": missing_runtime,
        "missing_bundled": missing_bundled,
        "files": {name: {"path": str(path.resolve()),
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                  for name, path in (("extension", extension), ("runtime", runtime), ("bundled", bundled))},
        "limitation": "Static direct-import comparison; not a complete ABI or runtime safety test",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extension", required=True, type=Path)
    parser.add_argument("--runtime-dll", required=True, type=Path)
    parser.add_argument("--bundled-dll", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--dependency-path", action="append", type=Path, default=[],
                        help="Append an isolated directory containing the optional pefile package")
    args = parser.parse_args()
    for path in args.dependency_path:
        if not path.is_dir():
            parser.error(f"Dependency directory does not exist: {path}")
        sys.path.append(str(path.resolve()))
    report = inspect(args.extension, args.runtime_dll, args.bundled_dll)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return int(bool(report["missing_runtime"] or report["missing_bundled"]))


if __name__ == "__main__":
    raise SystemExit(main())
