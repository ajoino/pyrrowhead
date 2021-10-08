from enum import Enum
from pathlib import Path

import typer
import yaml
from rich.text import Text

from pyrrowhead import rich_console

class AccessPolicy(str, Enum):
    UNRESTRICTED = 'NOT_SECURE'
    CERTIFICATE = 'CERTIFICATE'
    TOKEN = 'TOKEN'

CoreSystemAddress = typer.Option('127.0.0.1', '--address', '-a')
def CoreSystemPort(port: int):
    return typer.Option(port, '--port', '-p')

CertDirectory = typer.Option(Path('.'), '--cert-dir')
service_definition_argument = typer.Argument(..., metavar='SERVICE_DEFINITION', help='')
service_uri_argument = typer.Argument(..., metavar='SERVICE_URI', help='')
service_interface_argument = typer.Argument(
        ..., metavar='SERVICE_INTERFACE',
        help='Must be of format <PROTOCOL>-<SECURITY>-<PAYLOAD>.'
)
def system_option(
        system_name: str,
):
    return typer.Option(
            (None, None, None),
            show_default=False,
            metavar='SYSTEM_NAME ADDRESS PORT',
            help=f'{system_name.capitalize()} '
                 f'system definition.'
),
raw_output = typer.Option(
        False,
        '--raw-output',
        '-r',
        show_default=False,
        help='Show information as json formatted string, '
             'use together with --raw-indent option to '
             'pretty print.',
)
raw_indent = typer.Option(
        None,
        '--raw-indent',
        metavar='NUM_SPACES',
        help='Print json with NUM_SPACES '
             'spaces of indentation.',
)


