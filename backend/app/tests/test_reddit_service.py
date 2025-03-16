import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from app.core.config import get_settings
from app.services.reddit import RedditService
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session

@pytest_asyncio.fixture
async def reddit_service(mock_db):
    """Create a RedditService instance with a mock db session"""
    with patch('asyncpraw.Reddit') as mock_reddit:
        # Setup mock Reddit instance with required attributes
        mock_reddit_instance = AsyncMock()
        settings = get_settings()
        mock_reddit_instance.client_id = settings.REDDIT_CLIENT_ID
        mock_reddit_instance.client_secret = settings.REDDIT_CLIENT_SECRET
        mock_reddit_instance.user_agent = settings.REDDIT_USER_AGENT
        mock_reddit_instance.read_only = True
        mock_reddit.return_value = mock_reddit_instance
        
        service = RedditService(db=mock_db)
        yield service
        if hasattr(service, 'close'):
            await service.close()

@pytest.mark.asyncio
async def test_reddit_client_initialization(reddit_service):
    """Test that the Reddit client is initialized with correct settings"""
    settings = get_settings()
    assert reddit_service.reddit.client_id == settings.REDDIT_CLIENT_ID
    assert reddit_service.reddit.client_secret == settings.REDDIT_CLIENT_SECRET
    assert reddit_service.reddit.user_agent == settings.REDDIT_USER_AGENT
    assert reddit_service.reddit.read_only == True

@pytest.mark.asyncio
async def test_get_subreddit_info(mock_db):
    """Test retrieving subreddit information"""
    with patch('asyncpraw.Reddit') as mock_reddit:
        # Setup mock subreddit
        mock_subreddit = AsyncMock()
        mock_subreddit.display_name = "testsubreddit"
        mock_subreddit.subscribers = 1000
        mock_subreddit.active_user_count = 100
        mock_subreddit.created_utc = 1600000000
        mock_subreddit.description = "Test description"
        
        # Setup mock Reddit instance
        mock_reddit_instance = AsyncMock()
        mock_reddit_instance.subreddit = AsyncMock()
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        mock_reddit.return_value = mock_reddit_instance
        
        # Create service with mock
        service = RedditService(db=mock_db)
        service.reddit = mock_reddit_instance
        
        # Test getting subreddit info
        info = await service.get_subreddit_info("testsubreddit")
        
        # Verify results
        assert info.name == "testsubreddit"
        assert info.subscribers == 1000
        assert info.active_users == 100
        assert info.description == "Test description"

@pytest.mark.asyncio
async def test_get_subreddit_posts(mock_db):
    """Test retrieving subreddit posts"""
    with patch('asyncpraw.Reddit') as mock_reddit:
        # Setup mock posts
        mock_posts = []
        for i in range(3):
            mock_author = AsyncMock()
            mock_author.__str__ = lambda self, i=i: f"author{i}"
            mock_post = AsyncMock(
                id=f"post{i}",
                title=f"Test Post {i}",
                selftext=f"Content {i}",
                author=mock_author,
                score=i*10,
                num_comments=i*5,
                created_utc=1600000000 + i*3600
            )
            mock_posts.append(mock_post)
        
        # Create an async iterator for the posts
        class AsyncIterator:
            def __init__(self, items):
                self.items = items
                self.index = 0
            
            def __aiter__(self):
                return self
            
            async def __anext__(self):
                try:
                    item = self.items[self.index]
                    self.index += 1
                    return item
                except IndexError:
                    raise StopAsyncIteration
        
        # Setup mock subreddit
        mock_subreddit = AsyncMock()
        mock_subreddit.top = AsyncMock()
        mock_subreddit.top.return_value = AsyncIterator(mock_posts)
        
        # Setup mock Reddit instance
        mock_reddit_instance = AsyncMock()
        mock_reddit_instance.subreddit = AsyncMock()
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        mock_reddit.return_value = mock_reddit_instance
        
        # Create service with mock
        service = RedditService(db=mock_db)
        service.reddit = mock_reddit_instance
        
        # Test getting posts
        posts = await service.get_subreddit_posts("testsubreddit", limit=3)
        
        # Verify results
        assert len(posts) == 3
        for i, post in enumerate(posts):
            assert post['id'] == f"post{i}"
            assert post['title'] == f"Test Post {i}"
            assert post['content'] == f"Content {i}"
            assert post['author'] == f"author{i}"
            assert post['score'] == i*10
            assert post['num_comments'] == i*5

