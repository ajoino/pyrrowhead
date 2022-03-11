from pathlib import Path

import pytest
from click.testing import Result

from pyrrowhead import utils


@pytest.fixture(autouse=True, scope="class")
def user_tmp_path(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("user")
    return tmp_path


@pytest.fixture()
def mock_pyrrowhead_path(user_tmp_path, monkeypatch):
    def mockreturn() -> Path:
        return user_tmp_path / ".pyrrowhead"

    monkeypatch.setattr(utils, "get_pyrrowhead_path", mockreturn)

    return user_tmp_path / ".pyrrowhead"


def debug_runner_output(res: Result, code: int = 0):
    if res.exit_code != code:
        print(res.output)
        print(res.exception)
