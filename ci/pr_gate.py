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


def require_results(expected: bool, changes: str, results: dict[str, str], names: set[str] | None = None) -> None:
    if changes != 'success':
        raise ValueError('Path classification did not succeed')
    if names is not None and set(results) != names:
        raise ValueError(f'Missing or unexpected jobs: {set(results)} != {names}')
    required = 'success' if expected else 'skipped'
    if not results or any(result != required for result in results.values()):
        raise ValueError(f'Expected substantive jobs {required}: {results}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['classify', 'verify'])
    parser.add_argument('--mode', choices=['fast', 'full'])
    args = parser.parse_args()
    if args.command == 'classify':
        if not args.mode:
            parser.error('classify requires --mode')
        event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        if 'pull_request' in event:
            pr = event['pull_request']
            # No API 300-file truncation; include both sides of renames/deletes.
            raw = subprocess.check_output([
                'git', 'diff', '--name-only', '--no-renames', '-z',
                f"{pr['base']['sha']}...{pr['head']['sha']}",
            ])
            paths = [p for p in raw.decode('utf-8').split('\0') if p]
            expected = applicable(paths, args.mode)
        elif event.get("before") and event["before"] != "0" * 40:
            raw = subprocess.check_output([
                "git", "diff", "--name-only", "--no-renames", "-z",
                event["before"], event["after"],
            ])
            expected = applicable([p for p in raw.decode("utf-8").split("\0") if p], args.mode)
        else:
            expected = True  # First push or explicit dispatch always runs all lanes.
        with Path(os.environ['GITHUB_OUTPUT']).open('a', encoding='utf-8') as output:
            output.write(f"required={str(expected).lower()}\n")
        print(f'Substantive {args.mode} jobs required: {expected}')
    else:
        value = os.environ['REQUIRED']
        if value not in {'true', 'false'}:
            raise ValueError(f'Invalid scope result: {value!r}')
        require_results(value == 'true', os.environ['CHANGES_RESULT'], json.loads(os.environ['JOB_RESULTS']), set(os.environ['EXPECTED_JOBS'].split(',')))
        print('Applicable jobs succeeded' if value == 'true' else 'Documentation/unrelated scope: substantive jobs not required')


if __name__ == '__main__':
    main()
