"""Check the public package version against its installed distribution metadata."""

from importlib.metadata import version

import pytuflow


def test_typing_release_version_matches_distribution() -> None:
    assert pytuflow.__version__ == "1.2.8"
    assert version("pytuflow") == pytuflow.__version__
