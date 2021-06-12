from pathlib import Path

import typer

ENV_PYRROWHEAD_DIRECTORY = 'PYRROWHEAD_INSTALL_DIRECTORY'
ENV_PYRROWHEAD_ACTIVE_CLOUD = 'PYRROWHEAD_ACTIVE_CLOUD'
APP_NAME = 'pyrrowhead'
APP_DIR = Path(typer.get_app_dir(APP_NAME))
LOCAL_CLOUDS_SUBDIR = 'local-clouds'
CLOUD_CONFIG_FILE_NAME = 'cloud_config.yaml'