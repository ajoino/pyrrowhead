import shutil
import subprocess
from typing import Optional, Callable

import typer
from rich.text import Text

from pyrrowhead.cloud.file_generators import generate_all_files
from pyrrowhead.cloud.initialize_cloud import initialize_cloud
from pyrrowhead import rich_console
from pyrrowhead.utils import (
    get_config,
    set_config,
    validate_cloud_config_file,
)
from pyrrowhead.constants import CLOUD_CONFIG_FILE_NAME


def install_cloud(config_file_path, installation_target, password):
    cloud_config = validate_cloud_config_file(config_file_path)

    with rich_console.status(Text("Installing Arrowhead local cloud...")):
        generate_all_files(
            cloud_config, config_file_path, installation_target, password
        )
        initialize_cloud(
            installation_target,
            cloud_config["cloud_name"],
            cloud_config["organization_name"],
            password=password,
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


def password_option(name: str, callback: Optional[Callable] = None) -> typer.Option:
    typer.Option(
        "123456",
        prompt=True,
        confirmation_prompt=True,
        hide_input=True,
        prompt_required=False,
        help=f"Password for {name} certificates. Defaults to '123456' if not set",
        callback=callback,
    ),


def org_callback(ctx: typer.Context, password: str) -> str:
    pass
