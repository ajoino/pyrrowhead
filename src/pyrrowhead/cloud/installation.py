import shutil
import subprocess
from pathlib import Path
from typing import Optional

import yaml
import yamlloader  # type: ignore
from rich.text import Text

from pyrrowhead.cloud.file_generators import generate_all_files
from pyrrowhead.cloud.initialize_cloud import initialize_cloud
from pyrrowhead import rich_console
from pyrrowhead.types_ import CloudDict
from pyrrowhead.utils import (
    get_config,
    set_config,
    PyrrowheadError,
    validate_cloud_config,
)
from pyrrowhead.constants import CLOUD_CONFIG_FILE_NAME


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
    elif not validate_cloud_config(cloud_config):
        raise PyrrowheadError("Malformed configuration file:" "Missing cloud key(s)")

    return cloud_config


def install_cloud(config_file_path, installation_target):
    cloud_config = validate_cloud_config_file(config_file_path)

    with rich_console.status(Text("Installing Arrowhead local cloud...")):
        generate_all_files(cloud_config, config_file_path, installation_target)
        initialize_cloud(
            installation_target,
            cloud_config["cloud_name"],
            cloud_config["organization_name"],
        )
    rich_console.print("Finished installing the [blue]Arrowhead[/blue] local cloud!")


def uninstall_cloud(
    installation_target, complete=False, keep_root=False, keep_sysop=False
):
    config_path = installation_target / CLOUD_CONFIG_FILE_NAME

    cloud_config = validate_cloud_config_file(config_path)

    cloud_name = cloud_config["cloud_name"]
    org_name = cloud_config["organization_name"]

    if complete:
        # shutil.rmtree(installation_target)
        config = get_config()

        del config["local-clouds"][f"{cloud_name}.{org_name}"]
        set_config(config)
    else:
        if not keep_sysop:
            shutil.rmtree(installation_target / "certs")
        else:
            # TODO: Code that deletes everything except the sysop.* files
            pass
        shutil.rmtree(installation_target / "core_system_config")
        shutil.rmtree(installation_target / "sql")
        (installation_target / "docker-compose.yml").unlink()
        (installation_target / "initSQL.sh").unlink()
    subprocess.run(["docker", "volume", "rm", f"mysql.{cloud_name}.{org_name}"])
    rich_console.print("Uninstallation complete")
