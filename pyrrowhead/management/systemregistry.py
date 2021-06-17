import json
from typing import Optional
from pathlib import Path

import typer
from rich import box
from rich.syntax import Syntax
from rich.table import Table, Column
from rich.text import Text

from pyrrowhead import rich_console
from pyrrowhead.management.common import CoreSystemAddress, CoreSystemPort, CertDirectory
from pyrrowhead.management.utils import get_service, post_service, delete_service
from pyrrowhead.utils import get_core_system_address_and_port, get_active_cloud_directory

sys_app = typer.Typer(name='systems')


@sys_app.command(name='list')
def list_systems(
        system_name: Optional[str] = typer.Argument('', show_default=False),
        # show_provider: bool = typer.Option(None, '--show-provider', '-s'),
        # show_access_policy: bool = typer.Option(False, '--show-access-policy', '-c', show_default=False),
        raw_output: bool = typer.Option(False, '--raw-output', '-r', show_default=False),
        indent: Optional[int] = typer.Option(None, '--raw-indent')
):
    active_cloud_directory = get_active_cloud_directory()
    address, port = get_core_system_address_and_port(
            'service_registry',
            active_cloud_directory,
    )

    response_data = get_service(
            f'https://{address}:{port}/serviceregistry/mgmt/systems',
            active_cloud_directory,
    ).json()

    if raw_output:
        rich_console.print(Syntax(json.dumps(response_data, indent=indent), 'json'))
        raise typer.Exit()

    table = create_system_table(response_data)

    rich_console.print(table)


@sys_app.command(name='add')
def add_system(
        system_name: str,
        # Add a callback to verify ip
        system_address: str = typer.Argument(..., metavar='ADDRESS'),
        system_port: int = typer.Argument(..., metavar='PORT'),
        certificate_file: Optional[Path] = None
):
    active_cloud_directory = get_active_cloud_directory()
    address, port = get_core_system_address_and_port(
            'service_registry',
            active_cloud_directory,
    )

    system_record = {
        "systemName": system_name,
        "address": system_address,
        "port": system_port,
    }

    response_data = post_service(
            f'https://{address}:{port}/serviceregistry/mgmt/systems',
            active_cloud_directory,
            json=system_record,
    ).json()

    rich_console.print(Syntax(json.dumps(response_data, indent=2), 'json'))


@sys_app.command(name='remove')
def remove_system(
        system_id
):
    active_cloud_directory = get_active_cloud_directory()
    address, port = get_core_system_address_and_port(
            'service_registry',
            active_cloud_directory,
    )

    response_data = delete_service(
            f'https://{address}:{port}/serviceregistry/mgmt/systems/{system_id}',
            active_cloud_directory,
    )



def create_system_table(response):
    system_data = response

    system_table = Table(
            Column(header='id', style='red'),
            Column(header='System name', style='blue'),
            Column(header='Address', style='purple'),
            Column(header='Port', style='bright_white'),
            title='Registered systems',
            box=box.SIMPLE,
    )

    for system in system_data['data']:
        system_table.add_row(
            str(system["id"]),
            system["systemName"],
            system["address"],
            str(system["port"]),
        )

    return system_table