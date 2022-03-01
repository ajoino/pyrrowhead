from pathlib import Path
from typing import Tuple
import configparser

import typer

from pyrrowhead import constants
from pyrrowhead import utils
from pyrrowhead.constants import APP_NAME, LOCAL_CLOUDS_SUBDIR, CONFIG_FILE


def _is_initialized(pyrrowhead_path: Path) -> Tuple[bool, bool, bool]:
    path_exists = pyrrowhead_path.is_dir()
    config_exists = pyrrowhead_path.joinpath(CONFIG_FILE).is_file()
    cloud_dir_exists = pyrrowhead_path.joinpath(LOCAL_CLOUDS_SUBDIR).is_dir()
    return path_exists, config_exists, cloud_dir_exists


def _setup_pyrrowhead():
    pyrrowhead_path = constants.get_pyrrowhead_path()
    config = configparser.ConfigParser()

    path_exists, config_exists, cloud_dir_exists = _is_initialized(pyrrowhead_path)

    if all((path_exists, config_exists, cloud_dir_exists)):
        return

    if not path_exists:
        print("Initializing pyrrowhead directory.")
        pyrrowhead_path.mkdir()
    if len(list(pyrrowhead_path.iterdir())) > 2:
        raise RuntimeError(
            "Pyrrowhead directory contains unknown objects, initialization aborted."
        )
    if not config_exists and not cloud_dir_exists:
        print("Initializing config file.")
        config[APP_NAME] = {}
        config[LOCAL_CLOUDS_SUBDIR] = {}
        utils.set_config(config)

        print("Initializing empty local cloud directory.")
        pyrrowhead_path.joinpath(LOCAL_CLOUDS_SUBDIR).mkdir()
    elif config_exists and not cloud_dir_exists:
        print("Initializing empty local cloud directory.")
        pyrrowhead_path.joinpath(LOCAL_CLOUDS_SUBDIR).mkdir()
    elif not config_exists and cloud_dir_exists:
        print("Initializing config file.")
        for org_path in pyrrowhead_path.joinpath(LOCAL_CLOUDS_SUBDIR).iterdir():
            for cloud_path in org_path.iterdir():
                config["local-clouds"][
                    ".".join((str(cloud_path.name), str(org_path.name)))
                ] = str(cloud_path.absolute())

        utils.set_config(config)

    print("Initialization completed.")
