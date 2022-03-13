import os
from pathlib import Path
from contextlib import contextmanager
from typing import Tuple, Optional
import configparser
from ipaddress import ip_address

import typer
import yaml
import yamlloader

from pyrrowhead.types_ import CloudDict


class PyrrowheadError(Exception):
    pass


def get_config() -> configparser.ConfigParser:
    from pyrrowhead.constants import CONFIG_FILE

    config = configparser.ConfigParser()
    with open(get_pyrrowhead_path() / CONFIG_FILE, "r") as config_file:
        config.read_file(config_file)

    return config


def set_config(config: configparser.ConfigParser):
    from pyrrowhead.constants import CONFIG_FILE

    with open(get_pyrrowhead_path().joinpath(CONFIG_FILE), "w") as config_file:
        config.write(config_file)


@contextmanager
def switch_directory(path: Path):
    origin = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)


def set_active_cloud(cloud_identifier):
    config = get_config()

    config["pyrrowhead"]["active-cloud"] = cloud_identifier

    set_config(config)


def get_active_cloud_directory() -> Path:
    config = get_config()

    active_cloud_identifier = config["pyrrowhead"]["active-cloud"]

    active_cloud_directory = config["local-clouds"][active_cloud_identifier]

    return Path(active_cloud_directory)


def get_core_system_address_and_port(
    core_system: str, cloud_directory: Path
) -> Tuple[str, int, bool, str]:
    from pyrrowhead.constants import CLOUD_CONFIG_FILE_NAME

    with open(cloud_directory / CLOUD_CONFIG_FILE_NAME, "r") as cloud_config_file:
        cloud_config = yaml.safe_load(cloud_config_file)
    address = cloud_config["cloud"]["core_systems"][core_system]["address"]
    port = cloud_config["cloud"]["core_systems"][core_system]["port"]
    secure = cloud_config["cloud"]["ssl_enabled"]
    scheme = "https" if secure else "http"

    return address, port, secure, scheme


def get_local_cloud_directory(dir: Optional[Path] = None) -> Path:
    from pyrrowhead.constants import LOCAL_CLOUDS_SUBDIR

    if dir is not None:
        print("The '-d' option is currently not in use.")
        raise typer.Exit(-1)

    return get_pyrrowhead_path().joinpath(LOCAL_CLOUDS_SUBDIR)


def get_pyrrowhead_path() -> Path:
    from pyrrowhead.constants import APP_NAME

    return Path(typer.get_app_dir(APP_NAME))


def validate_san(san_candidate: str):
    if not (san_candidate.startswith("dns:") or san_candidate.startswith("ip:")):
        raise PyrrowheadError(
            "Subject Alternative Name must start with either 'ip:' or 'dns:'"
        )
    elif san_candidate.startswith("ip:"):
        if not check_valid_ip(san_candidate[3:]):
            raise PyrrowheadError(f"Malformed san ip: '{san_candidate}'")
    else:
        # san_candidate.startswith("dns:"):
        if not check_valid_dns(san_candidate[4:]):
            raise PyrrowheadError(f"Malformed san dns: '{san_candidate}'")


def check_valid_ip(ip_candidate: str):
    try:
        ip_address(ip_candidate)
        return True
    except ValueError:
        return False


def check_valid_dns(identifier: str):
    import re

    identifier_re = re.compile(
        r"^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)"
        r"*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$"
    )

    return identifier_re.search(identifier) is not None


def validate_cloud_config_file(config_file_path: Path) -> CloudDict:
    if not config_file_path.is_file():
        raise PyrrowheadError(
            "Target cloud is not set up properly,"
            " run `pyrrowhead cloud create` before installing cloud."
        )

    with open(config_file_path, "r") as config_file:
        try:
            cloud_config: Optional[CloudDict] = yaml.load(
                config_file, Loader=yamlloader.ordereddict.CSafeLoader
            ).get("cloud")
        except AttributeError:
            raise PyrrowheadError(
                "Malformed configuration file: " "Could not load YAML document"
            )

    if cloud_config is None:
        raise PyrrowheadError(
            "Malformed cloud configuration file: Missing cloud information."
        )
    elif set(cloud_config.keys()) != set(CloudDict.__annotations__.keys()):
        raise PyrrowheadError("Malformed configuration file:" "Missing cloud key(s)")

    return cloud_config
