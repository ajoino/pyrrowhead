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
from pyrrowhead.types_ import ConfigDict, CloudDict, ClientSystemDict
from pyrrowhead.constants import CLOUD_CONFIG_FILE_NAME
from pyrrowhead.utils import PyrrowheadError


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

    if system_address is None:
        addr = str(ipaddress.ip_network(cloud_config["subnet"])[1])
    else:
        addr = system_address

    taken_ports = [
        sys["port"]
        for sys in cloud_config.get("client_systems").values()
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

    for sys in cloud_config.get("client_systems").values():
        if (
            sys["system_name"] == system_name
            and sys["address"] == addr
            and sys["port"] == port
        ):
            raise ValueError(
                f'Client system with name "{system_name}", address {addr}, and port {port} already exists'
            )

    system_dict: ClientSystemDict = {
        "system_name": system_name,
        "address": addr,
        "port": port,
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
