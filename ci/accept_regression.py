"""Verify source identity before accepting complete regression evidence."""
import argparse
import json
from pathlib import Path

from compare_regression import compare_reports
from run_regression import REQUIRED_GROUPS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    for label, expected in (("upstream", args.upstream), ("candidate", args.candidate)):
        report = json.loads((args.root / label / "report.json").read_text())
        if report["source"]["sha"] != expected:
            raise ValueError(f"Wrong {label} source identity")
    result = compare_reports(args.root / "upstream/report.json", args.root / "candidate/report.json", list(REQUIRED_GROUPS))
    (args.root / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return result["status"] != "passed"


if __name__ == "__main__":
    raise SystemExit(main())
