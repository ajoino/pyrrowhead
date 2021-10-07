from pyrrowhead.management.utils import get_service, post_service
from pyrrowhead.utils import get_core_system_address_and_port, get_active_cloud_directory


def list_authorization_rules():
    active_cloud_directory = get_active_cloud_directory()
    address, port, secure, scheme = get_core_system_address_and_port(
            'authorization',
            active_cloud_directory,
    )
    response = get_service(
            f'{scheme}://{address}:{port}/authorization/mgmt/intracloud',
            active_cloud_directory,
    )
    response_data = response.json()
    status = response.status_code
    return response_data, status


def add_authorization_rule(consumer_id: int, provider_id: int, interface_id: int, service_definition_id: int):
    active_cloud_directory = get_active_cloud_directory()
    address, port, secure, scheme = get_core_system_address_and_port(
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
            f'{scheme}://{address}:{port}/authorization/mgmt/intracloud/',
            active_cloud_directory,
            json=rule_message,
    )


def remove_authorization_rule():
    raise NotImplementedError