from types import SimpleNamespace

from cryptography.fernet import Fernet, MultiFernet

from scripts.rotate_resource_encryption import rotate_resource_items


class FakeSession:
    def __init__(self, items):
        self.items = items
        self.calls = 0
        self.flush_calls = 0

    async def scalars(self, _statement):
        self.calls += 1
        return self.items if self.calls == 1 else []

    async def flush(self):
        self.flush_calls += 1


async def test_rotation_reencrypts_old_tokens_with_primary_key():
    new_key = Fernet.generate_key()
    old_key = Fernet.generate_key()
    item = SimpleNamespace(
        id=1,
        encrypted_value=Fernet(old_key).encrypt(b"secret").decode(),
    )
    session = FakeSession([item])

    count = await rotate_resource_items(session, MultiFernet([Fernet(new_key), Fernet(old_key)]))

    assert count == 1
    assert Fernet(new_key).decrypt(item.encrypted_value.encode()) == b"secret"
    assert session.flush_calls == 1
