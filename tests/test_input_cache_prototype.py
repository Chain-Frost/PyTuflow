"""Differential contracts for the experimental model-owned fragment cache."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from pytuflow import TCF
from pytuflow._tmf.deferred_dependency_fallback import collect_fallback_dependencies


def _model(tmp_path: Path) -> TCF:
    """Create nested, scenario- and event-dependent sources for 480-run reuse."""
    (tmp_path / "events.tef").write_text(
        "Define Event == Q10\n BC Event Source == _event_ | ten\nEnd Define\n"
        "Define Event == Q100\n BC Event Source == _event_ | hundred\nEnd Define\n",
        encoding="utf-8",
    )
    (tmp_path / "geometry.tgc").write_text(
        "IF Scenario == DEV\n Read GIS Code == dev.shp\n"
        "ELSE\n Read GIS Code == exg.shp\nEND IF\n"
        "Read Grid Zpts == terrain.tif\n",
        encoding="utf-8",
    )
    (tmp_path / "boundary.tbc").write_text(
        "Read GIS BC == boundary_<<Dir>>.shp\n", encoding="utf-8"
    )
    (tmp_path / "bc.csv").write_text(
        "Name,Source,Column 1,Column 2\n"
        "flow,inflow__event_.csv,Time,Flow\n", encoding="utf-8"
    )
    path = tmp_path / "model.tcf"
    path.write_text(
        "Event File == events.tef\n"
        "Set Variable Dir == _event_\n"
        "Geometry Control File == geometry.tgc\n"
        "BC Database == bc.csv\n"
        "BC Control File == boundary.tbc\n",
        encoding="utf-8",
    )
    return TCF(path)


def _flags(count: int) -> list[str]:
    """Generate explicitly distinct run flag sets without changing the model."""
    return [
        f"-s1 {('DEV', 'EXG')[i % 2]} "
        f"-e1 {('Q10', 'Q100')[(i // 2) % 2]} -s2 unused{i}"
        for i in range(count)
    ]


def _inputs(model: TCF) -> list[Any]:
    """Collect the parsed build-state objects used by the fragment compiler."""
    return model.find_input(recursive=True)


@pytest.mark.parametrize("count", [4, 36, 240, 480])
def test_per_input_cache_matches_plan_cache_and_cleans_up(tmp_path: Path, count: int) -> None:
    """Keep every immutable run and fragment in the same source order."""
    model = _model(tmp_path)
    flags = _flags(count)
    expected = model.collect_file_dependencies(flags)
    alternative = model.collect_file_dependencies(flags, _cache_location="input")
    assert expected.passed and alternative.passed
    assert alternative.runs == expected.runs
    assert alternative.fragments == expected.fragments
    assert alternative.fragment_evaluations == expected.fragment_evaluations
    assert alternative.fragment_reuses == expected.fragment_reuses
    assert alternative.fallback_runs == expected.fallback_runs
    assert all(not hasattr(item, "_prototype_batch_fragments") for item in _inputs(model))
    # Re-running the accepted path must not reuse stale experiment cache data.
    assert model.collect_file_dependencies(flags).runs == expected.runs


def test_failed_run_does_not_publish_an_incomplete_input_cache(tmp_path: Path) -> None:
    """A failing run must not contaminate later successful source references."""
    path = tmp_path / "model.tcf"
    path.write_text(
        "Read Grid Zpts == terrain.tif\n"
        "IF Scenario == BAD\n PAUSE\nEND IF\n",
        encoding="utf-8",
    )
    model = TCF(path)
    flags = ["-s1 BAD", "-s1 GOOD", "-s1 GOOD -e1 A"]
    baseline = model.collect_file_dependencies(flags)
    candidate = model.collect_file_dependencies(flags, _cache_location="input")
    assert candidate.runs == baseline.runs
    assert candidate.runs[0].error is not None
    assert candidate.runs[1].error is None
    assert candidate.runs[1].file_references == collect_fallback_dependencies(
        model, ["-s1 GOOD"]
    ).runs[0].file_references
    assert all(not hasattr(item, "_prototype_batch_fragments") for item in _inputs(model))


def test_input_cache_cleans_up_when_flag_generator_raises(tmp_path: Path) -> None:
    """Never retain an experiment-only cache after an unexpected batch error."""
    model = _model(tmp_path)

    def flags():
        """Yield a run, then simulate an interrupted batch."""
        yield "-s1 DEV -e1 Q10"
        raise RuntimeError("interrupted")

    with pytest.raises(RuntimeError, match="interrupted"):
        model.collect_file_dependencies(flags(), _cache_location="input")
    assert all(not hasattr(item, "_prototype_batch_fragments") for item in _inputs(model))
    assert model.collect_file_dependencies(["-s1 DEV -e1 Q10"]).passed
