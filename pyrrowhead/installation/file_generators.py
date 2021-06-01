"""
Generates and copies files to the target directory.
"""
from pathlib import Path
import shutil
from functools import partial
from collections import OrderedDict
import os, stat
from importlib.resources import path

from jinja2 import Environment, PackageLoader, select_autoescape
import yaml
import yamlloader
from rich.text import Text

from pyrrowhead.database_config.passwords import db_passwords
import pyrrowhead.database_config as database_config
import pyrrowhead.certificate_generation as certificate_generation
from pyrrowhead import rich_console

yaml_safedump = partial(yaml.dump, Dumper=yamlloader.ordereddict.CSafeDumper)

def generate_config_files(cloud_config, target_path):
    """
    Creates the property files for all core services in yaml_path
    Args:
        yaml_path: Path to cloud config
        target_path: Path to cloud directory
    """
    env = Environment(
            loader=PackageLoader("pyrrowhead"),
            autoescape=select_autoescape()
    )

    core_systems = cloud_config['core_systems']

    sr_address = core_systems['service_registry']['domain']
    sr_port = core_systems['service_registry']['port']

    for system, config in core_systems.items():
        system_cn = f'{config["system_name"]}.{cloud_config["cloud_name"]}.{cloud_config["company_name"]}.arrowhead.eu'
        template = env.get_template(f"core_system_config/{system}.properties")

        system_config_file = template.render(
                **config,
                system_cn=system_cn,
                cloud_name=cloud_config["cloud_name"],
                password=db_passwords[system],
                sr_address=sr_address,
                sr_port=sr_port,
                ssl_enabled=cloud_config["ssl_enabled"]
        )

        core_system_config_path = Path(target_path) / 'core_system_config'
        core_system_config_path.mkdir(parents=True, exist_ok=True)
        with open(core_system_config_path / f'{system}.properties', 'w+') as target_file:
            target_file.write(system_config_file)

def generate_certgen(cloud_config, target_path):
    env = Environment(
            loader=PackageLoader("pyrrowhead"),
            autoescape=select_autoescape()
    )

    template = env.get_template('certificates/mk_certs.sh')

    certgen_content = template.render(**cloud_config)

    certgen_path = Path(target_path) / 'certgen'
    certgen_path.mkdir(parents=True, exist_ok=True)
    with open(certgen_path / 'mk_certs.sh', 'w+') as target_file:
        target_file.write(certgen_content)

def generate_docker_compose_file(cloud_config, target_path):
    docker_compose_content = OrderedDict({
        'version': '3',
        'services': OrderedDict({
            f'mysql.{cloud_config["cloud_name"]}': {
                'container_name': f'mysql.{cloud_config["cloud_name"]}',
                'image': 'mysql:5.7',
                'environment': ['MYSQL_ROOT_PASSWORD=123456'],
                'volumes': [f'mysql.{cloud_config["cloud_name"]}:/var/lib/mysql', './sql:/docker-entrypoint-initdb.d/'],
                'ports': ['3306:3306'],
            },
        }),
        'volumes': {
            f'mysql.{cloud_config["cloud_name"]}': {
                'external': True
            }
        }
    })

    for core_system, config in cloud_config['core_systems'].items():
        core_name = config['domain']
        cloud_name = cloud_config["cloud_name"]
        docker_compose_content['services'][core_name] = {
            'container_name': f'{core_name}.{cloud_config["cloud_name"]}',
            'image': f'svetlint/{core_name}:4.3.0',
            'depends_on': [f'mysql.{cloud_name}'],
            'volumes': [
                f'./core_system_config/{core_system}.properties:/{core_name}/application.properties',
                f'./cloud-{cloud_name}/crypto/{core_system}.p12:/{core_name}/{core_system}.p12',
                f'./cloud-{cloud_name}/crypto/truststore.p12:/{core_name}/truststore.p12',
            ],
            'ports': [f'{config["port"]}:{config["port"]}'],
        }

    with open(Path(target_path) / 'docker-compose.yml', 'w+') as target_file:
        yaml_safedump(docker_compose_content, target_file)

def generate_all_files(cloud_config, yaml_path, target_path):
    generate_config_files(cloud_config, target_path)
    rich_console.print(Text('Generated core system configuration files.'))
    generate_certgen(cloud_config, target_path)
    rich_console.print(Text('Generated certificate generation files.'))
    generate_docker_compose_file(cloud_config, target_path)
    rich_console.print(Text('Generated docker-compose.yml.'))
    # Copy files that need not be generated
    with path(database_config, 'initSQL.sh') as init_sql_path:
        shutil.copy(init_sql_path, target_path)
    with path(certificate_generation, 'lib_certs.sh') as lib_cert_path:
        shutil.copy(lib_cert_path, target_path / 'certgen')
    with path(certificate_generation, 'rm_certs.sh') as rm_certs_path:
        shutil.copy(rm_certs_path, target_path / 'certgen')
    # Copy the config file
    try:
        shutil.copy(yaml_path.absolute(), target_path)
    except shutil.SameFileError:
        ...
    # Make mk_certs.sh executable
    mk_cert_path = target_path / 'certgen/mk_certs.sh'
    os.chmod(mk_cert_path, os.stat(mk_cert_path).st_mode | stat.S_IEXEC)
    rich_console.print(Text('Copyied files.'))
