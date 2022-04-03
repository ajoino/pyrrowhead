from typing import Optional, Tuple, Dict

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table, Column

from pyrrowhead import rich_console
from pyrrowhead.management.common import AccessPolicy
from pyrrowhead.management.utils import (
    get_service,
    post_service,
    delete_service as del_service,
)
from pyrrowhead.utils import (
    get_core_system_address_and_port,
    get_active_cloud_directory,
)


def inspect_service(service_id: int):
    active_cloud_directory = get_active_cloud_directory()
    address, port, secure, scheme = get_core_system_address_and_port(
        "service_registry",
        active_cloud_directory,
    )

    response = get_service(
        f"{scheme}://{address}:{port}/serviceregistry/mgmt/{service_id}",
        active_cloud_directory,
    )

    return response.json(), response.status_code


def add_service(
    service_definition: str,
    uri: str,
    interface: str,
    access_policy: AccessPolicy,
    system: Tuple[str, str, int],
):
    active_cloud_directory = get_active_cloud_directory()
    sr_address, sr_port, secure, scheme = get_core_system_address_and_port(
        "service_registry",
        active_cloud_directory,
    )

    system_name, address, port = system

    registry_request = {
        "serviceDefinition": service_definition,
        "serviceUri": uri,
        "interfaces": [interface],
        "secure": access_policy,
        "providerSystem": {
            "systemName": system_name,
            "address": address,
            "port": port,
        },
    }

    response = post_service(
        f"{scheme}://{sr_address}:{sr_port}/serviceregistry/mgmt/",
        active_cloud_directory,
        json=registry_request,
    )

    return response.json(), response.status_code


def list_filter(
    orch_rule: Dict,
    service_definition: Optional[str],
    system_name: Optional[str],
    system_id: Optional[int],
):
    if service_definition is not None:
        return orch_rule["serviceDefinition"]["serviceDefinition"] == service_definition
    elif system_name is not None:
        return orch_rule["provider"]["systemName"] == system_name
    elif system_id is not None:
        return orch_rule["provider"]["id"] == system_id

    return True


def list_services(
    service_definition: Optional[str],
    system_name: Optional[str],
    system_id: Optional[int],
) -> Dict:
    active_cloud_directory = get_active_cloud_directory()
    address, port, secure, scheme = get_core_system_address_and_port(
        "service_registry",
        active_cloud_directory,
    )

    endpoint = f"{scheme}://{address}:{port}/serviceregistry/mgmt/"

    response_data = get_service(
        endpoint,
        active_cloud_directory,
    ).json()

    if any((system_name, system_id)):
        response_data = {
            "data": [
                service
                for service in response_data["data"]
                if (
                    system_name == service["provider"]["systemName"]
                    or system_id == service["provider"]["id"]
                )
            ]
        }

    response_data["data"] = [
        orch_rule
        for orch_rule in response_data["data"]
        if list_filter(orch_rule, service_definition, system_name, system_id)
    ]

    return response_data


def delete_service(service_id: int):
    active_cloud_directory = get_active_cloud_directory()
    address, port, secure, scheme = get_core_system_address_and_port(
        "service_registry",
        active_cloud_directory,
    )

    response = del_service(
        f"https://{address}:{port}/serviceregistry/mgmt/{id}",
        active_cloud_directory,
    )

    return response.json(), response.status_code


def create_service_table(
    response_data: Dict, show_system, show_access_policy, show_service_uri
) -> Table:
    service_table = Table(
        Column(header="id", style="red"),
        Column(header="Service definition", style="bright_blue"),
        Column(header="Interface", style="green"),
        title="Registered Services",
        box=box.SIMPLE,
    )

    if show_service_uri:
        service_table.add_column(header="Service URI", style="bright_yellow")
    if show_access_policy:
        service_table.add_column(
            header="Access Policy",
            style="orange3",
        )
    if show_system:
        service_table.add_column(
            header="System",
            style="blue",
        )

    for service in response_data["data"]:
        row_data = [
            str(service["id"]),
            f'{service["serviceDefinition"]["serviceDefinition"]}  '
            f'(id: {service["serviceDefinition"]["id"]})',
            service["interfaces"][0]["interfaceName"],
        ]

        if show_service_uri:
            row_data.append(service["serviceUri"])
        if show_access_policy:
            row_data.append(service["secure"])
        if show_system:
            row_data.append(
                f'{service["provider"]["systemName"]}  '
                f'(id: {service["provider"]["id"]})'
            )
        service_table.add_row(*row_data)

    return service_table


def grouped_services():
    active_cloud_directory = get_active_cloud_directory()
    address, port, secure, scheme = get_core_system_address_and_port(
        "service_registry",
        active_cloud_directory,
    )
    response = get_service(
        f"{scheme}://{address}:{port}/serviceregistry/mgmt/grouped",
        active_cloud_directory,
    )
    return response.json(), response.status_code


def get_system_id_from_name(system_name: str, address: str = "", port: int = -1) -> int:
    active_cloud_directory = get_active_cloud_directory()
    sr_address, sr_port, secure, scheme = get_core_system_address_and_port(
        "service_registry",
        active_cloud_directory,
    )

    scheme = "https" if secure else "http"
    response_data = get_service(
        f"{scheme}://{sr_address}:{sr_port}/serviceregistry/mgmt/systems",
        active_cloud_directory,
    ).json()

    candidate_systems = [
        system
        for system in response_data["data"]
        if system["systemName"] == system_name
    ]

    if len(address) > 0 and port >= 0:
        candidate_systems = [
            system
            for system in candidate_systems
            if system["address"] == address and system["port"] == port
        ]

    if len(candidate_systems) == 0:
        return -1
    elif len(candidate_systems) > 1:
        return -2

    return candidate_systems[0]["id"]


def render_service(response_data):
    tab_break = "\n\t"
    provider = response_data["provider"]
    render_group = Group(
        (f'Service URI: {response_data["serviceUri"]}'),
        (
            f"Interfaces: [bright_yellow]\n\t"
            f'{tab_break.join(interface["interfaceName"] for interface in response_data["interfaces"])}'  # noqa
            f"[/bright_yellow]"
        ),
        (f'Access policy: [orange3]{response_data["secure"]}[/orange3]'),
        (f'Version: {response_data["version"]}'),
        (
            f"Provider:"
            f'{tab_break}Id: {provider["id"]}'
            f'{tab_break}System name: [blue]{provider["systemName"]}[/blue]'
            f'{tab_break}Address: {provider["address"]}'
            f'{tab_break}Port: {provider["port"]}'
        ),
        (
            f"End of validity: [red]"
            f'{response_data.get("endOfValidity", "[green]Always valid[/green]")}'
            f"[/red]"
        ),
    )
    if metadata := response_data.get("metadata"):
        render_group.renderables.append(
            f"Metadata: {tab_break} "
            f'{tab_break.join(f"{name}: {value}" for name, value in metadata.items())}'
        )
    rich_console.print(
        (
            f' Service "{response_data["serviceDefinition"]["serviceDefinition"]}" '
            f'(id: {response_data["id"]})'
        ),
        Panel(render_group, box=box.HORIZONTALS, expand=False),
    )
