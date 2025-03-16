import asyncio

from app.core.config import get_settings
from app.models import RedditPost, ThemePost
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import delete, select


async def cleanup_removed_subreddit_posts():
    """Clean up posts from removed subreddits."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with AsyncSession(engine) as session:
        try:
            # Get all posts from removed subreddits
            result = await session.execute(
                select(RedditPost.id)
                .where(RedditPost.subreddit_name.is_(None))
            )
            post_ids = [post_id for post_id, in result.all()]
            
            if not post_ids:
                print("No posts from removed subreddits found.")
                return
            
            print(f"Found {len(post_ids)} posts from removed subreddits.")
            
            # Delete theme_posts entries that reference these posts
            await session.execute(
                delete(ThemePost).where(ThemePost.post_id.in_(post_ids))
            )
            
            # Delete the posts themselves
            await session.execute(
                delete(RedditPost).where(RedditPost.id.in_(post_ids))
            )
            
            await session.commit()
            print("Successfully cleaned up posts from removed subreddits.")
            
        except Exception as e:
            await session.rollback()
            print(f"Error cleaning up posts: {str(e)}")
            raise

if __name__ == "__main__":
    asyncio.run(cleanup_removed_subreddit_posts()) 