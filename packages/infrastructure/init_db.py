import asyncio
from sqlalchemy import text
from packages.infrastructure.database import engine
from packages.domain.models import Base
from packages.observability.logger import logger


async def init_database():
    async with engine.begin() as conn:
        logger.info("Enabling PostgreSQL extensions: vector, pg_trgm")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        logger.info("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema initialized successfully.")


if __name__ == "__main__":
    asyncio.run(init_database())

