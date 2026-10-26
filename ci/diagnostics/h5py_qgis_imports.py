"""Issue #31: isolate QGIS/h5py load-order failures in new processes.

Run with the real OSGeo4W interpreter, no virtual environments:
  python -X faulthandler ci/diagnostics/h5py_qgis_imports.py --out native-imports.json

Reports contain private local module/DLL paths. Inspect before sharing.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

CASES = ("h5py_only", "qgis_only", "qgis_then_h5py", "h5py_then_qgis", "qgis_then_pytuflow")


def record(event: str, **details: object) -> None:
    print(json.dumps({"event": event, **details}, default=str), flush=True)


def loaded_dlls() -> dict[str, object]:
    if sys.platform != "win32":
        return {"status": "not_windows"}
    try:
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.EnumProcessModulesEx.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(wintypes.HMODULE),
            wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.DWORD,
        ]
        psapi.GetModuleFileNameExW.argtypes = [
            wintypes.HANDLE, wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD,
        ]
        psapi.GetModuleFileNameExW.restype = wintypes.DWORD
        process = kernel32.GetCurrentProcess()
        modules = (wintypes.HMODULE * 4096)()
        needed = wintypes.DWORD()
        if not psapi.EnumProcessModulesEx(
            process, modules, ctypes.sizeof(modules), ctypes.byref(needed), 0x03
        ):
            return {"error": f"EnumProcessModulesEx: {ctypes.get_last_error()}"}
        paths: list[str] = []
        for module in modules[: needed.value // ctypes.sizeof(wintypes.HMODULE)]:
            name = ctypes.create_unicode_buffer(32768)
            if psapi.GetModuleFileNameExW(process, module, name, len(name)):
                if any(s in name.value.lower() for s in (
                    "hdf5", "h5py", "zlib", "crypto", "qgis", "gdal", "qt6", "python3",
                )):
                    paths.append(name.value)
        return {"modules": sorted(set(paths))}
    except Exception as error:
        return {"error": repr(error)}


def load_h5py() -> None:
    record("before_h5py", dlls_already_loaded=loaded_dlls())
    import h5py
    record("after_h5py", path=h5py.__file__, hdf5=h5py.version.hdf5_version,
           version=h5py.__version__, dlls=loaded_dlls())


def load_qgis() -> object:
    record("before_qgis")
    from qgis.core import QgsApplication
    prefix = os.environ.get("QGIS_PREFIX_PATH")
    if prefix:
        QgsApplication.setPrefixPath(prefix, True)
    app = QgsApplication([], False)
    record("before_qgis_init")
    app.initQgis()
    record("after_qgis_init", prefix=QgsApplication.prefixPath(), dlls=loaded_dlls())
    return app


def child(case: str) -> int:
    record("start", case=case, python=sys.version, executable=sys.executable)
    app = None
    try:
        if case == "h5py_only":
            load_h5py()
        elif case == "qgis_only":
            app = load_qgis()
        elif case == "qgis_then_h5py":
            app = load_qgis()
            load_h5py()
        elif case == "h5py_then_qgis":
            load_h5py()
            app = load_qgis()
        elif case == "qgis_then_pytuflow":
            app = load_qgis()
            record("before_pytuflow")
            import pytuflow
            record("after_pytuflow", path=pytuflow.__file__)
        record("complete")
        return 0
    except BaseException as error:
        traceback.print_exc()
        record("python_exception", error=repr(error), dlls_at_failure=loaded_dlls())
        return 1
    finally:
        if app is not None:
            record("before_qgis_exit")
            app.exitQgis()
            record("after_qgis_exit")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("native-imports.json"))
    parser.add_argument("--child-case", choices=CASES, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child_case:
        return child(args.child_case)
    reports = []
    for case in CASES:
        command = [
            sys.executable, "-X", "faulthandler", str(Path(__file__).absolute()),
            "--child-case", case,
        ]
        try:
            proc = subprocess.run(command, capture_output=True, text=True,
                                  errors="replace", timeout=90, check=False)
            report = {
                "case": case, "returncode": proc.returncode,
                "stdout": proc.stdout, "stderr": proc.stderr,
            }
        except subprocess.TimeoutExpired as error:
            report = {
                "case": case, "timeout": True,
                "stdout": str(error.stdout), "stderr": str(error.stderr),
            }
        reports.append(report)
        print(f"{case}: {report.get('returncode', 'TIMEOUT')}", flush=True)
    args.out.write_text(json.dumps({
        "python": sys.version, "executable": sys.executable, "cases": reports,
    }, indent=2), encoding="utf-8")
    print(f"Report: {args.out.absolute()}", flush=True)
    return 1 if any(x.get("returncode") != 0 for x in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
