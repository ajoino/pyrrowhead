import subprocess

from rich.text import Text

from pyrrowhead import rich_console
from pyrrowhead.new_certificate_generation.generate_certificates import (
    setup_certificates,
)


def check_sql_initialized(cloud_directory):
    return (cloud_directory / "sql/create_empty_arrowhead_db.sql").is_file()


def check_mysql_volume_exists(cloud_name, org_name):
    ps_output = subprocess.run(
        ["docker", "volume", "ls"],
        capture_output=True,
    ).stdout.decode()
    # If mysql volume doesn't exists in stdout find returns -1
    return ps_output.find(f"mysql.{cloud_name}.{org_name}") != -1


def initialize_cloud(
    cloud_directory,
    cloud_name,
    organization_name,
    cloud_password,
    org_password,
):
    setup_certificates(
        cloud_directory / "cloud_config.yaml",
        cloud_password=cloud_password,
        org_password=org_password,
    )
    rich_console.print(Text("Created certificates."))
    if not check_sql_initialized(cloud_directory):
        subprocess.run(["./initSQL.sh"], cwd=cloud_directory, capture_output=True)
        rich_console.print(Text("Initialized SQL tables."))
    if not check_mysql_volume_exists(cloud_name, organization_name):
        subprocess.run(
            f"docker volume create --name mysql.{cloud_name}."
            f"{organization_name}".split(),
            capture_output=True,
        )
        rich_console.print(Text("Created docker volume."))
