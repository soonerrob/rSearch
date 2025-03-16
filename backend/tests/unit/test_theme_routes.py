import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.cancellation import CancellationScope, CancellationToken
from app.models import Audience, Theme, ThemePost, ThemeQuestion
from app.routers.themes import router
from fastapi import HTTPException


@pytest.mark.asyncio
class TestThemeRoutes:
    """Test suite for theme routes."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, async_session):
        """Setup test fixtures."""
        self.session = await anext(async_session)

    @pytest_asyncio.fixture
    async def mock_audience(self):
        """Create a mock audience for testing."""
        audience = Audience(
            name="Test Audience",
            timeframe="day",
            collection_progress=0.0,
            is_collecting=False
        )
        self.session.add(audience)
        await self.session.commit()
        return audience

    @pytest_asyncio.fixture
    async def mock_theme(self, mock_audience):
        """Create a mock theme for testing."""
        theme = Theme(
            audience_id=mock_audience.id,
            category="Test Category",
            summary="Test Summary",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(theme)
        await self.session.commit()
        return theme

    async def test_get_audience_themes(self, mock_audience, mock_theme):
        """Test getting themes for an audience."""
        # Test normal operation
        themes = await router.get_audience_themes(mock_audience.id, self.session)
        assert len(themes) == 1
        assert themes[0].id == mock_theme.id
        assert themes[0].category == "Test Category"

        # Test audience not found
        with pytest.raises(HTTPException) as exc_info:
            await router.get_audience_themes(999, self.session)
        assert exc_info.value.status_code == 404
        assert "Audience not found" in str(exc_info.value.detail)

        # Test audience is collecting
        mock_audience.is_collecting = True
        await self.session.commit()
        with pytest.raises(HTTPException) as exc_info:
            await router.get_audience_themes(mock_audience.id, self.session)
        assert exc_info.value.status_code == 202
        assert "Initial data collection is in progress" in str(exc_info.value.detail)

    async def test_request_theme_refresh(self, mock_audience, mock_theme):
        """Test refreshing themes for an audience."""
        # Create a mock theme question
        question = ThemeQuestion(
            theme_id=mock_theme.id,
            question="Test Question",
            answer=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(question)
        await self.session.commit()

        # Test normal operation
        async with CancellationScope() as token:
            themes = await router.request_theme_refresh(mock_audience.id, None, self.session)
            assert len(themes) > 0
            assert all(isinstance(theme, Theme) for theme in themes)
            assert all(theme.category for theme in themes)
            assert all(theme.summary for theme in themes)

            # Verify old theme was deleted and question was updated
            old_theme = await self.session.get(Theme, mock_theme.id)
            assert old_theme is None

            # Verify question was updated to point to new theme
            questions = await self.session.execute(
                select(ThemeQuestion).where(ThemeQuestion.theme_id.in_([t.id for t in themes]))
            )
            questions = questions.scalars().all()
            assert len(questions) == 1
            assert questions[0].question == "Test Question"

        # Test audience not found
        with pytest.raises(HTTPException) as exc_info:
            await router.request_theme_refresh(999, None, self.session)
        assert exc_info.value.status_code == 404
        assert "Audience not found" in str(exc_info.value.detail)

        # Test audience is collecting
        mock_audience.is_collecting = True
        await self.session.commit()
        with pytest.raises(HTTPException) as exc_info:
            await router.request_theme_refresh(mock_audience.id, None, self.session)
        assert exc_info.value.status_code == 202
        assert "Initial data collection is in progress" in str(exc_info.value.detail)

        # Test cancellation
        mock_audience.is_collecting = False
        await self.session.commit()
        token = CancellationToken()
        token.cancel()
        with pytest.raises(HTTPException) as exc_info:
            async with CancellationScope(token):
                await router.request_theme_refresh(mock_audience.id, None, self.session)
        assert exc_info.value.status_code == 499
        assert "Operation cancelled" in str(exc_info.value.detail) 