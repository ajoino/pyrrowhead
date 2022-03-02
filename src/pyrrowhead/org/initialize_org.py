from pathlib import Path

from utils import get_local_cloud_directory


def check_org_exists(org_name: str) -> bool:
    org_dir =