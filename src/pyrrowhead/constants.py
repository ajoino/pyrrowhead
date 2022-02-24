from pathlib import Path

import typer

ENV_PYRROWHEAD_DIRECTORY = 'PYRROWHEAD_INSTALL_DIRECTORY'
ENV_PYRROWHEAD_ACTIVE_CLOUD = 'PYRROWHEAD_ACTIVE_CLOUD'
APP_NAME = 'pyrrowhead'
LOCAL_CLOUDS_SUBDIR = 'local-clouds'
CLOUD_CONFIG_FILE_NAME = 'cloud_config.yaml'
CONFIG_FILE = 'config.cfg'


def get_local_cloud_directory() -> Path:
    return get_pyrrowhead_path().joinpath(LOCAL_CLOUDS_SUBDIR)


OPT_CLOUDS_DIRECTORY = typer.Option(
        None,
        '--dir',
        '-d',
        callback=get_local_cloud_directory,
        help='Directory of local cloud. Should only be used when a local cloud is installed outside the default path.',
)
ARG_CLOUD_IDENTIFIER = typer.Argument(
        None,
        help=
'''
Cloud identifier string of format <CLOUD_NAME>.<ORG_NAME>.
Mutually exclusive with options -c and -o.
''',
)
OPT_CLOUD_NAME = typer.Option(None, '--cloud', '-c', help='CLOUD_NAME. Mandatory with option -o and mutually exclusive with argument CLOUD_IDENTIFIER')
OPT_ORG_NAME = typer.Option(None, '--org', '-o', help='ORG_NAME. Mandatory with option -c and mutually exclusive with argument CLOUD_IDENTIFIER')


def get_pyrrowhead_path() -> Path:
    return Path(typer.get_app_dir(APP_NAME, force_posix=True))