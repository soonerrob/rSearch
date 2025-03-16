from typing import AsyncGenerator

from app.core.database import get_session
from app.services.reddit import RedditService
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


async def get_reddit_service(db: AsyncSession = Depends(get_session)) -> RedditService:
    """Dependency for getting RedditService instance."""
    return RedditService(db)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async for session in get_session():
        yield session 