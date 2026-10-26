"""Resolve the event's exact review base and protect pre-overlay test definitions."""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import subprocess


def select_base(event: dict, upstream: str) -> str:
    if "pull_request" in event:
        value = event["pull_request"]["base"]["sha"]
    else:
        value = event.get("before")
        if not value or value == "0" * 40:
            value = upstream
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise ValueError("Review base must be an exact commit SHA")
    return value


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args])


def test_inventory(revision: str) -> set[str]:
    # Read committed source before shared FM overlays can replace test files.
    names = git("ls-tree", "-r", "--name-only", "-z", revision, "--", "tests").decode().split("\0")
    inventory = set()
    for name in names:
        if not name.endswith(".py"):
            continue
        tree = ast.parse(git("show", f"{revision}:{name}"), filename=name)

        def visit(node, parents=()):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    qualified = (*parents, child.name)
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test"):
                        inventory.add(name + "::" + "::".join(qualified))
                    visit(child, qualified)
                else:
                    visit(child, parents)
        visit(tree)
    return inventory


def verify_inventory(base: str, candidate: str) -> dict:
    old, new = test_inventory(base), test_inventory(candidate)
    removed = sorted(old - new)
    return {"base": base, "candidate": candidate, "base_count": len(old),
            "candidate_count": len(new), "removed": removed,
            "status": "passed" if old and not removed else "failed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--candidate", default="HEAD")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
    base = select_base(event, args.upstream)
    if git("rev-parse", "--verify", base + "^{commit}").decode().strip() != base:
        raise ValueError("Review base is not the requested commit")
    candidate = git("rev-parse", "--verify", args.candidate + "^{commit}").decode().strip()
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
        output.write(f"sha={base}\n")
    result = verify_inventory(base, candidate)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result["status"] != "passed"


if __name__ == "__main__":
    raise SystemExit(main())
