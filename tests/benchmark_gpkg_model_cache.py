"""Exploratory within-process A/B timings; not native M480 acceptance evidence.

Run from the repository root after installing PyTuflow and its dependencies.
The source TCF and flags are synthetic and kept in a temporary directory.
Timing is producer-only, does not execute TUFLOW or perform physical preflight,
and does not substitute for repeated fresh-process, real-model comparisons.
"""

from __future__ import annotations

import argparse
import gc
import json
import runpy
import statistics
import tempfile
from pathlib import Path
from time import perf_counter


def main() -> None:
    """Compare the existing plan cache with temporary model-input storage."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=480)
    parser.add_argument("--blocks", type=int, default=2)
    args = parser.parse_args()
    if args.runs < 1 or args.blocks < 1:
        parser.error("runs and blocks must be positive")
    fixtures = runpy.run_path(
        str(Path(__file__).with_name("test_input_cache_prototype.py"))
    )
    make_model = fixtures["_model"]
    make_flags = fixtures["_flags"]
    measures: dict[str, list[float]] = {"plan": [], "input": []}
    with tempfile.TemporaryDirectory(prefix="pytuflow_cache_prototype_") as d:
        model = make_model(Path(d))
        flags = make_flags(args.runs)
        expected = model.collect_file_dependencies(flags)
        if not expected.passed:
            raise RuntimeError("Baseline synthetic fragment collection failed")
        if expected.fallback_runs:
            raise RuntimeError("Fixture did not exercise the fast fragment path")
        for block in range(args.blocks):
            order = (
                ("plan", "input", "input", "plan") if block % 2 == 0
                else ("input", "plan", "plan", "input")
            )
            for mode in order:
                gc.collect()
                begin = perf_counter()
                observed = model.collect_file_dependencies(
                    flags, _cache_location=mode
                )
                elapsed = perf_counter() - begin
                if observed.runs != expected.runs:
                    raise AssertionError(f"{mode} cache changed ordered run data")
                if observed.fragments != expected.fragments:
                    raise AssertionError(f"{mode} cache changed published fragments")
                measures[mode].append(elapsed)

    medians = {mode: statistics.median(values) for mode, values in measures.items()}
    print(
        json.dumps(
            {
                "scenario": "synthetic reusable nested model",
                "runs": args.runs,
                "blocks": args.blocks,
                "measurement": "warm-process dependency collection only",
                "medians_seconds": medians,
                "samples_seconds": measures,
                "input_over_plan_ratio": medians["input"] / medians["plan"],
                "fragment_evaluations": expected.fragment_evaluations,
                "fragment_reuses": expected.fragment_reuses,
                "whole_run_fallbacks": expected.fallback_runs,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
