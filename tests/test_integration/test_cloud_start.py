import pytest
from typer.testing import CliRunner

from pyrrowhead.main import app
from .conftest import debug_runner_output

runner = CliRunner()


@pytest.mark.usefixtures("user_tmp_path")
class TestCloudStart:
    cloud_id = "test-start.test-start"

    @pytest.fixture(autouse=True)
    def install_and_remove_cloud(self, mock_pyrrowhead_path):
        res = runner.invoke(app, f"cloud create {self.cloud_id} --install".split())
        yield
        res = runner.invoke(app, f"cloud uninstall {self.cloud_id} --complete".split())

    def test_mysql_port_taken(self, mock_pyrrowhead_path):
        import socket

        bad_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        bad_socket.bind(("127.0.0.1", 3306))

        res = runner.invoke(app, f"cloud up {self.cloud_id}".split())

        print(res.output)
        debug_runner_output(res, -1)
        assert res.exit_code == -1

    def test_sr_port_taken(self, mock_pyrrowhead_path):
        import socket

        bad_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        bad_socket.bind(("127.0.0.1", 8443))

        res = runner.invoke(app, f"cloud up {self.cloud_id}".split())

        print(res.output)
        debug_runner_output(res, -1)
        assert res.exit_code == -1
