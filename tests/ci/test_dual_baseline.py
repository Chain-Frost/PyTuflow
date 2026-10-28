"""Ensure a previously fixed upstream failure cannot return unnoticed."""
from copy import deepcopy
import pytest

from ci.accept_regression import accept
from tests.ci import test_regression_comparison as fixtures


@pytest.fixture
def evidence():
    writer = fixtures.RegressionComparisonTests()
    writer.setUp()
    yield writer
    writer.doCleanups()


def write(writer, label, cases, sha):
    path = writer.write_report(label, deepcopy(cases))
    writer.modify(path, lambda report: report["source"].update(sha=sha))
    return path


PASS = {"outcome": "passed"}
FAIL = {"outcome": "failed", "failure_type": "AssertionError", "failure_signature": "original defect", "phase": "call"}


def test_reintroduced_upstream_failure_fails_against_fixed_base(evidence):
    write(evidence, "upstream", {"test_existing": FAIL}, "a" * 40)
    write(evidence, "base", {"test_existing": PASS}, "b" * 40)
    write(evidence, "candidate", {"test_existing": FAIL}, "c" * 40)
    result = accept(evidence.root, "a" * 40, "b" * 40, "c" * 40, ["tmf"])
    assert result["comparisons"]["upstream"]["status"] == "passed"
    assert result["comparisons"]["base"]["status"] == "failed"
    assert result["status"] == "failed"


def test_removing_a_test_added_after_upstream_fails(evidence):
    write(evidence, "upstream", {"test_existing": PASS}, "a" * 40)
    write(evidence, "base", {"test_existing": PASS, "test_added": PASS}, "b" * 40)
    write(evidence, "candidate", {"test_existing": PASS}, "c" * 40)
    result = accept(evidence.root, "a" * 40, "b" * 40, "c" * 40, ["tmf"])
    assert result["status"] == "failed"
    assert any("Removed test" in p for p in result["problems"])


@pytest.mark.parametrize("base_sha", ["a" * 40, "b" * 40])
def test_fixed_failure_and_new_passing_test_are_accepted(evidence, base_sha):
    write(evidence, "upstream", {"test_existing": FAIL}, "a" * 40)
    if base_sha != "a" * 40:
        write(evidence, "base", {"test_existing": PASS}, base_sha)
    write(evidence, "candidate", {"test_existing": PASS, "test_added": PASS}, "c" * 40)
    result = accept(evidence.root, "a" * 40, base_sha, "c" * 40, ["tmf"])
    assert result["status"] == "passed"
    assert result["base_reuses_upstream"] == (base_sha == "a" * 40)


@pytest.mark.parametrize("wrong", [False, True])
def test_distinct_base_cannot_be_missing_or_have_wrong_identity(evidence, wrong):
    write(evidence, "upstream", {"test_existing": PASS}, "a" * 40)
    write(evidence, "candidate", {"test_existing": PASS}, "c" * 40)
    if wrong:
        write(evidence, "base", {"test_existing": PASS}, "a" * 40)
    result = accept(evidence.root, "a" * 40, "b" * 40, "c" * 40, ["tmf"])
    assert result["status"] == "failed"
    assert any("Invalid base identity" in p for p in result["problems"])
