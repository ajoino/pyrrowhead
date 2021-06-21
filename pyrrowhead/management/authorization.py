import json
from typing import Optional

import typer
from rich.syntax import Syntax

from pyrrowhead import rich_console
from pyrrowhead.management.utils import get_service, post_service
from pyrrowhead.utils import get_core_system_address_and_port, get_active_cloud_directory

auth_app = typer.Typer(name='authorization')

@auth_app.command(name='list')
def list_authorization_rules(
        service_definition: Optional[str] = typer.Option(None, metavar='SERVICE_DEFINITION'),
        provider_id: Optional[int] = typer.Option(None),
        provider_name: Optional[str] = typer.Option(None),
        consumer_id: Optional[int] = typer.Option(None),
        consumer_name: Optional[str] = typer.Option(None),
):
    active_cloud_directory = get_active_cloud_directory()
    address, port = get_core_system_address_and_port(
            'authorization',
            active_cloud_directory,
    )

    response_data = get_service(
            f'https://{address}:{port}/authorization/mgmt/intracloud',
            active_cloud_directory,
    ).json()


    rich_console.print(Syntax(json.dumps(response_data, indent=2), 'json'))



@auth_app.command(name='add')
def add_authorization_rule(
        consumer_id: int = typer.Option(...),
        provider_id: int = typer.Option(...),
        interface_id: int = typer.Option(...),
        service_definition_id: int = typer.Option(...),
):
    active_cloud_directory = get_active_cloud_directory()
    address, port = get_core_system_address_and_port(
            'authorization',
            active_cloud_directory,
    )

    rule_message = {
        "consumerId": consumer_id,
        "providerIds": [provider_id],
        "interfaceIds": [interface_id],
        "serviceDefinitionIds": [service_definition_id]
    }

    response_data = post_service(
            f'https://{address}:{port}/authorization/mgmt/intracloud/',
            active_cloud_directory,
            json=rule_message,
    )

@auth_app.command(name='remove')
def remove_authorization_rule():
    pass