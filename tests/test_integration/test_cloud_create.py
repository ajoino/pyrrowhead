import string
from ipaddress import ip_network
from pathlib import Path
from typing import List, Set

import pytest
from typer.testing import CliRunner
import yaml

from pyrrowhead.main import app
from pyrrowhead.constants import (
    LOCAL_CLOUDS_SUBDIR,
    CLOUD_CONFIG_FILE_NAME,
    CONFIG_FILE,
)
from pyrrowhead.types_ import CloudDict
from tests.test_integration.conftest import debug_runner_output

runner = CliRunner()


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

    @pytest.mark.parametrize(
        "args", ["cloud client-add test-cloud.test-org -n consumer"] * 3
    )
    def test_add_client_similar(self, mock_pyrrowhead_path, args):
        res = runner.invoke(app, args.split())

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

    def test_add_client_exact_same(self, mock_pyrrowhead_path):
        res = runner.invoke(
            app,
            "cloud client-add test-cloud.test-org -n test-cloud -a 127.0.0.1 -p 6002".split(),
        )

        debug_runner_output(res, -1)
        assert res.exit_code == -1

    @pytest.mark.parametrize("sys_name", ["test_system", "tëst-sŷstẽm"])
    def test_add_client_bad_name(self, sys_name):
        res = runner.invoke(
            app,
            f"cloud client-add test-cloud.test-org -n {sys_name}".split(),
        )

        debug_runner_output(res, -1)
        assert res.exit_code == -1

    @pytest.mark.parametrize("addr", ["127:0.1.1", "400:500:600:700"])
    def test_bad_address(self, addr):
        res = runner.invoke(
            app,
            f"cloud client-add test-cloud.test-org -n bad -a {addr}".split(),
        )

        debug_runner_output(res, -1)
        assert res.exit_code == -1

    @pytest.mark.parametrize(
        "san",
        [
            "ips:127.0.0.1",
            "ip:499.200.100.154",
            "ip:499:200.55",
            "dna:small.medium.large",
        ],
    )
    def test_add_client_bad_san(self, san):
        res = runner.invoke(
            app,
            f"cloud client-add test-cloud.test-org -n bad --san {san}".split(),
        )

        debug_runner_output(res, -1)
        assert res.exit_code == -1

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

    @pytest.mark.parametrize("i", list(range(3)))
    def test_cloud_config_client_similar(self, cloud_config, i):
        client_sys = cloud_config["client_systems"]
        network = ip_network(self.ip_network)
        assert client_sys[f"consumer-00{i}"] == {
            "system_name": "consumer",
            "address": str(network[1]),
            "port": 5000 + i,
            "sans": [],
        }

    def test_cloud_config_client_similar_no_extra(self, cloud_config):
        client_sys = cloud_config["client_systems"]
        assert (
            len(
                [sys for sys in client_sys.values() if sys["system_name"] == "consumer"]
            )
            == 3
        )

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


class TestBadPyrrowheadDirSetup:
    @pytest.fixture(autouse=True, scope="function")
    def create_and_clear_pyrrowhead_path(self, mock_pyrrowhead_path, request):
        if not mock_pyrrowhead_path.exists():
            mock_pyrrowhead_path.mkdir()
        yield
        if "noautofixt" in request.keywords:
            return
        for p in mock_pyrrowhead_path.iterdir():
            if p.is_file():
                p.unlink()
            if p.is_dir():
                p.rmdir()

    def populate_with_garbage(self, path, num_files):
        for name in string.ascii_lowercase[:num_files]:
            with open(path / f"{name}.txt", "w") as name_file:
                name_file.write("nothing")

    def test_empty_existing_dir(self, mock_pyrrowhead_path):
        res = runner.invoke(app, f"cloud --help".split())

        debug_runner_output(res)
        assert res.exit_code == 0

    def test_only_config_exists(self, mock_pyrrowhead_path):
        res = runner.invoke(app, f"cloud --help".split())

        mock_pyrrowhead_path.joinpath(LOCAL_CLOUDS_SUBDIR).rmdir()

        debug_runner_output(res)
        assert res.exit_code == 0

    def test_only_dir_exists(self, mock_pyrrowhead_path):
        res = runner.invoke(app, f"cloud --help".split())

        mock_pyrrowhead_path.joinpath(CONFIG_FILE).unlink()

        debug_runner_output(res)
        assert res.exit_code == 0

    def test_single_wrong_file(self, mock_pyrrowhead_path):
        mock_pyrrowhead_path.joinpath("a.txt").touch()

        res = runner.invoke(
            app,
            f"cloud --help".split(),
        )

        debug_runner_output(res, -1)
        assert res.exit_code == -1

    def test_single_wrong_dir(self, mock_pyrrowhead_path):
        mock_pyrrowhead_path.joinpath("abcdefgo").mkdir()

        res = runner.invoke(app, f"cloud --help".split())

        debug_runner_output(res, -1)
        assert res.exit_code == -1

    def test_too_many_files(self, mock_pyrrowhead_path):
        self.populate_with_garbage(mock_pyrrowhead_path, 3)

        res = runner.invoke(app, f"cloud --help".split())

        debug_runner_output(res, -1)
        assert res.exit_code == -1

    def test_two_wrong_files(self, mock_pyrrowhead_path):
        self.populate_with_garbage(mock_pyrrowhead_path, 2)

        res = runner.invoke(app, f"cloud --help".split())

        debug_runner_output(res, -1)
        assert res.exit_code == -1

    def test_dir_correct_file_wrong(self, mock_pyrrowhead_path):
        self.populate_with_garbage(mock_pyrrowhead_path, 1)
        mock_pyrrowhead_path.joinpath(LOCAL_CLOUDS_SUBDIR).mkdir()

        res = runner.invoke(app, f"cloud --help".split())

        debug_runner_output(res, -1)
        assert res.exit_code == -1

    def test_file_correct_dir_wrong(self, mock_pyrrowhead_path):
        mock_pyrrowhead_path.joinpath(CONFIG_FILE).touch()
        mock_pyrrowhead_path.joinpath("abcdefgo").mkdir()

        res = runner.invoke(app, f"cloud --help".split())

        debug_runner_output(res, -1)
        assert res.exit_code == -1

    @pytest.mark.parametrize(
        "key",
        [
            "cloud_name",
            "organization_name",
            "ssl_enabled",
            "subnet",
            "core_san",
            "client_systems",
            "core_systems",
        ],
    )
    @pytest.mark.noautofixt
    def test_bad_cloud_config_missing_keys(self, mock_pyrrowhead_path, key):
        res = runner.invoke(app, "cloud create test.test".split())
        cloud_config_path = mock_pyrrowhead_path.joinpath(
            LOCAL_CLOUDS_SUBDIR, "test", "test", CLOUD_CONFIG_FILE_NAME
        )
        with open(cloud_config_path, "r") as config_fd:
            config = yaml.safe_load(config_fd)
        del config["cloud"][key]
        with open(cloud_config_path, "w") as config_fd:
            yaml.dump(config, config_fd)

        res = runner.invoke(app, "cloud install test.test".split())

        debug_runner_output(res, 1)
        assert res.exit_code == -1
