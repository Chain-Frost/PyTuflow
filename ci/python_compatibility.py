"""Audit tracked production and CI Python against the minimum language grammar."""
import ast
from pathlib import Path
import subprocess
import sys


def main():
    files = subprocess.check_output(["git", "ls-files", "-z", "--", "*.py"], text=True).split("\0")
    # New bootstrap files are included before the first commit as well.
    files = sorted(set(files) | {str(p) for p in Path("ci").glob("*.py")})
    errors = []
    for name in filter(None, files):
        try:
            ast.parse(Path(name).read_bytes(), filename=name, feature_version=(3, 11))
        except SyntaxError as error:
            errors.append(f"{name}:{error.lineno}: {error.msg}")
    print(f"Python {sys.version}; Python 3.11 grammar: {len(files) - 1} files, {len(errors)} errors")
    print("\n".join(errors))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
