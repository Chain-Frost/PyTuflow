"""Regression tests for temporary input-owned dependency fragment caches."""

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
def test_input_owned_fragments_match_normal_run_and_clean_up(
    tmp_path: Path, count: int
) -> None:
    """Reuse immutable fragments without retaining state on parsed inputs."""
    model = _model(tmp_path)
    flags = _flags(count)
    actual = model.collect_file_dependencies(flags)
    assert actual.passed
    assert actual.fallback_runs == 0
    assert actual.fragment_reuses > 0
    assert len(actual.fragments) > 0
    assert all(
        not hasattr(item, "_batch_dependency_fragments") for item in _inputs(model)
    )
    repeated = model.collect_file_dependencies(flags)
    assert repeated.runs == actual.runs
    assert repeated.fragments == actual.fragments
    assert repeated.fragment_reuses == actual.fragment_reuses
    if count <= 36:
        assert actual.runs == collect_fallback_dependencies(model, flags).runs


def test_failed_run_does_not_publish_an_incomplete_input_cache(tmp_path: Path) -> None:
    """A failed run must not contaminate subsequent successful contexts."""
    path = tmp_path / "model.tcf"
    path.write_text(
        "Read Grid Zpts == terrain.tif\n"
        "IF Scenario == BAD\n PAUSE\nEND IF\n",
        encoding="utf-8",
    )
    model = TCF(path)
    flags = ["-s1 BAD", "-s1 GOOD", "-s1 GOOD -e1 A"]
    actual = model.collect_file_dependencies(flags)
    assert actual.runs[0].error is not None
    assert actual.runs[0].file_references == ()
    assert actual.runs[1].error is None
    assert actual.runs[1].file_references == collect_fallback_dependencies(
        model, ["-s1 GOOD"]
    ).runs[0].file_references
    assert all(
        not hasattr(item, "_batch_dependency_fragments") for item in _inputs(model)
    )


def test_input_cache_cleans_up_when_flag_generator_raises(tmp_path: Path) -> None:
    """Clean up input-owned cache after interruption of a generator."""
    model = _model(tmp_path)

    def flags():
        """Yield a run, then interrupt the next iteration."""
        yield "-s1 DEV -e1 Q10"
        raise RuntimeError("interrupted")

    with pytest.raises(RuntimeError, match="interrupted"):
        model.collect_file_dependencies(flags())
    assert all(
        not hasattr(item, "_batch_dependency_fragments") for item in _inputs(model)
    )
    assert model.collect_file_dependencies(["-s1 DEV -e1 Q10"]).passed


def test_overlapping_batches_do_not_share_input_cache(tmp_path: Path) -> None:
    """Overlapping batches must reject foreign cached fragments."""
    model = _model(tmp_path)
    overlap: list[object] = []

    def flags():
        """Invoke another batch after the outer batch has cached one run."""
        yield "-s1 DEV -e1 Q10"
        overlap.append(model.collect_file_dependencies(["-s1 DEV -e1 Q10"]))
        yield "-s1 EXG -e1 Q100"

    outer = model.collect_file_dependencies(flags())
    assert outer.passed
    assert len(overlap) == 1
    nested = overlap[0]
    assert not nested.passed
    assert nested.runs[0].error is not None
    assert "another active batch" in nested.runs[0].error
    assert all(
        not hasattr(item, "_batch_dependency_fragments") for item in _inputs(model)
    )
