from pathlib import Path
from typing import Optional, List, Tuple, Callable
from functools import wraps

import typer

from pyrrowhead import rich_console
from pyrrowhead.cloud.installation import install_cloud, uninstall_cloud
from pyrrowhead.cloud.create import CloudConfiguration, create_cloud_config
from pyrrowhead.cloud.start import start_local_cloud
from pyrrowhead.cloud.stop import stop_local_cloud
from pyrrowhead.cloud.configuration import enable_ssl as enable_ssl_func
from pyrrowhead.cloud.client_add import add_client_system
from pyrrowhead.utils import (
    switch_directory,
    set_active_cloud as set_active_cloud_func,
    get_config,
    check_valid_dns,
    PyrrowheadError,
)
from pyrrowhead.constants import (
    OPT_CLOUDS_DIRECTORY,
    OPT_CLOUD_NAME,
    OPT_ORG_NAME,
    ARG_CLOUD_IDENTIFIER,
    CLOUD_CONFIG_FILE_NAME,
)

cloud_app = typer.Typer(
    name="cloud",
    help="Used to set up, configure, start, and stop local clouds using "
    "the appropriate subcommand. See list below.",
)


def print_pyrrowhead_error(func: Callable[..., None]) -> Callable[..., None]:
    @wraps(func)
    def decorator(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except PyrrowheadError as e:
            rich_console.print(e)
            raise typer.Exit(-1)

    return decorator


def decide_cloud_directory(
    cloud_identifier: Optional[str],
    cloud_name: Optional[str],
    organization_name: Optional[str],
    clouds_directory: Path,
) -> Tuple[Path, str]:
    if cloud_identifier and any((cloud_name, organization_name)):
        rich_console.print(
            "CLOUD_IDENTIFIER and [CLOUD_NAME and ORG_NAME] are " "mutually exclusive."
        )
        raise typer.Exit(-1)
    if (
        cloud_identifier is not None
        and len(split_cloud_identifier := cloud_identifier.split(".")) == 2
    ):
        ret = (
            clouds_directory.joinpath(
                *[part for part in reversed(split_cloud_identifier)]
            ),
            cloud_identifier,
        )
    elif cloud_name is not None and organization_name is not None:
        ret = (
            clouds_directory.joinpath(organization_name, cloud_name),
            f"{cloud_name}.{organization_name}",
        )
    else:
        rich_console.print(
            "Could not decide local cloud. "
            "Did you forget to provide CLOUD_NAME or ORG_NAME?"
        )
        raise typer.Exit(-1)

    if not ret[0].exists():
        rich_console.print(f'Could not find local cloud "{ret[1]}"')
        raise typer.Exit(-1)

    return ret


@cloud_app.command()
@print_pyrrowhead_error
def configure(
    cloud_identifier: str = ARG_CLOUD_IDENTIFIER,
    cloud_name: Optional[str] = OPT_CLOUD_NAME,
    organization_name: Optional[str] = OPT_ORG_NAME,
    clouds_directory: Path = OPT_CLOUDS_DIRECTORY,
    enable_ssl: Optional[bool] = typer.Option(None, "--enable-ssl/--disable-ssl"),
):
    """
    Statically configures an existing local cloud.

    The local cloud needs to be reinstalled after being configured
    to make sure the changes are applied.
    """
    target, cloud_identifier = decide_cloud_directory(
        cloud_identifier,
        cloud_name,
        organization_name,
        clouds_directory,
    )
    with switch_directory(target):
        if enable_ssl is not None:
            enable_ssl_func(enable_ssl)


@cloud_app.command()
@print_pyrrowhead_error
def list(
    # organization_filter: str = typer.Option('', '--organization', '-o'),
):
    """
    Lists all local clouds.
    """
    config = get_config()

    for cloud_identifier, directory in config["local-clouds"].items():
        if not Path(directory).exists():
            rich_console.print(cloud_identifier, "Path does not exist", style="red")
        else:
            rich_console.print(cloud_identifier, directory)


@cloud_app.command()
@print_pyrrowhead_error
def install(
    cloud_identifier: str = ARG_CLOUD_IDENTIFIER,
    cloud_name: Optional[str] = OPT_CLOUD_NAME,
    organization_name: Optional[str] = OPT_ORG_NAME,
    cloud_directory: Path = OPT_CLOUDS_DIRECTORY,
):
    """
    Installs cloud by creating certificate files and core service configuration files.

    CLOUD_NAME and ORG_name are the cloud and organization names used in the generated certificates.
    """  # noqa
    target, cloud_identifier = decide_cloud_directory(
        cloud_identifier,
        cloud_name,
        organization_name,
        cloud_directory,
    )

    config_file = target / CLOUD_CONFIG_FILE_NAME

    install_cloud(config_file, target)


@cloud_app.command()
@print_pyrrowhead_error
def uninstall(
    cloud_identifier: str = ARG_CLOUD_IDENTIFIER,
    cloud_name: Optional[str] = OPT_CLOUD_NAME,
    organization_name: Optional[str] = OPT_ORG_NAME,
    clouds_directory: Path = OPT_CLOUDS_DIRECTORY,
    complete: bool = typer.Option(
        False,
        "--complete",
        help="Completely removes all files, including cloud_config.yaml",
    ),
    # keep_root: bool = typer.Option(False, '--keep-root', ),
):
    """
    Uninstalls cloud by removing certificate files and core service configuration files.
    Keeps the cloud_config.yaml file by default.

    CLOUD_NAME and ORG_name are the cloud and organization names used in the generated certificates.
    """  # noqa
    target, cloud_identifier = decide_cloud_directory(
        cloud_identifier,
        cloud_name,
        organization_name,
        clouds_directory,
    )

    stop_local_cloud(target)
    uninstall_cloud(target, complete)


@cloud_app.command()
@print_pyrrowhead_error
def create(
    cloud_identifier: Optional[str] = ARG_CLOUD_IDENTIFIER,
    cloud_name: Optional[str] = OPT_CLOUD_NAME,
    organization_name: Optional[str] = OPT_ORG_NAME,
    installation_target: Path = OPT_CLOUDS_DIRECTORY,
    ip_network: str = typer.Option(
        "172.16.1.0/24",
        metavar="IP",
        help="IP network the docker network uses to run the local clouds",
    ),
    core_san: Optional[List[str]] = typer.Option(
        None,
        "--san",
        metavar="SUBJECT_ALTERNATIVE_NAME",
        help="Subject alternative names to include in the core system certificates."
        " An example is the IP-address of the device the core systems are running"
        " on. IPs should be prefixed with 'ip:' and DNS strings prefixed "
        "with 'dns:', for example ip:127.0.0.1 and dns:host123.example-org.com",
    ),
    ssl_enabled: Optional[bool] = typer.Option(
        True,
        "--ssl-enabled/--ssl-disabled",
        show_default=False,
        help="Enabled/disable local cloud security. Enabled by default. "
        "SSL rarely be disabled.",
    ),
    do_install: bool = typer.Option(
        False, "--install", help="Install local cloud after running the setup command."
    ),
    include: Optional[List[CloudConfiguration]] = typer.Option(
        [],
        case_sensitive=False,
        help="Core systems to include apart from the mandatory core systems. "
        "--include eventhandler includes the eventhandler. "
        "--include intercloud includes the gateway and gatekeeper. "
        "--include onboarding includes the system and device registry, "
        "certificate authority and onboarding systems.",
    ),
):
    """
    Sets up local clouds by creating a folder structure and cloud_config.yaml file.

    CLOUD_NAME and ORG_name are the cloud and organization names used in the generated certificates.
    """  # noqa
    if not cloud_identifier and not cloud_name and not organization_name:
        rich_console.print(
            "You must either provide the 'CLOUD_IDENTIFIER' argument or both the "
            "'CLOUD_NAME' and 'ORG_NAME' options."
        )
        raise typer.Exit(-1)
    if (
        cloud_identifier is None
        and cloud_name is not None
        and organization_name is not None
    ):
        cloud_identifier = ".".join((cloud_name, organization_name))
    elif cloud_identifier is not None:
        cloud_name, organization_name = cloud_identifier.split(".")
    else:
        rich_console.print(
            "CLOUD_IDENTIFIER, or CLOUD_NAME or ORG_NAME are of unknown types."
        )
        raise typer.Exit(-1)

    if not check_valid_dns(cloud_identifier):
        rich_console.print(f'"{cloud_identifier}" is not a valid cloud identifier')
        raise typer.Exit(-1)

    create_cloud_config(
        target_directory=installation_target,
        cloud_identifier=cloud_identifier,
        cloud_name=cloud_name,
        organization_name=organization_name,
        ssl_enabled=ssl_enabled,
        ip_subnet=ip_network,
        core_san=core_san,
        do_install=do_install,
        include=include,
    )


@cloud_app.command()
@print_pyrrowhead_error
def up(
    cloud_identifier: str = ARG_CLOUD_IDENTIFIER,
    cloud_name: Optional[str] = OPT_CLOUD_NAME,
    organization_name: Optional[str] = OPT_ORG_NAME,
    clouds_directory: Path = OPT_CLOUDS_DIRECTORY,
    set_active_cloud: bool = typer.Option(
        True,
        " /--no-set-active",
        " /-N",
        show_default=False,
        help="Does not set this cloud as the active cloud, "
        "useful if you want to start another cloud in the background.",
    ),
):
    """
    Starts local cloud core system docker containers.

    If this command fails during the mysql startup, it might be because you are running
    another mysql instance on port 3306. You must either terminate that service (e.g. running
    `systemctl stop mysql.service`) or change the port of mysql in the configuration and reinstall
    the local cloud before starting it again.

    This command might take a while if this is the first time starting a local cloud on this machine
    as docker needs to pull the images.
    """  # noqa
    target, cloud_identifier = decide_cloud_directory(
        cloud_identifier,
        cloud_name,
        organization_name,
        clouds_directory,
    )
    try:
        start_local_cloud(target)
        if set_active_cloud:
            set_active_cloud_func(cloud_identifier)
    except KeyboardInterrupt:
        stop_local_cloud(target)
        raise typer.Abort()


@cloud_app.command()
@print_pyrrowhead_error
def down(
    cloud_identifier: str = ARG_CLOUD_IDENTIFIER,
    cloud_name: Optional[str] = OPT_CLOUD_NAME,
    organization_name: Optional[str] = OPT_ORG_NAME,
    clouds_directory: Path = OPT_CLOUDS_DIRECTORY,
):
    """
    Shuts down local cloud.
    """
    target, cloud_identifier = decide_cloud_directory(
        cloud_identifier,
        cloud_name,
        organization_name,
        clouds_directory,
    )
    stop_local_cloud(target)
    set_active_cloud_func("")


@cloud_app.command(name="client-add")
@print_pyrrowhead_error
def system(
    cloud_identifier: str = ARG_CLOUD_IDENTIFIER,
    cloud_name: Optional[str] = OPT_CLOUD_NAME,
    organization_name: Optional[str] = OPT_ORG_NAME,
    clouds_directory: Path = OPT_CLOUDS_DIRECTORY,
    system_name: str = typer.Option(
        ..., "--name", "-n", metavar="SYSTEM_NAME", help="System name"
    ),
    system_address: Optional[str] = typer.Option(
        None, "--addr", "-a", metavar="ADDRESS", help="System address"
    ),
    system_port: Optional[int] = typer.Option(
        None, "--port", "-p", metavar="PORT", help="System port"
    ),
    system_addl_addr: Optional[List[str]] = typer.Option(
        None,
        "--san",
        "-s",
        metavar="SAN",
        help="Client subject alternative name.",
    ),
):
    """
    Adds system to the cloud configuration.
    """
    target, cloud_identifier = decide_cloud_directory(
        cloud_identifier,
        cloud_name,
        organization_name,
        clouds_directory,
    )

    config_file = target / "cloud_config.yaml"

    add_client_system(
        config_file,
        system_name,
        system_address,
        system_port,
        system_addl_addr,
    )
