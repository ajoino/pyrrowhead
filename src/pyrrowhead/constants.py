import typer

from pyrrowhead.utils import get_local_cloud_directory

# String constants
ENV_PYRROWHEAD_DIRECTORY = "PYRROWHEAD_INSTALL_DIRECTORY"
ENV_PYRROWHEAD_ACTIVE_CLOUD = "PYRROWHEAD_ACTIVE_CLOUD"
APP_NAME = "pyrrowhead"
LOCAL_CLOUDS_SUBDIR = "local-clouds"
CLOUD_CONFIG_FILE_NAME = "cloud_config.yaml"
CONFIG_FILE = "config.cfg"
ORG_CERT_DIR = "org-certs"
ROOT_CERT_DIR = "root-certs"

# Typer constants
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
)
ARG_ORG_NAME = typer.Argument(
    None,
    help="""
    Organization name.
    """,
)
OPT_CLOUD_NAME = typer.Option(
    None,
    "--cloud",
    "-c",
    help="CLOUD_NAME. Mandatory with option -o and "
    "mutually exclusive with argument CLOUD_IDENTIFIER",
)
OPT_ORG_NAME = typer.Option(
    None,
    "--org",
    "-o",
    help="ORG_NAME. Mandatory with option -c and "
    "mutually exclusive with argument CLOUD_IDENTIFIER",
)
