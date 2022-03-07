from pathlib import Path

import pytest
from typer.testing import CliRunner

from pyrrowhead import utils
from pyrrowhead.main import app
from pyrrowhead.constants import (
    LOCAL_CLOUDS_SUBDIR,
    CLOUD_CONFIG_FILE_NAME,
    CONFIG_FILE,
)


runner = CliRunner()


@pytest.fixture(scope="class")
def pyrrowhead_tmp_path(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp(".pyrrowhead")
    return tmp_path


@pytest.fixture()
def mock_pyrrowhead_path(pyrrowhead_tmp_path, monkeypatch):
    def mockreturn() -> Path:
        return pyrrowhead_tmp_path

    monkeypatch.setattr(utils, "get_pyrrowhead_path", mockreturn)

    return pyrrowhead_tmp_path


class TestTutorial:
    def test_create_cloud(self, mock_pyrrowhead_path):
        res = runner.invoke(app, "cloud create test-cloud.test-org".split())

        assert res.exit_code == 0

    def test_client_add(self, mock_pyrrowhead_path):
        res1 = runner.invoke(
            app, "cloud client-add test-cloud.test-org -n consumer".split()
        )
        res2 = runner.invoke(
            app, "cloud client-add test-cloud.test-org -n provider".split()
        )

        assert res1.exit_code == 0
        assert res2.exit_code == 0

    def test_client_install(self, mock_pyrrowhead_path):
        res = runner.invoke(app, "cloud install test-cloud.test-org".split())

        assert res.exit_code == 0

    def test_start_cloud(self, mock_pyrrowhead_path):
        res = runner.invoke(app, "cloud up test-cloud.test-org".split())

        assert res.exit_code == 0

    def test_systems_list(self, mock_pyrrowhead_path):
        res = runner.invoke(app, "systems list".split())

        assert res.exit_code == 0

    def test_stop_cloud(self, mock_pyrrowhead_path):
        res = runner.invoke(app, "cloud down test-cloud.test-org".split())

        assert res.exit_code == 0
        res = runner.invoke(app, "cloud uninstall test-cloud.test-org".split())

        assert res.exit_code == 0


class TestLocalCloudCreation:
    cloud_name = "test-cloud"
    org_name = "test-org"
    cloud_identifier = f"{cloud_name}.{org_name}"

    def test_create_local_cloud(self, mock_pyrrowhead_path):
        res = runner.invoke(app, f"cloud create {self.cloud_identifier}".split())

        assert res.exit_code == 0
        assert mock_pyrrowhead_path.joinpath(CONFIG_FILE).is_file()
        assert mock_pyrrowhead_path.joinpath(LOCAL_CLOUDS_SUBDIR).is_dir()
        assert mock_pyrrowhead_path.joinpath(
            LOCAL_CLOUDS_SUBDIR,
            self.org_name,
            self.cloud_name,
            CLOUD_CONFIG_FILE_NAME,
        ).is_file()

    def test_install_local_cloud(self, mock_pyrrowhead_path):
        res = runner.invoke(app, f"cloud install {self.cloud_identifier}".split())

        org_path = mock_pyrrowhead_path.joinpath(LOCAL_CLOUDS_SUBDIR, self.org_name)
        root_cert_path = org_path.joinpath("root-certs", "crypto")
        org_cert_path = org_path.joinpath("org-certs", "crypto")
        cloud_path = org_path.joinpath(self.cloud_name)
        cloud_cert_path = cloud_path.joinpath("certs", "crypto")

        assert res.exit_code == 1
        assert mock_pyrrowhead_path.joinpath()
