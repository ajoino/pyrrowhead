from pathlib import Path

import typer
import yaml
import yamlloader

from pyrrowhead import rich_console


def enable_ssl(enable):
    config_dir = Path.cwd() / "core_system_config"

    if not config_dir.is_dir():
        rich_console.print("core_system_config directory does not exist")
        raise typer.Exit()

    # Update property files
    for property_path in config_dir.iterdir():
        with open(property_path, "r") as property_file:
            lines = property_file.readlines()
            update_line = f"server.ssl.enabled={str(enable).lower()}\n"
            updated_lines = [
                line if not line.startswith("server.ssl.enabled") else update_line
                for line in lines
            ]
        with open(property_path, "w") as property_file:
            property_file.writelines(updated_lines)

    with open(Path.cwd() / "cloud_config.yaml") as config_file:
        cloud_config = yaml.load(config_file, Loader=yamlloader.ordereddict.CSafeLoader)
        cloud_config["cloud"]["ssl_enabled"] = enable
    with open(Path.cwd() / "cloud_config.yaml", "w") as config_file:
        yaml.dump(cloud_config, config_file, Dumper=yamlloader.ordereddict.CSafeDumper)
