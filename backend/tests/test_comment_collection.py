from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.models.comment import Comment
from app.models.post import Post
from app.services.comment_service import (CommentCollectionConfig,
                                          collect_comments_for_post,
                                          update_comments)
from sqlmodel.ext.asyncio.session import AsyncSession


class MockRedditComment:
    def __init__(
        self,
        id: str,
        content: str,
        author: str,
        score: int,
        edited: bool = False,
        awards: int = 0,
        replies: list = None
    ):
        self.id = id
        self.content = content
        self.author = author
        self.score = score
        self.edited = edited
        self.awards = awards
        self.replies = replies or []


@pytest.fixture
def mock_reddit_client():
    client = AsyncMock()
    
    # Mock top-level comments
    comments = [
        MockRedditComment(
            id="comment1",
            content="High quality comment",
            author="user1",
            score=100,
            awards=2,
            replies=[
                MockRedditComment(
                    id="reply1",
                    content="Good reply",
                    author="user2",
                    score=50
                ),
                MockRedditComment(
                    id="reply2",
                    content="Low score reply",
                    author="user3",
                    score=2
                )
            ]
        ),
        MockRedditComment(
            id="comment2",
            content="Too short",
            author="user4",
            score=80
        ),
        MockRedditComment(
            id="comment3",
            content="Another good comment with sufficient length",
            author="user5",
            score=60,
            edited=True
        )
    ]
    
    client.get_post_comments = AsyncMock(return_value=comments)
    client.get_comment = AsyncMock(
        return_value=MockRedditComment(
            id="comment1",
            content="Updated content",
            author="user1",
            score=150,
            awards=3,
            edited=True
        )
    )
    
    return client


@pytest.fixture
async def test_post(session: AsyncSession):
    post = Post(
        reddit_id="test_post",
        title="Test Post",
        content="Test Content",
        score=100,
        subreddit_name="test_subreddit"
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


@pytest.mark.asyncio
async def test_collect_comments_basic(
    session: AsyncSession,
    mock_reddit_client,
    test_post
):
    """Test basic comment collection with default config"""
    config = CommentCollectionConfig(
        limit_top=2,
        limit_replies=1,
        min_score=5,
        min_length=10
    )
    
    comments = await collect_comments_for_post(
        test_post.reddit_id,
        session,
        mock_reddit_client,
        config
    )
    
    # Should collect 2 top comments (skipping the short one) and 1 reply
    assert len(comments) == 3
    
    # Verify top comment
    top_comment = next(c for c in comments if c.reddit_id == "comment1")
    assert top_comment.score == 100
    assert top_comment.level == 0
    assert top_comment.awards_received == 2
    
    # Verify reply
    reply = next(c for c in comments if c.reddit_id == "reply1")
    assert reply.score == 50
    assert reply.level == 1
    assert reply.parent_id == "comment1"


@pytest.mark.asyncio
async def test_comment_filtering(
    session: AsyncSession,
    mock_reddit_client,
    test_post
):
    """Test comment filtering based on score and length"""
    config = CommentCollectionConfig(
        limit_top=10,
        limit_replies=5,
        min_score=70,  # Should filter out comment3
        min_length=15  # Should filter out comment2
    )
    
    comments = await collect_comments_for_post(
        test_post.reddit_id,
        session,
        mock_reddit_client,
        config
    )
    
    # Should only collect comment1 and its reply
    assert len(comments) == 2
    collected_ids = {c.reddit_id for c in comments}
    assert "comment1" in collected_ids
    assert "reply1" in collected_ids
    assert "comment2" not in collected_ids  # Too short
    assert "comment3" not in collected_ids  # Score too low


@pytest.mark.asyncio
async def test_update_comments(
    session: AsyncSession,
    mock_reddit_client,
    test_post
):
    """Test updating existing comments"""
    # First create a comment
    comment = Comment(
        reddit_id="comment1",
        content="Original content",
        author="user1",
        score=100,
        post_id=test_post.id,
        last_updated=datetime.utcnow() - timedelta(hours=25)
    )
    session.add(comment)
    await session.commit()
    
    # Update comments
    updated = await update_comments(
        test_post.reddit_id,
        session,
        mock_reddit_client
    )
    
    assert len(updated) == 1
    updated_comment = updated[0]
    assert updated_comment.content == "Updated content"
    assert updated_comment.score == 150
    assert updated_comment.awards_received == 3
    assert updated_comment.is_edited is True


@pytest.mark.asyncio
async def test_update_comments_respects_age(
    session: AsyncSession,
    mock_reddit_client,
    test_post
):
    """Test that comment updates respect minimum age"""
    # Create a recently updated comment
    comment = Comment(
        reddit_id="comment1",
        content="Original content",
        author="user1",
        score=100,
        post_id=test_post.id,
        last_updated=datetime.utcnow() - timedelta(hours=1)  # Updated 1 hour ago
    )
    session.add(comment)
    await session.commit()
    
    # Try to update comments
    updated = await update_comments(
        test_post.reddit_id,
        session,
        mock_reddit_client,
        min_age_hours=24
    )
    
    # Should not update because comment is too recent
    assert len(updated) == 0
    
    # Verify comment wasn't changed
    await session.refresh(comment)
    assert comment.content == "Original content"
    assert comment.score == 100 