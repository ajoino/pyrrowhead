from pathlib import Path
from typing import Optional, List, Tuple

import typer

from pyrrowhead.org.initialize_org import mk_org_dir, populate_org_dir
from pyrrowhead import rich_console
from pyrrowhead.utils import (
    switch_directory,
    set_active_cloud as set_active_cloud_func,
    get_config,
    PyrrowheadError,
)
from pyrrowhead.constants import (
    OPT_CLOUDS_DIRECTORY,
    OPT_CLOUD_NAME,
    OPT_ORG_NAME,
    ARG_ORG_NAME,
    ARG_CLOUD_IDENTIFIER,
)


org_app = typer.Typer(name="org")


@org_app.command()
def setup(org_name: str = ARG_ORG_NAME):
    try:
        mk_org_dir(org_name)
    except PyrrowheadError as e:
        rich_console.print(str(e))
        raise typer.Exit(-1)

    rich_console.print(f"Created organization {org_name}")


@org_app.command()
def install(org_name: str = ARG_ORG_NAME):
    password = "123456"
    populate_org_dir(org_name, password)


@org_app.command()
def add_cert(org_name: str = ARG_ORG_NAME):
    pass


@org_app.command()
def add_key(org_name: str = ARG_ORG_NAME):
    pass


@org_app.command()
def add_p12(org_name: str = ARG_ORG_NAME):
    pass
