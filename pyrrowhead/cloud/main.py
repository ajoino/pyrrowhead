from pathlib import Path
from typing import Optional, List, Tuple
import os
import subprocess

import typer

from pyrrowhead.cloud.installation import install_cloud, uninstall_cloud
from pyrrowhead.cloud.setup import CloudConfiguration, create_cloud_config
from pyrrowhead.cloud.start import start_local_cloud
from pyrrowhead.cloud.stop import stop_local_cloud
from pyrrowhead.cloud.configuration import enable_ssl as enable_ssl_func
from pyrrowhead.utils import (
    clouds_directory,
    switch_directory,
    set_active_cloud as set_active_cloud_func
)
from pyrrowhead.constants import ENV_PYRROWHEAD_ACTIVE_CLOUD


cloud_app = typer.Typer(name='cloud')

def decide_cloud_directory(
        cloud_identifier: str,
        cloud_name: str,
        organization_name: str,
        clouds_directory: Path
) -> Tuple[Path, str]:
    if cloud_identifier:
        return (
            clouds_directory.joinpath(*[part for part in reversed(cloud_identifier.split('.'))]),
            cloud_identifier,
        )
    elif cloud_name is not None and organization_name is not None:
        return (
            clouds_directory.joinpath(organization_name, cloud_name),
            f'{cloud_name}.{organization_name}',
        )
    else:
        raise RuntimeError()

@cloud_app.command()
def configure(
        cloud_identifier: str = typer.Argument(''),
        cloud_name: Optional[str] = typer.Option(None, '--cloud', '-c'),
        organization_name: Optional[str] = typer.Option(None, '--org', '-o'),
        clouds_directory: Path = clouds_directory,
        enable_ssl: Optional[bool] = typer.Option(None, '--enable-ssl/--disable-ssl')
):
    target, cloud_identifier = decide_cloud_directory(
            cloud_identifier,
            cloud_name,
            organization_name,
            clouds_directory,
    )
    with switch_directory(target):
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
    target, cloud_identifier = decide_cloud_directory(
            cloud_identifier,
            cloud_name,
            organization_name,
            clouds_directory,
    )
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
    target, cloud_identifier = decide_cloud_directory(
            cloud_identifier,
            cloud_name,
            organization_name,
            clouds_directory,
    )

    stop_local_cloud(target)
    uninstall_cloud(target, complete, keep_root)


@cloud_app.command()
def setup(
        cloud_identifier: str = typer.Argument(''),
        cloud_name: Optional[str] = typer.Option(None, '--cloud', '-c'),
        organization_name: Optional[str] = typer.Option(None, '--org', '-o'),
        installation_target: Path = clouds_directory,
        ip_network: str = typer.Option('172.16.1.0/24'),
        ssl_enabled: bool = typer.Option(True, '--ssl-enabled'),
        do_install: bool = typer.Option(False, '--install'),
        include: Optional[List[CloudConfiguration]] = typer.Option('', case_sensitive=False),
):
    if cloud_identifier:
        cloud_name, organization_name = cloud_identifier.split('.')

    create_cloud_config(
            installation_target,
            cloud_name,
            organization_name,
            ssl_enabled,
            ip_network,
            do_install,
            include,
    )


@cloud_app.command()
def up(
        cloud_identifier: str = typer.Argument(''),
        cloud_name: Optional[str] = typer.Option(None, '--cloud', '-c'),
        organization_name: Optional[str] = typer.Option(None, '--org', '-o'),
        clouds_directory: Path = clouds_directory,
        set_active_cloud: bool = typer.Option(True, ' /--no-set-active', ' /-N', show_default=False),
):
    target, cloud_identifier = decide_cloud_directory(
            cloud_identifier,
            cloud_name,
            organization_name,
            clouds_directory,
    )
    start_local_cloud(target)
    if set_active_cloud:
        set_active_cloud_func(cloud_identifier)


@cloud_app.command()
def down(
        cloud_identifier: str = typer.Argument(''),
        cloud_name: Optional[str] = typer.Option(None, '--cloud', '-c'),
        organization_name: Optional[str] = typer.Option(None, '--org', '-o'),
        clouds_directory: Path = clouds_directory,
):
    target, cloud_identifier = decide_cloud_directory(
            cloud_identifier,
            cloud_name,
            organization_name,
            clouds_directory,
    )
    stop_local_cloud(target)
    set_active_cloud_func('')