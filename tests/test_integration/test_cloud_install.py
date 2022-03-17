import pytest
import shutil

from typer.testing import CliRunner

from pyrrowhead.main import app
from pyrrowhead.constants import CLOUD_CONFIG_FILE_NAME

from tests.test_integration.conftest import debug_runner_output

runner = CliRunner()


@pytest.mark.usefixtures("user_tmp_path")
class TestCloudInstall:
    @pytest.fixture(autouse=True)
    def create_cloud(self, mock_pyrrowhead_path):
        runner.invoke(app, "cloud create install-test-cloud.install-test-org")
        yield
        shutil.rmtree(mock_pyrrowhead_path)

    @pytest.mark.parametrize(
        "options",
        [
            "install-test-cloud.install-test-org",
            "-o install-test-org -c install-test-cloud",
            "-c install-test-cloud -o install-test-org",
        ],
    )
    def test_good_options(self, options, mock_pyrrowhead_path):
        res = runner.invoke(app, f"cloud install {options}")

        debug_runner_output(res)
        assert res.exit_code == 0

    @pytest.mark.parametrize(
        "options",
        [
            "uninstall-test-cloud.uninstall-test-org",
            "-o install-test-org -c uninstall-test-cloud",
            "-o uninstall-test-org -c install-test-cloud",
            "-o uninstall-test-org -c uninstall-test-cloud",
            "-o install-test-org",
            "-c install-test-cloud",
            "-o uninstall-test-org",
            "-c uninstall-test-cloud",
            "install-test-cloud.install-test-org -o install-test-org -c install-test-cloud",
            "install-test-cloud.install-test-org -o install-test-org -c uninstall-test-cloud",
            "install-test-cloud.install-test-org -o uninstall-test-org -c install-test-cloud",
            "install-test-cloud.install-test-org -o uninstall-test-org -c uninstall-test-cloud",
            "install-test-cloud.install-test-org -c install-test-cloud",
            "install-test-cloud.install-test-org -c uninstall-test-cloud",
            "install-test-cloud.install-test-org -o install-test-org",
            "install-test-cloud.install-test-org -o uninstall-test-org",
        ],
    )
    def test_bad_options(self, options, mock_pyrrowhead_path):
        res = runner.invoke(app, f"cloud install {options}")

        debug_runner_output(res)
        assert res.exit_code == -1

    def test_missing_cloud_config(self, mock_pyrrowhead_path):
        mock_pyrrowhead_path.joinpath(
            "local-clouds/install-test-org/install-test-cloud", CLOUD_CONFIG_FILE_NAME
        ).unlink()

        res = runner.invoke(app, f"cloud install install-test-cloud.install-test-org")

        debug_runner_output(res, -1)
        assert res.exit_code == -1

    def test_empty_cloud_config(self, mock_pyrrowhead_path):
        mock_pyrrowhead_path.joinpath(
            "local-clouds/install-test-org/install-test-cloud", CLOUD_CONFIG_FILE_NAME
        ).unlink()
        mock_pyrrowhead_path.joinpath(
            "local-clouds/install-test-org/install-test-cloud", CLOUD_CONFIG_FILE_NAME
        ).touch()

        res = runner.invoke(app, f"cloud install install-test-cloud.install-test-org")

        debug_runner_output(res)
        assert res.exit_code == -1

    def test_damaged_cloud_config(self, mock_pyrrowhead_path):
        with open(
            mock_pyrrowhead_path.joinpath(
                "local-clouds/install-test-org/install-test-cloud",
                CLOUD_CONFIG_FILE_NAME,
            ),
            "r+",
        ) as config_file:
            config_file.writelines(["1234567890"] * 100)

        res = runner.invoke(app, f"cloud install install-test-cloud.install-test-org")

        debug_runner_output(res)
        assert res.exit_code == -1

    def test_missing_config_key(self, mock_pyrrowhead_path):
        mock_pyrrowhead_path.joinpath(
            "local-clouds/install-test-org/install-test-cloud", CLOUD_CONFIG_FILE_NAME
        ).unlink()
        with open(
            mock_pyrrowhead_path.joinpath(
                "local-clouds/install-test-org/install-test-cloud",
                CLOUD_CONFIG_FILE_NAME,
            ),
            "w",
        ) as config_file:
            config_file.write("cloud:")

        res = runner.invoke(app, f"cloud install install-test-cloud.install-test-org")

        debug_runner_output(res)
        assert res.exit_code == -1


class TestCloudUninstall:
    pass
