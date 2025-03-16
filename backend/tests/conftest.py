import asyncio
from datetime import datetime
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from app.core.config import get_settings
from app.models import RedditPost, Subreddit
from app.models.audience import Audience
from app.models.post import Post
from app.models.theme import Theme
from app.services.reddit import RedditService
from app.services.themes import ThemeService
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Test database URL
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/reddit_research_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_reddit_post():
    """Mock Reddit post for testing"""
    post = MagicMock()
    post.id = "test_id"
    post.title = "Test Post"
    post.selftext = "Test content"
    post.score = 100
    post.created_utc = 1234567890
    post.url = "https://reddit.com/test"
    post.permalink = "/r/test/comments/test_id"
    post.subreddit.display_name = "test"
    return post

@pytest.fixture
def mock_subreddit():
    """Mock subreddit for testing"""
    subreddit = MagicMock()
    subreddit.display_name = "test"
    subreddit.title = "Test Subreddit"
    subreddit.subscribers = 1000
    return subreddit

@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create a test database engine."""
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    await engine.dispose()

@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for a test."""
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

@pytest_asyncio.fixture
async def async_engine():
    """Create async engine for testing"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async session for testing"""
    async_session = AsyncSessionLocal()
    try:
        yield async_session
    finally:
        await async_session.close()

@pytest_asyncio.fixture
async def reddit_service():
    """Mock Reddit service for testing"""
    service = AsyncMock(spec=RedditService)
    service.get_posts.return_value = [
        {
            "id": "test_id",
            "title": "Test Post",
            "content": "Test content",
            "author": "test_author",
            "score": 100,
            "num_comments": 10,
            "created_utc": datetime.now().timestamp(),
            "url": "https://reddit.com/test",
            "permalink": "/r/test/comments/test_id"
        }
    ]
    return service

@pytest_asyncio.fixture
async def theme_service(session, reddit_service):
    """Create theme service for testing"""
    return ThemeService(session, reddit_service)

@pytest_asyncio.fixture
async def mock_audience(session):
    """Create a mock audience for testing"""
    audience = Audience(name="Test Audience", timeframe="year", posts_per_subreddit=100)
    session.add(audience)
    await session.flush()
    return audience 