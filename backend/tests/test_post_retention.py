import pytest
from app.models import (Audience, AudienceSubreddit, RedditPost, Subreddit,
                        Theme, ThemePost)
from app.schemas.audience import AudienceUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import delete, select


@pytest.mark.asyncio
class TestPostRetention:
    """Test suite for post retention logic."""

    async def test_delete_audience_with_shared_subreddit(self, session: AsyncSession):
        """Test that posts are retained when a subreddit is shared between audiences."""
        # Create two audiences
        audience1 = Audience(name="Test Audience 1", timeframe="year", posts_per_subreddit=100)
        audience2 = Audience(name="Test Audience 2", timeframe="year", posts_per_subreddit=100)
        session.add(audience1)
        session.add(audience2)
        await session.commit()

        # Create the subreddit first if it doesn't exist
        shared_subreddit = "python"
        result = await session.execute(
            select(Subreddit).where(Subreddit.name == shared_subreddit)
        )
        subreddit = result.scalar_one_or_none()
        if not subreddit:
            subreddit = Subreddit(
                name=shared_subreddit,
                display_name="Python",
                description="Python programming language community",
                subscribers=100000,
                active_users=1000
            )
            session.add(subreddit)
            await session.commit()

        # Add same subreddit to both audiences
        audience1_subreddit = AudienceSubreddit(audience_id=audience1.id, subreddit_name=shared_subreddit)
        audience2_subreddit = AudienceSubreddit(audience_id=audience2.id, subreddit_name=shared_subreddit)
        session.add(audience1_subreddit)
        session.add(audience2_subreddit)
        await session.commit()

        # Create some posts for the shared subreddit
        posts = [
            RedditPost(
                reddit_id=f"post{i}",
                subreddit_name=shared_subreddit,
                title=f"Test Post {i}",
                content="Test content",
                author="test_author",
                score=100,
                num_comments=10
            )
            for i in range(3)
        ]
        for post in posts:
            session.add(post)
        await session.commit()

        # Delete audience1
        # Get the audience with its subreddits
        result = await session.execute(
            select(Audience)
            .where(Audience.id == audience1.id)
        )
        audience = result.scalar_one_or_none()
        
        if not audience:
            raise ValueError("Audience not found")
        
        # Get all subreddit names for this audience
        result = await session.execute(
            select(AudienceSubreddit).where(AudienceSubreddit.audience_id == audience1.id)
        )
        subreddits = result.scalars().all()
        subreddit_names = [s.subreddit_name for s in subreddits]
        
        # For each subreddit, check if it's used by other audiences
        for subreddit_name in subreddit_names:
            # Check if subreddit is used by other audiences
            result = await session.execute(
                select(AudienceSubreddit)
                .where(
                    (AudienceSubreddit.subreddit_name == subreddit_name) &
                    (AudienceSubreddit.audience_id != audience1.id)
                )
            )
            other_audience_uses = result.first() is not None
            
            # Only delete posts if subreddit is not used by other audiences
            if not other_audience_uses:
                # Get posts from this subreddit
                result = await session.execute(
                    select(RedditPost.id).where(RedditPost.subreddit_name == subreddit_name)
                )
                post_ids = [post_id for post_id, in result.all()]
                
                if post_ids:
                    # Delete theme_posts entries that reference these posts
                    await session.execute(
                        delete(ThemePost).where(ThemePost.post_id.in_(post_ids))
                    )
                    
                    # Then delete the posts themselves
                    await session.execute(
                        delete(RedditPost).where(RedditPost.id.in_(post_ids))
                    )
        
        # Delete all theme posts associated with themes of this audience
        await session.execute(
            delete(ThemePost).where(
                ThemePost.theme_id.in_(
                    select(Theme.id).where(Theme.audience_id == audience1.id)
                )
            )
        )
        
        # Delete all themes associated with this audience
        await session.execute(
            delete(Theme).where(Theme.audience_id == audience1.id)
        )
        
        # Delete all audience_subreddits associations
        await session.execute(
            delete(AudienceSubreddit).where(
                AudienceSubreddit.audience_id == audience1.id
            )
        )
        
        # Finally delete the audience
        await session.delete(audience)
        await session.commit()

        # Verify posts still exist since subreddit is used by audience2
        result = await session.execute(
            select(RedditPost).where(RedditPost.subreddit_name == shared_subreddit)
        )
        remaining_posts = result.scalars().all()
        assert len(remaining_posts) == 3, "Posts should be retained when subreddit is shared"

        # Verify audience1 was deleted
        result = await session.execute(
            select(Audience).where(Audience.id == audience1.id)
        )
        assert result.first() is None, "Audience1 should be deleted"

        # Verify audience2 and its association still exist
        result = await session.execute(
            select(AudienceSubreddit).where(AudienceSubreddit.audience_id == audience2.id)
        )
        assert result.first() is not None, "Audience2's subreddit association should remain"

    async def test_delete_audience_with_unique_subreddit(self, session: AsyncSession):
        """Test that posts are deleted when a subreddit is unique to an audience."""
        # Create an audience
        audience = Audience(name="Test Audience", timeframe="year", posts_per_subreddit=100)
        session.add(audience)
        await session.commit()

        # Create the subreddit first if it doesn't exist
        unique_subreddit = "unique_python_test"
        result = await session.execute(
            select(Subreddit).where(Subreddit.name == unique_subreddit)
        )
        subreddit = result.scalar_one_or_none()
        if not subreddit:
            subreddit = Subreddit(
                name=unique_subreddit,
                display_name="Unique Python Test",
                description="Test subreddit",
                subscribers=100,
                active_users=10
            )
            session.add(subreddit)
            await session.commit()

        # Add a unique subreddit
        audience_subreddit = AudienceSubreddit(audience_id=audience.id, subreddit_name=unique_subreddit)
        session.add(audience_subreddit)
        await session.commit()

        # Create some posts for the unique subreddit
        posts = [
            RedditPost(
                reddit_id=f"unique_post{i}",
                subreddit_name=unique_subreddit,
                title=f"Test Post {i}",
                content="Test content",
                author="test_author",
                score=100,
                num_comments=10
            )
            for i in range(3)
        ]
        for post in posts:
            session.add(post)
        await session.commit()

        # Delete the audience
        # Get the audience with its subreddits
        result = await session.execute(
            select(Audience)
            .where(Audience.id == audience.id)
        )
        audience = result.scalar_one_or_none()
        
        if not audience:
            raise ValueError("Audience not found")
        
        # Get all subreddit names for this audience
        result = await session.execute(
            select(AudienceSubreddit).where(AudienceSubreddit.audience_id == audience.id)
        )
        subreddits = result.scalars().all()
        subreddit_names = [s.subreddit_name for s in subreddits]
        
        # For each subreddit, check if it's used by other audiences
        for subreddit_name in subreddit_names:
            # Check if subreddit is used by other audiences
            result = await session.execute(
                select(AudienceSubreddit)
                .where(
                    (AudienceSubreddit.subreddit_name == subreddit_name) &
                    (AudienceSubreddit.audience_id != audience.id)
                )
            )
            other_audience_uses = result.first() is not None
            
            # Only delete posts if subreddit is not used by other audiences
            if not other_audience_uses:
                # Get posts from this subreddit
                result = await session.execute(
                    select(RedditPost.id).where(RedditPost.subreddit_name == subreddit_name)
                )
                post_ids = [post_id for post_id, in result.all()]
                
                if post_ids:
                    # Delete theme_posts entries that reference these posts
                    await session.execute(
                        delete(ThemePost).where(ThemePost.post_id.in_(post_ids))
                    )
                    
                    # Then delete the posts themselves
                    await session.execute(
                        delete(RedditPost).where(RedditPost.id.in_(post_ids))
                    )
        
        # Delete all theme posts associated with themes of this audience
        await session.execute(
            delete(ThemePost).where(
                ThemePost.theme_id.in_(
                    select(Theme.id).where(Theme.audience_id == audience.id)
                )
            )
        )
        
        # Delete all themes associated with this audience
        await session.execute(
            delete(Theme).where(Theme.audience_id == audience.id)
        )
        
        # Delete all audience_subreddits associations
        await session.execute(
            delete(AudienceSubreddit).where(
                AudienceSubreddit.audience_id == audience.id
            )
        )
        
        # Finally delete the audience
        await session.delete(audience)
        await session.commit()

        # Verify posts were deleted since subreddit was unique to this audience
        result = await session.execute(
            select(RedditPost).where(RedditPost.subreddit_name == unique_subreddit)
        )
        remaining_posts = result.scalars().all()
        assert len(remaining_posts) == 0, "Posts should be deleted when subreddit is unique to deleted audience"

    async def test_remove_subreddit_from_audience(self, session: AsyncSession):
        """Test that posts are retained when removing a subreddit that exists in another audience."""
        # Clean up any existing posts for the python subreddit
        await session.execute(
            delete(RedditPost).where(RedditPost.subreddit_name == "python")
        )
        await session.commit()

        # Create two audiences
        audience1 = Audience(name="Test Audience 1", timeframe="year", posts_per_subreddit=100)
        audience2 = Audience(name="Test Audience 2", timeframe="year", posts_per_subreddit=100)
        session.add(audience1)
        session.add(audience2)
        await session.commit()

        # Create the subreddit first if it doesn't exist
        shared_subreddit = "python"
        result = await session.execute(
            select(Subreddit).where(Subreddit.name == shared_subreddit)
        )
        subreddit = result.scalar_one_or_none()
        if not subreddit:
            subreddit = Subreddit(
                name=shared_subreddit,
                display_name="Python",
                description="Python programming language community",
                subscribers=100000,
                active_users=1000
            )
            session.add(subreddit)
            await session.commit()

        # Add shared subreddit to both audiences
        audience1_subreddit = AudienceSubreddit(audience_id=audience1.id, subreddit_name=shared_subreddit)
        audience2_subreddit = AudienceSubreddit(audience_id=audience2.id, subreddit_name=shared_subreddit)
        session.add(audience1_subreddit)
        session.add(audience2_subreddit)
        await session.commit()

        # Create some posts
        posts = [
            RedditPost(
                reddit_id=f"shared_post{i}",
                subreddit_name=shared_subreddit,
                title=f"Test Post {i}",
                content="Test content",
                author="test_author",
                score=100,
                num_comments=10
            )
            for i in range(3)
        ]
        for post in posts:
            session.add(post)
        await session.commit()

        # Remove subreddit from audience1
        # Get current subreddit names before update
        result = await session.execute(
            select(AudienceSubreddit).where(AudienceSubreddit.audience_id == audience1.id)
        )
        current_subreddits = result.scalars().all()
        current_subreddit_names = {s.subreddit_name for s in current_subreddits}
        
        # Get new subreddit names as a set (empty in this case)
        new_subreddit_names = set()
        
        # Find subreddits that were removed
        removed_subreddit_names = current_subreddit_names - new_subreddit_names
        
        # Delete posts from removed subreddits
        if removed_subreddit_names:
            # For each removed subreddit, check if it's used by other audiences
            for subreddit_name in removed_subreddit_names:
                # Check if subreddit is used by other audiences
                result = await session.execute(
                    select(AudienceSubreddit)
                    .where(
                        (AudienceSubreddit.subreddit_name == subreddit_name) &
                        (AudienceSubreddit.audience_id != audience1.id)
                    )
                )
                other_audience_uses = result.first() is not None
                
                # Only delete posts if subreddit is not used by other audiences
                if not other_audience_uses:
                    # Get posts from this subreddit
                    result = await session.execute(
                        select(RedditPost.id).where(RedditPost.subreddit_name == subreddit_name)
                    )
                    post_ids = [post_id for post_id, in result.all()]
                    
                    if post_ids:
                        # Delete theme_posts entries that reference these posts
                        await session.execute(
                            delete(ThemePost).where(ThemePost.post_id.in_(post_ids))
                        )
                        
                        # Then delete the posts themselves
                        await session.execute(
                            delete(RedditPost).where(RedditPost.id.in_(post_ids))
                        )
            
            # Get all theme IDs for this audience
            result = await session.execute(
                select(Theme.id).where(Theme.audience_id == audience1.id)
            )
            theme_ids = [theme_id for theme_id, in result.all()]
            
            if theme_ids:
                # Delete theme posts
                await session.execute(
                    delete(ThemePost).where(ThemePost.theme_id.in_(theme_ids))
                )
                
                # Delete the themes
                await session.execute(
                    delete(Theme).where(Theme.id.in_(theme_ids))
                )
        
        # Remove existing audience-subreddit associations
        await session.execute(
            delete(AudienceSubreddit).where(AudienceSubreddit.audience_id == audience1.id)
        )
        
        await session.commit()

        # Verify posts still exist since subreddit is used by audience2
        result = await session.execute(
            select(RedditPost).where(RedditPost.subreddit_name == shared_subreddit)
        )
        remaining_posts = result.scalars().all()
        assert len(remaining_posts) == 3, "Posts should be retained when subreddit is still used by another audience"

        # Verify audience1's association was removed
        result = await session.execute(
            select(AudienceSubreddit).where(AudienceSubreddit.audience_id == audience1.id)
        )
        assert result.first() is None, "Audience1's subreddit association should be removed"

        # Verify audience2's association still exists
        result = await session.execute(
            select(AudienceSubreddit).where(AudienceSubreddit.audience_id == audience2.id)
        )
        assert result.first() is not None, "Audience2's subreddit association should remain"

    async def test_theme_cleanup_on_subreddit_removal(self, session: AsyncSession):
        """Test that themes and theme posts are properly cleaned up when removing a subreddit."""
        # Create an audience
        audience = Audience(name="Test Audience", timeframe="year", posts_per_subreddit=100)
        session.add(audience)
        await session.commit()

        # Create the subreddit first if it doesn't exist
        subreddit_name = "python"
        result = await session.execute(
            select(Subreddit).where(Subreddit.name == subreddit_name)
        )
        subreddit = result.scalar_one_or_none()
        if not subreddit:
            subreddit = Subreddit(
                name=subreddit_name,
                display_name="Python",
                description="Python programming language community",
                subscribers=100000,
                active_users=1000
            )
            session.add(subreddit)
            await session.commit()

        # Add a subreddit
        audience_subreddit = AudienceSubreddit(audience_id=audience.id, subreddit_name=subreddit_name)
        session.add(audience_subreddit)
        await session.commit()

        # Create some posts
        posts = [
            RedditPost(
                reddit_id=f"theme_cleanup_post{i}",
                subreddit_name=subreddit_name,
                title=f"Test Post {i}",
                content="Test content",
                author="test_author",
                score=100,
                num_comments=10
            )
            for i in range(3)
        ]
        for post in posts:
            session.add(post)
        await session.commit()

        # Create a theme and theme posts
        theme = Theme(
            audience_id=audience.id,
            category="Test Category",
            summary="Test Summary"
        )
        session.add(theme)
        await session.commit()

        theme_posts = [
            ThemePost(theme_id=theme.id, post_id=post.id, relevance_score=0.8)
            for post in posts
        ]
        for theme_post in theme_posts:
            session.add(theme_post)
        await session.commit()

        # Remove the subreddit from the audience
        # Get current subreddit names before update
        result = await session.execute(
            select(AudienceSubreddit).where(AudienceSubreddit.audience_id == audience.id)
        )
        current_subreddits = result.scalars().all()
        current_subreddit_names = {s.subreddit_name for s in current_subreddits}
        
        # Get new subreddit names as a set (empty in this case)
        new_subreddit_names = set()
        
        # Find subreddits that were removed
        removed_subreddit_names = current_subreddit_names - new_subreddit_names
        
        # Delete posts from removed subreddits
        if removed_subreddit_names:
            # For each removed subreddit, check if it's used by other audiences
            for subreddit_name in removed_subreddit_names:
                # Check if subreddit is used by other audiences
                result = await session.execute(
                    select(AudienceSubreddit)
                    .where(
                        (AudienceSubreddit.subreddit_name == subreddit_name) &
                        (AudienceSubreddit.audience_id != audience.id)
                    )
                )
                other_audience_uses = result.first() is not None
                
                # Only delete posts if subreddit is not used by other audiences
                if not other_audience_uses:
                    # Get posts from this subreddit
                    result = await session.execute(
                        select(RedditPost.id).where(RedditPost.subreddit_name == subreddit_name)
                    )
                    post_ids = [post_id for post_id, in result.all()]
                    
                    if post_ids:
                        # Delete theme_posts entries that reference these posts
                        await session.execute(
                            delete(ThemePost).where(ThemePost.post_id.in_(post_ids))
                        )
                        
                        # Then delete the posts themselves
                        await session.execute(
                            delete(RedditPost).where(RedditPost.id.in_(post_ids))
                        )
            
            # Get all theme IDs for this audience
            result = await session.execute(
                select(Theme.id).where(Theme.audience_id == audience.id)
            )
            theme_ids = [theme_id for theme_id, in result.all()]
            
            if theme_ids:
                # Delete theme posts
                await session.execute(
                    delete(ThemePost).where(ThemePost.theme_id.in_(theme_ids))
                )
                
                # Delete the themes
                await session.execute(
                    delete(Theme).where(Theme.id.in_(theme_ids))
                )
        
        # Remove existing audience-subreddit associations
        await session.execute(
            delete(AudienceSubreddit).where(AudienceSubreddit.audience_id == audience.id)
        )
        
        await session.commit()

        # Verify theme posts were deleted
        result = await session.execute(
            select(ThemePost).where(ThemePost.theme_id == theme.id)
        )
        remaining_theme_posts = result.scalars().all()
        assert len(remaining_theme_posts) == 0, "Theme posts should be deleted when removing subreddit"

        # Verify theme was deleted
        result = await session.execute(
            select(Theme).where(Theme.id == theme.id)
        )
        assert result.first() is None, "Theme should be deleted when removing subreddit" 