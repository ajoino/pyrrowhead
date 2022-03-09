from typer.testing import CliRunner

from pyrrowhead.main import app
from tests.test_integration.conftest import debug_runner_output

runner = CliRunner()


class TestTutorial:
    def test_create_cloud(self, mock_pyrrowhead_path):
        res = runner.invoke(app, "cloud create test-cloud.test-org".split())

        debug_runner_output(res)
        assert res.exit_code == 0

    def test_client_add(self, mock_pyrrowhead_path):
        res1 = runner.invoke(
            app, "cloud client-add test-cloud.test-org -n consumer".split()
        )
        res2 = runner.invoke(
            app, "cloud client-add test-cloud.test-org -n provider".split()
        )

        debug_runner_output(res1)
        assert res1.exit_code == 0
        debug_runner_output(res2)
        assert res2.exit_code == 0

    def test_client_install(self, mock_pyrrowhead_path):
        res = runner.invoke(app, "cloud install test-cloud.test-org".split())

        debug_runner_output(res)
        assert res.exit_code == 0

    def test_start_cloud(self, mock_pyrrowhead_path):
        res = runner.invoke(app, "cloud up test-cloud.test-org".split())

        debug_runner_output(res)
        assert res.exit_code == 0

    def test_systems_list(self, mock_pyrrowhead_path):
        res = runner.invoke(app, "systems list".split())

        debug_runner_output(res)
        assert res.exit_code == 0

    def test_stop_cloud(self, mock_pyrrowhead_path):
        res = runner.invoke(app, "cloud down test-cloud.test-org".split())

        debug_runner_output(res)
        assert res.exit_code == 0
        res = runner.invoke(app, "cloud uninstall test-cloud.test-org".split())

        debug_runner_output(res)
        assert res.exit_code == 0
