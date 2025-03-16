import asyncio

from app.core.config import get_settings
from app.models import RedditPost, ThemePost
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import select


async def verify_cleanup():
    """Verify that all posts have valid subreddit references."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with AsyncSession(engine) as session:
        try:
            # Check for posts with null subreddit names
            result = await session.execute(
                select(RedditPost)
                .where(RedditPost.subreddit_name.is_(None))
            )
            invalid_posts = result.scalars().all()
            
            if invalid_posts:
                print(f"Found {len(invalid_posts)} posts with null subreddit names:")
                for post in invalid_posts:
                    print(f"- Post ID {post.id}: {post.title}")
            else:
                print("No posts with null subreddit names found.")
            
            # Check for theme posts referencing non-existent posts
            result = await session.execute(
                select(ThemePost)
                .outerjoin(RedditPost, ThemePost.post_id == RedditPost.id)
                .where(RedditPost.id.is_(None))
            )
            orphaned_theme_posts = result.scalars().all()
            
            if orphaned_theme_posts:
                print(f"\nFound {len(orphaned_theme_posts)} theme posts referencing non-existent posts:")
                for theme_post in orphaned_theme_posts:
                    print(f"- Theme Post ID {theme_post.id} references missing Post ID {theme_post.post_id}")
            else:
                print("\nNo orphaned theme posts found.")
            
        except Exception as e:
            print(f"Error during verification: {str(e)}")
            raise

if __name__ == "__main__":
    asyncio.run(verify_cleanup()) 