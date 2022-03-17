import typer

# String constants
ENV_PYRROWHEAD_DIRECTORY = "PYRROWHEAD_INSTALL_DIRECTORY"
ENV_PYRROWHEAD_ACTIVE_CLOUD = "PYRROWHEAD_ACTIVE_CLOUD"
APP_NAME = "pyrrowhead"
LOCAL_CLOUDS_SUBDIR = "local-clouds"
CLOUD_CONFIG_FILE_NAME = "cloud_config.yaml"
CONFIG_FILE = "config.cfg"
ORG_CERT_DIR = "org_certs"
ROOT_CERT_DIR = "root_certs"

# Typer constants
ARG_ORG_NAME = typer.Argument(
    None,
    help="""
    Organization name.
    """,
)
