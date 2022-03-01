import shutil
import subprocess

import typer
import yaml
import yamlloader
from rich.text import Text

from pyrrowhead.cloud.file_generators import generate_all_files
from pyrrowhead.cloud.initialize_cloud import initialize_cloud
from pyrrowhead import rich_console
from pyrrowhead.utils import get_config, set_config


def install_cloud(config_file_path, installation_target):
    if config_file_path.suffix not in {".yaml", ".yml"}:
        raise typer.BadParameter("Configuration file must end with .yaml or .yml")
    elif not config_file_path.is_file():
        raise typer.BadParameter("Configuration file does not exist")

    with open(config_file_path, "r") as config_file:
        try:
            cloud_config = yaml.load(
                config_file, Loader=yamlloader.ordereddict.CSafeLoader
            )["cloud"]
        except (TypeError, KeyError):
            raise typer.BadParameter("Malformed configuration file")

    with rich_console.status(Text("Installing an Arrowhead local cloud...")):
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
    if not (installation_target / "cloud_config.yaml").exists():
        typer.BadParameter(
            f"{installation_target} does not contain an Arrowhead local cloud."
        )

    with open(installation_target / "cloud_config.yaml") as config_file:
        cloud_config = yaml.load(
            config_file, Loader=yamlloader.ordereddict.CSafeLoader
        )["cloud"]

    cloud_name = cloud_config["cloud_name"]
    org_name = cloud_config["organization_name"]

    if complete:
        # shutil.rmtree(installation_target)
        config = get_config()

        del config["local-clouds"][f"{cloud_name}.{org_name}"]
        set_config(config)
    else:
        if not keep_sysop:
            shutil.rmtree(installation_target / f"certs")
        else:
            # TODO: Code that deletes everything except the sysop.* files
            pass
        shutil.rmtree(installation_target / "core_system_config")
        shutil.rmtree(installation_target / "sql")
        (installation_target / "docker-compose.yml").unlink()
        (installation_target / "initSQL.sh").unlink()
    subprocess.run(["docker", "volume", "rm", f"mysql.{cloud_name}.{org_name}"])
    rich_console.print("Uninstallation complete")
    raise typer.Exit()
