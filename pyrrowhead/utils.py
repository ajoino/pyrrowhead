import os
from pathlib import Path
from contextlib import contextmanager

import typer

from pyrrowhead import constants

APP_NAME = 'pyrrowhead'
APP_DIR = Path(typer.get_app_dir(APP_NAME))
clouds_directory = typer.Argument(APP_DIR / 'local-clouds', envvar=[constants.PYRROWHEAD_DIRECTORY])

@contextmanager
def switch_directory(path: Path):
    origin = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)