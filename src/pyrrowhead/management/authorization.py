from rich import box
from rich.table import Table, Column

from pyrrowhead.management.utils import get_service, post_service
from pyrrowhead.utils import (
    get_core_system_address_and_port,
    get_active_cloud_directory,
)


def list_authorization_rules():
    active_cloud_directory = get_active_cloud_directory()
    address, port, secure, scheme = get_core_system_address_and_port(
        "authorization",
        active_cloud_directory,
    )
    response = get_service(
        f"{scheme}://{address}:{port}/authorization/mgmt/intracloud",
        active_cloud_directory,
    )
    response_data = response.json()
    status = response.status_code
    return response_data, status


def add_authorization_rule(
    consumer_id: int, provider_id: int, interface_id: int, service_definition_id: int
):
    active_cloud_directory = get_active_cloud_directory()
    address, port, secure, scheme = get_core_system_address_and_port(
        "authorization",
        active_cloud_directory,
    )

    rule_message = {
        "consumerId": consumer_id,
        "providerIds": [provider_id],
        "interfaceIds": [interface_id],
        "serviceDefinitionIds": [service_definition_id],
    }

    response_data = post_service(
        f"{scheme}://{address}:{port}/authorization/mgmt/intracloud/",
        active_cloud_directory,
        json=rule_message,
    )


def remove_authorization_rule():
    raise NotImplementedError


def create_authorization_table(response_data):
    auth_table = Table(
        Column(header="id", style="red"),
        Column(header="Consumer (id)", style="bright_blue"),
        Column(style="bright_blue"),
        Column(header="Provider (id)", style="blue"),
        Column(style="blue"),
        Column(header="Service definition (id)", style="green"),
        Column(style="green"),
        Column(header="Interface (id)", style="bright_yellow"),
        Column(style="bright_yellow"),
        title="Authorization rule",
        box=box.HORIZONTALS,
    )

    """
    if show_service_uri:
        service_table.add_column(
                header='Service URI',
                style='bright_yellow'
        )
    if show_access_policy:
        service_table.add_column(
                header='Access Policy',
                style='orange3',
        )
    if show_system:
        service_table.add_column(
                header='System',
                style='blue',
        )
    """

    for auth_rule in response_data["data"]:
        row_data = [
            str(auth_rule["id"]),
            f'{auth_rule["consumerSystem"]["systemName"]}',
            f'(id: {auth_rule["consumerSystem"]["id"]})',
            f'{auth_rule["providerSystem"]["systemName"]}',
            f'(id: {auth_rule["providerSystem"]["id"]})',
            f'{auth_rule["serviceDefinition"]["serviceDefinition"]}',
            f'(id: {auth_rule["serviceDefinition"]["id"]})',
            f'{auth_rule["interfaces"][0]["interfaceName"]}',
            f'(id: {auth_rule["interfaces"][0]["id"]})',
        ]

        """
        if show_service_uri:
            row_data.append(service['serviceUri'])
        if show_access_policy:
            row_data.append(service['secure'])
        if show_system:
            row_data.append(f'{service["provider"]["systemName"]}  (id: {service["provider"]["id"]})')
        service_table.add_row(*row_data)
        """
        auth_table.add_row(*row_data)

    return auth_table
