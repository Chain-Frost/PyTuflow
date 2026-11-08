import pytest

from ci.pr_gate import applicable, require_live_pr_state, require_results


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
    event = {"pull_request": {"base": {"sha": base}, "head": {"sha": head}, "draft": True}} if event_kind == "pull_request" else {"before": base, "after": head}
    event_path, output = tmp_path / "event.json", tmp_path / "output"
    event_path.write_text(json.dumps(event))
    env = dict(os.environ, GITHUB_EVENT_PATH=str(event_path), GITHUB_OUTPUT=str(output))
    helper = Path(__file__).resolve().parents[2] / "ci/pr_gate.py"
    subprocess.run([sys.executable, str(helper), "classify", "--mode", "full"], cwd=tmp_path, env=env, check=True)
    assert output.read_text() == f"required={expected}\npython312_required={'false' if event_kind == 'pull_request' else 'true'}\n"

@pytest.mark.parametrize("result", ["failure", "cancelled", "skipped", "pending", ""])
@pytest.mark.parametrize("substantive", [True, False])
def test_full_gate_fails_closed_when_fast_gate_is_not_successful(result, substantive):
    lanes = {name: "success" if substantive else "skipped"
             for name in ("python311_full", "python312_full", "python314_full")}
    with pytest.raises(ValueError, match="Fast contracts gate"):
        require_results(substantive, "success", lanes, set(lanes), fast_gate_result=result)


@pytest.mark.parametrize("substantive", [True, False])
def test_full_gate_accepts_complete_fast_and_full_results(substantive):
    lanes = {name: "success" if substantive else "skipped"
             for name in ("python311_full", "python312_full", "python314_full")}
    require_results(substantive, "success", lanes, set(lanes), fast_gate_result="success")


def test_full_gate_cli_rejects_missing_fast_output(monkeypatch):
    import json
    import sys
    from ci.pr_gate import main

    monkeypatch.setattr(sys, "argv", ["pr_gate.py", "verify", "--require-fast-gate"])
    monkeypatch.setenv("REQUIRED", "true")
    monkeypatch.setenv("CHANGES_RESULT", "success")
    monkeypatch.setenv("EXPECTED_JOBS", "python311_full,python312_full,python314_full")
    monkeypatch.setenv("JOB_RESULTS", json.dumps({
        name: "skipped" for name in ("python311_full", "python312_full", "python314_full")
    }))
    monkeypatch.delenv("FAST_GATE_RESULT", raising=False)
    with pytest.raises(ValueError, match="Fast contracts gate"):
        main()


def test_staged_workflow_has_single_scope_and_fail_closed_gates():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    workflow = (root / ".github/workflows/original-library-regression.yml").read_text()
    lane = (root / ".github/workflows/original-library-lane.yml").read_text()
    assert not (root / ".github/workflows/original-library-quick.yml").exists()
    assert workflow.count("      - id: scope") == 1
    assert "ci/resource-efficiency-20261108" in workflow
    assert "'ci-validation/**'" in workflow
    assert workflow.count("    name: Fast contracts gate") == 1
    assert workflow.count("    name: Original library acceptance") == 1
    assert workflow.count("    if: always()") == 2
    assert "needs: [changes, fast_gate]" in workflow
    assert workflow.count("needs.fast_gate.result == 'success'") == 3
    # An optional skipped Python 3.12 fast lane is a transitive dependency of
    # fast_gate. GitHub's implicit success() would otherwise skip both required
    # full lanes despite a successful fast gate.
    assert workflow.count("if: always() && needs.changes.result == 'success'") == 3
    assert "run: python ci/pr_gate.py verify --require-fast-gate --conditional-python312" in workflow
    assert "types: [opened, synchronize, reopened, ready_for_review, converted_to_draft]" in workflow
    assert workflow.count("PYTHON312_REQUIRED:") == 2
    assert workflow.count("PR_GATE_TOKEN:") == 2
    assert workflow.count("--verify-current-pr") == 2
    assert "pull-requests: read" in workflow
    assert workflow.count("needs.changes.outputs.python312_required == 'true'") == 2
    assert workflow.count("run_contracts: false") == 3
    assert "run_contracts:" in lane and "default: true" in lane
    assert lane.count("if: inputs.run_contracts") == 5



