from collections import OrderedDict
from enum import Enum

import yaml
import yamlloader

from pyrrowhead.installation.installation import install_cloud


class CloudConfiguration(str, Enum):
    INTERCLOUD = "intercloud"
    EVENTHANDLER = "eventhandler"
    ONBOARDING = "onboarding"


def create_cloud_config(target_directory, cloud_name, company_name, ssl_enabled, ip_address, do_install, include):
    mandatory_core_systems = OrderedDict({
        "service_registry": {
            "system_name": "service_registry",
            "address": ip_address,
            "domain": "serviceregistry",
            "port": 8443,
        },
        "orchestrator": {
            "system_name": "orchestrator",
            "address": ip_address,
            "domain": "orchestrator",
            "port": 8441,
        },
        "authorization": {
            "system_name": "authorization",
            "address": ip_address,
            "domain": "authorization",
            "port": 8445,
        }
    })
    inter_cloud_core = OrderedDict({
        "gateway": {
            "system_name": "gateway",
            "address": ip_address,
            "domain": "gateway",
            "port": 8453,
        },
        "gatekeeper": {
            "system_name": "gatekeeper",
            "address": ip_address,
            "domain":  "gatekeeper",
            "port": 8449,
        }
    })
    event_handling_core = {
        "event_handler": {
            "system_name": "event_handler",
            "address": ip_address,
            "domain": "eventhandler",
            "port": 8455
        }
    }
    onboarding_core = OrderedDict({
        "system_registry": {},
        "device_registry": {},
        "onboarding_controller": {},
        "certificate_authority": {},
    })

    cloud_core_services = mandatory_core_systems
    if CloudConfiguration.EVENTHANDLER in include:
        cloud_core_services.update(event_handling_core)
    if CloudConfiguration.INTERCLOUD in include:
        cloud_core_services.update(inter_cloud_core)
    if CloudConfiguration.ONBOARDING in include:
        cloud_core_services.update(onboarding_core)
    cloud_config = {
        "cloud": OrderedDict({
            "cloud_name": cloud_name,
            "company_name": company_name,
            "ssl_enabled": ssl_enabled,

            "client_systems": None,
            "core_systems": cloud_core_services,
        })
    }

    with open(target_directory / 'cloud_config.yaml', 'w') as yaml_file:
        yaml.dump(cloud_config, yaml_file, Dumper=yamlloader.ordereddict.CSafeDumper)

    if do_install:
        install_cloud(target_directory / 'cloud_config.yaml', target_directory)
