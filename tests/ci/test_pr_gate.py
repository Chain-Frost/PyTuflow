import pytest

from ci.pr_gate import applicable, require_results


@pytest.mark.parametrize('mode', ['fast', 'full'])
@pytest.mark.parametrize('path', ['README.md', 'docs/usage.rst', 'CONTRIBUTING.md'])
def test_documentation_does_not_require_expensive_jobs(mode, path):
    assert not applicable([path], mode)


@pytest.mark.parametrize('mode', ['fast', 'full'])
@pytest.mark.parametrize('path', ['pytuflow/x.py', 'tests/data/input.txt', 'ci/pr_gate.py',
                                  'hatch_build.py', 'requirements-dev.txt', 'MANIFEST.in'])
def test_code_build_and_fixture_changes_require_jobs(mode, path):
    assert applicable(['README.md', path], mode)


def test_gate_workflow_edits_require_their_substantive_jobs():
    assert applicable(['.github/workflows/original-library-quick.yml'], 'fast')
    assert applicable(['.github/workflows/original-library-regression.yml'], 'full')


@pytest.mark.parametrize('result', ['failure', 'cancelled', 'skipped', 'pending'])
def test_required_job_cannot_be_skipped_or_fail(result):
    with pytest.raises(ValueError):
        require_results(True, 'success', {'regression': result, 'wheel': 'success'})


def test_successful_code_and_explicit_documentation_outcomes():
    require_results(True, 'success', {'regression': 'success', 'wheel': 'success'})
    require_results(False, 'success', {'regression': 'skipped', 'wheel': 'skipped'})


def test_classifier_failure_and_empty_results_fail_closed():
    with pytest.raises(ValueError):
        require_results(False, 'failure', {'regression': 'skipped'})
    with pytest.raises(ValueError):
        require_results(True, 'success', {})


@pytest.mark.parametrize("path", ["unknown.bin", ".github/actions/setup/action.yml", "ci/policy.md", "tests/README.md"])
def test_unknown_and_control_paths_fail_closed(path):
    assert applicable([path], "fast")
    assert applicable([path], "full")


def test_missing_named_job_fails_closed():
    with pytest.raises(ValueError, match="Missing or unexpected"):
        require_results(True, "success", {"regression": "success"}, {"regression", "wheel"})


@pytest.mark.parametrize("result", ["failure", "cancelled", "skipped", "", "pending"])
def test_every_required_lane_fails_closed(result):
    names = {"py310", "py312", "py314", "wheel310", "wheel312", "wheel314"}
    for name in names:
        jobs = dict.fromkeys(names, "success")
        jobs[name] = result
        with pytest.raises(ValueError):
            require_results(True, "success", jobs, names)


@pytest.mark.parametrize("event_kind", ["pull_request", "push"])
@pytest.mark.parametrize("renamed, expected", [(False, "false"), (True, "true")])
def test_real_git_scope_classification(tmp_path, event_kind, renamed, expected):
    import json
    import os
    from pathlib import Path
    import subprocess
    import sys

    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], text=True).strip()

    git("init", "-q")
    git("config", "user.name", "Scope test")
    git("config", "user.email", "scope@example.invalid")
    (tmp_path / "source.py").write_text("# example\n")
    git("add", ".")
    git("commit", "-qm", "base")
    base = git("rev-parse", "HEAD")
    if renamed:
        git("mv", "source.py", "README.md")
    else:
        (tmp_path / "README.md").write_text("prose\n")
        git("add", ".")
    git("commit", "-qm", "change")
    head = git("rev-parse", "HEAD")
    event = {"pull_request": {"base": {"sha": base}, "head": {"sha": head}}} if event_kind == "pull_request" else {"before": base, "after": head}
    event_path, output = tmp_path / "event.json", tmp_path / "output"
    event_path.write_text(json.dumps(event))
    env = dict(os.environ, GITHUB_EVENT_PATH=str(event_path), GITHUB_OUTPUT=str(output))
    helper = Path(__file__).resolve().parents[2] / "ci/pr_gate.py"
    subprocess.run([sys.executable, str(helper), "classify", "--mode", "full"], cwd=tmp_path, env=env, check=True)
    assert output.read_text() == f"required={expected}\n"
