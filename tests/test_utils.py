"""
These tests cover code that is not run in the integration tests.
"""
from sys import platform

from pyrrowhead.utils import get_pyrrowhead_path
from pyrrowhead.constants import APP_NAME


def test_get_pyrrowhead_path():
    # get_pyrrowhead_path is mocked in the integration tests,

    assert get_pyrrowhead_path().name == APP_NAME
