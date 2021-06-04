from pathlib import Path
from typing import Union, List, Dict

import yaml
import requests

def get_ssl_files(cert_dir: Path):
    if (cloud_path := cert_dir / 'cloud_config.yaml').exists():
        with open(cloud_path) as cloud_file:
            cloud_config = yaml.safe_load(cloud_file)
        cloud_name = cloud_config["cloud"]["cloud_name"]
        cert_subpath = f'cloud-{cloud_name}/crypto/sysop.crt'
        key_subpath = f'cloud-{cloud_name}/crypto/sysop.key'
        ca_subpath = f'cloud-{cloud_name}/crypto/sysop.ca'
    else:
        cert_subpath = 'sysop.crt'
        key_subpath = 'sysop.key'
        ca_subpath = 'sysop.ca'
    return (
        cert_subpath, key_subpath, ca_subpath
    )

def get_service(
        url: str,
        cert_dir: Path,
):
    *certkey, ca_path = get_ssl_files(cert_dir)
    resp = requests.get(url, cert=certkey, verify=ca_path)
    return resp

def post_service(
        url: str,
        cert_dir: Path,
        json: Union[Dict, List] = None,
        text: str = ''
):
    *certkey, ca_path = get_ssl_files(cert_dir)
    if json:
        resp = requests.post(url, json=json, cert=certkey, verify=ca_path)
    else:
        resp = requests.post(url, text=text, cert=certkey, verify=ca_path)
    return resp

def delete_service(
        url: str,
        cert_dir: Path,
):
    *certkey, ca_path = get_ssl_files(cert_dir)

    resp = requests.delete(url, cert=certkey, verify=ca_path)
    return resp
