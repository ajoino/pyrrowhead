from pathlib import Path
import socket
import ssl
import subprocess
import time

import yaml
import yamlloader
from rich.text import Text
import typer

from pyrrowhead import rich_console
from .stop import stop_local_cloud
from pyrrowhead.utils import switch_directory

def check_server(address, port, certfile, keyfile, cafile):
    if certfile:
        context = ssl.create_default_context(cafile=cafile)
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = False
        context.load_cert_chain(certfile, keyfile)
        try:
            with socket.create_connection((address, port)) as sock:
                with context.wrap_socket(sock, server_hostname=address):
                    return True
        except (ConnectionRefusedError, ConnectionResetError, ssl.SSLEOFError):
            return False

    with socket.create_connection((address, port)) as sock:
        print(sock)


def is_port_in_use(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def check_returncode(output, status, cloud_directory: Path = Path.cwd()):
    if output.returncode != 0:
        rich_console.print(Text('Encountered an error during startup: '))
        rich_console.print(Text(output.stderr.decode()))
        status.update(Text('Stopping local cloud...'))
        stop_local_cloud(cloud_directory)
        rich_console.print(Text('Local cloud Stopped.'))
        raise typer.Exit()


def start_local_cloud(cloud_directory: Path):
    with open(cloud_directory / 'cloud_config.yaml') as config_file:
        cloud_config = yaml.load(config_file, Loader=yamlloader.ordereddict.Loader)
    cloud_name = cloud_config["cloud"]["cloud_name"]

    sysop_certfile = cloud_directory / f'cloud-{cloud_name}/crypto/sysop.crt'
    sysop_keyfile = cloud_directory / f'cloud-{cloud_name}/crypto/sysop.key'
    sysop_cafile = cloud_directory / f'cloud-{cloud_name}/crypto/sysop.ca'

    core_systems = cloud_config["cloud"]["core_systems"]

    with switch_directory(cloud_directory):
        with rich_console.status("MySQL instance starting...") as status:
            output = subprocess.run(['docker-compose', 'up', '-d', f'mysql.{cloud_name}'], capture_output=True)
            check_returncode(output, status)
            rich_console.print(Text('MySQL instance started.'))
            for core_system, core_system_config in core_systems.items():
                status.update(Text(f'{core_system_config["system_name"].replace("_", " ").capitalize()} starting...'))
                output = subprocess.run(['docker-compose', 'up', '-d', core_system_config["domain"]], capture_output=True)
                check_returncode(output, status)
                while not check_server(
                        core_system_config["address"],
                        core_system_config["port"],
                        sysop_certfile, sysop_keyfile, sysop_cafile,
                ): time.sleep(1)
                rich_console.print(Text(f'{core_system_config["system_name"].replace("_", " ").capitalize()} started.'))
            rich_console.print('Local cloud is up and running!')