@pytest.mark.asyncio
async def test_rate_limiting(mock_db):
    """Test that rate limiting is working"""
    with patch('asyncpraw.Reddit') as mock_reddit:
        # Setup mock subreddit that simulates rate limiting
        mock_subreddit = AsyncMock()
        mock_subreddit.display_name = "testsubreddit"
        mock_subreddit.subscribers = 1000
        mock_subreddit.active_user_count = 100
        mock_subreddit.created_utc = 1600000000
        mock_subreddit.description = "Test description"
        
        # Make the second call raise a rate limit error
        calls = 0
        async def mock_load():
            nonlocal calls
            calls += 1
            if calls > 1:
                raise Exception("RATELIMIT: 5 seconds")
        mock_subreddit.load = mock_load
        
        # Setup mock Reddit instance
        mock_reddit_instance = AsyncMock()
        mock_reddit_instance.subreddit = AsyncMock()
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        mock_reddit.return_value = mock_reddit_instance
        
        # Create service with mock
        service = RedditService(db=mock_db)
        service.reddit = mock_reddit_instance
        
        # First call should succeed
        info = await service.get_subreddit_info("testsubreddit")
        assert info.name == "testsubreddit"
        
        # Second call should handle rate limiting
        with pytest.raises(Exception) as exc_info:
            await service.get_subreddit_info("testsubreddit")
        assert "RATELIMIT: 5 seconds" in str(exc_info.value)

@pytest.mark.asyncio
async def test_error_handling(mock_db):
    """Test error handling for various scenarios"""
    with patch('asyncpraw.Reddit') as mock_reddit:
        # Setup mock subreddit that raises error
        mock_subreddit = AsyncMock()
        mock_subreddit.display_name = "nonexistent"
        
        async def mock_load():
            raise Exception("Subreddit not found")
        mock_subreddit.load = mock_load
        
        # Setup mock Reddit instance
        mock_reddit_instance = AsyncMock()
        mock_reddit_instance.subreddit = AsyncMock()
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        mock_reddit.return_value = mock_reddit_instance
        
        # Create service with mock
        service = RedditService(db=mock_db)
        service.reddit = mock_reddit_instance
        
        # Test error handling
        with pytest.raises(Exception) as exc_info:
            await service.get_subreddit_info("nonexistent")
        assert "Subreddit not found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_read_only_mode(mock_db):
    """Test that the client is in read-only mode"""
    with patch('asyncpraw.Reddit') as mock_reddit:
        # Setup mock Reddit instance with read_only property
        mock_reddit_instance = AsyncMock()
        mock_reddit_instance.read_only = True
        
        # Setup mock subreddit with subscribe method
        mock_subreddit = AsyncMock()
        async def mock_subscribe():
            raise Exception("Write operation not allowed")
        mock_subreddit.subscribe = mock_subscribe
        
        # Setup mock Reddit instance
        mock_reddit_instance.subreddit = AsyncMock()
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        mock_reddit.return_value = mock_reddit_instance
        
        # Create service with mock
        service = RedditService(db=mock_db)
        service.reddit = mock_reddit_instance
        
        # Verify read-only mode
        assert service.reddit.read_only == True
        
        # Get the subreddit instance
        subreddit = await service.reddit.subreddit("test")
        
        # Attempt write operation should fail
        with pytest.raises(Exception) as exc_info:
            await subreddit.subscribe()
        assert "Write operation not allowed" in str(exc_info.value) 