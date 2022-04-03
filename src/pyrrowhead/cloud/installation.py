import ipaddress
import shutil
import subprocess
from collections import OrderedDict
from functools import partial
from importlib.resources import path
from pathlib import Path
from typing import Dict

import yaml
import yamlloader
from jinja2 import Environment, PackageLoader, select_autoescape
from rich.text import Text

from pyrrowhead import rich_console, database_config
from pyrrowhead.database_config.passwords import db_passwords
from pyrrowhead.new_certificate_generation.generate_certificates import (
    generate_certificates,
    store_sysop,
    store_root_files,
    store_org_files,
    store_cloud_cert,
    store_system_files,
    store_truststore,
)
from pyrrowhead.types_ import CloudDict
from pyrrowhead.utils import (
    get_config,
    set_config,
    validate_cloud_config_file,
    PyrrowheadError,
    store_cloud_config_file,
)
from pyrrowhead.constants import CLOUD_CONFIG_FILE_NAME


yaml_safedump = partial(yaml.dump, Dumper=yamlloader.ordereddict.CSafeDumper)


def install_cloud(
    cloud_dir: Path,
    cloud_password: str,
    org_password: str,
):
    cloud_config = validate_cloud_config_file(
        cloud_dir.joinpath(CLOUD_CONFIG_FILE_NAME)
    )

    with rich_console.status(Text("Installing Arrowhead local cloud...")):
        try:
            files_created = []
            core_system_config_file_strings = generate_config_files(
                cloud_config, cloud_dir, cloud_password
            )
            cloud_dir.joinpath("core_system_config").mkdir(parents=True, exist_ok=True)
            for (
                core_config_path,
                core_config,
            ) in core_system_config_file_strings.items():
                with open(core_config_path, "w") as core_config_file:
                    core_config_file.write(core_config)
                files_created.append(core_config_path)
            rich_console.print(Text("Generated core system configuration files."))
            docker_compose_content = generate_docker_compose_file(
                cloud_config, cloud_dir, cloud_password
            )
            with open(
                (compose_path := cloud_dir.joinpath("docker-compose.yml")), "w"
            ) as docker_file:
                yaml_safedump(docker_compose_content, docker_file)
                files_created.append(compose_path)
            rich_console.print(Text("Generated docker-compose.yml."))
            (
                root_data,
                org_data,
                cloud_data,
                sysop_data,
                system_keycerts,
            ) = generate_certificates(
                cloud_config,
                cloud_dir,
                cloud_password,
                org_password,
            )
            stored_root_paths = store_root_files(
                *root_data,
                password="123456",
            )
            files_created.extend(stored_root_paths)
            stored_org_paths = store_org_files(
                cloud_config["org_name"],
                *org_data,
                root_keycert=root_data[1],
                password=org_password,
            )
            files_created.extend(stored_org_paths)
            stored_cloud_paths = store_cloud_cert(
                cloud_config["cloud_name"],
                cloud_config["org_name"],
                *cloud_data,
                org_keycert=org_data[1],
                root_keycert=root_data[1],
                password=cloud_password,
            )
            files_created.extend(stored_cloud_paths)
            stored_sysop_paths = store_sysop(
                cloud_config["cloud_name"],
                *sysop_data,
                root_keycert=root_data[1],
                org_keycert=org_data[1],
                cloud_keycert=cloud_data[1],
                password=cloud_password,
            )
            files_created.extend(stored_sysop_paths)
            system_paths = []
            for keycert_path, keycert in system_keycerts.items():
                _system_paths = store_system_files(
                    keycert_path,
                    keycert,
                    root_keycert=root_data[1],
                    org_keycert=org_data[1],
                    cloud_keycert=cloud_data[1],
                    password=cloud_password,
                )
                system_paths.extend(_system_paths)
            files_created.extend(system_paths)
            truststore_paths = store_truststore(
                cloud_data[0],
                cloud_data[1].cert,
                password=cloud_password,
            )
            files_created.extend(truststore_paths)
            rich_console.print("Generated truststore.p12")
            with path(database_config, "initSQL.sh") as init_sql_path:
                # with contextlib.suppress(shutil.SameFileError):
                copy_path = shutil.copy(init_sql_path, cloud_dir)
                files_created.append(Path(copy_path))
            if not check_sql_initialized(cloud_dir):
                subprocess.run(["./initSQL.sh"], cwd=cloud_dir, capture_output=True)
                files_created.extend(cloud_dir.joinpath("sql").glob("**/*"))
                rich_console.print(Text("Initialized SQL tables."))
            rich_console.print(Text("Copied files."))
            if not check_mysql_volume_exists(
                cloud_config["cloud_name"], cloud_config["org_name"]
            ):
                subprocess.run(
                    f"docker volume create --name mysql.{cloud_config['cloud_name']}."
                    f"{cloud_config['org_name']}".split(),
                    capture_output=True,
                )
                rich_console.print(Text("Created docker volume."))
        except (PyrrowheadError, OSError, FileNotFoundError) as e:
            for p in files_created:
                if p.is_file():
                    p.unlink()
                elif p.is_dir():
                    shutil.rmtree(p)
            raise PyrrowheadError(
                f"An error occured during the installation: "
                f"{e}.\nRemoving all created files."
            ) from e
        else:
            cloud_config["installed"] = True
            store_cloud_config_file(
                cloud_dir.joinpath(CLOUD_CONFIG_FILE_NAME), cloud_config
            )
            rich_console.print(
                "Finished installing the [blue]Arrowhead[/blue] local cloud!"
            )


