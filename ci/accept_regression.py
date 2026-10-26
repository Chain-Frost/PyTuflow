"""Require source identities and regression parity against upstream and PR base."""
import argparse
import json
from pathlib import Path

from ci.compare_regression import compare_reports
from ci.run_regression import REQUIRED_GROUPS


def accept(root: Path, upstream: str, base: str, candidate: str,
           required_groups: list[str] | None = None) -> dict:
    result = {"status": "failed", "problems": [], "comparisons": {},
              "expected_sources": {"upstream": upstream, "base": base, "candidate": candidate},
              "base_reuses_upstream": base == upstream}
    paths = {"upstream": root / "upstream/report.json",
             "base": root / ("upstream" if base == upstream else "base") / "report.json",
             "candidate": root / "candidate/report.json"}
    for label, path in paths.items():
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
            if report["source"]["sha"] != result["expected_sources"][label]:
                raise ValueError("wrong source SHA")
        except (OSError, ValueError, KeyError, TypeError) as error:
            result["problems"].append(f"Invalid {label} identity: {error}")
    if not result["problems"]:
        for label in ("upstream", "base"):
            comparison = compare_reports(paths[label], paths["candidate"],
                                         required_groups or list(REQUIRED_GROUPS))
            result["comparisons"][label] = comparison
            result["problems"].extend(f"{label}: {p}" for p in comparison["problems"])
    if not result["problems"]:
        result["status"] = "passed"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    result = accept(args.root, args.upstream, args.base, args.candidate)
    args.root.mkdir(parents=True, exist_ok=True)
    (args.root / "acceptance.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for label, comparison in result["comparisons"].items():
        (args.root / f"{label}-comparison.json").write_text(
            json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result["status"] != "passed"


if __name__ == "__main__":
    raise SystemExit(main())
