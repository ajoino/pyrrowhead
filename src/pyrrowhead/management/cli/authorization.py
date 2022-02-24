from typing import Optional

import typer

from pyrrowhead.management import authorization
from pyrrowhead import rich_console

auth_app = typer.Typer(name='authorization')


@auth_app.command(name='list')
def list_authorization_cli(
        service_definition: Optional[str] = typer.Option(None, metavar='SERVICE_DEFINITION'),
        provider_id: Optional[int] = typer.Option(None),
        provider_name: Optional[str] = typer.Option(None),
        consumer_id: Optional[int] = typer.Option(None),
        consumer_name: Optional[str] = typer.Option(None),
):
    """
    Prints all orchestration rules, no filters or sorting options are implemented yet.
    """
    response_data, status = authorization.list_authorization_rules()

    rich_console.print(authorization.create_authorization_table(response_data))


@auth_app.command(name='add')
def add_authorization_cli(
        consumer_id: int = typer.Option(...),
        provider_id: int = typer.Option(...),
        interface_id: int = typer.Option(...),
        service_definition_id: int = typer.Option(...),
):
    """
    Add authorization rule by ids.
    """
    authorization.add_authorization_rule(consumer_id, provider_id, interface_id, service_definition_id)


@auth_app.command(name='remove')
def remove_authorization_cli():
    """Not implemented."""
    rich_console.print("Not implemented.")
    raise typer.Exit(-1)
    authorization.remove_authorization_rule()