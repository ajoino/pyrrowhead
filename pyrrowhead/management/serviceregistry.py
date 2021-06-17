from enum import Enum
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import json

import typer
from rich import box
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.table import Table, Column
from rich.console import RenderGroup
from rich.rule import Rule
from rich.bar import Bar

from pyrrowhead.management.common import CoreSystemAddress, CoreSystemPort, CertDirectory
from pyrrowhead.management.utils import get_service, post_service, delete_service
from pyrrowhead import rich_console
from pyrrowhead.utils import get_core_system_address_and_port, get_active_cloud_directory

SRPort = CoreSystemPort(8443)

sr_app = typer.Typer(name='services')


@sr_app.command(name='list')
def services(
        service_definition: Optional[str] = typer.Option(None, show_default=False, metavar='SERVICE_DEFINITION',
                                                         help='Filter services by SERVICE_DEFINITION'),
        system_name: Optional[str] = typer.Option(None, show_default=False, metavar='SYSTEM_NAME',
                                                  help='Filter services by SYSTEM_NAME'),
        system_id: Optional[int] = typer.Option(None, show_default=False, metavar='SYSTEM_ID',
                                                help='Filter services by SYSTEM_ID'),
        show_service_uri: bool = typer.Option(False, '--show-service-uri', '-u', show_default=False,
                                              help='Show service uri'),
        show_access_policy: bool = typer.Option(False, '--show-access-policy', '-c', show_default=False,
                                                help='Show access policy'),
        show_provider: bool = typer.Option(None, '--show-provider', '-s', help='Show provider system'),
        raw_output: bool = typer.Option(False, '--raw-output', '-r', show_default=False,
                                        help='Show information as json'),
        indent: Optional[int] = typer.Option(None, '--raw-indent', metavar='NUM_SPACES',
                                             help='Print json with NUM_SPACES spaces of indentation')
):
    """
    List services registered in the active local cloud, sorted by id. Services shown can
    be filtered by service definition or system. More information about the
    services can be seen with the -usc flags. The raw json data is accessed by the -r flag.
    """
    active_cloud_directory = get_active_cloud_directory()
    address, port = get_core_system_address_and_port(
            'service_registry',
            active_cloud_directory,
    )

    try:
        list_data = list_services(
                service_definition,
                system_name,
                system_id,
                address,
                port,
                active_cloud_directory,
        )
    except RuntimeError as e:
        rich_console.print(e)
        raise typer.Exit(code=-1)

    if raw_output:
        rich_console.print(Syntax(json.dumps(list_data, indent=indent), 'json'))
        raise typer.Exit()

    service_table = create_service_table(list_data, show_provider, show_access_policy, show_service_uri)

    rich_console.print(service_table)


@sr_app.command(name='inspect')
def inspect_service(
        service_id: int,
        raw_output: Optional[bool] = None,
        indent: Optional[int] = None,
):
    """
    Show all information regarding specific service.
    """
    active_cloud_directory = get_active_cloud_directory()
    address, port = get_core_system_address_and_port(
            'service_registry',
            active_cloud_directory,
    )

    response_data = get_service(
            f'https://{address}:{port}/serviceregistry/mgmt/{service_id}',
            active_cloud_directory,
    ).json()

    if raw_output:
        rich_console.print(Syntax(json.dumps(response_data, indent=indent), 'json'))
        raise typer.Exit()

    tab_break = "\n\t"
    provider = response_data["provider"]
    render_group = RenderGroup(
            (f'Service URI: {response_data["serviceUri"]}'),
            (f'Interfaces: [bright_yellow]\n\t{tab_break.join(interface["interfaceName"] for interface in response_data["interfaces"])}[/bright_yellow]'),
            (f'Access policy: [orange3]{response_data["secure"]}[/orange3]'),
            (f'Version: {response_data["version"]}'),
            (
                    f'Provider:'
                    f'{tab_break}Id: {provider["id"]}'
                    f'{tab_break}System name: [blue]{provider["systemName"]}[/blue]'
                    f'{tab_break}Address: {provider["address"]}'
                    f'{tab_break}Port: {provider["port"]}'
            ),
            # TODO: "Always valid" should be printed in green and not red
            ( f'End of validity: [red]{response_data.get("endOfValidity", "[green]Always valid[/green]")}[/red]'),
    )
    if (metadata := response_data.get("metadata")):
        render_group.renderables.append(f'Metadata: {tab_break} {tab_break.join(f"{name}: {value}" for name, value in metadata.items())}')
    rich_console.print(
            (f' Service "{response_data["serviceDefinition"]["serviceDefinition"]}" (id: {service_id})'),
            Panel(render_group, box=box.HORIZONTALS, expand=False)
    )

