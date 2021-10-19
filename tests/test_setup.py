from pathlib import Path
import shutil

import pytest
import typer
from typer.testing import CliRunner

from pyrrowhead.main import app

PYRROWHEAD_TEST_ORG = 'pyrrowhead--test--org'

class TestCloudSetup:
    runner = CliRunner()
    local_clouds_dir = Path(typer.get_app_dir('pyrrowhead')) / 'local-clouds'

    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pyrrowhead_test_org_dir = cls.local_clouds_dir / PYRROWHEAD_TEST_ORG
        shutil.rmtree(pyrrowhead_test_org_dir)

    @pytest.mark.dependency()
    def test_cloud_setup(self):
        result = self.runner.invoke(app, ["cloud", "setup", ".".join(["test", PYRROWHEAD_TEST_ORG])])
        assert result.exit_code == 0
        assert (pyrrowhead_org_dir := self.local_clouds_dir / PYRROWHEAD_TEST_ORG).exists()
        assert (pyrrowhead_org_dir / 'test/cloud_config.yaml').exists()

    @pytest.mark.depedency(depends=["test_cloud_setup"])
    def test_cloud_install(self):
        result = self.runner.invoke(app, ["cloud", "install", ".".join(["test", PYRROWHEAD_TEST_ORG])])
        assert result.exit_code == 0
        assert (self.local_clouds_dir / PYRROWHEAD_TEST_ORG / 'test/cloud-test/crypto').is_dir()

    @pytest.mark.depedency(depends=["test_cloud_install"])
    def test_cloud_uninstall(self):
        result = self.runner.invoke(app, ["cloud", "uninstall", ".".join(["test", PYRROWHEAD_TEST_ORG])])
        print(f'{result.exception=}')
        assert result.exit_code == 0
        assert not (self.local_clouds_dir / PYRROWHEAD_TEST_ORG / 'test/cloud-test/crypto').is_dir()

