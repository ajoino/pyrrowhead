from pathlib import Path

from typer.testing import CliRunner
from pyrrowhead.main import app

def run_cloud_setup(cloud_identifier: str):
    return CliRunner().invoke(app, ["cloud", "setup", cloud_identifier])