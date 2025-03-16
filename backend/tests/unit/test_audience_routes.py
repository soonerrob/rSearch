import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.cancellation import CancellationScope, CancellationToken
from app.models import Audience, AudienceSubreddit, Subreddit
from app.routers.audiences import router
from fastapi import HTTPException
from sqlalchemy import select


@pytest.mark.asyncio
class TestAudienceRoutes:
    """Test suite for audience routes."""

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

    @pytest_asyncio.fixture
    async def mock_audience(self, mock_subreddit):
        """Create a mock audience for testing."""
        audience = Audience(
            name="Test Audience",
            description="Test Description",
            timeframe="day",
            posts_per_subreddit=100,
            is_collecting=False,
            collection_progress=0.0
        )
        
        # Create audience-subreddit link
        audience_subreddit = AudienceSubreddit(subreddit_name="testsubreddit")
        audience.subreddits.append(audience_subreddit)
        
        self.session.add(audience)
        await self.session.commit()
        return audience

    async def test_create_audience(self, mock_subreddit):
        """Test creating a new audience."""
        # Test data
        name = "New Audience"
        description = "Test Description"
        subreddit_names = ["testsubreddit"]
        
        # Create audience
        audience = await router.create_audience(
            name=name,
            description=description,
            subreddit_names=subreddit_names,
            db=self.session
        )
        
        # Verify audience was created
        assert audience.name == name
        assert audience.description == description
        assert len(audience.subreddits) == 1
        assert audience.is_collecting == True
        assert audience.collection_progress == 0.0

    async def test_get_audiences(self, mock_audience):
        """Test getting all audiences."""
        # Test normal operation
        audiences = await router.get_audiences(self.session)
        assert len(audiences) == 1
        assert audiences[0].id == mock_audience.id
        assert audiences[0].name == "Test Audience"

    async def test_get_audience(self, mock_audience):
        """Test getting a specific audience."""
        # Test normal operation
        audience = await router.get_audience(mock_audience.id, self.session)
        assert audience.id == mock_audience.id
        assert audience.name == "Test Audience"
        assert len(audience.subreddits) == 1

        # Test audience not found
        with pytest.raises(HTTPException) as exc_info:
            await router.get_audience(999, self.session)
        assert exc_info.value.status_code == 404
        assert "Audience not found" in str(exc_info.value.detail)

    async def test_update_audience(self, mock_audience):
        """Test updating an audience."""
        # Test data
        new_name = "Updated Audience"
        new_description = "Updated Description"
        new_timeframe = "week"
        new_posts_per_subreddit = 200
        new_subreddit_names = ["testsubreddit"]
        
        # Update audience
        updated = await router.update_audience(
            audience_id=mock_audience.id,
            name=new_name,
            description=new_description,
            timeframe=new_timeframe,
            posts_per_subreddit=new_posts_per_subreddit,
            subreddit_names=new_subreddit_names,
            db=self.session
        )
        
        # Verify updates
        assert updated.name == new_name
        assert updated.description == new_description
        assert updated.timeframe == new_timeframe
        assert updated.posts_per_subreddit == new_posts_per_subreddit
        assert len(updated.subreddits) == 1

    async def test_delete_audience(self, mock_audience):
        """Test deleting an audience."""
        # Delete audience
        await router.delete_audience(mock_audience.id, self.session)
        
        # Verify audience was deleted
        result = await self.session.execute(
            select(Audience).where(Audience.id == mock_audience.id)
        )
        assert result.first() is None
        
        # Verify subreddit link was deleted
        result = await self.session.execute(
            select(AudienceSubreddit).where(AudienceSubreddit.audience_id == mock_audience.id)
        )
        assert result.first() is None

        # Test deleting non-existent audience
        with pytest.raises(HTTPException) as exc_info:
            await router.delete_audience(999, self.session)
        assert exc_info.value.status_code == 404
        assert "Audience not found" in str(exc_info.value.detail) 