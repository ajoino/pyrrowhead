from typing import Optional
from pathlib import Path

import typer
from rich import box
from rich.syntax import Syntax
from rich.table import Table, Column
from rich.text import Text

from pyrrowhead import rich_console
from pyrrowhead.management.common import CoreSystemAddress, CoreSystemPort, CertDirectory
from pyrrowhead.management.utils import get_service

sys_app = typer.Typer(name='systems')


@sys_app.command(name='list')
def list_systems(
        system_name: Optional[str] = typer.Argument('', show_default=False),
        id: Optional[int] = None,
        all: bool = typer.Option(None, '--all', '-A'),
        # show_provider: bool = typer.Option(None, '--show-provider', '-s'),
        # show_access_policy: bool = typer.Option(False, '--show-access-policy', '-c', show_default=False),
        raw_output: bool = typer.Option(False, '--raw-output', '-r', show_default=False),
        address: str = CoreSystemAddress,
        port: int = CoreSystemPort(8437),
        cert_dir: Path = CertDirectory,
):
    if id and all:
        rich_console.print(Text("--id and --all/-A are mutually exclusive options"))
        raise typer.Exit()
    pass
    if system_name:
        print(f'https://{address}:{port}/systemregistry/mgmt/systemname/{system_name}')
        resp = get_service(
                f'https://{address}:{port}/systemregistry/mgmt/systemname/{system_name}',
                cert_dir,
        )
    elif id:
        resp = get_service(
                f'https://{address}:{port}/systemregistry/mgmt/system/{id}',
                cert_dir,
        )
    elif all:
        resp = get_service(
                f'https://{address}:{port}/systemregistry/mgmt/systems',
                cert_dir,
        )
    else:
        pass

    table = create_system_table(resp)

    rich_console.print(table)


@sys_app.command(name='add')
def add_system():
    pass


@sys_app.command(name='remove')
def remove_system():
    pass


def create_system_table(response):
    system_data = response.json()

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