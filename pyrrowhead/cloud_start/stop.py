import subprocess
import os
from pathlib import Path

from rich.text import Text

from pyrrowhead import rich_console
from pyrrowhead.utils import switch_directory


def stop_local_cloud(cloud_directory: Path):
    with switch_directory(cloud_directory):
        with rich_console.status(Text('Stopping local cloud...')):
            output = subprocess.run(['docker-compose', 'down'], capture_output=True)