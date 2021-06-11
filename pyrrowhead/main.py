from pathlib import Path
from typing import Optional, List

import typer

from pyrrowhead.cloud_start.start import start_local_cloud
from pyrrowhead.cloud_start.stop import stop_local_cloud
from pyrrowhead.installation.installation import install_cloud, uninstall_cloud
from pyrrowhead.installation.setup import create_cloud_config, CloudConfiguration
from pyrrowhead.configuration.setup import enable_ssl as enable_ssl_func
from pyrrowhead.management.serviceregistry import sr_app
from pyrrowhead.management.orchestrator import orch_app
from pyrrowhead.management.authorization import auth_app
from pyrrowhead.management.systemregistry import sys_app

app = typer.Typer()
app.add_typer(sr_app)
app.add_typer(orch_app)
app.add_typer(auth_app)
app.add_typer(sys_app)


@app.command()
def configure(enable_ssl: Optional[bool] = typer.Option(None, '--enable-ssl/--disable-ssl')):
    if enable_ssl is not None:
        enable_ssl_func(enable_ssl)


@app.command()
def install(config_file: Path, installation_target: Optional[Path] = typer.Argument(None)):
    target = installation_target if installation_target else config_file.parent

    install_cloud(config_file, target)


@app.command()
def uninstall(
        installation_target: Path,
        complete: bool = typer.Option(False, '--complete'),
        keep_root: bool = typer.Option(False, '--keep-root'),
):
    uninstall_cloud(installation_target, complete, keep_root)

@app.command()
def setup(
        installation_target: Path,
        cloud_name: str,
        company_name: str,
        ip_address: str = typer.Option('172.16.1.0/24'),
        ssl_enabled: bool = typer.Option(True, '--ssl-enabled'),
        do_install: bool = typer.Option(False, '--install'),
        include: Optional[List[CloudConfiguration]] = typer.Option('', case_sensitive=False),
):
    create_cloud_config(
            installation_target,
            cloud_name,
            company_name,
            ssl_enabled,
            ip_address,
            do_install,
            include,
    )



@app.command()
def up(cloud_directory: Path = typer.Option(Path.cwd())):
    start_local_cloud(cloud_directory)

@app.command()
def down(cloud_directory: Path = typer.Option(Path.cwd())):
    stop_local_cloud(cloud_directory)


if __name__ == '__main__':
    app()

    # install_cloud(cloud_config, installation_target)
