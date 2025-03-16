import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.cancellation import CancellationScope, CancellationToken
from app.models import Subreddit
from app.routers.subreddits import router
from fastapi import HTTPException
from sqlalchemy import select


@pytest.mark.asyncio
class TestSubredditRoutes:
    """Test suite for subreddit routes."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, async_session):
        """Setup test fixtures."""
        self.session = await anext(async_session)

    @pytest_asyncio.fixture
    async def mock_subreddit(self):
        """Create a mock subreddit for testing."""
        subreddit = Subreddit(
            name="testsubreddit",
            display_name="Test Subreddit",
            description="Test Description",
            subscribers=1000,
            active_users=100,
            posts_per_day=10,
            comments_per_day=50
        )
        self.session.add(subreddit)
        await self.session.commit()
        return subreddit

    async def test_get_trending_subreddits(self, mock_subreddit):
        """Test getting trending subreddits."""
        # Test normal operation
        subreddits = await router.get_trending_subreddits(self.session)
        assert len(subreddits) == 1
        assert subreddits[0].id == mock_subreddit.id
        assert subreddits[0].name == "testsubreddit"

    async def test_search_subreddits(self, mock_subreddit):
        """Test searching subreddits."""
        # Test normal operation
        subreddits = await router.search_subreddits("test", self.session)
        assert len(subreddits) == 1
        assert subreddits[0].id == mock_subreddit.id
        assert subreddits[0].name == "testsubreddit"

        # Test no results
        subreddits = await router.search_subreddits("nonexistent", self.session)
        assert len(subreddits) == 0

    async def test_get_subreddit_info(self, mock_subreddit):
        """Test getting subreddit information."""
        # Test normal operation
        subreddit = await router.get_subreddit_info("testsubreddit", self.session)
        assert subreddit.id == mock_subreddit.id
        assert subreddit.name == "testsubreddit"
        assert subreddit.display_name == "Test Subreddit"

        # Test subreddit not found
        with pytest.raises(HTTPException) as exc_info:
            await router.get_subreddit_info("nonexistent", self.session)
        assert exc_info.value.status_code == 404
        assert "Subreddit not found" in str(exc_info.value.detail)

    async def test_get_subreddit_posts(self, mock_subreddit):
        """Test getting subreddit posts."""
        # Test normal operation
        posts = await router.get_subreddit_posts("testsubreddit", self.session)
        assert isinstance(posts, list)

        # Test subreddit not found
        with pytest.raises(HTTPException) as exc_info:
            await router.get_subreddit_posts("nonexistent", self.session)
        assert exc_info.value.status_code == 404
        assert "Subreddit not found" in str(exc_info.value.detail) 