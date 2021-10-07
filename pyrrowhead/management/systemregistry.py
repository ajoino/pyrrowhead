from typing import Optional
from pathlib import Path

from rich import box
from rich.table import Table, Column

from pyrrowhead.management.utils import get_service, post_service, delete_service
from pyrrowhead.utils import get_core_system_address_and_port, get_active_cloud_directory


def list_systems():
    active_cloud_directory = get_active_cloud_directory()
    address, port, secure, scheme = get_core_system_address_and_port(
            'service_registry',
            active_cloud_directory,
    )
    scheme = 'https' if secure else 'http'
    response = get_service(
            f'{scheme}://{address}:{port}/serviceregistry/mgmt/systems',
            active_cloud_directory,
    )
    response_data, status = response.json(), response.status_code
    return response_data, status


def add_system(
        system_name: str,
        system_address: str,
        system_port: int,
        certificate_file: Optional[Path] = None,
):
    active_cloud_directory = get_active_cloud_directory()
    address, port, secure, scheme = get_core_system_address_and_port(
            'service_registry',
            active_cloud_directory,
    )

    system_record = {
        "systemName": system_name,
        "address": system_address,
        "port": system_port,
    }

    response_data = post_service(
            f'{scheme}://{address}:{port}/serviceregistry/mgmt/systems',
            active_cloud_directory,
            json=system_record,
    ).json()

    return response_data


def remove_system(system_id: int):
    active_cloud_directory = get_active_cloud_directory()
    address, port, secure, scheme = get_core_system_address_and_port(
            'service_registry',
            active_cloud_directory,
    )

    response = delete_service(
            f'{scheme}://{address}:{port}/serviceregistry/mgmt/systems/{system_id}',
            active_cloud_directory,
    )

    return response.json(), response.status_code


def create_system_table(response):
    system_data = response

    system_table = Table(
            Column(header='id', style='red'),
            Column(header='System name', style='blue'),
            Column(header='Address', style='purple'),
            Column(header='Port', style='bright_white'),
            title='Registered systems',
            box=box.SIMPLE,
    )

    for system in system_data['data']:
        system_table.add_row(
            str(system["id"]),
            system["systemName"],
            system["address"],
            str(system["port"]),
        )

    return system_table