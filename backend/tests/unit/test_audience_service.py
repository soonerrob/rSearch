import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from app.core.cancellation import CancellationScope, CancellationToken
from app.models import (Audience, AudienceSubreddit, RedditPost, Subreddit,
                        Theme, ThemePost, ThemeQuestion)
from app.services.audiences import AudienceService
from sqlalchemy import select


@pytest.mark.asyncio
class TestAudienceService:
    """Test suite for AudienceService async operations."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, async_session):
        """Setup test fixtures."""
        self.session = await anext(async_session)
        self.service = AudienceService(self.session)
        
        # Mock Reddit service
        self.service.reddit_service = AsyncMock()
        self.service.reddit_service.get_subreddit_info_async.return_value = Subreddit(
            name="testsubreddit",
            display_name="Test Subreddit",
            description="Test Description",
            subscribers=1000,
            active_users=100,
            posts_per_day=10,
            comments_per_day=50,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock Theme service
        self.service.theme_service = AsyncMock()

    @pytest_asyncio.fixture
    async def test_audience(self):
        """Create a test audience."""
        audience = Audience(
            name="Test Audience",
            description="Test Description",
            timeframe="day",
            posts_per_subreddit=100,
            is_collecting=False,
            collection_progress=0.0
        )
        
        # Add a test subreddit
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
        await self.session.flush()
        
        # Create audience-subreddit link
        audience_subreddit = AudienceSubreddit(subreddit_name="testsubreddit")
        audience.subreddits.append(audience_subreddit)
        
        self.session.add(audience)
        await self.session.commit()
        return audience

    async def test_create_audience(self):
        """Test creating a new audience."""
        # Test data
        name = "New Audience"
        description = "Test Description"
        subreddit_names = ["testsubreddit", "anothersubreddit"]
        
        # Create audience
        audience = await self.service.create_audience(
            name=name,
            description=description,
            subreddit_names=subreddit_names
        )
        
        # Verify audience was created
        assert audience.name == name
        assert audience.description == description
        assert len(audience.subreddits) == 2
        assert audience.is_collecting == True
        assert audience.collection_progress == 0.0
        
        # Verify Reddit service was called
        self.service.reddit_service.get_subreddit_info_async.assert_called()
        self.service.reddit_service.sync_subreddit_to_db_async.assert_called()

    async def test_collect_initial_data(self, test_audience):
        """Test collecting initial data for an audience."""
        # Setup mocks
        self.service.theme_service.collect_posts_for_audience.return_value = []
        self.service.theme_service.analyze_themes.return_value = []
        
        # Test normal operation
        async with CancellationScope() as token:
            await self.service.collect_initial_data(test_audience.id, token)
            
            # Verify theme service was called
            self.service.theme_service.collect_posts_for_audience.assert_called_once()
            self.service.theme_service.analyze_themes.assert_called_once()
            
            # Verify audience status was updated
            audience = await self.session.get(Audience, test_audience.id)
            assert audience.is_collecting == False
            assert audience.collection_progress == 100.0
        
        # Test cancellation
        token = CancellationToken()
        token.cancel()
        with pytest.raises(asyncio.CancelledError):
            await self.service.collect_initial_data(test_audience.id, token)

    async def test_update_audience(self, test_audience):
        """Test updating an audience."""
        # Test data
        new_name = "Updated Audience"
        new_description = "Updated Description"
        new_timeframe = "week"
        new_posts_per_subreddit = 200
        new_subreddit_names = ["testsubreddit", "newsubreddit"]
        
        # Update audience
        updated = await self.service.update_audience(
            audience_id=test_audience.id,
            name=new_name,
            description=new_description,
            timeframe=new_timeframe,
            posts_per_subreddit=new_posts_per_subreddit,
            subreddit_names=new_subreddit_names
        )
        
        # Verify updates
        assert updated.name == new_name
        assert updated.description == new_description
        assert updated.timeframe == new_timeframe
        assert updated.posts_per_subreddit == new_posts_per_subreddit
        assert len(updated.subreddits) == 2
        assert {s.subreddit_name for s in updated.subreddits} == set(new_subreddit_names)
        
        # Verify Reddit service was called for new subreddit
        self.service.reddit_service.get_subreddit_info_async.assert_called_once_with("newsubreddit")
        self.service.reddit_service.sync_subreddit_to_db_async.assert_called_once()

    async def test_delete_audience(self, test_audience):
        """Test deleting an audience."""
        # Create some test data
        theme = Theme(
            audience_id=test_audience.id,
            category="Test Category",
            summary="Test Summary"
        )
        self.session.add(theme)
        await self.session.flush()
        
        post = RedditPost(
            reddit_id="test123",
            subreddit_name="testsubreddit",
            title="Test Post",
            content="Test Content",
            author="testuser",
            score=100,
            num_comments=10
        )
        self.session.add(post)
        await self.session.flush()
        
        theme_post = ThemePost(
            theme_id=theme.id,
            post_id=post.id,
            relevance_score=0.8
        )
        self.session.add(theme_post)
        
        theme_question = ThemeQuestion(
            theme_id=theme.id,
            question="Test Question"
        )
        self.session.add(theme_question)
        await self.session.commit()
        
        # Delete audience
        await self.service.delete_audience(test_audience.id)
        
        # Verify everything was deleted
        result = await self.session.execute(
            select(Audience).where(Audience.id == test_audience.id)
        )
        assert result.first() is None
        
        result = await self.session.execute(
            select(Theme).where(Theme.audience_id == test_audience.id)
        )
        assert result.first() is None
        
        result = await self.session.execute(
            select(ThemePost).where(ThemePost.theme_id == theme.id)
        )
        assert result.first() is None
        
        result = await self.session.execute(
            select(ThemeQuestion).where(ThemeQuestion.theme_id == theme.id)
        )
        assert result.first() is None
        
        result = await self.session.execute(
            select(RedditPost).where(RedditPost.id == post.id)
        )
        assert result.first() is None
        
        result = await self.session.execute(
            select(AudienceSubreddit).where(AudienceSubreddit.audience_id == test_audience.id)
        )
        assert result.first() is None 