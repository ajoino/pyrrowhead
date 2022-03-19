from pathlib import Path
from typing import Optional, List, Callable
from functools import wraps

import typer

from pyrrowhead import rich_console
from pyrrowhead.cloud.installation import (
    install_cloud,
    uninstall_cloud,
)
from pyrrowhead.cloud.create import CloudConfiguration, create_cloud_config
from pyrrowhead.cloud.run import start_local_cloud, stop_local_cloud
from pyrrowhead.cloud.configuration import enable_ssl as enable_ssl_func
from pyrrowhead.cloud.client_add import add_client_system
from pyrrowhead.utils import (
    switch_directory,
    set_active_cloud as set_active_cloud_func,
    get_config,
    PyrrowheadError,
    get_local_cloud_directory,
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


def cloud_name_callback(ctx: typer.Context, cloud_name: Optional[str]) -> str:
    if cloud_name is not None and cloud_name != "":
        if ctx.params.get("cloud_identifier") is not None:
            rich_console.print(
                "CLOUD_IDENTIFIER and the CLOUD_NAME and"
                " ORG_NAME options are mutually exclusive."
            )
            raise typer.Exit(-1)
        return cloud_name
    elif ctx.params.get("cloud_identifier") is None:
        rich_console.print(
            "CLOUD_IDENTIFIER or CLOUD_NAME and" " ORG_NAME must be given."
        )
        raise typer.Exit(-1)

    cloud_name, _ = ctx.params.get("cloud_identifier").split(".")  # type: ignore
    return cloud_name  # type: ignore


def org_name_callback(ctx: typer.Context, org_name: Optional[str]) -> str:
    if org_name is not None and org_name != "":
        if ctx.params.get("cloud_identifier") is not None:
            rich_console.print(
                "CLOUD_IDENTIFIER and the CLOUD_NAME and "
                "ORG_NAME options are mutually exclusive."
            )
            raise typer.Exit(-1)
        return org_name
    elif ctx.params.get("cloud_identifier") is None:
        rich_console.print("CLOUD_IDENTIFIER or CLOUD_NAME and ORG_NAME must be given.")
        raise typer.Exit(-1)

    _, org_name = ctx.params.get("cloud_identifier").split(".")  # type: ignore
    return org_name  # type: ignore


OPT_CLOUD_NAME = typer.Option(
    None,
    "--cloud",
    "-c",
    help="CLOUD_NAME. Mandatory with option -o and "
    "mutually exclusive with argument CLOUD_IDENTIFIER",
    callback=cloud_name_callback,
)
OPT_ORG_NAME = typer.Option(
    None,
    "--org",
    "-o",
    help="ORG_NAME. Mandatory with option -c and "
    "mutually exclusive with argument CLOUD_IDENTIFIER",
    callback=org_name_callback,
)
OPT_CLOUDS_DIRECTORY = typer.Option(
    None,
    "--dir",
    "-d",
    callback=get_local_cloud_directory,
    hidden=True,
    help="Directory of local cloud. Experimental feature. "
    "Should only be used when a local cloud is "
    "installed outside the default path.",
)
ARG_CLOUD_IDENTIFIER = typer.Argument(
    None,
    help="""
Cloud identifier string of format <CLOUD_NAME>.<ORG_NAME>.
Mutually exclusive with options -c and -o.
""",
    is_eager=True,
)


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
    with switch_directory(clouds_directory):
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


def password_callback(password: str):
    if not len(password) >= 6:
        rich_console.print("Password must be at least 6 characters long.")
        raise typer.BadParameter("TEST")

    return password


def org_password_callback(ctx: typer.Context, password: Optional[str]):
    # TODO: replace with utils.get_names_from_context
    cloud_identifier: str = ctx.params.get("cloud_identifier")  # type:ignore
    cloud_name: str = ctx.params.get("cloud_name")  # type:ignore
    org_name: str = ctx.params.get("organization_name")  # type:ignore
    cloud_directory: Path = ctx.params["cloud_directory"]
    if isinstance(cloud_identifier, str) and cloud_identifier != "":
        cloud_name, org_name = cloud_identifier.split(".")

    if (
        not cloud_directory.joinpath(org_name, "org-certs").is_dir()
        or password is not None
    ):
        return password

    forced_password = typer.prompt(
        "Organization certificates detected. Org cert password: ",
        hide_input=True,
        confirmation_prompt=True,
    )

    return forced_password


@cloud_app.command()
@print_pyrrowhead_error
def install(
    cloud_identifier: str = ARG_CLOUD_IDENTIFIER,
    cloud_name: Optional[str] = OPT_CLOUD_NAME,
    organization_name: Optional[str] = OPT_ORG_NAME,
    cloud_directory: Path = OPT_CLOUDS_DIRECTORY,
    cloud_password: str = typer.Option(
        "123456",
        metavar="CLOUD_PASSWORD",
        envvar="CLOUD_CERT_PASSWORD",
        prompt=True,
        confirmation_prompt=True,
        hide_input=True,
        prompt_required=False,
        help="Password for cloud certificates.",
        callback=password_callback,
    ),
    org_password: Optional[str] = typer.Option(
        "123456",
        metavar="ORG_PASSWORD",
        envvar="ORG_CERT_PASSWORD",
        prompt=True,
        confirmation_prompt=True,
        hide_input=True,
        prompt_required=False,
        help="Password for organization certificates.",
        callback=org_password_callback,
    ),
    root_password: Optional[str] = typer.Option(
        "123456",
        metavar="ROOT_PASSWORD",
        prompt=True,
        confirmation_prompt=True,
        hide_input=True,
        prompt_required=False,
        help="Password for root certificates.",
    ),
):
    """
    Installs cloud by creating certificate files and core service configuration files.

    CLOUD_NAME and ORG_name are the cloud and organization names used in the generated certificates.
    """  # noqa
    install_cloud(
        cloud_directory,
        cloud_password=cloud_password,
        org_password=org_password,
    )


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
    stop_local_cloud(clouds_directory)
    uninstall_cloud(clouds_directory, complete)


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

    create_cloud_config(
        target_directory=installation_target,
        cloud_name=cloud_name,
        org_name=organization_name,
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
    try:
        start_local_cloud(clouds_directory)
        if set_active_cloud:
            set_active_cloud_func(cloud_identifier)
    except KeyboardInterrupt:
        stop_local_cloud(clouds_directory)
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
    stop_local_cloud(clouds_directory)
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
    config_file = clouds_directory / "cloud_config.yaml"

    add_client_system(
        config_file,
        system_name,
        system_address,
        system_port,
        system_addl_addr,
    )
