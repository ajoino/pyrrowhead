"""
This module is work-in-progress.
"""
from pathlib import Path
from typing import Optional

import typer

from pyrrowhead.org.initialize_org import (
    mk_org_dir,
    copy_org_certificates,
)
from pyrrowhead import rich_console
from pyrrowhead.utils import (
    PyrrowheadError,
    check_valid_dns,
    get_pyrrowhead_path,
)
from pyrrowhead.constants import (
    ARG_ORG_NAME,
    LOCAL_CLOUDS_SUBDIR,
)


org_app = typer.Typer(name="org")


@org_app.command()
def create(org_name: str = ARG_ORG_NAME):
    """
    Initializes an empty organization with name ORG_NAME.
    """
    org_dir = get_pyrrowhead_path().joinpath(LOCAL_CLOUDS_SUBDIR, org_name)
    if not check_valid_dns(org_name):
        rich_console.print(
            PyrrowheadError(f'"{org_name}" is not a valid organization name.')
        )
        raise typer.Exit(-1)

    try:
        mk_org_dir(org_name, org_dir)
    except PyrrowheadError as e:
        rich_console.print(str(e))
        raise typer.Exit(-1)

    rich_console.print(f"Created organization {org_name}")


@org_app.command()
def cert_gen(org_name: str = ARG_ORG_NAME):
    password = "123456"  # noqa


@org_app.command()
def add_cert(
    org_name: str = ARG_ORG_NAME,
    key_path: Path = typer.Option(..., "--key-path", "-k"),
    cert_path: Optional[Path] = typer.Option(..., "--cert-path", "-c"),
    certgen: Optional[bool] = typer.Option(False, "--certgen", "-g"),
):
    if not key_path.is_file():
        rich_console.print(f"Cannot find key at {key_path}")
        raise typer.Exit(-1)

    if cert_path is not None:
        copy_org_certificates(org_name, key_path, cert_path)


@org_app.command()
def add_p12(org_name: str = ARG_ORG_NAME):
    pass
