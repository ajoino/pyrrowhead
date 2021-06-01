from pathlib import Path
from typing import Optional, Tuple, List

import typer

from pyrrowhead.installation.installation import install_cloud, uninstall_cloud
from pyrrowhead.installation.setup import create_cloud_config, CloudConfiguration
from pyrrowhead.configuration.setup import enable_ssl as enable_ssl_func

app = typer.Typer()


@app.command()
def configure(enable_ssl: Optional[bool] = typer.Option(None, '--enable-ssl/--disable-ssl')):
    if enable_ssl is not None:
        enable_ssl_func(enable_ssl)


@app.command()
def install(config_file: str, installation_target: Optional[str] = typer.Argument(None)):
    config_file_path = Path(config_file)
    target = Path(installation_target) if installation_target else config_file_path.parent

    install_cloud(config_file_path, target)


@app.command()
def uninstall(
        installation_target: str,
        complete: bool = typer.Option(False, '--complete'),
        keep_root: bool = typer.Option(False, '--keep-root'),
):
    uninstall_cloud(Path(installation_target), complete, keep_root)


@app.command()
def setup(
        installation_target: str,
        cloud_name: str,
        company_name: str,
        ip_address: str = typer.Option('127.0.0.1'),
        ssl_enabled: bool = typer.Option(True, '--ssl-enabled'),
        do_install: bool = typer.Option(False, '--install'),
        include: Optional[List[CloudConfiguration]] = typer.Option('', case_sensitive=False),
):
    create_cloud_config(
            Path(installation_target),
            cloud_name,
            company_name,
            ssl_enabled,
            ip_address,
            do_install,
            include,
    )



if __name__ == '__main__':
    app()

    # install_cloud(cloud_config, installation_target)
