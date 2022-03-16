import subprocess
from pathlib import Path
from ipaddress import ip_address
from datetime import datetime, timedelta
from typing import Tuple, List, Optional, Dict, NamedTuple

import yaml
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization.pkcs12 import (
    serialize_key_and_certificates as serialize_p12,
    load_key_and_certificates as load_p12,
)
from cryptography import x509
from cryptography.x509 import Certificate, CertificateSigningRequest
from cryptography.x509.oid import NameOID

from pyrrowhead import rich_console
from pyrrowhead.types_ import ConfigDict
from pyrrowhead.utils import PyrrowheadError, validate_san


class KeyCertPair(NamedTuple):
    key: RSAPrivateKey
    cert: Certificate


def set_password_encryption(password: Optional[str] = None):
    if not password:
        return serialization.NoEncryption()

    return serialization.BestAvailableEncryption(password.encode())


def generate_private_key() -> RSAPrivateKey:
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )


def get_general_name(san_with_prefix: str) -> x509.GeneralName:
    validate_san(san_with_prefix)
    if san_with_prefix.startswith("ip:"):
        return x509.IPAddress(ip_address(san_with_prefix[3:]))
    else:
        # san_with_prefix.startswith("dns:"):
        return x509.DNSName(san_with_prefix[4:])


def generate_root_certificate() -> KeyCertPair:
    root_key_alias = "arrowhead.eu"

    root_key = generate_private_key()

    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, root_key_alias)]
    )
    root_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(root_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365.25 * 10))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=False,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(root_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(root_key_alias)]), critical=False
        )
        .sign(root_key, hashes.SHA256())
    )

    return KeyCertPair(root_key, root_cert)


def generate_ca_signing_request(
    common_name: str,
    ca: bool,
    path_length: Optional[int],
) -> Tuple[RSAPrivateKey, CertificateSigningRequest]:
    key = generate_private_key()

    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)]))
        .add_extension(
            x509.BasicConstraints(
                ca=ca,
                path_length=path_length,
            ),
            critical=False,
        )
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(common_name)]), critical=False
        )
        .sign(key, hashes.SHA256())
    )

    return key, csr


def generate_system_signing_request(
    common_name: str,
    ip: Optional[str],
    sans: Optional[List[str]],
) -> Tuple[RSAPrivateKey, CertificateSigningRequest]:
    key = generate_private_key()

    general_names: List[x509.GeneralName] = []
    if ip is not None:
        general_names.append(x509.IPAddress(ip_address(ip)))
    if sans is not None:
        general_names.extend(get_general_name(san) for san in sans)

    csr_builder = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)]))
        .add_extension(
            x509.SubjectAlternativeName(general_names),
            critical=False,
        )
    )

    csr = csr_builder.sign(key, hashes.SHA256())
    return key, csr


def sign_certificate_request(
    csr: CertificateSigningRequest,
    issuer_cert: Certificate,
    issuer_key: RSAPrivateKey,
) -> Certificate:
    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(issuer_cert.subject)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365.25 * 10))
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(csr.public_key()),
            critical=False,
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(issuer_key.public_key()),
            critical=False,
        )
    )

    for extension in csr.extensions:
        cert_builder = cert_builder.add_extension(
            extension.value,
            extension.critical,
        )

    cert = cert_builder.sign(issuer_key, hashes.SHA256())

    return cert


def generate_ca_cert(
    common_name: str,
    ca: bool,
    path_length: Optional[int],
    issuer_cert: Certificate,
    issuer_key: RSAPrivateKey,
) -> KeyCertPair:
    ca_key, ca_csr = generate_ca_signing_request(common_name, ca, path_length)
    ca_cert = sign_certificate_request(ca_csr, issuer_cert, issuer_key)

    return KeyCertPair(ca_key, ca_cert)


def generate_system_cert(
    common_name: str,
    ip: Optional[str],
    issuer_cert: Certificate,
    issuer_key: RSAPrivateKey,
    sans: Optional[List[str]] = None,
) -> KeyCertPair:
    system_key, system_csr = generate_system_signing_request(common_name, ip, sans)
    system_cert = sign_certificate_request(system_csr, issuer_cert, issuer_key)

    return KeyCertPair(system_key, system_cert)


