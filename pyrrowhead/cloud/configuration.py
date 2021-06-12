from pathlib import Path

import typer
import yaml
import yamlloader


def enable_ssl(enable):
    config_dir = Path.cwd() / 'core_system_config'

    if not config_dir.is_dir():
        raise typer.Exit('core_system_config directory does not exist')

    # Update property files
    for property_path in config_dir.iterdir():
        with open(property_path, 'r') as property_file:
            lines = property_file.readlines()
            update_line = f'server.ssl.enabled={str(enable).lower()}\n'
            updated_lines = [update_line if line.startswith('server.ssl.enabled') else line for line in lines]
        with open(property_path, 'w') as property_file:
            property_file.writelines(updated_lines)

    with open(Path.cwd() / 'cloud_config.yaml') as config_file:
        cloud_config = yaml.load(config_file, Loader=yamlloader.ordereddict.CSafeLoader)
        cloud_config["cloud"]["ssl_enabled"] = enable
    with open(Path.cwd() / 'cloud_config.yaml', 'w') as config_file:
        yaml.dump(cloud_config, config_file, Dumper=yamlloader.ordereddict.CSafeDumper)

