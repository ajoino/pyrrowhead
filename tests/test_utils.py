"""
These tests cover code that is not run in the integration tests.
"""
from sys import platform

from pyrrowhead.utils import get_pyrrowhead_path


def test_get_pyrrowhead_path():
    # get_pyrrowhead_path is mocked in the integration tests,

    if platform in {"linux", "linux2", "darwin"}:
        assert get_pyrrowhead_path().name == ".pyrrowhead"
