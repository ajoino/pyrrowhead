from pathlib import Path
from typing import Optional, List, Tuple

import typer

from pyrrowhead import rich_console
from pyrrowhead.cloud.installation import install_cloud, uninstall_cloud
from pyrrowhead.cloud.setup import CloudConfiguration, create_cloud_config
from pyrrowhead.cloud.start import start_local_cloud
from pyrrowhead.cloud.stop import stop_local_cloud
from pyrrowhead.cloud.configuration import enable_ssl as enable_ssl_func
from pyrrowhead.utils import (
    clouds_directory,
    switch_directory,
    set_active_cloud as set_active_cloud_func, get_config
)


cloud_app = typer.Typer(name='cloud')

def decide_cloud_directory(
        cloud_identifier: str,
        cloud_name: str,
        organization_name: str,
        clouds_directory: Path
) -> Tuple[Path, str]:
    if len(split_cloud_identifier := cloud_identifier.split('.')) == 2:
        return (
            clouds_directory.joinpath(*[part for part in reversed(split_cloud_identifier)]),
            cloud_identifier,
        )
    elif cloud_name is not None and organization_name is not None:
        return (
            clouds_directory.joinpath(organization_name, cloud_name),
            f'{cloud_name}.{organization_name}',
        )
    elif cloud_identifier != '':
        return (
            clouds_directory,
            cloud_identifier
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
    config = get_config()

    for cloud_identifier, directory in config['local-clouds'].items():
        if not Path(directory).exists():
            rich_console.print(cloud_identifier, 'Path does not exist', style='red')
        else:
            rich_console.print(cloud_identifier, directory)

@cloud_app.command()
def install(
        cloud_identifier: str = typer.Argument(''),
        cloud_name: Optional[str] = typer.Option(None, '--cloud', '-c'),
        organization_name: Optional[str] = typer.Option(None, '--org', '-o'),
        cloud_directory: Path = clouds_directory,
):
    target, cloud_identifier = decide_cloud_directory(
            cloud_identifier,
            cloud_name,
            organization_name,
            cloud_directory,
    )

    config_file = target / 'cloud_config.yaml'
    print(target)

    if not target.exists():
        raise RuntimeError('Target cloud is not set up properly, run `pyrrowhead cloud setup` before installing cloud.')

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
        ssl_enabled: Optional[bool] = typer.Option(True, '--ssl-enabled/--ssl-disabled', show_default=False),
        do_install: bool = typer.Option(False, '--install'),
        include: Optional[List[CloudConfiguration]] = typer.Option('', case_sensitive=False),
):
    if cloud_identifier:
        cloud_name, organization_name = cloud_identifier.split('.')
    if not cloud_identifier:
        cloud_identifier = '.'.join((cloud_name, organization_name))

    create_cloud_config(
            installation_target,
            cloud_identifier,
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
    try:
        start_local_cloud(target)
        if set_active_cloud:
            set_active_cloud_func(cloud_identifier)
    except KeyboardInterrupt:
        stop_local_cloud(target)
        raise typer.Abort()


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