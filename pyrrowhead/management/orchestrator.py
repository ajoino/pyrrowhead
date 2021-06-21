import json
from enum import Enum
from typing import Optional, Tuple, Dict, Any

import typer
from rich import box
from rich.syntax import Syntax
from rich.table import Table, Column

from pyrrowhead import rich_console
from pyrrowhead.management.utils import get_service, post_service, delete_service
from pyrrowhead.utils import get_core_system_address_and_port, get_active_cloud_directory

orch_app = typer.Typer(name='orchestration')

class SortbyChoices(str, Enum):
    RULE_ID = 'id'
    PRIORITY = 'priority'
    CONSUMER = 'consumer'
    PROVIDER = 'provider'
    SERVICE = 'service'

def table_sort(rule, choice):
    if choice == SortbyChoices.RULE_ID:
        return rule['id']
    elif choice == SortbyChoices.PRIORITY:
        return rule['priority']
    elif choice == SortbyChoices.CONSUMER:
        return rule['consumerSystem']['id']
    elif choice == SortbyChoices.PROVIDER:
        return rule['providerSystem']['id']
    elif choice == SortbyChoices.SERVICE:
        return rule['serviceDefinition']['id']
    else:
        raise RuntimeError(f'Invalid sorting choice: {choice}')

def table_condition(
        orch_rule: Dict,
        service_definition: Optional[str],
        consumer_id: Optional[int],
        consumer_name: Optional[str],
        provider_id: Optional[int],
        provider_name: Optional[str],
):
    if service_definition is not None:
        return orch_rule['serviceDefinition']['serviceDefinition'] == service_definition
    elif consumer_id is not None:
        breakpoint()
        return orch_rule['consumerSystem']['id'] == consumer_id
    elif consumer_name is not None:
        return orch_rule['consumerSystem']['systemName'] == consumer_name
    elif provider_id is not None:
        return orch_rule['providerSystem']['id'] == provider_id
    elif provider_name is not None:
        return orch_rule['providerSystem']['systemName'] == provider_name
    else:
        return True


def create_orchestration_table(
        response_data: Dict,
        service_definition: Optional[str],
        consumer_id: Optional[int],
        consumer_name: Optional[str],
        provider_id: Optional[int],
        provider_name: Optional[str],
        sort_by: str,
):
    table = Table(
            Column(header='id', style='red'),
            Column(header='Consumer (id)', style='bright_blue'),
            Column(header='Provider (id)', style='blue'),
            Column(header='Service Definition (id)', style='green'),
            Column(header='Interface', style='bright_yellow'),
            Column(header='priority', style='bright_white'),
            box=box.HORIZONTALS,
    )

    for orch_rule in sorted(response_data['data'], key=lambda x: table_sort(x, sort_by)):
        if not table_condition(
                orch_rule,
                service_definition,
                consumer_id,
                consumer_name,
                provider_id,
                provider_name,
        ):
            continue
        table.add_row(
                str(orch_rule['id']),
                f'{orch_rule["consumerSystem"]["systemName"]} ({orch_rule["consumerSystem"]["id"]})',
                f'{orch_rule["providerSystem"]["systemName"]} ({orch_rule["providerSystem"]["id"]})',
                f'{orch_rule["serviceDefinition"]["serviceDefinition"]} ({orch_rule["serviceDefinition"]["id"]})',
                orch_rule['serviceInterface']['interfaceName'],
                str(orch_rule['priority']),
        )

    return table



@orch_app.command(name='list')
def list_orchestration_rules(
        service_definition: Optional[str] = typer.Option(None, metavar='SERVICE_DEFINITION'),
        provider_id: Optional[int] = typer.Option(None),
        provider_name: Optional[str] = typer.Option(None),
        consumer_id: Optional[int] = typer.Option(None),
        consumer_name: Optional[str] = typer.Option(None),
        sort_by: SortbyChoices = typer.Option('id'),
        raw_output: bool = typer.Option(False),
        raw_indent: Optional[int] = typer.Option(None),
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

    if raw_output:
        rich_console.print(Syntax(json.dumps(response_data, indent=raw_indent), 'json'))
        raise typer.Exit()
    
    table = create_orchestration_table(
            response_data,
            service_definition,
            consumer_id,
            consumer_name,
            provider_id,
            provider_name,
            sort_by,
    )

    rich_console.print(table)
    


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
        "attribute": metadata,
    }]

    response_data = post_service(
            f'https://{address}:{port}/orchestrator/mgmt/store',
            active_cloud_directory,
            json=orchestration_input,
    ).json()

@orch_app.command(name='remove')
def remove_orchestration_rule(
        orchestration_id: int
):
    active_cloud_directory = get_active_cloud_directory()
    address, port = get_core_system_address_and_port(
            'orchestrator',
            active_cloud_directory,
    )

    response_data = delete_service(
            f'https://{address}:{port}/orchestrator/mgmt/store/{orchestration_id}',
            active_cloud_directory,
    )
