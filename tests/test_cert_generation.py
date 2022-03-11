import pytest
from cryptography.hazmat.primitives.serialization import (
    NoEncryption,
    BestAvailableEncryption,
)

from pyrrowhead.new_certificate_generation.generate_certificates import (
    set_password_encryption,
    get_general_name,
)
from pyrrowhead.utils import PyrrowheadError


def test_no_password():
    assert isinstance(set_password_encryption(), NoEncryption)


def test_simple_password():
    best_encryption = BestAvailableEncryption("abc123".encode())
    assert set_password_encryption("abc123").password == best_encryption.password


@pytest.mark.parametrize(
    "san",
    [
        "id:127.0.0.1",
        "bad:127.0.0.1",
        "ip:127.0.0:1",
        "dnd:hob.goblin",
        "dns:owl_bear",
    ],
)
def test_get_general_name_bad(san):
    with pytest.raises(PyrrowheadError):
        get_general_name(san)
