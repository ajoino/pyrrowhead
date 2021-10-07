from enum import Enum
from pathlib import Path

import typer
import yaml
from rich.text import Text

from pyrrowhead import rich_console

CoreSystemAddress = typer.Option('127.0.0.1', '--address', '-a')
def CoreSystemPort(port: int):
    return typer.Option(port, '--port', '-p')

CertDirectory = typer.Option(Path('.'), '--cert-dir')


class AccessPolicy(str, Enum):
    UNRESTRICTED = 'NOT_SECURE'
    CERTIFICATE = 'CERTIFICATE'
    TOKEN = 'TOKEN'