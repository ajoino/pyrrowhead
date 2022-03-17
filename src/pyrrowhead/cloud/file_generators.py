"""
Generates and copies files to the target directory.
"""
from pathlib import Path
import shutil
from functools import partial
from collections import OrderedDict
from importlib.resources import path
import ipaddress

from jinja2 import Environment, PackageLoader, select_autoescape
import yaml
import yamlloader  # type: ignore
from rich.text import Text

from pyrrowhead.database_config.passwords import db_passwords
from pyrrowhead import database_config
from pyrrowhead import rich_console
from pyrrowhead.types_ import CloudDict

yaml_safedump = partial(yaml.dump, Dumper=yamlloader.ordereddict.CSafeDumper)


def generate_config_files(cloud_config: CloudDict, target_path, password):
    """
    Creates the property files for all core services in yaml_path
    Args:
        yaml_path: Path to cloud config
        target_path: Path to cloud directory
    """
    env = Environment(
        loader=PackageLoader("pyrrowhead"), autoescape=select_autoescape()
    )

    core_systems = cloud_config["core_systems"]

    sr_address = core_systems["service_registry"]["address"]
    sr_port = core_systems["service_registry"]["port"]

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

        core_system_config_path = Path(target_path) / "core_system_config"
        core_system_config_path.mkdir(parents=True, exist_ok=True)
        with open(
            core_system_config_path / f"{system}.properties", "w+"
        ) as target_file:
            target_file.write(system_config_file)


def generate_docker_compose_file(cloud_config: CloudDict, target_path, password):
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

    with open(Path(target_path) / "docker-compose.yml", "w+") as target_file:
        yaml_safedump(docker_compose_content, target_file)


def generate_cloud_files(cloud_config, yaml_path, target_path, password):
    generate_config_files(cloud_config, target_path, password)
    rich_console.print(Text("Generated core system configuration files."))
    generate_docker_compose_file(cloud_config, target_path, password)
    rich_console.print(Text("Generated docker-compose.yml."))
    # Copy files that need not be generated
    with path(database_config, "initSQL.sh") as init_sql_path:
        shutil.copy(init_sql_path, target_path)
    # with path(certificate_generation, "lib_certs.sh") as lib_cert_path:
    #    shutil.copy(lib_cert_path, target_path / "certgen")
    # with path(certificate_generation, "rm_certs.sh") as rm_certs_path:
    #    shutil.copy(rm_certs_path, target_path / "certgen")
    # Copy the config file
    try:
        shutil.copy(yaml_path.absolute(), target_path)
    except shutil.SameFileError:
        pass
    rich_console.print(Text("Copied files."))
