from typing import Dict, TypedDict, Optional


class SystemDict(TypedDict):
    system_name: str
    address: str
    port: int
    domain: str


class CloudDict(TypedDict):
    cloud_name: str
    organization_name: str
    ssl_enabled: bool
    subnet: str
    core_systems: Dict[str, SystemDict]
    client_systems: Optional[Dict[str, SystemDict]]


class ConfigDict(TypedDict):
    cloud: CloudDict