def uninstall_cloud(
    installation_target, complete=False, keep_root=False, keep_sysop=False
):
    config_path = installation_target / CLOUD_CONFIG_FILE_NAME

    cloud_config = validate_cloud_config_file(config_path)

    cloud_name = cloud_config["cloud_name"]
    org_name = cloud_config["org_name"]

    if complete:
        # shutil.rmtree(installation_target)
        config = get_config()

        del config["local-clouds"][f"{cloud_name}.{org_name}"]
        set_config(config)
    else:
        if not keep_sysop:
            shutil.rmtree(installation_target / "certs")
        else:
            # TODO: Code that deletes everything except the sysop.* files
            pass
        shutil.rmtree(installation_target / "core_system_config")
        shutil.rmtree(installation_target / "sql")
        (installation_target / "docker-compose.yml").unlink()
        (installation_target / "initSQL.sh").unlink()
    subprocess.run(["docker", "volume", "rm", f"mysql.{cloud_name}.{org_name}"])
    cloud_config["installed"] = False
    store_cloud_config_file(config_path, cloud_config)
    rich_console.print("Uninstallation complete")


def generate_config_files(
    cloud_config: CloudDict, cloud_dir, password
) -> Dict[Path, str]:
    """
    Creates the property files for all core services in yaml_path
    Args:
        yaml_path: Path to cloud config
        cloud_dir: Path to cloud directory
    """
    env = Environment(
        loader=PackageLoader("pyrrowhead"), autoescape=select_autoescape()
    )

    core_systems = cloud_config["core_systems"]

    sr_address = core_systems["service_registry"]["address"]
    sr_port = core_systems["service_registry"]["port"]

    config_file_strings = {}
    for system, config in core_systems.items():
        system_cn = (
            f'{config["domain"]}.{cloud_config["cloud_name"]}.'
            f'{cloud_config["org_name"]}.arrowhead.eu'
        )
        template = env.get_template(f"core_system_config/{system}.properties")

        system_config_file = template.render(
            **config,
            system_cn=system_cn,
            cloud_name=cloud_config["cloud_name"],
            organization_name=cloud_config["org_name"],
            password=db_passwords[system],
            sr_address=sr_address,
            sr_port=sr_port,
            ssl_enabled=cloud_config["ssl_enabled"],
            cert_pw=password,
        )

        core_system_config_path = Path(cloud_dir).joinpath(
            "core_system_config", f"{system}.properties"
        )

        config_file_strings[core_system_config_path] = system_config_file

    return config_file_strings


def generate_docker_compose_file(
    cloud_config: CloudDict, target_path, password
) -> Dict:
    cloud_identifier = f'{cloud_config["cloud_name"]}.{cloud_config["org_name"]}'
    docker_compose_content = OrderedDict(
        {
            "version": "3",
            "services": OrderedDict(
                {
                    f"mysql.{cloud_identifier}": {
                        "container_name": f"mysql.{cloud_identifier}",
                        "image": "mysql:5.7",
                        "environment": [f"MYSQL_ROOT_PASSWORD={password}"],
                        "volumes": [
                            f"mysql.{cloud_identifier}:/var/lib/mysql",
                            "./sql:/docker-entrypoint-initdb.d/",
                        ],
                        "networks": {
                            cloud_identifier: {
                                "ipv4_address": str(
                                    ipaddress.ip_network(cloud_config["subnet"])[2]
                                )
                            }
                        },
                        "ports": ["3306:3306"],
                    },
                }
            ),
            "volumes": {f"mysql.{cloud_identifier}": {"external": True}},
            "networks": {
                f"{cloud_identifier}": {
                    "ipam": {"config": [{"subnet": cloud_config["subnet"]}]}
                }
            },
        }
    )

    for core_system, config in cloud_config["core_systems"].items():
        core_name = config["domain"]
        # cloud_name = cloud_config["cloud_name"]
        docker_compose_content["services"][core_name] = {  # type: ignore
            "container_name": f"{core_name}.{cloud_identifier}",
            "image": f"svetlint/{core_name}:4.3.0",
            "depends_on": [f"mysql.{cloud_identifier}"],
            "volumes": [
                f"./core_system_config/{core_system}.properties:/"
                f"{core_name}/application.properties",
                f"./certs/crypto/{core_system}.p12:/{core_name}/{core_system}.p12",
                f"./certs/crypto/truststore.p12:/{core_name}/truststore.p12",
            ],
            "networks": {cloud_identifier: {"ipv4_address": config["address"]}},
            "ports": [f'{config["port"]}:{config["port"]}'],
        }

    return docker_compose_content


def check_sql_initialized(cloud_directory):
    return (cloud_directory / "sql/create_empty_arrowhead_db.sql").is_file()


def check_mysql_volume_exists(cloud_name, org_name):
    ps_output = subprocess.run(
        ["docker", "volume", "ls"],
        capture_output=True,
    ).stdout.decode()
    # If mysql volume doesn't exists in stdout find returns -1
    return ps_output.find(f"mysql.{cloud_name}.{org_name}") != -1
