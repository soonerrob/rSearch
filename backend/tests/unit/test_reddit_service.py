from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from app.models import Subreddit
from app.services.reddit import RedditService

pytestmark = pytest.mark.asyncio

class AsyncIterator:
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item

@pytest.mark.asyncio
class TestRedditService:
    """Test suite for RedditService"""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, reddit_service):
        """Setup test fixtures."""
        self.service = reddit_service
        self.mock_client = AsyncMock()
        self.service.reddit = self.mock_client
        return self

    async def test_get_subreddit_posts_async(self, mock_reddit_post):
        """Test getting posts from a subreddit asynchronously."""
        # Setup mock
        mock_subreddit = AsyncMock()
        mock_subreddit.top = AsyncMock()
        mock_subreddit.top.return_value = AsyncIterator([mock_reddit_post])
        self.mock_client.subreddit = AsyncMock(return_value=mock_subreddit)
        
        # Test
        posts = await self.service.get_subreddit_posts_async("test")
        
        # Verify
        assert len(posts) == 1
        assert posts[0] == mock_reddit_post
        self.mock_client.subreddit.assert_called_once_with("test")
        mock_subreddit.top.assert_called_once_with(time_filter="year", limit=500)

    async def test_get_trending_subreddits_async(self, mock_subreddit):
        """Test getting trending subreddits asynchronously."""
        # Setup mock
        mock_subreddits = [mock_subreddit]
        mock_listing = AsyncIterator(mock_subreddits)
        mock_subreddits_obj = AsyncMock()
        mock_subreddits_obj.popular = AsyncMock()
        mock_subreddits_obj.popular.return_value = mock_listing
        self.mock_client.subreddits = mock_subreddits_obj
        
        # Test
        subreddits = await self.service.get_trending_subreddits_async()
        
        # Verify
        assert len(subreddits) == 1
        assert isinstance(subreddits[0], Subreddit)
        assert subreddits[0].display_name == mock_subreddit.display_name
        mock_subreddits_obj.popular.assert_called_once_with(limit=100)

    async def test_search_subreddits_async(self, mock_subreddit):
        """Test searching subreddits asynchronously."""
        # Setup mock
        mock_subreddits = [mock_subreddit]
        mock_listing = AsyncIterator(mock_subreddits)
        mock_subreddits_obj = AsyncMock()
        mock_subreddits_obj.search = AsyncMock()
        mock_subreddits_obj.search.return_value = mock_listing
        self.mock_client.subreddits = mock_subreddits_obj
        
        # Test
        subreddits = await self.service.search_subreddits_async("test")
        
        # Verify
        assert len(subreddits) == 1
        assert isinstance(subreddits[0], Subreddit)
        assert subreddits[0].display_name == mock_subreddit.display_name
        mock_subreddits_obj.search.assert_called_once_with("test", limit=200)

    async def test_get_subreddit_info_async(self, mock_subreddit):
        """Test getting subreddit info asynchronously."""
        # Setup mock
        self.mock_client.subreddit = AsyncMock(return_value=mock_subreddit)
        
        # Test
        subreddit = await self.service.get_subreddit_info_async("test")
        
        # Verify
        assert isinstance(subreddit, Subreddit)
        assert subreddit.display_name == mock_subreddit.display_name
        self.mock_client.subreddit.assert_called_once_with("test") 