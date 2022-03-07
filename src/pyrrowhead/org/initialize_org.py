import shutil
from pathlib import Path
from typing import Optional

from pyrrowhead.utils import get_local_cloud_directory, PyrrowheadError
from pyrrowhead.constants import ORG_CERT_DIR, ROOT_CERT_DIR
from pyrrowhead.new_certificate_generation.generate_certificates import (
    generate_and_store_root_files,
    generate_and_store_org_files,
    KeyCertPair,
    load_p12,
)


def load_root_certificates(org_dir: Path, password: str):
    root_cert_dir = org_dir / ROOT_CERT_DIR / "crypto"
    with open(root_cert_dir / "root.p12", "rb") as root_p12:
        root_key, root_cert, *_ = load_p12(root_p12.read(), password.encode())
    return root_key, root_cert


def create_root_certificates(org_dir: Path, password: str) -> KeyCertPair:
    root_cert_dir = org_dir / ROOT_CERT_DIR / "crypto"
    root_cert_dir.mkdir(parents=True)
    pair = generate_and_store_root_files(root_cert_dir, password)
    return pair


def create_org_certificates(
    org_name: str,
    org_dir: Path,
    root_key,
    root_cert,
    password,
) -> KeyCertPair:
    org_cert_dir = org_dir / ORG_CERT_DIR / "crypto"
    org_cert_dir.mkdir(parents=True)
    pair = generate_and_store_org_files(
        org_name, org_cert_dir, root_key, root_cert, password
    )
    return pair


def copy_org_certificates(
    org_name: str,
    key_path: Path,
    cert_path: Optional[Path] = None,
):
    org_dir = get_local_cloud_directory() / org_name
    org_cert_dir = org_dir / ORG_CERT_DIR / "crypto"
    shutil.copy(key_path, org_cert_dir / f"{org_name}.key")

    if cert_path is not None:
        shutil.copy(key_path, org_cert_dir / f"{org_name}.crt")


def populate_org_dir(org_name: str, password: str):
    org_dir = get_local_cloud_directory() / org_name

    if not all(
        org_dir.joinpath(subdir).exists() for subdir in (ORG_CERT_DIR, ROOT_CERT_DIR)
    ):
        root_key_cert = create_root_certificates(org_dir, password)
        create_org_certificates(org_name, org_dir, *root_key_cert, password)
    elif not org_dir.joinpath(ORG_CERT_DIR).exists():
        root_key_cert = create_root_certificates(org_dir, password)
        root_key, root_cert = load_root_certificates(org_dir, password)
        create_org_certificates(org_name, org_dir, root_key, root_cert, password)


def mk_org_dir(org_name: str):
    org_dir = get_local_cloud_directory() / org_name

    if org_dir.is_dir():
        raise PyrrowheadError(f'Organization "{org_name}" already exists')
    if not org_dir.exists():
        org_dir.mkdir()
