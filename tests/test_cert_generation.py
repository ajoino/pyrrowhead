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
    "san,exception",
    [
        ("id:127.0.0.1", PyrrowheadError),
        ("bad:127.0.0.1", PyrrowheadError),
        ("dnd:hob.goblin", PyrrowheadError),
        ("ip:127.0.0:1", ValueError),
    ],
)
def test_get_general_name_bad(san, exception):
    with pytest.raises(exception):
        get_general_name(san)
