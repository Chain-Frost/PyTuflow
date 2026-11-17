"""Repeatable, solver-free dependency-collection benchmark for large BC databases.

Run against the baseline and candidate in separate clean checkouts with the
same Python, dependencies, fixture options and filesystem conditions. Times
are only comparable when both processes run under equivalent conditions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import tempfile
from itertools import product
from pathlib import Path
from time import perf_counter
from typing import Any

from pytuflow import TCF


def _fixture(directory: Path, *, rows: int) -> Path:
    """Generate a temporary read-only inspection model with repeated BC sources."""
    database = directory / "bc.csv"
    database.write_text(
        "Name,Source,Column 1,Column 2\n"
        + "".join(
            f"BC{i:04d},rain_<<~e1~>>_<<~e2~>>_<<~e3~>>.csv,Time,Flow{i:04d}\n"
            for i in range(rows)
        ),
        encoding="utf-8",
    )
    tcf = directory / "model.tcf"
    tcf.write_text(
        "IF Scenario == EXG\n"
        "Read GIS BC == boundaries_exg.shp\n"
        "ELSE\n"
        "Read GIS BC == boundaries_dev.shp\n"
        "END IF\n"
        "BC Database == bc.csv\n"
        "Read Grid Zpts == terrain_<<~e1~>>.tif\n",
        encoding="utf-8",
    )
    return tcf


def _checksum(runs: tuple[Any, ...]) -> str:
    """Record reproducible selected provenance, independent of fixture directory."""
    digest = hashlib.sha256()
    for run in runs:
        row = {
            "index": run.index,
            "flags": run.flags,
            "error": run.error,
            "files": [
                (
                    ref.path_pattern.name,
                    ref.layer_pattern,
                    ref.csv_columns,
                    ref.origin,
                )
                for ref in run.file_references
            ],
            "sources": [
                (
                    ref.database_kind,
                    ref.entry_name,
                    ref.path_pattern.name,
                    ref.csv_columns,
                    ref.input_uuid,
                )
                for ref in run.database_sources
            ],
            "activation": [
                (item.sequence, item.database_kind, item.database_path.name)
                for item in run.database_activations
            ],
            "commands": [
                (item.command_index, item.command_name, item.command_text, item.reference_count)
                for item in run.ordered_inputs
            ],
        }
        # The UUID is an ownership identifier within one parse, not a stable
        # cross-checkout fingerprint. Use complete field-level parity tests
        # against the ordinary fallback before interpreting this benchmark.
        row["sources"] = [item[:-1] for item in row["sources"]]
        digest.update(json.dumps(row, ensure_ascii=False, sort_keys=True).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=40, help="Repeated BC database rows (default 40).")
    parser.add_argument("--aep", type=int, default=8, help="AEP selections.")
    parser.add_argument("--durations", type=int, default=13, help="Duration selections.")
    parser.add_argument("--tps", type=int, default=10, help="Temporal patterns.")
    parser.add_argument("--repeats", type=int, default=3, help="Independent collections using the same parsed TCF.")
    parser.add_argument("--json-output", type=Path, help="Write benchmark JSON to a new file, apart from parser logs.")
    arguments = parser.parse_args()
    if min(arguments.rows, arguments.aep, arguments.durations, arguments.tps, arguments.repeats) < 1:
        parser.error("All numeric options must be positive")
    runs = tuple(
        f"-s1 EXG -e1 Q{a:02d} -e2 D{d:03d} -e3 TP{tp:02d}"
        for a, d, tp in product(
            range(arguments.aep), range(arguments.durations), range(arguments.tps)
        )
    )
    with tempfile.TemporaryDirectory(prefix="pytuflow-bc-dependency-") as location:
        tcf = _fixture(Path(location), rows=arguments.rows)
        parse_start = perf_counter()
        model = TCF(tcf)
        parse_seconds = perf_counter() - parse_start
        elapsed: list[float] = []
        checksums: set[str] = set()
        counts: list[tuple[int, int, int, int]] = []
        for _ in range(arguments.repeats):
            started = perf_counter()
            batch = model.collect_file_dependencies(runs)
            elapsed.append(perf_counter() - started)
            if not batch.passed:
                raise RuntimeError(
                    f"Dependency collection failed: {[run.error for run in batch.runs if run.error]}"
                )
            checksums.add(_checksum(batch.runs))
            counts.append(
                (
                    len(batch.runs),
                    sum(len(run.database_sources) for run in batch.runs),
                    batch.fragment_evaluations,
                    batch.fragment_reuses,
                )
            )
        if len(checksums) != 1 or len(set(counts)) != 1:
            raise RuntimeError("Repeated equivalent selections changed their dependency results")
        report = {
            "run_count": len(runs),
            "bc_rows": arguments.rows,
            "repeats": arguments.repeats,
            "parse_seconds": round(parse_seconds, 4),
            "collection_seconds": [round(value, 4) for value in elapsed],
            "median_collection_seconds": round(statistics.median(elapsed), 4),
            "run_count_and_source_count": counts[0][:2],
            "fragment_evaluations": counts[0][2],
            "fragment_reuses": counts[0][3],
            "selected_provenance_sha256": next(iter(checksums)),
            "interpretation": "Benchmark only. Compare full fallback semantics and matched native samples.",
        }
    document = json.dumps(report, indent=2)
    if arguments.json_output is not None:
        with arguments.json_output.open("x", encoding="utf-8") as output:
            output.write(document + "\n")
    print(document)


if __name__ == "__main__":
    main()
