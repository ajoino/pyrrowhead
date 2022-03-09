from typing import Dict, TypedDict, Optional, List


class SystemDict(TypedDict):
    system_name: str
    address: str
    port: int


class ClientSystemDict(SystemDict):
    sans: List[str]


class CoreSystemDict(SystemDict):
    domain: str


class CloudDict(TypedDict):
    cloud_name: str
    organization_name: str
    ssl_enabled: bool
    subnet: str
    core_san: List[str]
    core_systems: Dict[str, CoreSystemDict]
    client_systems: Dict[str, ClientSystemDict]


class ConfigDict(TypedDict):
    cloud: CloudDict
