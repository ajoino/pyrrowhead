from pathlib import Path
import json
from typing import List, Optional
import ipaddress
import hashlib
from collections import OrderedDict

import typer
import yaml
import yamlloader
from rich.text import Text
from rich.syntax import Syntax

from pyrrowhead import rich_console
from pyrrowhead.types import ConfigDict, CloudDict
from pyrrowhead.constants import CLOUD_CONFIG_FILE_NAME


def find_first_missing(ints: List[int], start: int, stop: int) -> int:
    for i in range(start, stop):
        if i not in set(ints):
            break

    return i


def add_system(
    config_file_path: Path,
    system_name: str,
    system_address: Optional[str],
    system_port: Optional[int],
    system_additional_addresses: Optional[List[str]],
):
    with open(config_file_path, "r") as config_file:
        try:
            cloud_config: CloudDict = yaml.load(
                config_file, Loader=yamlloader.ordereddict.CSafeLoader
            )["cloud"]
        except (TypeError, KeyError):
            raise RuntimeError("Malformed configuration file")

    if system_name == cloud_config["cloud_name"]:
        raise ValueError(
            "Systems cannot share name with cloud.\nThis is a pyrrowhead restriction due to how the certificate files are named."
        )

    if system_address is None:
        addr = str(ipaddress.ip_network(cloud_config["subnet"])[1])
    else:
        addr = system_address

    id = system_name
    port = system_port

    if (client_systems := cloud_config["client_systems"]) is not None:
        taken_ports = [
            sys["port"]
            for sys in cloud_config["client_systems"].values()
            if sys["address"] == addr and sys["system_name"] == system_name
        ]

        if system_name in client_systems:
            id += "-" + str(
                len(
                    tuple(
                        sys
                        for sys in cloud_config["client_systems"].values()
                        if sys["system_name"] == system_name
                    )
                )
            ).rjust(3, "0")

        if system_port is None or system_port not in taken_ports:
            port = find_first_missing(taken_ports, 5000, 8000)

        for sys in client_systems.values():
            if (
                sys["system_name"] == system_name
                and sys["address"] == addr
                and sys["port"] == port
            ):
                raise ValueError(
                    f'Client system with name "{system_name}", address {addr}, and port {port} already exists'
                )

    system_dict = {
        "system_name": system_name,
        "address": addr,
        "port": port,
        "domain": system_additional_addresses,
    }

    if cloud_config["client_systems"] is None:
        cloud_config["client_systems"] = {}

    cloud_config["client_systems"][id] = system_dict
    cloud_config["client_systems"] = {
        key: cloud_config["client_systems"][key]
        for key in sorted(cloud_config["client_systems"])
    }

    config_dict: ConfigDict = {"cloud": cloud_config}

    with open(config_file_path, "w") as config_file:
        yaml.dump(config_dict, config_file, Dumper=yamlloader.ordereddict.CSafeDumper)
