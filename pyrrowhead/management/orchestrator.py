import json
from typing import Optional, Tuple, Dict, Any

import typer
from rich.syntax import Syntax

from pyrrowhead import rich_console
from pyrrowhead.management.utils import get_service, post_service
from pyrrowhead.utils import get_core_system_address_and_port, get_active_cloud_directory

orch_app = typer.Typer(name='orchestration')

@orch_app.command(name='list')
def list_orchestration_rules(
        service_definition: Optional[str] = typer.Option(None, metavar='SERVICE_DEFINITION'),
        provider_id: Optional[int] = typer.Option(None),
        provider_name: Optional[str] = typer.Option(None),
        consumer_id: Optional[int] = typer.Option(None),
        consumer_name: Optional[str] = typer.Option(None),
):
    active_cloud_directory = get_active_cloud_directory()
    address, port = get_core_system_address_and_port(
            'orchestrator',
            active_cloud_directory,
    )

    response_data = get_service(
            f'https://{address}:{port}/orchestrator/mgmt/store',
            active_cloud_directory,
    ).json()

    rich_console.print(Syntax(json.dumps(response_data, indent=2), 'json'))


@orch_app.command(name='add')
def add_orchestration_rule(
        service_definition: str,
        consumer_id: int = typer.Option(...),
        provider_system: Tuple[str, str, int] = typer.Option(...),
        service_interface: str = typer.Option(..., '--interface'),
        priority: int = typer.Option(1),
        metadata: Optional[int] = None
):
    active_cloud_directory = get_active_cloud_directory()
    address, port = get_core_system_address_and_port(
            'orchestrator',
            active_cloud_directory,
    )
    cloud_name = active_cloud_directory.name
    org_name = active_cloud_directory.parents[0].name

    orchestration_input = [{
        "serviceDefinitionName": service_definition,
        "serviceInterfaceName": service_interface,
        "consumerSystemId": consumer_id,
        "providerSystem": dict(zip(("systemName", "address", "port"), provider_system)),
        "cloud": {"operator": org_name, "name": cloud_name},
        "priority": priority,
        #"attribute": metadata,
    }]

    response_data = post_service(
            f'https://{address}:{port}/orchestrator/mgmt/store',
            active_cloud_directory,
            json=orchestration_input,
    )

    rich_console.print(response_data)
    rich_console.print(response_data.text)
    rich_console.print(Syntax(json.dumps(orchestration_input, indent=2), 'json'))

@orch_app.command(name='remove')
def remove_orchestration_rule():
    pass