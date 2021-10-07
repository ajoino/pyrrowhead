from enum import Enum
from typing import Optional, Tuple, Dict

import typer
from rich import box
from rich.table import Table, Column

from pyrrowhead import rich_console
from pyrrowhead.management.serviceregistry import grouped_services
from pyrrowhead.management.utils import get_service, post_service, delete_service
from pyrrowhead.management.authorization import add_authorization_rule
from pyrrowhead.utils import get_core_system_address_and_port, get_active_cloud_directory


class SortbyChoices(str, Enum):
    RULE_ID = 'id'
    PRIORITY = 'priority'
    CONSUMER = 'consumer'
    PROVIDER = 'provider'
    SERVICE = 'service'

def get_ids_from_service_definition(
        service_definition: str,
        interface_name: str,
        provider_name: str,
        address: str,
        port: int
) -> Tuple[int, int, int]:
    """
    Args:
        service_definition:
        interface_name:
        provider_name:
        address:
        port:

    Returns:
        Tuple of service definition id, interface id, and provider id
    """
    response_data, status = grouped_services()

    services_by_definition = response_data.get("servicesGroupedByServiceDefinition")
    for service_definition_entry in services_by_definition:
        if service_definition_entry["serviceDefinition"] == service_definition:
            for service in service_definition_entry["providerServices"]:
                if service["provider"]["systemName"] == provider_name and service["provider"]["address"] == address and service["provider"]["port"] == port:
                    correct_service = service
                    break
            else:
                rich_console.print(
                        f'Could not find provider {provider_name}@{address}:{port} for '
                        f'any service with service definition {service_definition}.'
                )
                raise typer.Exit()
            break
    else:
        rich_console.print(
                f'Could not find any services with service definition {service_definition}.'
        )
        raise typer.Exit()
    service_definition_id = correct_service["serviceDefinition"]["id"]
    provider_id = correct_service["provider"]["id"]
    interfaces = correct_service["interfaces"]
    for interface in interfaces:
        if interface["interfaceName"] == interface_name:
            interface_id = interface["id"]
            break
    else:
        rich_console.print(
                f'Could not find interface {interface_name} for service '
                f'{service_definition} in provider {provider_name}@{address}:{port}, '
                f'available interfaces are {", ".join(interface["interfaceName"] for interface in interfaces)}'
        )
        raise typer.Exit()
    return service_definition_id, interface_id, provider_id


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


def list_orchestration_rules():
    active_cloud_directory = get_active_cloud_directory()
    address, port, secure, scheme = get_core_system_address_and_port(
            'orchestrator',
            active_cloud_directory,
    )
    scheme = 'https' if secure else 'http'
    response= get_service(
            f'{scheme}://{address}:{port}/orchestrator/mgmt/store',
            active_cloud_directory,
    )
    return response.json(), response.status_code


def add_orchestration_rule(
        service_definition: str,
        service_interface: str,
        provider_system: Tuple[str, str, int],
        consumer_id: Optional[int] = None,  # Union[int, str, Tuple[str, str, int]] = typer.Option(...),
        priority: int = 1,
        metadata: Optional[int] = None,
        add_auth_rule: Optional[bool] = None,
):
    active_cloud_directory = get_active_cloud_directory()
    address, port, secure, scheme = get_core_system_address_and_port(
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
        # "cloud": {"operator": org_name, "name": cloud_name, "secure": secure},
        "priority": priority,
        "attribute": metadata,
    }]

    response = post_service(
            f'{scheme}://{address}:{port}/orchestrator/mgmt/store',
            active_cloud_directory,
            json=orchestration_input,
    )

    if add_auth_rule:
        service_definition_id, interface_id, provider_id = get_ids_from_service_definition(
                service_definition,
                service_interface,
                *provider_system
        )
        add_authorization_rule(consumer_id, provider_id, interface_id, service_definition_id)

    return response.json, response.status_code


def remove_orchestration_rule(orchestration_id):
    active_cloud_directory = get_active_cloud_directory()
    address, port, secure, scheme = get_core_system_address_and_port(
            'orchestrator',
            active_cloud_directory,
    )
    response = delete_service(
            f'{scheme}://{address}:{port}/orchestrator/mgmt/store/{orchestration_id}',
            active_cloud_directory,
    )
    return response.json(), response.status_code
