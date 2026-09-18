"""Re-encrypt resource items with the first configured Fernet key."""

import asyncio

from cryptography.fernet import MultiFernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import src.all_models  # noqa: F401
from src.database import SessionLocal
from src.resources.config import get_resource_encryption_keys, get_resource_fernet
from src.resources.models import ResourceItem

BATCH_SIZE = 500


async def rotate_resource_items(session: AsyncSession, fernet: MultiFernet) -> int:
    rotated = 0
    last_id = 0
    while True:
        items = list(
            await session.scalars(
                select(ResourceItem)
                .where(ResourceItem.id > last_id)
                .order_by(ResourceItem.id)
                .limit(BATCH_SIZE)
            )
        )
        if not items:
            return rotated

        for item in items:
            item.encrypted_value = fernet.rotate(item.encrypted_value.encode()).decode()
        last_id = items[-1].id
        rotated += len(items)
        await session.flush()


async def main() -> None:
    if len(get_resource_encryption_keys()) < 2:
        raise RuntimeError("Rotation requires RESOURCE_ENCRYPTION_KEYS=new_key,old_key[,older_key]")

    async with SessionLocal() as session, session.begin():
        rotated = await rotate_resource_items(session, get_resource_fernet())
    print(f"Rotated {rotated} resource item(s).")


if __name__ == "__main__":
    asyncio.run(main())
