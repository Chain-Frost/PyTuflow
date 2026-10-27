"""Native loader evidence must not become a pass through swallowed exceptions."""
import json
import subprocess
import sys

import pytest

from ci.diagnostics.h5py_qgis_imports import assess_child, main, output_text


def events(*items):
    return "\n".join(json.dumps(item) for item in items)


def healthy():
    return events({"event": "after_qgis_init", "mdal": True},
                  {"event": "after_pytuflow_readers", "h5py_available": True},
                  {"event": "after_h5py", "roundtrip": True}, {"event": "complete"})


def test_swallowed_native_loader_diagnostic_fails_even_with_zero_exit():
    result = assess_child("qgis_then_pytuflow", 0, healthy(),
                          "Windows fatal exception: code 0xc0000139")
    assert result["status"] == "failed"
    assert any("0xc0000139" in problem for problem in result["problems"])


def test_lazy_root_import_without_reader_backend_evidence_is_not_a_pass():
    stdout = events({"event": "after_qgis_init", "mdal": True},
                    {"event": "after_h5py", "roundtrip": True}, {"event": "complete"})
    result = assess_child("qgis_then_pytuflow", 0, stdout, "")
    assert result["problems"] == ["No public-reader h5py capability evidence"]


@pytest.mark.parametrize("stdout", ["", '{"event":"complete"}',
                                   events({"event": "after_qgis_init", "mdal": False},
                                          {"event": "complete"})])
def test_zero_exit_without_provider_and_roundtrip_evidence_is_not_accepted(stdout):
    assert assess_child("qgis_then_h5py", 0, stdout, "")["status"] == "failed"


def test_nonzero_exit_and_python_exception_are_preserved():
    result = assess_child("qgis_then_h5py", 1,
                          healthy() + '\n{"event":"python_exception"}', "raw stderr")
    assert "Child process exit 1" in result["problems"]
    assert "Child reported a Python exception" in result["problems"]


@pytest.mark.parametrize("case,stdout", [
    ("h5py_only", events({"event": "after_h5py", "roundtrip": True}, {"event": "complete"})),
    ("qgis_only", events({"event": "after_qgis_init", "mdal": True}, {"event": "complete"})),
    ("qgis_then_h5py", healthy()),
])
def test_complete_selected_control_has_only_its_own_capability_requirements(case, stdout):
    assert assess_child(case, 0, stdout, "")["status"] == "passed"


def test_timeout_retains_partial_bytes_and_fails(tmp_path, monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1, output=b"partial\n", stderr=b"native stderr")
    monkeypatch.setattr("ci.diagnostics.h5py_qgis_imports.subprocess.run", timeout)
    output = tmp_path / "nested" / "report.json"
    monkeypatch.setattr("sys.argv", ["probe", "--case", "h5py_only", "--out", str(output)])
    assert main() == 1
    record = json.loads(output.read_text())["cases"][0]
    assert record["timeout"] is True
    assert record["stdout"] == "partial\n"
    assert record["stderr"] == "native stderr"
    assert output_text(None) == ""


def test_snapshot_is_forwarded_and_raw_exit_is_not_rewritten(tmp_path, monkeypatch):
    package = tmp_path / "source" / "pytuflow"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    output = tmp_path / "report.json"
    seen = []
    def run(command, **kwargs):
        seen.append(command)
        return subprocess.CompletedProcess(command, -1073741511, "partial output", "entry point")
    monkeypatch.setattr("ci.diagnostics.h5py_qgis_imports.subprocess.run", run)
    monkeypatch.setattr("sys.argv", ["probe", "--case", "qgis_then_h5py", "--out", str(output),
                                     "--source-root", str(package.parent)])
    previous_path = list(sys.path)
    try:
        assert main() == 1
    finally:
        sys.path[:] = previous_path
    assert seen[0][-2:] == ["--source-root", str(package.parent.resolve())]
    record = json.loads(output.read_text())["cases"][0]
    assert record["returncode"] == -1073741511
    assert record["returncode_u32"] == 0xC0000139
    assert record["stdout"] == "partial output"


def test_addons_follow_bundled_paths_and_are_forwarded_to_children(tmp_path, monkeypatch):
    original = list(sys.path)
    monkeypatch.setattr(sys, "path", list(original))
    seen = []
    def run(command, **kwargs):
        seen.append(command)
        return subprocess.CompletedProcess(command, 0, healthy(), "")
    monkeypatch.setattr("ci.diagnostics.h5py_qgis_imports.subprocess.run", run)
    monkeypatch.setattr(sys, "argv", ["probe", "--case", "h5py_only",
                                     "--dependency-path", str(tmp_path),
                                     "--out", str(tmp_path / "report.json")])
    assert main() == 0
    assert sys.path[:len(original)] == original
    assert sys.path[-1] == str(tmp_path.resolve())
    assert seen[0][-2:] == ["--dependency-path", str(tmp_path.resolve())]
