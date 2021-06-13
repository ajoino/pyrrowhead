from enum import Enum
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import json

import typer
from rich import box
from rich.syntax import Syntax
from rich.text import Text
from rich.table import Table, Column

from pyrrowhead.management.common import CoreSystemAddress, CoreSystemPort, CertDirectory
from pyrrowhead.management.utils import get_service, post_service, delete_service
from pyrrowhead import rich_console
from pyrrowhead.utils import get_core_system_address_and_port, get_active_cloud_directory

SRPort = CoreSystemPort(8443)

sr_app = typer.Typer(name='services')

@sr_app.command(name='list')
def services(
        service_definition: Optional[str] = typer.Option(None, show_default=False),
        system_name: Optional[str] = typer.Option(None, show_default=False),
        system_id: Optional[int] = typer.Option(None, show_default=False),
        show_provider: bool = typer.Option(None, '--show-provider', '-s'),
        show_access_policy: bool = typer.Option(False, '--show-access-policy', '-c', show_default=False),
        show_service_uri: bool = typer.Option(False, '--show-service-uri', '-u', show_default=False),
        raw_output: bool = typer.Option(False, '--raw-output', '-r', show_default=False),
):
    active_cloud_directory = get_active_cloud_directory()
    address, port = get_core_system_address_and_port(
            'service_registry',
            active_cloud_directory,
    )

    list_data = list_services(
            service_definition,
            system_name,
            system_id,
            address,
            port,
            active_cloud_directory,
    )

    if raw_output:
        print(json.dumps(list_data))
        # TODO: return resp.json()?
        raise typer.Exit()

    service_table = create_service_table(list_data, show_provider, show_access_policy, show_service_uri)

    rich_console.print(service_table)


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
        system: Tuple[str, str, int] = typer.Option((None, None, None), show_default=False),
        sr_address: str = '127.0.0.1',
        sr_port: int = 8443,
        cert_dir: Path = CertDirectory,
        #system_id: Optional[int] = None,
):
    # TODO: Implement system_id
    if any(system) and False:
        rich_console.print('system and system-id are mutually exclusive options.')
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
            "port":  port,
        }
    }
    resp = post_service(
            f'https://{sr_address}:{sr_port}/serviceregistry/mgmt/',
            cert_dir,
            json=registry_request,
    )

    # Add service code
    if resp.status_code in {400, 401, 500}:
        rich_console.print(Text(f'Service registration failed: {resp.json()["errorMessage"]}'))


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
        resp = get_service(
                f'https://{address}:{port}/serviceregistry/mgmt/serviceDef/{service_definition}',
                cloud_dir,
        )
        response_data = resp.json()
    else:
        resp = get_service(
                f'https://{address}:{port}/serviceregistry/mgmt/',
                cloud_dir,
        )
        if any((system_name, system_id)):
            response_data = {
                "data":
                    [
                        service for service in resp.json()["data"]
                        if (system_name == service["provider"]["systemName"]
                        or system_id == service["provider"]["id"])
                    ]
            }
        else:
            response_data = resp.json()

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