def generate_core_system_certs(
    cloud_config: ConfigDict, cloud_cert, cloud_key
) -> Dict[str, KeyCertPair]:
    cloud_name = cloud_config["cloud"]["cloud_name"]
    org_name = cloud_config["cloud"]["organization_name"]
    return {
        core_system["system_name"]: generate_system_cert(
            common_name=f'{core_system["system_name"]}.'
            f"{cloud_name}.{org_name}.arrowhead.eu",
            ip=core_system["address"],
            issuer_cert=cloud_cert,
            issuer_key=cloud_key,
            sans=cloud_config["cloud"]["core_san"],
        )
        for core_system in cloud_config["cloud"]["core_systems"].values()
    }


def generate_client_system_certs(
    cloud_config: ConfigDict, cloud_cert, cloud_key
) -> Dict[str, KeyCertPair]:
    cloud_name = cloud_config["cloud"]["cloud_name"]
    org_name = cloud_config["cloud"]["organization_name"]
    return {
        client_id: generate_system_cert(
            f'{client_system["system_name"]}.{cloud_name}.{org_name}.arrowhead.eu',
            client_system["address"],
            cloud_cert,
            cloud_key,
            client_system.get("sans", None),
        )
        for client_id, client_system in cloud_config["cloud"]["client_systems"].items()
    }


def store_system_files(
    core_keycert: KeyCertPair,
    core_cert_path: Path,
    root_cert,
    org_cert,
    cloud_cert,
    password: Optional[str],
):
    core_name = core_keycert.cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[
        0
    ].value

    with open(core_cert_path.with_suffix(".p12"), "wb") as p12_file:
        p12_file.write(
            serialize_p12(
                name=core_name.encode(),
                key=core_keycert.key,
                cert=core_keycert.cert,
                cas=[cloud_cert, org_cert, root_cert],
                encryption_algorithm=set_password_encryption(password),
            )
        )
        print(root_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME))
    with open(core_cert_path.with_suffix(".crt"), "wb") as crt_file:
        crt_file.write(core_keycert.cert.public_bytes(serialization.Encoding.PEM))
    with open(core_cert_path.with_suffix(".key"), "wb") as key_file:
        key_file.write(
            core_keycert.key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=set_password_encryption(password),
            )
        )


