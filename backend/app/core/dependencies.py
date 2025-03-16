from typing import AsyncGenerator

from app.core.database import get_async_session
from app.services.reddit import RedditService
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


async def get_async_reddit_service() -> RedditService:
    """Get an async RedditService instance."""
    return RedditService(use_async=True)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async for session in get_async_session():
        yield session 