@pytest.mark.parametrize("substantive", [True, False])
@pytest.mark.parametrize("python312_required", [True, False])
@pytest.mark.parametrize("kind", ["fast", "full"])
def test_conditional_python312_gate_accepts_expected_outcomes(
    substantive, python312_required, kind
):
    names = {f"python{version}_{kind}" for version in ("311", "312", "314")}
    results = {name: ("success" if substantive else "skipped") for name in names}
    optional = {f"python312_{kind}"} if not python312_required else set()
    if not python312_required:
        results[f"python312_{kind}"] = "skipped"
    require_results(
        substantive, "success", results, names,
        fast_gate_result="success" if kind == "full" else None,
        optional_skipped_jobs=optional,
    )


@pytest.mark.parametrize("wrong", ["failure", "cancelled", "skipped", "pending", ""])
@pytest.mark.parametrize("kind", ["fast", "full"])
def test_ready_to_merge_requires_successful_python312(wrong, kind):
    names = {f"python{version}_{kind}" for version in ("311", "312", "314")}
    outcomes = {name: "success" for name in names}
    outcomes[f"python312_{kind}"] = wrong
    with pytest.raises(ValueError, match="Expected substantive job outcomes"):
        require_results(
            True, "success", outcomes, names,
            fast_gate_result="success" if kind == "full" else None,
        )


@pytest.mark.parametrize("name", ["python311_fast", "python314_fast"])
def test_draft_only_allows_python312_skip(name):
    outcomes = {"python311_fast": "success", "python312_fast": "skipped", "python314_fast": "success"}
    outcomes[name] = "skipped"
    with pytest.raises(ValueError, match="Expected substantive job outcomes"):
        require_results(
            True, "success", outcomes, set(outcomes),
            optional_skipped_jobs={"python312_fast"},
        )


@pytest.mark.parametrize("draft, expected", [(True, "false"), (False, "true")])
def test_ready_status_controls_optional_python312(tmp_path, monkeypatch, draft, expected):
    import json
    import subprocess
    import sys
    from ci.pr_gate import main

    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], text=True).strip()

    git("init", "-q")
    git("config", "user.name", "Scope test")
    git("config", "user.email", "scope@example.invalid")
    (tmp_path / "source.py").write_text("before = True\n")
    git("add", ".")
    git("commit", "-qm", "before")
    base = git("rev-parse", "HEAD")
    (tmp_path / "source.py").write_text("after = True\n")
    git("commit", "-qam", "after")
    head = git("rev-parse", "HEAD")
    event = tmp_path / "event.json"
    output = tmp_path / "output"
    event.write_text(json.dumps({"pull_request": {
        "base": {"sha": base}, "head": {"sha": head}, "draft": draft,
    }}))
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["pr_gate.py", "classify", "--mode", "full"])
    main()
    assert output.read_text() == f"required=true\npython312_required={expected}\n"


def test_missing_pr_draft_fails_closed(tmp_path, monkeypatch):
    import json
    import sys
    from ci.pr_gate import main

    path = tmp_path / "event.json"
    path.write_text(json.dumps({"pull_request": {"base": {}, "head": {}}}))
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(path))
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "output"))
    monkeypatch.setattr(sys, "argv", ["pr_gate.py", "classify", "--mode", "full"])
    with pytest.raises(ValueError, match="draft"):
        main()


@pytest.mark.parametrize("flag", [None, "", "unknown", "pending"])
def test_gate_rejects_missing_or_invalid_python312_flag(monkeypatch, flag):
    import json
    import sys
    from ci.pr_gate import main

    monkeypatch.setattr(sys, "argv", ["pr_gate.py", "verify", "--conditional-python312"])
    monkeypatch.setenv("REQUIRED", "true")
    monkeypatch.setenv("CHANGES_RESULT", "success")
    monkeypatch.setenv("EXPECTED_JOBS", "python311_fast,python312_fast,python314_fast")
    monkeypatch.setenv("JOB_RESULTS", json.dumps({
        "python311_fast": "success", "python312_fast": "skipped", "python314_fast": "success",
    }))
    if flag is None:
        monkeypatch.delenv("PYTHON312_REQUIRED", raising=False)
    else:
        monkeypatch.setenv("PYTHON312_REQUIRED", flag)
    with pytest.raises(ValueError, match="Python 3.12 classification"):
        main()