class AccessPolicy(str, Enum):
    UNRESTRICTED = 'NOT_SECURE'
    CERTIFICATE = 'CERTIFICATE'
    TOKEN = 'TOKEN'


@sr_app.command(name='add')
def add_service(
        service_definition: str,
        uri: str,
        interface: str,
        access_policy: AccessPolicy = typer.Argument(AccessPolicy.CERTIFICATE),
        system: Optional[Tuple[str, str, int]] = typer.Option((None, None, None), show_default=False),
        system_id: Optional[int] = None,
):
    active_cloud_directory = get_active_cloud_directory()
    address, port = get_core_system_address_and_port(
            'service_registry',
            active_cloud_directory,
    )

    # TODO: Implement system_id
    if all((all(system), system_id)):
        rich_console.print('System and system-id are mutually exclusive options.')
        raise typer.Exit()
    elif not any((all(system), system_id)):
        rich_console.print('One option of --system or --system-id must be set.')
        raise typer.Exit()

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
        }
    }
    try:
        resp = post_service(
                f'https://{address}:{port}/serviceregistry/mgmt/',
                active_cloud_directory,
                json=registry_request,
        )
    except IOError as e:
        rich_console.print(e)
        raise typer.Exit(-1)

    # Add service code
    if resp.status_code in {400, 401, 500}:
        rich_console.print(Text(f'Service registration failed: {resp.json()["errorMessage"]}'))
        raise typer.Exit(-1)


@sr_app.command(name='remove')
def remove_service(
        id: int,
        sr_address: str = '127.0.0.1',
        sr_port: int = 8443,
        cert_dir: Path = CertDirectory,
):
    resp = delete_service(
            f'https://{sr_address}:{sr_port}/serviceregistry/mgmt/{id}',
            cert_dir,
    )

    if resp.status_code in {400, 401, 500}:
        rich_console.print(Text(f'Service unregistration failed: {resp.json()["errorMessage"]}'))
        raise typer.Exit(-1)


def list_services(
        service_definition: Optional[str],
        system_name: Optional[str],
        system_id: Optional[int],
        address: Optional[str],
        port: Optional[int],
        cloud_dir: Optional[Path]
) -> Dict:
    exclusive_options = (service_definition, system_name, system_id)

    if len(list(option for option in exclusive_options if option is not None)) > 1:
        raise RuntimeError('Only one of the options <--service-definition, --system-name, --system-id> may be used.')

    if service_definition:
        endpoint = f'https://{address}:{port}/serviceregistry/mgmt/serviceDef/{service_definition}'
    else:
        endpoint = f'https://{address}:{port}/serviceregistry/mgmt/'

    response_data = get_service(endpoint, cloud_dir, ).json()

    if any((system_name, system_id)):
        response_data = {"data":
            [
                service for service in response_data["data"]
                if (system_name == service["provider"]["systemName"]
                    or system_id == service["provider"]["id"])
            ]
        }

    return response_data


def create_service_table(response_data: Dict, show_system, show_access_policy, show_service_uri) -> Table:
    service_table = Table(
            Column(header='id', style='red'),
            Column(header='Service definition'),
            Column(header='Interface', style='green'),
            title="Registered Services",
            box=box.SIMPLE,
    )

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

    # Returned data is formatted differently if service registry is queried by id

    for service in response_data["data"]:
        row_data = [
            str(service['id']),
            service['serviceDefinition']['serviceDefinition'],
            service['interfaces'][0]['interfaceName'],
        ]

        if show_service_uri:
            row_data.append(service['serviceUri'])
        if show_access_policy:
            row_data.append(service['secure'])
        if show_system:
            row_data.append(f'{service["provider"]["systemName"]}  (id: {service["provider"]["id"]})')
        service_table.add_row(*row_data)

    return service_table
