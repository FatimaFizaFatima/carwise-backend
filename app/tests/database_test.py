import asyncio
from sqlalchemy import text
from app.db.database import SessionLocal

async def test_database_connection():
    async with SessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        print("Database result:", result.scalar())


if __name__ == "__main__":
    asyncio.run(test_database_connection())