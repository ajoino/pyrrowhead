from pathlib import Path
from typing import List, Optional
import ipaddress

import yaml
import yamlloader  # type: ignore

from pyrrowhead.types_ import CloudDict, ClientSystemDict
from pyrrowhead.utils import (
    PyrrowheadError,
    check_valid_dns,
    validate_san,
    check_valid_ip,
)


def find_first_missing(ints: List[int], start: int, stop: int) -> int:
    for i in range(start, stop):
        if i not in set(ints):
            break

    return i


def add_client_system(
    config_file_path: Path,
    system_name: str,
    system_address: Optional[str],
    system_port: Optional[int],
    system_additional_addresses: Optional[List[str]],
):
    with open(config_file_path, "r") as config_file:
        cloud_config: CloudDict = yaml.load(
            config_file, Loader=yamlloader.ordereddict.CSafeLoader
        )["cloud"]

    if system_address is not None and check_valid_ip(system_address):
        addr = system_address
    elif system_address is not None:
        raise PyrrowheadError(
            f"System address '{system_address}' " f"is not a valid ip address."
        )
    else:
        addr = str(ipaddress.ip_network(cloud_config["subnet"])[1])

    if not check_valid_dns(system_name):
        raise PyrrowheadError(
            f"System name '{system_name}' " f"is not a valid dns string."
        )

    if system_additional_addresses is not None:
        for name in system_additional_addresses:
            validate_san(name)

    for sys in cloud_config.get("client_systems", {}).values():
        if (
            sys["system_name"] == system_name
            and sys["address"] == system_address
            and sys["port"] == system_port
        ):
            raise PyrrowheadError(
                f'Client system with name "{system_name}", '
                f"address {system_address}, and port {system_address} already exists"
            )

    taken_ports = [
        sys["port"]
        for sys in cloud_config.get("client_systems", {}).values()
        if sys["address"] == addr
    ]
    if system_port is None or system_port in taken_ports:
        port = find_first_missing(taken_ports, 5000, 8000)
    else:
        port = system_port

    id = (
        system_name
        + "-"
        + str(
            len(
                tuple(
                    sys
                    for sys in cloud_config["client_systems"].values()
                    if sys["system_name"] == system_name
                )
            )
        ).rjust(3, "0")
    )

    system_dict: ClientSystemDict = {
        "system_name": system_name,
        "address": addr,
        "port": port,
        "sans": [],
    }

    if system_additional_addresses is not None:
        system_dict["sans"] = system_additional_addresses

    cloud_config["client_systems"][id] = system_dict

    with open(config_file_path, "w") as config_file:
        yaml.dump(
            {"cloud": cloud_config},
            config_file,
            Dumper=yamlloader.ordereddict.CSafeDumper,
        )
