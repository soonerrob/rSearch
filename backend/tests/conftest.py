"""Test configuration and fixtures."""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator, Dict, Generator, List
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.models import RedditPost, Subreddit
from app.models.audience import Audience
from app.models.comment import Comment
from app.models.theme import Theme
from app.services.reddit import RedditService
from app.services.themes import ThemeService
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

# Test settings
def get_test_settings() -> Settings:
    """Get test settings with test database."""
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///./test.db",
        REDDIT_CLIENT_ID="test_client_id",
        REDDIT_CLIENT_SECRET="test_client_secret",
        OPENAI_API_KEY="test_openai_key"
    )

# Override settings for tests
@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    """Override settings with test settings."""
    test_settings = get_test_settings()
    monkeypatch.setattr("app.core.config.get_settings", lambda: test_settings)
    return test_settings

# Test database engine
test_engine = create_async_engine(
    get_test_settings().DATABASE_URL,
    echo=True
)

# Test session factory
TestingSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Configure pytest-asyncio using markers
pytestmark = [
    pytest.mark.asyncio(scope="function"),
    pytest.mark.filterwarnings("ignore::DeprecationWarning")
]

# Configure logging
logging.basicConfig(level=logging.ERROR, force=True)
for name in ['aiohttp', 'asyncio']:
    logger = logging.getLogger(name)
    logger.setLevel(logging.ERROR)
    logger.addHandler(logging.NullHandler())
    logger.propagate = False

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
    engine = create_async_engine(get_settings().DATABASE_URL, echo=True)
    
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
    engine = create_async_engine(get_settings().DATABASE_URL, echo=True)
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

@pytest.fixture
def mock_audience():
    """Create a mock audience for testing."""
    return Audience(
        id=1,
        name="Test Audience",
        description="Test audience for unit tests",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def sample_posts() -> List[Dict]:
    """Create sample posts for testing."""
    return [
        {
            "id": 1,
            "reddit_id": "post1",
            "subreddit_name": "music",
            "title": "I'm new to music production and need help with mixing. What tools do you recommend?",
            "content": "I've been trying to mix my tracks but I'm not getting the results I want. Looking for software recommendations and tips.",
            "author": "user1",
            "score": 100,
            "num_comments": 15,
            "engagement_score": 0.8,
            "created_at": datetime.utcnow() - timedelta(days=1),
            "updated_at": datetime.utcnow() - timedelta(days=1)
        },
        {
            "id": 2,
            "reddit_id": "post2",
            "subreddit_name": "music",
            "title": "Having issues with my DAW",
            "content": "My software keeps having issues with latency and crashes. Anyone else experiencing this?",
            "author": "user2",
            "score": 50,
            "num_comments": 8,
            "engagement_score": 0.6,
            "created_at": datetime.utcnow() - timedelta(days=2),
            "updated_at": datetime.utcnow() - timedelta(days=2)
        }
    ]

@pytest.fixture
def sample_comments() -> List[Dict]:
    """Create sample comments for testing."""
    return [
        {
            "id": 1,
            "reddit_id": "comment1",
            "post_id": 1,
            "content": "I recommend starting with Reaper, it's affordable and powerful.",
            "author": "helper1",
            "score": 50,
            "depth": 0,
            "is_submitter": False,
            "engagement_score": 0.9,
            "created_at": datetime.utcnow() - timedelta(days=1),
            "updated_at": datetime.utcnow() - timedelta(days=1)
        },
        {
            "id": 2,
            "reddit_id": "comment2",
            "post_id": 2,
            "content": "Try increasing your buffer size and updating your drivers.",
            "author": "helper2",
            "score": 30,
            "depth": 0,
            "is_submitter": False,
            "engagement_score": 0.8,
            "created_at": datetime.utcnow() - timedelta(days=2),
            "updated_at": datetime.utcnow() - timedelta(days=2)
        }
    ]

@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
def mock_openai_response():
    """Get mock OpenAI response."""
    return {
        "answer": "This is a mock AI response for testing.",
        "confidence": 0.9,
        "sources": [
            {"title": "Test Post 1", "score": 100, "url": "https://reddit.com/test1"},
            {"title": "Test Post 2", "score": 90, "url": "https://reddit.com/test2"}
        ]
    }

@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return get_settings()

@pytest_asyncio.fixture(scope="function")
async def cleanup_sessions():
    """Clean up any remaining sessions after each test."""
    yield
    # Add cleanup code here if needed

@pytest_asyncio.fixture
def theme_service():
    """Create a ThemeService instance for testing."""
    return ThemeService()

@pytest.fixture(scope="function")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get test database session."""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Set up test database before tests."""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all) 