import asyncio

from app.core.database import AsyncSessionLocal
from sqlalchemy import text


async def check_analyses():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text('SELECT COUNT(*) FROM post_analysis'))
        count = result.scalar()
        print(f'Number of post analyses: {count}')

if __name__ == '__main__':
    asyncio.run(check_analyses()) 