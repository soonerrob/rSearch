import asyncio

from app.core.database import AsyncSessionLocal, engine, get_session
from sqlalchemy import text


async def test_db_connection():
    try:
        # Test engine
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT 1'))
            print('Engine connection test: PASSED')
        
        # Test session factory
        async with AsyncSessionLocal() as session:
            result = await session.execute(text('SELECT 1'))
            print('Session factory test: PASSED')
        
        # Test session dependency
        async for session in get_session():
            result = await session.execute(text('SELECT 1'))
            print('Session dependency test: PASSED')
            break
            
    except Exception as e:
        print(f'Test failed: {str(e)}')

if __name__ == "__main__":
    asyncio.run(test_db_connection()) 