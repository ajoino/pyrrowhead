from pathlib import Path
from typing import Optional, List, Tuple

import typer

from pyrrowhead import rich_console
from pyrrowhead.utils import (
    switch_directory,
    set_active_cloud as set_active_cloud_func,
    get_config,
)
from pyrrowhead.constants import (
    OPT_CLOUDS_DIRECTORY,
    OPT_CLOUD_NAME,
    OPT_ORG_NAME,
    ARG_ORG_NAME,
    ARG_CLOUD_IDENTIFIER,
)


