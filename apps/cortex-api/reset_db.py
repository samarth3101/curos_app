import asyncio

from app.infrastructure.database import get_engine
from app.shared.base_model import Base


async def reset_db():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database reset successfully.")

asyncio.run(reset_db())
