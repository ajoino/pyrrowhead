from pathlib import Path
from typing import Optional, List

import typer

from pyrrowhead.cloud.installation import install_cloud, uninstall_cloud
from pyrrowhead.cloud.setup import CloudConfiguration, create_cloud_config
from pyrrowhead.cloud_start.start import start_local_cloud
from pyrrowhead.cloud_start.stop import stop_local_cloud
from pyrrowhead.configuration.setup import enable_ssl as enable_ssl_func
from pyrrowhead.utils import clouds_directory

cloud_app = typer.Typer(name='cloud')


@cloud_app.command()
def configure(enable_ssl: Optional[bool] = typer.Option(None, '--enable-ssl/--disable-ssl')):
    if enable_ssl is not None:
        enable_ssl_func(enable_ssl)


@cloud_app.command()
def list(
        organization_filter: str = typer.Option('', '--organization', '-o'),
        clouds_dir: Path = clouds_directory
):
    for organization_dir in clouds_dir.iterdir():
        if organization_filter and organization_dir.name != organization_filter:
            continue
        for cloud_dir in organization_dir.iterdir():
            print(".".join(part for part in reversed(cloud_dir.parts[-2:])))


@cloud_app.command()
def install(
        cloud_identifier: str = typer.Argument(''),
        cloud_name: Optional[str] = typer.Option(None, '--cloud', '-c'),
        organization_name: Optional[str] = typer.Option(None, '--org', '-o'),
        clouds_directory: Path = clouds_directory,
):
    #target = installation_target if installation_target else config_file.parent

    if cloud_identifier:
        target = clouds_directory.joinpath(*[part for part in reversed(cloud_identifier.split('.'))])
    elif cloud_name is not None and organization_name is not None:
        target = clouds_directory.joinpath(organization_name, cloud_name)
    else:
        raise RuntimeError()
    config_file = target / 'cloud_config.yaml'

    if not target.exists():
        raise RuntimeError('Target cloud is not setup, please use `pyrrowhead cloud setup ...` before installing cloud.')

    install_cloud(config_file, target)


@cloud_app.command()
def uninstall(
        cloud_identifier: str = typer.Argument(''),
        cloud_name: Optional[str] = typer.Option(None, '--cloud', '-c'),
        organization_name: Optional[str] = typer.Option(None, '--org', '-o'),
        clouds_directory: Path = clouds_directory,
        complete: bool = typer.Option(False, '--complete'),
        keep_root: bool = typer.Option(False, '--keep-root'),
):
    if cloud_identifier:
        target = clouds_directory.joinpath(*[part for part in reversed(cloud_identifier.split('.'))])
    elif cloud_name is not None and organization_name is not None:
        target = clouds_directory.joinpath(organization_name, cloud_name)
    else:
        raise RuntimeError()

    uninstall_cloud(target, complete, keep_root)


@cloud_app.command()
def setup(
        cloud_name: str,
        company_name: str,
        installation_target: Path = clouds_directory,
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


@cloud_app.command()
def up(cloud_directory: Path = typer.Option(Path.cwd())):
    start_local_cloud(cloud_directory)


@cloud_app.command()
def down(cloud_directory: Path = typer.Option(Path.cwd())):
    stop_local_cloud(cloud_directory)