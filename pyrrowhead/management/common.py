from pathlib import Path

import typer
import yaml

CoreSystemAddress = typer.Option('127.0.0.1', '--address', '-a')
def CoreSystemPort(port: int):
    return typer.Option(port, '--port', '-p')

CertDirectory = typer.Option(Path('.'), '--cert-dir')