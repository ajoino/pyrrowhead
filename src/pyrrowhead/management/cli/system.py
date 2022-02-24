import json
from pathlib import Path
from typing import Optional

import typer
from rich.syntax import Syntax

from pyrrowhead.management import systemregistry
from pyrrowhead import rich_console

sys_app = typer.Typer(name='systems')


@sys_app.command(name='list')
def list_systems_cli(
        raw_output: bool = typer.Option(False, '--raw-output', '-r', show_default=False),
        indent: Optional[int] = typer.Option(None, '--raw-indent')
):
    """List systems registered in the local cloud"""
    response_data, status = systemregistry.list_systems()

    if raw_output:
        if status >= 400:
            rich_console.print(f'Error code {status}.')
        rich_console.print(Syntax(json.dumps(response_data, indent=indent), 'json'))
        raise typer.Exit()

    table = systemregistry.create_system_table(response_data)

    rich_console.print(table)


@sys_app.command(name='add')
def add_system_cli(
        system_name: str,
        # Add a callback to verify ip
        system_address: str = typer.Argument(..., metavar='ADDRESS'),
        system_port: int = typer.Argument(..., metavar='PORT'),
        certificate_file: Optional[Path] = None
):
    response_data = systemregistry.add_system(system_name, system_address, system_port, certificate_file)

    rich_console.print(Syntax(json.dumps(response_data, indent=2), 'json'))


@sys_app.command(name='remove')
def remove_system_cli(
        system_id: int
):
    """Remove system by id."""
    response_data, status = systemregistry.remove_system(system_id)