def store_sysop(
    sysop_certs: KeyCertPair,
    root_cert: Certificate,
    org_cert: Certificate,
    cloud_cert: Certificate,
    cert_directory: Path,
    password: Optional[str],
):
    with open(sysop_p12 := cert_directory / "sysop.p12", "wb") as p12_file:
        cloud_name = cloud_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[
            0
        ].value
        p12_file.write(
            serialize_p12(
                name=f"sysop.{cloud_name}".encode(),
                key=sysop_certs.key,
                cert=sysop_certs.cert,
                cas=[cloud_cert, org_cert, root_cert],
                encryption_algorithm=set_password_encryption(password),
            )
        )
    with open(sysop_p12.with_suffix(".crt"), "wb") as crt_file:
        crt_file.write(sysop_certs.cert.public_bytes(serialization.Encoding.PEM))
    with open(sysop_p12.with_suffix(".key"), "wb") as key_file:
        key_file.write(
            sysop_certs.key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    with open(sysop_p12.with_suffix(".ca"), "wb") as ca_file:
        ca_file.write(cloud_cert.public_bytes(serialization.Encoding.PEM))
        ca_file.write(org_cert.public_bytes(serialization.Encoding.PEM))
        ca_file.write(root_cert.public_bytes(serialization.Encoding.PEM))


def store_truststore(cloud_cert: Certificate, cert_directory: Path, password: str):
    cloud_long_name = cloud_cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[
        0
    ].value
    cloud_short_name, *_ = cloud_long_name.split(".")
    res = subprocess.run(
        f"keytool -importcert -trustcacerts"
        f" -noprompt -storepass {password!s}"
        f" -keystore {cert_directory}/truststore.p12"
        f" -file {cert_directory}/{cloud_short_name}.crt"
        f" -alias {cloud_long_name}".split(),
        capture_output=True,
    )
    if res.returncode != 0:
        raise PyrrowheadError(f"Could not create truststore:\n{res.stdout!s}")
    rich_console.print("Generated truststore.p12")


def generate_and_store_root_files(
    root_cert_directory: Path, password=Optional[str]
) -> KeyCertPair:
    root_keycert = generate_root_certificate()
    with open(root_cert_directory / "root.p12", "wb") as root_p12:
        root_p12.write(
            serialize_p12(
                name=b"arrowhead.eu",
                key=root_keycert.key,
                cert=root_keycert.cert,
                cas=None,
                encryption_algorithm=set_password_encryption(password),
            )
        )
    with open(root_cert_directory / "root.crt", "wb") as root_crt:
        root_crt.write(root_keycert.cert.public_bytes(serialization.Encoding.PEM))

    return root_keycert


def generate_and_store_org_files(
    org_name: str,
    org_cert_dir: Path,
    root_key,
    root_cert,
    password: Optional[str],
) -> KeyCertPair:
    org_keycert = generate_ca_cert(
        f"{org_name}.arrowhead.eu",
        ca=True,
        path_length=None,
        issuer_cert=root_cert,
        issuer_key=root_key,
    )
    with open(org_cert_dir / f"{org_name}.p12", "wb") as org_p12:
        org_p12.write(
            serialize_p12(
                name=f"{org_name}.arrowhead.eu".encode(),
                key=org_keycert.key,
                cert=org_keycert.cert,
                cas=[root_cert],
                encryption_algorithm=set_password_encryption(password),
            )
        )
    with open(org_cert_dir / f"{org_name}.crt", "wb") as crt_org:
        crt_org.write(org_keycert.cert.public_bytes(serialization.Encoding.PEM))
    with open(org_cert_dir / f"{org_name}.key", "wb") as key_org:
        key_org.write(
            org_keycert.key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    return org_keycert


def generate_and_store_cloud_cert(
    cloud_name: str,
    org_name: str,
    cloud_cert_dir: Path,
    org_key: RSAPrivateKey,
    org_cert: Certificate,
    root_cert: Certificate,
    password: Optional[str],
) -> KeyCertPair:
    cloud_keycert = generate_ca_cert(
        f"{cloud_name}.{org_name}.arrowhead.eu",
        ca=True,
        path_length=2,
        issuer_cert=org_cert,
        issuer_key=org_key,
    )
    with open(cloud_cert_dir / f"{cloud_name}.p12", "wb") as cloud_p12:
        cloud_p12.write(
            serialize_p12(
                name=f"{cloud_name}.{org_name}.arrowhead.eu".encode(),
                key=cloud_keycert.key,
                cert=cloud_keycert.cert,
                cas=[org_cert, root_cert],
                encryption_algorithm=set_password_encryption(password),
            )
        )
    with open(cloud_cert_dir / f"{cloud_name}.crt", "wb") as cloud_crt:
        cloud_crt.write(cloud_keycert.cert.public_bytes(serialization.Encoding.PEM))
    with open(cloud_cert_dir / f"{cloud_name}.key", "wb") as cloud_key_file:
        cloud_key_file.write(
            cloud_keycert.key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    return cloud_keycert


def generate_cloud_files(
    cloud_config: ConfigDict,
    cloud_cert_dir: Path,
    cloud_key: RSAPrivateKey,
    cloud_cert: Certificate,
    org_cert: Certificate,
    root_cert: Certificate,
    password: str,
):
    cloud_name = cloud_config["cloud"]["cloud_name"]
    org_name = cloud_config["cloud"]["organization_name"]

    core_system_certs = generate_core_system_certs(cloud_config, cloud_cert, cloud_key)
    client_system_certs = generate_client_system_certs(
        cloud_config, cloud_cert, cloud_key
    )
    sysop_cert = generate_system_cert(
        f"sysop.{cloud_name}.{org_name}.arrowhead.eu",
        None,
        issuer_cert=cloud_cert,
        issuer_key=cloud_key,
    )

    if not all(
        (cloud_cert_dir / "sysop").with_suffix(suf).exists()
        for suf in (".p12", ".crt", ".key", ".ca")
    ):
        store_sysop(
            sysop_cert, root_cert, org_cert, cloud_cert, cloud_cert_dir, password
        )
    for core_name, core_cert in core_system_certs.items():
        if all(
            (core_cert_path := cloud_cert_dir / core_name).with_suffix(suf).exists()
            for suf in (".p12", ".crt", ".key")
        ):
            continue
        store_system_files(
            core_cert,
            core_cert_path,  # noqa
            root_cert,
            org_cert,
            cloud_cert,
            password,
        )
    for client_name, client_cert in client_system_certs.items():
        if all(
            (client_cert_path := cloud_cert_dir / client_name).with_suffix(suf).exists()
            for suf in {".p12", ".crt", ".key"}
        ):
            continue
        store_system_files(
            client_cert,
            client_cert_path,  # noqa
            root_cert,
            org_cert,
            cloud_cert,
            password,
        )
    store_truststore(cloud_cert, cloud_cert_dir, password)


def setup_certificates(cloud_config_path: Path, cloud_password: str, org_password: str):
    with open(cloud_config_path, "r") as cloud_config_file:
        cloud_config: ConfigDict = yaml.safe_load(cloud_config_file)

    cloud_name = cloud_config["cloud"]["cloud_name"]
    org_name = cloud_config["cloud"]["organization_name"]

    cloud_dir = cloud_config_path.parent
    cloud_cert_dir = cloud_dir / "certs/crypto/"
    org_cert_dir = cloud_dir.parent / "org-certs/crypto/"
    root_cert_dir = cloud_dir.parent / "root-certs/crypto"

    # TODO: Invert this horrible stack of ifs
    if not cloud_cert_dir.exists():
        print("Cloud cert does not exist, generating from organization cert...")
        if not org_cert_dir.exists():
            print("Organization cert does not exist, generating from root cert...")
            if not root_cert_dir.exists():
                print("Root cert does not exist, generating self-signed root cert.")
                root_cert_dir.mkdir(parents=True)
                root_key, root_cert = generate_and_store_root_files(
                    root_cert_dir, "123456"  # Self signed roots are insecure.
                )
            else:
                with open(root_cert_dir / "root.p12", "rb") as root_p12:
                    root_key, root_cert, *_ = load_p12(  # type: ignore
                        root_p12.read(), "123456".encode()
                    )  # noqa
                    if not isinstance(root_key, RSAPrivateKey) or not isinstance(
                        root_cert, Certificate
                    ):
                        raise PyrrowheadError("Could not open root key or certificate")

            org_cert_dir.mkdir(parents=True)
            org_key, org_cert = generate_and_store_org_files(  # type: ignore
                org_name,
                org_cert_dir,
                root_key,
                root_cert,
                org_password,
            )
        else:
            with open(org_cert_dir / f"{org_name}.p12", "rb") as org_p12:
                org_key, org_cert, ca_certs = load_p12(  # type: ignore
                    org_p12.read(), org_password.encode()
                )
                if not isinstance(org_key, RSAPrivateKey) or not isinstance(
                    org_cert, Certificate
                ):
                    raise PyrrowheadError("Could not read org key or certificate")
                if len(ca_certs) != 1:
                    raise PyrrowheadError(
                        f"Organization certificate can only have one CA, "
                        f"currently has {len(ca_certs)}."
                    )
                root_cert = ca_certs[0]

        cloud_cert_dir.mkdir(parents=True)
        cloud_key, cloud_cert = generate_and_store_cloud_cert(
            cloud_name,
            org_name,
            cloud_cert_dir,
            org_key,
            org_cert,
            root_cert,
            cloud_password,
        )
    else:
        with open(cloud_cert_dir / f"{cloud_name}.p12", "rb") as cloud_cert_file:
            cloud_key, cloud_cert, ca_certs = load_p12(  # type: ignore
                cloud_cert_file.read(), cloud_password.encode()
            )
            if len(ca_certs) != 2:
                raise RuntimeError(
                    f"Cloud cert must have exactly two CAs, "
                    f"currently have {len(ca_certs)}."
                )
            org_cert, root_cert = ca_certs

    generate_cloud_files(
        cloud_config,
        cloud_cert_dir,
        cloud_key,
        cloud_cert,
        org_cert,
        root_cert,
        cloud_password,
    )
