from pathlib import Path
import socket
import ssl
import subprocess
import time

from rich.text import Text

from pyrrowhead import rich_console
from pyrrowhead.cloud.stop import stop_local_cloud
from pyrrowhead.utils import (
    switch_directory,
    PyrrowheadError,
    validate_cloud_config_file,
)
from pyrrowhead.constants import CLOUD_CONFIG_FILE_NAME


def check_server(address, port, secure, certfile, keyfile, cafile):
    if secure:
        context = ssl.create_default_context(cafile=cafile.absolute())
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = False
        try:
            context.load_cert_chain(certfile, keyfile)
        except OSError:
            raise PyrrowheadError(
                "Could not load certificates in <pyrrowhead.cloud.start.check_server>."
            )

        try:
            with socket.create_connection((address, port)) as sock:
                with context.wrap_socket(sock, server_hostname=address):
                    return True
        except (
            ConnectionRefusedError,
            ConnectionResetError,
            OSError,
        ):
            return False
    else:
        try:
            with socket.create_connection((address, port)) as sock:
                return True
        except (ConnectionRefusedError, ConnectionResetError, OSError):
            return False


def check_returncode(output, status, cloud_directory: Path = Path.cwd()):
    if output.returncode != 0:
        rich_console.print(Text("Encountered an error during startup: "))
        rich_console.print(Text(output.stderr.decode()))
        status.stop()
        stop_local_cloud(cloud_directory)
        raise PyrrowheadError()


def start_local_cloud(cloud_directory: Path):
    cloud_config = validate_cloud_config_file(cloud_directory / CLOUD_CONFIG_FILE_NAME)

    cloud_name = cloud_config["cloud_name"]
    org_name = cloud_config["org_name"]
    ssl_enabled = cloud_config["ssl_enabled"]

    sysop_certfile = (cloud_directory / "certs/crypto/sysop.crt").absolute()
    sysop_keyfile = (cloud_directory / "certs/crypto/sysop.key").absolute()
    sysop_cafile = (cloud_directory / "certs/crypto/sysop.ca").absolute()
    core_systems = cloud_config["core_systems"]

    with switch_directory(cloud_directory):
        with rich_console.status("MySQL instance starting...") as status:
            output = subprocess.run(
                f"docker-compose up -d mysql.{cloud_name}.{org_name}".split(),
                capture_output=True,
            )
            check_returncode(output, status)
            rich_console.print(Text("MySQL instance started."))
            for core_system, core_system_config in core_systems.items():
                core_system_print_name = (
                    core_system_config["system_name"].replace("_", " ").capitalize()
                )
                status.update(Text(f"{core_system_print_name} starting..."))
                output = subprocess.run(
                    ["docker-compose", "up", "-d", core_system_config["domain"]],
                    capture_output=True,
                )
                check_returncode(output, status)
                while not check_server(
                    core_system_config["address"],
                    core_system_config["port"],
                    ssl_enabled,
                    sysop_certfile,
                    sysop_keyfile,
                    sysop_cafile,
                ):
                    time.sleep(1)
                rich_console.print(Text(f"{core_system_print_name} started."))
            rich_console.print("Local cloud is up and running!")
