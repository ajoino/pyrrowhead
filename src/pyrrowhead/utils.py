import os
from pathlib import Path
from contextlib import contextmanager
from typing import Tuple
import configparser

import typer
import yaml

from pyrrowhead import constants
from pyrrowhead.constants import APP_DIR, LOCAL_CLOUDS_SUBDIR, CLOUD_CONFIG_FILE_NAME

def get_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    with open(APP_DIR / 'config.cfg', 'r') as config_file:
        config.read_file(config_file)

    return config

def set_config(config: configparser.ConfigParser) -> None:
    with open(APP_DIR / 'config.cfg', 'w') as config_file:
        config.write(config_file)

def get_local_cloud_directory(dir: str = '') -> str:
    if dir:
        return dir

    config = get_config()

    return config['pyrrowhead']['default-clouds-directory']

def get_local_cloud(cloud_name: str):
    config = get_config()

    return config['pyrrowhead']['local-clouds']



clouds_directory = typer.Option(None, '--dir', '-d', callback=get_local_cloud_directory, envvar=[constants.ENV_PYRROWHEAD_DIRECTORY])


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

    config['pyrrowhead']['active-cloud'] = cloud_identifier

    set_config(config)

def get_active_cloud_directory() -> Path:
    config = get_config()

    active_cloud_identifier = config['pyrrowhead']['active-cloud']

    active_cloud_directory = config['local-clouds'][active_cloud_identifier]

    return Path(active_cloud_directory)


def get_core_system_address_and_port(core_system: str, cloud_directory: Path) -> Tuple[str, int, bool, str]:
    with open(cloud_directory / CLOUD_CONFIG_FILE_NAME, 'r') as cloud_config_file:
        cloud_config = yaml.safe_load(cloud_config_file)
    address = cloud_config["cloud"]["core_systems"][core_system]["address"]
    port = cloud_config["cloud"]["core_systems"][core_system]["port"]
    secure = cloud_config["cloud"]["ssl_enabled"]
    scheme = 'https' if secure else 'http'

    return address, port, secure, scheme
