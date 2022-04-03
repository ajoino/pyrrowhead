from typing import Dict

from pyrrowhead.constants import CLOUD_CONFIG_FILE_NAME
from pyrrowhead.utils import validate_cloud_config_file


def inspect(
    cloud_dir,
) -> Dict:
    cloud_config = validate_cloud_config_file(
        cloud_dir.joinpath(CLOUD_CONFIG_FILE_NAME)
    )

    cloud_info = {
        "Cloud name": cloud_config["cloud_name"],
        "Organization": cloud_config["org_name"],
        "Secure": cloud_config["ssl_enabled"],
        "Subnetwork": cloud_config["subnet"],
        "Alternative Addresses": cloud_config["core_san"],
        "Installed": cloud_config["installed"],
        "Location": cloud_dir,
    }
    core_systems = {
        core_name: {
            "Address": core_sys["address"],
            "Port": core_sys["port"],
        }
        for core_name, core_sys in cloud_config["core_systems"].items()
    }
    client_systems = {
        client_name: {
            "Address": client_sys["address"],
            "Port": client_sys["port"],
        }
        for client_name, client_sys in cloud_config["client_systems"].items()
    }
    return {
        "Cloud Information": cloud_info,
        "Core Systems": core_systems,
        "Client Systems": client_systems,
    }
