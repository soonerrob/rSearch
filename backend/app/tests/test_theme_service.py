import asyncio
from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.audience import Audience, AudienceSubreddit
from app.models.reddit_post import RedditPost
from app.models.subreddit import Subreddit
from app.models.theme import Theme
from app.services.themes import ThemeService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select as sqlmodel_select


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    mock = AsyncMock(spec=AsyncSession)
    return mock


@pytest.fixture
def mock_subreddits() -> List[Subreddit]:
    """Create mock subreddits"""
    return [
        Subreddit(
            name="python",
            display_name="Python",
            description="Python programming language",
            subscribers=1000000,
            active_users=5000,
            posts_per_day=100,
            created_at=datetime.utcnow() - timedelta(days=365)
        ),
        Subreddit(
            name="programming",
            display_name="Programming",
            description="Programming discussions",
            subscribers=2000000,
            active_users=10000,
            posts_per_day=200,
            created_at=datetime.utcnow() - timedelta(days=365)
        )
    ]


@pytest.fixture
def mock_audience(mock_subreddits) -> Audience:
    """Create a mock audience with subreddits"""
    audience = Audience(
        id=1,
        name="Test Audience",
        description="Test audience for developers",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        collection_progress=0.0,
        timeframe="week"  # Set a timeframe for testing
    )
    
    # Create AudienceSubreddit relationships
    audience_subreddits = [
        AudienceSubreddit(
            audience_id=audience.id,
            subreddit_name=subreddit.name,
            audience=audience,
            subreddit=subreddit
        )
        for subreddit in mock_subreddits
    ]
    
    audience.subreddits = audience_subreddits
    return audience


@pytest.fixture
def theme_service(mock_db) -> ThemeService:
    """Create a theme service instance with mock dependencies"""
    return ThemeService(db=mock_db)


@pytest.mark.asyncio
async def test_collect_posts_for_audience(theme_service, mock_db, mock_audience):
    """Test collecting posts for an audience"""
    # Mock database query for getting audience
    mock_audience_result = MagicMock()
    mock_audience_result.scalar_one_or_none = AsyncMock(return_value=mock_audience)
    
    # Mock database query for checking existing posts
    mock_post_result = MagicMock()
    mock_post_result.scalar_one_or_none = AsyncMock(side_effect=lambda: None)  # Always return None for new posts
    
    # Mock db.execute to return different results based on the query
    async def mock_execute(query):
        # Check the model being selected by looking at the SQL string
        query_str = str(query)
        if 'FROM audience' in query_str:
            return mock_audience_result
        return mock_post_result  # Default to post result for any other query
    mock_db.execute = AsyncMock(side_effect=mock_execute)
    
    # Mock db.add and db.commit
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    
    # Mock posts for each subreddit
    mock_posts = []
    for audience_subreddit in mock_audience.subreddits:
        subreddit_posts = [
            {
                'id': f"post_{audience_subreddit.subreddit.name}_{i}",
                'reddit_id': f"post_{audience_subreddit.subreddit.name}_{i}",
                'subreddit_name': audience_subreddit.subreddit.name,
                'title': f"Test Post {i}",
                'content': f"Test Content {i}",
                'author': f"user_{i}",
                'score': 100,
                'num_comments': 10,
                'created_at': datetime.utcnow() - timedelta(days=1)
            }
            for i in range(1, 3)  # 2 posts per subreddit
        ]
        mock_posts.extend(subreddit_posts)
    
    # Mock RedditService
    with patch('app.services.themes.RedditService') as mock_reddit_service:
        mock_reddit_instance = AsyncMock()
        mock_reddit_instance.get_subreddit_posts = AsyncMock(return_value=mock_posts)
        mock_reddit_service.return_value = mock_reddit_instance
        
        # Test collecting posts
        collected_posts = await theme_service.collect_posts_for_audience(mock_audience.id)
        
        assert len(collected_posts) == len(mock_posts)
        assert mock_audience.collection_progress == 100.0


@pytest.mark.asyncio
async def test_analyze_themes(theme_service, mock_db, mock_audience):
    """Test analyzing themes from collected posts"""
    # Mock posts
    mock_posts = [
        RedditPost(
            id=i,
            reddit_id=f"post_{i}",
            subreddit_name="python",
            title=f"Test Post {i}",
            content=f"Test Content {i}",
            author=f"user_{i}",
            score=100,
            num_comments=10,
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        for i in range(5)
    ]
    
    # Mock theme creation
    mock_theme = Theme(
        id=1,
        audience_id=mock_audience.id,
        category="Test Theme",
        summary="Test theme summary"
    )
    
    # Mock database operations for getting audience
    mock_audience_result = MagicMock()
    mock_audience_result.scalar_one_or_none = AsyncMock(return_value=mock_audience)
    
    # Mock database operations for getting posts
    mock_posts_result = MagicMock()
    mock_posts_result.scalars = MagicMock(return_value=mock_posts_result)
    mock_posts_result.all = MagicMock(return_value=mock_posts)
    
    # Set up mock.execute to return different results based on the query
    async def mock_execute(query):
        if isinstance(query, str) or "Audience" in str(query):
            return mock_audience_result
        return mock_posts_result
    
    mock_db.execute = AsyncMock(side_effect=mock_execute)
    
    # Test theme analysis
    themes = await theme_service.analyze_themes(mock_audience.id)
    
    assert len(themes) > 0
    assert all(isinstance(theme, Theme) for theme in themes)


@pytest.mark.asyncio
async def test_refresh_themes(theme_service, mock_db, mock_audience):
    """Test refreshing themes for an audience"""
    # Mock existing themes
    mock_themes = [
        Theme(
            id=i,
            audience_id=mock_audience.id,
            category=f"Theme {i}",
            summary=f"Summary {i}"
        )
        for i in range(3)
    ]
    
    # Mock database operations for getting audience
    mock_audience_result = MagicMock()
    mock_audience_result.scalar_one_or_none = AsyncMock(return_value=mock_audience)
    
    # Mock database operations for getting themes and posts
    mock_themes_result = MagicMock()
    mock_themes_result.scalars = MagicMock(return_value=mock_themes_result)
    mock_themes_result.all = MagicMock(return_value=mock_themes)
    
    # Set up mock.execute to return different results based on the query
    async def mock_execute(query):
        if isinstance(query, str) or "Audience" in str(query):
            return mock_audience_result
        return mock_themes_result
    
    mock_db.execute = AsyncMock(side_effect=mock_execute)
    
    # Test theme refresh
    await theme_service.refresh_themes(mock_audience.id)
    
    # Verify that old themes were deleted and new ones were created
    mock_db.execute.assert_called()


@pytest.mark.asyncio
async def test_error_handling(theme_service, mock_db):
    """Test error handling in theme service"""
    # Test non-existent audience
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = AsyncMock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)
    
    with pytest.raises(ValueError) as exc_info:
        await theme_service.collect_posts_for_audience(999)
    
    assert str(exc_info.value) == "Audience with id 999 not found" 