import subprocess
from pathlib import Path

def check_certs_exist(cloud_directory, cloud_name):
    cert_directory = cloud_directory / f'cloud-{cloud_name}/crypto'
    return (
        cert_directory.is_dir()
        and any(cert_directory.iterdir())
    )

def check_sql_initialized(cloud_directory):
    return (cloud_directory / 'sql/create_empty_arrowhead_db.sql').is_file()

def check_mysql_volume_exists(cloud_name):
    ps_output = subprocess.run(
            ['docker', 'volume', 'ls'],
            capture_output=True,
    ).stdout.decode()
    # If mysql volume doesn't exists in stdout find returns -1
    return ps_output.find(f'mysql.{cloud_name}') == -1

def initialize_cloud(cloud_directory, cloud_name):
    if not check_certs_exist(cloud_directory, cloud_name):
        subprocess.run(['./mk_certs.sh'], cwd=cloud_directory / 'certgen')
    if not check_sql_initialized(cloud_directory):
        subprocess.run(['./initSQL.sh'], cwd=cloud_directory)
    if check_mysql_volume_exists(cloud_name):
        subprocess.run(['docker', 'volume', 'create', '--name', f'mysql.{cloud_name}'])
