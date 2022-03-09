from pathlib import Path
from typing import Union, List, Dict, Optional

import requests


def get_ssl_files(cloud_directory: Path):
    if (cloud_directory / "cloud_config.yaml").exists():
        cert_subpath = "certs/crypto/sysop.crt"
        key_subpath = "certs/crypto/sysop.key"
        ca_subpath = "certs/crypto/sysop.ca"
    else:
        cert_subpath = "sysop.crt"
        key_subpath = "sysop.key"
        ca_subpath = "sysop.ca"
    return (
        cloud_directory / subpath for subpath in (cert_subpath, key_subpath, ca_subpath)
    )


def get_service(
    url: str,
    cloud_directory: Path,
):
    *certkey, ca_path = get_ssl_files(cloud_directory)
    resp = requests.get(url, cert=certkey, verify=ca_path)
    return resp


def post_service(
    url: str, cloud_directory: Path, json: Union[Dict, List] = None, text: str = ""
):
    *certkey, ca_path = get_ssl_files(cloud_directory)
    if json:
        resp = requests.post(url, json=json, cert=certkey, verify=ca_path)
    elif text:
        resp = requests.post(url, data=text, cert=certkey, verify=ca_path)
    else:
        resp = requests.post(url, cert=certkey, verify=ca_path)
    return resp


def delete_service(
    url: str,
    cloud_directory: Path,
    params: Optional[Dict[str, str]] = None,
):
    *certkey, ca_path = get_ssl_files(cloud_directory)

    resp = requests.delete(url, params=params, cert=certkey, verify=ca_path)
    return resp
