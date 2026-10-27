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
import warnings

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
                    "hdf5", "h5py", "zlib", "crypto", "qgis", "gdal", "qt6", "python3", "vtk", "rasterio",
                )):
                    paths.append(name.value)
        return {"modules": sorted(set(paths))}
    except Exception as error:
        return {"error": repr(error)}


def load_h5py() -> None:
    record("before_h5py", dlls_already_loaded=loaded_dlls())
    import h5py
    with h5py.File("native-import-probe.h5", "w", driver="core", backing_store=False) as handle:
        handle.create_dataset("values", data=[3, 5, 8], dtype="i8")
        if handle["values"][:].tolist() != [3, 5, 8]:
            raise RuntimeError("HDF5 in-memory roundtrip returned unexpected values")
    record("after_h5py", path=h5py.__file__, hdf5=h5py.version.hdf5_version,
           hdf5_built=h5py.version.hdf5_built_version_tuple,
           version=h5py.__version__, roundtrip=True, dlls=loaded_dlls())


def load_qgis() -> object:
    record("before_qgis")
    from qgis.core import Qgis, QgsApplication, QgsProviderRegistry
    prefix = os.environ.get("QGIS_PREFIX_PATH")
    if prefix:
        QgsApplication.setPrefixPath(prefix, True)
    app = QgsApplication([], False)
    record("before_qgis_init")
    app.initQgis()
    providers = QgsProviderRegistry.instance().providerList()
    mdal = QgsProviderRegistry.instance().providerMetadata("mdal") is not None
    record("after_qgis_init", prefix=QgsApplication.prefixPath(), version=Qgis.QGIS_VERSION,
           providers=providers, mdal=mdal, dlls=loaded_dlls())
    if not mdal:
        raise RuntimeError("Initialized QGIS has no registered MDAL mesh provider")
    return app


def child(case: str) -> int:
    warnings.simplefilter("error")
    record("start", case=case, python=sys.version, executable=sys.executable,
           environment={name: os.environ.get(name) for name in (
               "PATH", "PYTHONPATH", "PYTHONHOME", "QGIS_PREFIX_PATH", "QT_PLUGIN_PATH",
           )})
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
            from pytuflow import NCMesh, XMDF
            from pytuflow._outputs.pymesh import H5Engine, NCEngine
            available = H5Engine.available()
            record("after_pytuflow_readers", xmdf_module=XMDF.__module__,
                   ncmesh_module=NCMesh.__module__, h5py_available=available,
                   netcdf4_available=NCEngine.available(), dlls=loaded_dlls())
            if not available:
                raise RuntimeError("PyTuflow public readers report h5py unavailable after QGIS")
            load_h5py()
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


def assess_child(case: str, returncode: int, stdout: str, stderr: str) -> dict[str, object]:
    """Do not accept swallowed loader errors or incomplete child output as a pass."""
    events = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and isinstance(event.get("event"), str):
            events.append(event)
    names = {event["event"] for event in events}
    problems = []
    if returncode != 0:
        problems.append(f"Child process exit {returncode}")
    if "complete" not in names:
        problems.append("Missing completion event")
    if "python_exception" in names:
        problems.append("Child reported a Python exception")
    if "0xc0000139" in stderr.lower():
        problems.append("Native Windows entry-point diagnostic 0xc0000139")
    if case != "h5py_only" and not any(
        event["event"] == "after_qgis_init" and event.get("mdal") is True
        for event in events
    ):
        problems.append("No initialized real MDAL registration evidence")
    if case != "qgis_only" and not any(
        event["event"] == "after_h5py" and event.get("roundtrip") is True
        for event in events
    ):
        problems.append("No successful h5py import and HDF5 roundtrip evidence")
    if case == "qgis_then_pytuflow" and not any(
        event["event"] == "after_pytuflow_readers" and event.get("h5py_available") is True
        for event in events
    ):
        problems.append("No public-reader h5py capability evidence")
    return {"status": "passed" if not problems else "failed", "problems": problems,
            "events": events}


def output_text(value: bytes | str | None) -> str:
    return value.decode(errors="replace") if isinstance(value, bytes) else value or ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("native-imports.json"))
    parser.add_argument("--child-case", choices=CASES, help=argparse.SUPPRESS)
    parser.add_argument("--case", choices=CASES, action="append", dest="cases",
                        help="Select a control case; default runs all five")
    parser.add_argument("--source-root", type=Path,
                        help="Import PyTuflow from this exact source snapshot in each child")
    parser.add_argument("--timeout", type=int, default=90, help="Seconds allowed per child")
    parser.add_argument("--dependency-path", action="append", type=Path, default=[],
                        help="Append an isolated add-on directory after bundled packages in each child")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    for path in args.dependency_path:
        if not path.is_dir():
            parser.error(f"Dependency directory does not exist: {path}")
        sys.path.append(str(path.resolve()))
    if args.source_root:
        source = args.source_root.resolve()
        if not (source / "pytuflow" / "__init__.py").is_file():
            parser.error("--source-root must contain the intended pytuflow package")
        sys.path.insert(0, str(source))
    if args.child_case:
        return child(args.child_case)
    reports = []
    for case in args.cases or CASES:
        command = [
            sys.executable, "-X", "faulthandler", str(Path(__file__).absolute()),
            "--child-case", case,
        ]
        if args.source_root:
            command += ["--source-root", str(args.source_root.resolve())]
        for path in args.dependency_path:
            command += ["--dependency-path", str(path.resolve())]
        try:
            proc = subprocess.run(command, capture_output=True, text=True,
                                  errors="replace", timeout=args.timeout, check=False)
            report = {
                "case": case, "returncode": proc.returncode,
                "stdout": proc.stdout, "stderr": proc.stderr,
                "returncode_u32": proc.returncode & 0xFFFFFFFF,
                "command": command,
                **assess_child(case, proc.returncode, proc.stdout, proc.stderr),
            }
        except subprocess.TimeoutExpired as error:
            report = {
                "case": case, "timeout": True,
                "stdout": output_text(error.stdout), "stderr": output_text(error.stderr),
                "status": "failed", "problems": ["Child exceeded timeout"], "command": command,
            }
        reports.append(report)
        print(f"{case}: {report.get('returncode', 'TIMEOUT')}", flush=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "python": sys.version, "executable": sys.executable, "cases": reports,
        "passed": sum(item["status"] == "passed" for item in reports),
        "failed": sum(item["status"] == "failed" for item in reports),
    }, indent=2), encoding="utf-8")
    print(f"Report: {args.out.absolute()}", flush=True)
    return 1 if any(x["status"] != "passed" for x in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
