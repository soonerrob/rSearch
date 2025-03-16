import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from app.core.cancellation import CancellationScope, CancellationToken
from app.models import (Audience, RedditPost, Subreddit, Theme, ThemePost,
                        ThemeQuestion)
from sqlalchemy import select


@pytest.mark.asyncio
class TestThemeService:
    """Test suite for ThemeService async operations."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, theme_service, mock_reddit_post, async_session):
        """Setup test fixtures."""
        self.service = theme_service
        self.mock_post = mock_reddit_post
        self.session = await anext(async_session)

    @pytest_asyncio.fixture
    async def mock_audience(self):
        """Create a mock audience for testing."""
        # Create a test subreddit
        test_subreddit = Subreddit(
            name="testsubreddit",
            display_name="Test Subreddit",
            title="Test Subreddit Title",
            description="Test Description",
            subscribers=1000,
            active_users=100,
            posts_per_day=10,
            comments_per_day=50,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Create the audience
        audience = Audience(
            name="Test Audience",
            timeframe="day",
            collection_progress=0.0
        )

        # Add the subreddit to the session first
        self.session.add(test_subreddit)
        await self.session.flush()

        # Now add the audience and create the relationship
        audience.subreddits.append(test_subreddit)
        self.session.add(audience)
        await self.session.flush()
        await self.session.commit()
        
        return audience

    async def test_collect_posts_for_audience_async(self, mock_audience):
        """Test collecting posts for an audience asynchronously."""
        # Setup mock
        mock_subreddit = AsyncMock()
        mock_subreddit.hot.return_value = [self.mock_post]
        self.service.reddit_service.client.subreddit.return_value = mock_subreddit

        # Test normal operation
        async with CancellationScope() as token:
            posts = await self.service.collect_posts_for_audience_async(mock_audience.id, cancellation_token=token)
            assert len(posts) == 1
            assert posts[0].id == self.mock_post.id
            assert posts[0].title == self.mock_post.title
            self.service.reddit_service.client.subreddit.assert_called_once_with("testsubreddit")

        # Test cancellation
        token = CancellationToken()
        token.cancel()
        with pytest.raises(asyncio.CancelledError):
            await self.service.collect_posts_for_audience_async(mock_audience.id, cancellation_token=token)

    async def test_analyze_themes_async(self, mock_audience):
        """Test analyzing themes asynchronously."""
        # Setup mock
        mock_subreddit = AsyncMock()
        mock_subreddit.hot.return_value = [self.mock_post]
        self.service.reddit_service.client.subreddit.return_value = mock_subreddit

        # Test normal operation
        async with CancellationScope() as token:
            themes = await self.service.analyze_themes_async(mock_audience.id, cancellation_token=token)
            assert len(themes) > 0
            assert all(isinstance(theme, Theme) for theme in themes)
            assert all(theme.category for theme in themes)
            assert all(theme.summary for theme in themes)

        # Test cancellation
        token = CancellationToken()
        token.cancel()
        with pytest.raises(asyncio.CancelledError):
            await self.service.analyze_themes_async(mock_audience.id, cancellation_token=token)

    async def test_refresh_themes_async(self, mock_audience):
        """Test refreshing themes asynchronously."""
        # Setup mock
        mock_subreddit = AsyncMock()
        mock_subreddit.hot.return_value = [self.mock_post]
        self.service.reddit_service.client.subreddit.return_value = mock_subreddit

        # Test normal operation
        async with CancellationScope() as token:
            await self.service.refresh_themes_async(mock_audience.id, cancellation_token=token)
            # Verify themes were refreshed
            result = await self.session.execute(
                select(Theme).where(Theme.audience_id == mock_audience.id)
            )
            themes = result.scalars().all()
            assert len(themes) > 0

        # Test cancellation
        token = CancellationToken()
        token.cancel()
        with pytest.raises(asyncio.CancelledError):
            await self.service.refresh_themes_async(mock_audience.id, cancellation_token=token)

    async def test_get_recent_posts_async(self, mock_audience):
        """Test getting recent posts asynchronously."""
        # Create some test posts
        test_post = RedditPost(
            reddit_id="test123",
            subreddit_name="testsubreddit",
            title="Test Post",
            content="Test Content",
            author="testuser",
            score=100,
            num_comments=10,
            created_at=datetime.utcnow(),
            collected_at=datetime.utcnow()
        )
        self.session.add(test_post)
        await self.session.commit()

        # Test normal operation
        async with CancellationScope() as token:
            posts = await self.service._get_recent_posts_async(mock_audience.id, cancellation_token=token)
            assert len(posts) == 1
            assert posts[0].reddit_id == "test123"

        # Test cancellation
        token = CancellationToken()
        token.cancel()
        with pytest.raises(asyncio.CancelledError):
            await self.service._get_recent_posts_async(mock_audience.id, cancellation_token=token) 