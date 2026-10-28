"""Review-base provenance and pre-overlay test preservation contracts."""
import subprocess
import pytest
from ci import review_base


@pytest.mark.parametrize("event, expected", [
    ({"pull_request": {"base": {"sha": "b" * 40}}, "before": "c" * 40}, "b" * 40),
    ({"before": "c" * 40}, "c" * 40),
    ({"before": "0" * 40}, "a" * 40),
    ({}, "a" * 40),
])
def test_event_base_selection(event, expected):
    assert review_base.select_base(event, "a" * 40) == expected


@pytest.mark.parametrize("sha", ["main", "", None, "a" * 39, "--help"])
def test_bad_pr_base_is_never_replaced_with_upstream(sha):
    with pytest.raises(ValueError):
        review_base.select_base({"pull_request": {"base": {"sha": sha}}}, "a" * 40)


@pytest.mark.parametrize("change", ["remove", "rename", "delete_file", "add"])
def test_inventory_reads_commits_before_overlays(tmp_path, monkeypatch, change):
    monkeypatch.chdir(tmp_path)
    def git(*args):
        return subprocess.check_output(["git", *args], text=True).strip()
    git("init", "-q")
    git("config", "user.name", "Inventory test")
    git("config", "user.email", "inventory@example.invalid")
    folder = tmp_path / "tests/fm_lib/integration_tests"
    folder.mkdir(parents=True)
    path = folder / "test_conversion.py"
    path.write_text("class TestConversion:\n    def test_existing(self): pass\n")
    git("add", ".")
    git("commit", "-qm", "base")
    base = git("rev-parse", "HEAD")
    if change == "delete_file":
        path.unlink()
    elif change == "rename":
        path.write_text("class TestConversion:\n    def test_renamed(self): pass\n")
    elif change == "remove":
        path.write_text("class TestConversion: pass\n")
    else:
        path.write_text(path.read_text() + "    async def test_added(self): pass\n")
    git("add", "-A")
    git("commit", "-qm", "candidate")
    result = review_base.verify_inventory(base, git("rev-parse", "HEAD"))
    assert result["status"] == ("passed" if change == "add" else "failed")
    if change != "add":
        assert result["removed"] == ["tests/fm_lib/integration_tests/test_conversion.py::TestConversion::test_existing"]
