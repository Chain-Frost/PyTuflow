"""Path-aware, always-reported gates for existing substantive PR jobs."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def applicable(paths: list[str], mode: str) -> bool:
    # Only explicit prose paths can opt out. Unknown files require CI.
    return any(not (path.endswith((".md", ".rst")) and
                        (path.startswith("docs/") or "/" not in path))
               for path in paths)


def require_results(
    expected: bool,
    changes: str,
    results: dict[str, str],
    names: set[str] | None = None,
    fast_gate_result: str | None = None,
    optional_skipped_jobs: set[str] | None = None,
) -> None:
    if changes != 'success':
        raise ValueError('Path classification did not succeed')
    if fast_gate_result is not None and fast_gate_result != 'success':
        raise ValueError(f'Fast contracts gate must succeed before full acceptance: {fast_gate_result!r}')
    if names is not None and set(results) != names:
        raise ValueError(f'Missing or unexpected jobs: {set(results)} != {names}')
    optional_skipped_jobs = optional_skipped_jobs or set()
    if not optional_skipped_jobs <= results.keys():
        raise ValueError(f'Unknown optionally skipped jobs: {optional_skipped_jobs - results.keys()}')
    required = {name: ('skipped' if not expected or name in optional_skipped_jobs else 'success')
                for name in results}
    if not results or any(results[name] != result for name, result in required.items()):
        raise ValueError(f'Expected substantive job outcomes {required}: {results}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['classify', 'verify'])
    parser.add_argument('--mode', choices=['fast', 'full'])
    parser.add_argument('--require-fast-gate', action='store_true')
    parser.add_argument('--conditional-python312', action='store_true')
    args = parser.parse_args()
    if args.command == 'classify':
        if not args.mode:
            parser.error('classify requires --mode')
        event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        if 'pull_request' in event:
            pr = event['pull_request']
            draft = pr.get('draft')
            if not isinstance(draft, bool):
                raise ValueError('Missing or invalid pull-request draft status')
            python312_required = not draft  # Ready for review means full pre-merge acceptance.
            # No API 300-file truncation; include both sides of renames/deletes.
            raw = subprocess.check_output([
                'git', 'diff', '--name-only', '--no-renames', '-z',
                f"{pr['base']['sha']}...{pr['head']['sha']}",
            ])
            paths = [p for p in raw.decode('utf-8').split('\0') if p]
            expected = applicable(paths, args.mode)
        elif event.get("before") and event["before"] != "0" * 40:
            python312_required = True  # Explicit ci-validation push probes run all versions.
            raw = subprocess.check_output([
                "git", "diff", "--name-only", "--no-renames", "-z",
                event["before"], event["after"],
            ])
            expected = applicable([p for p in raw.decode("utf-8").split("\0") if p], args.mode)
        else:
            expected = True  # First push or explicit dispatch always runs all lanes.
            python312_required = True
        with Path(os.environ['GITHUB_OUTPUT']).open('a', encoding='utf-8') as output:
            output.write(f"required={str(expected).lower()}\n")
            output.write(f"python312_required={str(python312_required).lower()}\n")
        print(f'Substantive {args.mode} jobs required: {expected}; Python 3.12 required: {python312_required}')
    else:
        value = os.environ['REQUIRED']
        if value not in {'true', 'false'}:
            raise ValueError(f'Invalid scope result: {value!r}')
        optional_skips: set[str] = set()
        if args.conditional_python312:
            flag = os.environ.get('PYTHON312_REQUIRED')
            if flag not in {'true', 'false'}:
                raise ValueError(f'Missing or invalid Python 3.12 classification: {flag!r}')
            name = 'python312_full' if args.require_fast_gate else 'python312_fast'
            if name not in os.environ['EXPECTED_JOBS'].split(','):
                raise ValueError(f'Missing named Python 3.12 lane: {name}')
            if flag == 'false':
                optional_skips.add(name)
        require_results(
            value == 'true',
            os.environ['CHANGES_RESULT'],
            json.loads(os.environ['JOB_RESULTS']),
            set(os.environ['EXPECTED_JOBS'].split(',')),
            fast_gate_result=os.environ.get('FAST_GATE_RESULT', '') if args.require_fast_gate else None,
            optional_skipped_jobs=optional_skips,
        )
        print('Applicable jobs succeeded' if value == 'true' else 'Documentation/unrelated scope: substantive jobs not required')


if __name__ == '__main__':
    main()
