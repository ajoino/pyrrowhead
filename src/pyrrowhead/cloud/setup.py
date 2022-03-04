from pathlib import Path
from collections import OrderedDict
from enum import Enum
import ipaddress

import yaml
import yamlloader

from pyrrowhead.cloud.installation import install_cloud
from pyrrowhead.utils import get_config, set_config


class CloudConfiguration(str, Enum):
    INTERCLOUD = "intercloud"
    EVENTHANDLER = "eventhandler"
    ONBOARDING = "onboarding"


def create_cloud_config(
    target_directory: Path,
    cloud_identifier,
    cloud_name,
    organization_name,
    ssl_enabled,
    ip_subnet,
    do_install,
    include,
):
    network = ipaddress.ip_network(ip_subnet)
    mandatory_core_systems = OrderedDict(
        {
            "service_registry": {
                "system_name": "service_registry",
                "address": str(network[3]),
                "domain": "serviceregistry",
                "port": 8443,
            },
            "orchestrator": {
                "system_name": "orchestrator",
                "address": str(network[4]),
                "domain": "orchestrator",
                "port": 8441,
            },
            "authorization": {
                "system_name": "authorization",
                "address": str(network[5]),
                "domain": "authorization",
                "port": 8445,
            },
        }
    )
    inter_cloud_core = OrderedDict(
        {
            "gateway": {
                "system_name": "gateway",
                "domain": "gateway",
                "port": 8453,
            },
            "gatekeeper": {
                "system_name": "gatekeeper",
                "domain": "gatekeeper",
                "port": 8449,
            },
        }
    )
    event_handling_core = {
        "event_handler": {
            "system_name": "event_handler",
            "domain": "eventhandler",
            "port": 8455,
        }
    }
    onboarding_core = OrderedDict(
        {
            "system_registry": {
                "system_name": "system_registry",
                "domain": "systemregistry",
                "port": 8437,
            },
            "device_registry": {
                "system_name": "device_registry",
                "domain": "deviceregistry",
                "port": 8439,
            },
            "certificate_authority": {
                "system_name": "certificate_authority",
                "domain": "certificate-authority",
                "port": 8448,
            },
            "onboarding_controller": {
                "system_name": "onboarding_controller",
                "domain": "onboarding-controller",
                "port": 8435,
            },
        }
    )

    cloud_core_services = mandatory_core_systems
    ip_start = len(mandatory_core_systems) + 3
    if CloudConfiguration.EVENTHANDLER in include:
        cloud_core_services.update(insert_ips(event_handling_core, network, ip_start))
        ip_start += len(event_handling_core)
    if CloudConfiguration.INTERCLOUD in include:
        cloud_core_services.update(insert_ips(inter_cloud_core, network, ip_start))
        ip_start += len(inter_cloud_core)
    if CloudConfiguration.ONBOARDING in include:
        cloud_core_services.update(insert_ips(onboarding_core, network, ip_start))
        ip_start += len(onboarding_core)
    cloud_config = {
        "cloud": OrderedDict(
            {
                "cloud_name": cloud_name,
                "organization_name": organization_name,
                "ssl_enabled": ssl_enabled,
                "subnet": str(network),
                "client_systems": None,
                "core_systems": cloud_core_services,
            }
        )
    }

    target_directory = target_directory / f"{organization_name}/{cloud_name}"
    print(f"TEST CLOUD DIRECTORY: {target_directory}")

    if not target_directory.is_absolute():
        target_directory = target_directory.expanduser()

    if not target_directory.exists():
        Path.mkdir(target_directory, parents=True)

    with open(
        target_directory / "cloud_config.yaml",
        "w",
    ) as yaml_file:
        yaml.dump(cloud_config, yaml_file, Dumper=yamlloader.ordereddict.CSafeDumper)

    config = get_config()
    config["local-clouds"][cloud_identifier] = str(target_directory)

    set_config(config)

    if do_install:
        install_cloud(target_directory / "cloud_config.yaml", target_directory)


def insert_ips(system_dict, network, start):
    return {
        sys_name: {**sys_data, **{"address": str(network[i])}}
        for i, (sys_name, sys_data) in enumerate(system_dict.items(), start=start)
    }
