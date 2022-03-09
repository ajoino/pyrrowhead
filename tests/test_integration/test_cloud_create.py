from ipaddress import ip_network
from pathlib import Path
from typing import List, Set

import pytest
from click.testing import Result
from typer.testing import CliRunner
import yaml

from pyrrowhead import utils
from pyrrowhead.main import app
from pyrrowhead.constants import (
    LOCAL_CLOUDS_SUBDIR,
    CLOUD_CONFIG_FILE_NAME,
    CONFIG_FILE,
)
from pyrrowhead.types_ import CloudDict

runner = CliRunner()


@pytest.fixture(scope="class")
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


def cert_names(names: List[str]) -> Set[str]:
    endings = [".crt", ".key", ".p12"]
    return {f"{name}{end}" for name in names for end in endings}


def path_names(path: Path) -> Set[str]:
    return {p.name for p in path.iterdir()}


class TestLocalCloudCreation:
    cloud_name = "test-cloud"
    org_name = "test-org"
    cloud_identifier = f"{cloud_name}.{org_name}"
    spec_cloud_certs = {"truststore.p12", "sysop.ca"}
    ip_network = "172.16.2.0/24"
    san_1 = "ip:127.0.0.1"
    san_2 = "dns:test-cloud.test-org.com"

    @pytest.fixture()
    def cloud_config(self, mock_pyrrowhead_path) -> CloudDict:
        cloud_config_path = mock_pyrrowhead_path.joinpath(
            LOCAL_CLOUDS_SUBDIR,
            self.org_name,
            self.cloud_name,
            CLOUD_CONFIG_FILE_NAME,
        )

        with open(cloud_config_path, "r") as config_file:
            config = yaml.load(config_file)

        return config["cloud"]

    def test_create_local_cloud(self, mock_pyrrowhead_path):
        res = runner.invoke(
            app,
            f"cloud create {self.cloud_identifier} "
            f"--ip-network {self.ip_network} "
            f"--san {self.san_1} --san {self.san_2} "
            f"--include intercloud --include eventhandler".split(),
        )

        debug_runner_output(res)
        assert res.exit_code == 0
        assert len(list(mock_pyrrowhead_path.iterdir())) == 2
        assert mock_pyrrowhead_path.joinpath(CONFIG_FILE).is_file()
        assert mock_pyrrowhead_path.joinpath(LOCAL_CLOUDS_SUBDIR).is_dir()
        assert mock_pyrrowhead_path.joinpath(
            LOCAL_CLOUDS_SUBDIR,
            self.org_name,
            self.cloud_name,
            CLOUD_CONFIG_FILE_NAME,
        ).is_file()

    def test_add_client_similar(self, mock_pyrrowhead_path):
        for _ in range(3):
            res = runner.invoke(
                app, "cloud client-add test-cloud.test-org -n consumer".split()
            )

            debug_runner_output(res)
            assert res.exit_code == 0

    def test_add_client_all_options(self, mock_pyrrowhead_path):
        res = runner.invoke(
            app,
            "cloud client-add test-cloud.test-org -n test-system -a 127.0.0.1 -p 6000 -s dns:test-system.test-org.com -s ip:192.168.0.1".split(),
        )

        debug_runner_output(res)
        assert res.exit_code == 0

        res = runner.invoke(
            app,
            "cloud client-add test-cloud.test-org -n test-system -a 127.0.0.1 -p 6001 -s dns:test-system.test-org.com -s ip:192.168.0.1".split(),
        )

        debug_runner_output(res)
        assert res.exit_code == 0

        res = runner.invoke(
            app,
            "cloud client-add test-cloud.test-org -n test-cloud -a 127.0.0.1 -p 6002".split(),
        )

        debug_runner_output(res)
        assert res.exit_code == 0

    def test_cloud_config_general(self, cloud_config):

        assert cloud_config["cloud_name"] == self.cloud_name
        assert cloud_config["organization_name"] == self.org_name
        assert cloud_config["ssl_enabled"] == True
        assert cloud_config["subnet"] == self.ip_network
        assert set(cloud_config["core_san"]) == {self.san_1, self.san_2}

    def test_cloud_config_core(self, cloud_config):
        core_sys = cloud_config["core_systems"]
        network = ip_network(self.ip_network)
        assert core_sys["service_registry"] == {
            "system_name": "service_registry",
            "address": str(network[3]),
            "port": 8443,
            "domain": "serviceregistry",
        }
        assert core_sys["orchestrator"] == {
            "system_name": "orchestrator",
            "address": str(network[4]),
            "port": 8441,
            "domain": "orchestrator",
        }
        assert core_sys["authorization"] == {
            "system_name": "authorization",
            "address": str(network[5]),
            "port": 8445,
            "domain": "authorization",
        }
        assert core_sys["event_handler"] == {
            "system_name": "event_handler",
            "address": str(network[6]),
            "port": 8455,
            "domain": "eventhandler",
        }
        assert core_sys["gateway"] == {
            "system_name": "gateway",
            "address": str(network[7]),
            "port": 8453,
            "domain": "gateway",
        }
        assert core_sys["gatekeeper"] == {
            "system_name": "gatekeeper",
            "address": str(network[8]),
            "port": 8449,
            "domain": "gatekeeper",
        }

    def test_cloud_config_client_similar(self, cloud_config):
        client_sys = cloud_config["client_systems"]
        network = ip_network(self.ip_network)
        for i in range(3):
            assert client_sys[f"consumer-00{i}"] == {
                "system_name": "consumer",
                "address": str(network[1]),
                "port": 5000 + i,
                "sans": [],
            }

    def test_cloud_config_client_all_options(self, cloud_config):
        client_sys = cloud_config["client_systems"]

        assert client_sys["test-system-000"] == {
            "system_name": "test-system",
            "address": "127.0.0.1",
            "port": 6000,
            "sans": ["dns:test-system.test-org.com", "ip:192.168.0.1"],
        }
        assert client_sys["test-system-001"] == {
            "system_name": "test-system",
            "address": "127.0.0.1",
            "port": 6001,
            "sans": ["dns:test-system.test-org.com", "ip:192.168.0.1"],
        }
        assert client_sys["test-cloud-000"] == {
            "system_name": "test-cloud",
            "address": "127.0.0.1",
            "port": 6002,
            "sans": [],
        }

    def test_install_local_cloud(self, mock_pyrrowhead_path):
        res = runner.invoke(app, f"cloud install {self.cloud_identifier}".split())

        debug_runner_output(res)
        assert res.exit_code == 0

    def test_root_certs_installed(self, mock_pyrrowhead_path):
        org_path = mock_pyrrowhead_path.joinpath(LOCAL_CLOUDS_SUBDIR, self.org_name)
        root_cert_path = org_path.joinpath("root-certs", "crypto")
        assert {"root.crt", "root.p12"} == path_names(root_cert_path)

    def test_org_certs_installed(self, mock_pyrrowhead_path):
        org_path = mock_pyrrowhead_path.joinpath(LOCAL_CLOUDS_SUBDIR, self.org_name)
        org_cert_path = org_path.joinpath("org-certs", "crypto")
        assert cert_names([self.org_name]) == path_names(org_cert_path)

    def test_cloud_certs_installed(self, mock_pyrrowhead_path):
        org_path = mock_pyrrowhead_path.joinpath(LOCAL_CLOUDS_SUBDIR, self.org_name)
        cloud_path = org_path.joinpath(self.cloud_name)
        cloud_cert_path = cloud_path.joinpath("certs", "crypto")
        system_ids = [
            *[self.cloud_name, "sysop"],
            *[
                "service_registry",
                "orchestrator",
                "authorization",
                "gatekeeper",
                "gateway",
                "event_handler",
            ],
            *[f"consumer-00{i}" for i in range(3)],
            *[f"test-system-00{i}" for i in range(2)],
            *["test-cloud-000"],
        ]
        assert (
            path_names(cloud_cert_path)
            == cert_names(system_ids) | self.spec_cloud_certs
        )

    def test_cloud_dir_installed(self, mock_pyrrowhead_path):
        org_path = mock_pyrrowhead_path.joinpath(LOCAL_CLOUDS_SUBDIR, self.org_name)
        cloud_path = org_path.joinpath(self.cloud_name)
        assert {
            "certs",
            "core_system_config",
            "sql",
            "cloud_config.yaml",
            "docker-compose.yml",
            "initSQL.sh",
        } == path_names(cloud_path)

    def test_sql_installed(self, mock_pyrrowhead_path):
        org_path = mock_pyrrowhead_path.joinpath(LOCAL_CLOUDS_SUBDIR, self.org_name)
        sql_path = org_path.joinpath(self.cloud_name, "sql")

        assert {"privileges", "create_empty_arrowhead_db.sql"} <= set(
            path_names(sql_path)
        )