def test_gate_rejects_optional_unknown_job():
    with pytest.raises(ValueError, match="Unknown optionally skipped jobs"):
        require_results(
            True, "success", {"python311_fast": "success"},
            optional_skipped_jobs={"python312_fast"},
        )



def _pr_snapshot(*, draft: bool, head: str = "a" * 40, base: str = "b" * 40) -> dict:
    return {
        "number": 66, "state": "open", "draft": draft,
        "head": {"sha": head, "ref": "ci/feature"},
        "base": {"sha": base, "ref": "contrib/integration"},
    }


@pytest.mark.parametrize("draft", [True, False])
def test_live_pr_check_accepts_unchanged_review_state_and_revision(draft):
    pr = _pr_snapshot(draft=draft)
    require_live_pr_state({"pull_request": pr}, pr)


@pytest.mark.parametrize("event_draft, current_draft", [(True, False), (False, True)])
def test_live_pr_check_rejects_stale_draft_and_ready_reruns(event_draft, current_draft):
    with pytest.raises(ValueError, match="Stale PR draft/ready state"):
        require_live_pr_state(
            {"pull_request": _pr_snapshot(draft=event_draft)},
            _pr_snapshot(draft=current_draft),
        )


@pytest.mark.parametrize("revision", ["head", "base"])
def test_live_pr_check_rejects_moving_candidate_or_base(revision):
    old = _pr_snapshot(draft=True)
    live = _pr_snapshot(draft=True)
    live[revision]["sha"] = "c" * 40
    with pytest.raises(ValueError, match=f"Stale PR {revision} revision"):
        require_live_pr_state({"pull_request": old}, live)


def test_live_pr_check_rejects_retarget_to_another_base():
    old = _pr_snapshot(draft=False)
    live = _pr_snapshot(draft=False)
    live["base"]["ref"] = "contrib/other"
    with pytest.raises(ValueError, match="Stale PR base ref"):
        require_live_pr_state({"pull_request": old}, live)


@pytest.mark.parametrize("state", ["closed", "merged"])
def test_live_pr_check_rejects_closed_request(state):
    old = _pr_snapshot(draft=True)
    live = _pr_snapshot(draft=True)
    live["state"] = state
    with pytest.raises(ValueError, match="no longer open"):
        require_live_pr_state({"pull_request": old}, live)


def test_live_pr_verifier_rejects_missing_token(tmp_path, monkeypatch):
    import json
    from ci.pr_gate import verify_current_pr_state

    pr = _pr_snapshot(draft=True)
    path = tmp_path / "event.json"
    path.write_text(json.dumps({"number": 66, "pull_request": pr}))
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(path))
    monkeypatch.setenv("GITHUB_REPOSITORY", "Chain-Frost/PyTuflow")
    monkeypatch.delenv("PR_GATE_TOKEN", raising=False)
    with pytest.raises(ValueError, match="Missing GitHub token"):
        verify_current_pr_state()


def test_live_pr_verifier_rejects_stale_api_snapshot(tmp_path, monkeypatch):
    import json
    from io import BytesIO
    from ci import pr_gate

    pr = _pr_snapshot(draft=True)
    path = tmp_path / "event.json"
    path.write_text(json.dumps({"number": 66, "pull_request": pr}))
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(path))
    monkeypatch.setenv("GITHUB_REPOSITORY", "Chain-Frost/PyTuflow")
    monkeypatch.setenv("PR_GATE_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_API_URL", "https://api.github.com")
    payload = json.dumps(_pr_snapshot(draft=False)).encode()
    monkeypatch.setattr(pr_gate.urllib.request, "urlopen", lambda request, timeout: BytesIO(payload))
    with pytest.raises(ValueError, match="Stale PR draft/ready state"):
        pr_gate.verify_current_pr_state()
