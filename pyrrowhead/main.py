from pathlib import Path

import yaml
import yamlloader
import typer

from pyrrowhead.installation.installation import install_cloud, uninstall_cloud

app = typer.Typer()


@app.command()
def install(config_file: str, installation_target: str = typer.Argument(None)):
    config_file_path = Path(config_file)
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

    install_cloud(cloud_config, config_file_path, target)


@app.command()
def uninstall(installation_target: str, complete: bool = typer.Option(False, '--complete')):
    uninstall_cloud(Path(installation_target), complete)


if __name__ == '__main__':
    app()

    # install_cloud(cloud_config, installation_target)
