import os
from pathlib import Path
from contextlib import contextmanager
from typing import Tuple

import typer
import yaml

from pyrrowhead import constants
from pyrrowhead.constants import APP_DIR, LOCAL_CLOUDS_SUBDIR, CLOUD_CONFIG_FILE_NAME

clouds_directory = typer.Argument(APP_DIR / LOCAL_CLOUDS_SUBDIR, envvar=[constants.ENV_PYRROWHEAD_DIRECTORY])

@contextmanager
def switch_directory(path: Path):
    origin = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)

def set_active_cloud(cloud_identifier):
    with open(APP_DIR / 'active_cloud', "w") as active_cloud_file:
        active_cloud_file.write(cloud_identifier)


def get_active_cloud_directory() -> Path:
    with open(APP_DIR / 'active_cloud', "r") as active_cloud_file:
        cloud_name, org_name = active_cloud_file.read().split('.')

    return APP_DIR / LOCAL_CLOUDS_SUBDIR / org_name / cloud_name

def get_core_system_address_and_port(core_system: str, cloud_directory: Path) -> Tuple[str, int]:
    with open(cloud_directory / CLOUD_CONFIG_FILE_NAME, 'r') as cloud_config_file:
        cloud_config = yaml.safe_load(cloud_config_file)
    address = cloud_config["cloud"]["core_systems"][core_system]["address"]
    port = cloud_config["cloud"]["core_systems"][core_system]["port"]

    return address, port

