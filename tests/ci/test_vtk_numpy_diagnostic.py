"""Exact-match acceptance for the known-bad VTK/NumPy dependency pairing."""
import pytest

from ci.diagnostics.vtk_numpy_compat import (
    SHAPE_DEPRECATION,
    is_expected_shape_deprecation,
)


@pytest.mark.parametrize("warning", [
    DeprecationWarning(SHAPE_DEPRECATION),
    DeprecationWarning(SHAPE_DEPRECATION + "\nAs an alternative, use np.reshape."),
])
def test_expected_shape_warning_matches(warning):
    assert is_expected_shape_deprecation(warning)


@pytest.mark.parametrize("other", [
    DeprecationWarning("unrelated deprecation"),
    DeprecationWarning("Setting the shape on a NumPy array has been deprecated"),
    RuntimeError(SHAPE_DEPRECATION),
    UserWarning(SHAPE_DEPRECATION),
    ImportError("VTK unavailable"),
])
def test_unrelated_or_other_failures_are_not_accepted(other):
    assert not is_expected_shape_deprecation(other)
