import shutil
import subprocess
from pathlib import Path

import typer
import yaml
import yamlloader

from pyrrowhead.installation.file_generators import generate_all_files
from pyrrowhead.installation.initialize_cloud import initialize_cloud


def install_cloud(cloud_config, config_file_path, installation_target):
    target = Path(installation_target) if installation_target else config_file_path.parent

    if config_file_path.suffix not in {'.yaml', '.yml'}:
        raise typer.BadParameter('Configuration file must end with .yaml or .yml')
    elif not config_file_path.is_file():
        raise typer.BadParameter('Configuration file does not exist')

    with open(config_file_path, 'r') as config_file:
        try:
            cloud_config = yaml.load(config_file, Loader=yamlloader.ordereddict.CSafeLoader)['cloud']
        except (TypeError, KeyError):
            raise typer.BadParameter('Malformed configuration file')
    print(f"Generating and copying files to {installation_target}.")
    generate_all_files(cloud_config, config_file_path, installation_target)
    print(f"Initializing cloud certificates and databases.")
    initialize_cloud(installation_target, cloud_config["cloud_name"])


def uninstall_cloud(installation_target, complete=False):
    if not (installation_target / 'cloud_config.yaml').exists():
        typer.BadParameter(f'{installation_target} does not contain an Arrowhead local cloud.')

    with open(installation_target / 'cloud_config.yaml') as config_file:
        cloud_config = yaml.load(config_file, Loader=yamlloader.ordereddict.CSafeLoader)["cloud"]

    cloud_name = cloud_config["cloud_name"]

    if complete:
        shutil.rmtree(installation_target)
    else:
        shutil.rmtree(installation_target / 'certgen')
        shutil.rmtree(installation_target / f'cloud-{cloud_name}')
        shutil.rmtree(installation_target / 'cloud-root')
        shutil.rmtree(installation_target / 'core_system_config')
        shutil.rmtree(installation_target / 'sql')
        (installation_target / 'docker-compose.yml').unlink()
        (installation_target / 'initSQL.sh').unlink()
    subprocess.run(['docker', 'volume', 'rm', f'mysql.{cloud_name}'])
    typer.Exit('Uninstallation complete')