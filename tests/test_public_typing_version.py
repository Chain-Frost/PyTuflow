"""Check the public package version against its installed distribution metadata."""

from importlib.metadata import version

import pytuflow


def test_typing_release_version_matches_distribution() -> None:
    # Keep the contract valid when an upstream maintainer chooses a later version.
    assert version("pytuflow") == pytuflow.__version__
