import asyncio
from datetime import datetime

from app.core.config import get_settings
from app.models import Audience, RedditPost, Theme, ThemePost
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import delete, select


async def refresh_audience_data(audience_id: int):
    """Refresh data for a specific audience."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with AsyncSession(engine) as session:
        try:
            # Get the audience
            result = await session.execute(
                select(Audience).where(Audience.id == audience_id)
            )
            audience = result.scalar_one_or_none()
            if not audience:
                print(f"Audience {audience_id} not found")
                return
            
            # Delete existing theme posts
            result = await session.execute(
                select(Theme.id).where(Theme.audience_id == audience_id)
            )
            theme_ids = [theme_id for theme_id, in result.all()]
            
            if theme_ids:
                # Delete theme posts
                await session.execute(
                    delete(ThemePost).where(ThemePost.theme_id.in_(theme_ids))
                )
                print(f"Deleted theme posts for audience {audience_id}")
                
                # Delete themes
                await session.execute(
                    delete(Theme).where(Theme.id.in_(theme_ids))
                )
                print(f"Deleted themes for audience {audience_id}")
            
            # Delete posts
            subreddit_names = [s.subreddit_name for s in audience.subreddits]
            await session.execute(
                delete(RedditPost).where(RedditPost.subreddit_name.in_(subreddit_names))
            )
            print(f"Deleted posts for audience {audience_id}")
            
            # Update audience
            audience.updated_at = datetime.utcnow()
            audience.is_collecting = False
            audience.collection_progress = 0.0
            
            await session.commit()
            print(f"Successfully refreshed data for audience {audience_id}")
            
        except Exception as e:
            await session.rollback()
            print(f"Error refreshing audience {audience_id}: {str(e)}")
            raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python refresh_audience_data.py <audience_id>")
        sys.exit(1)
        
    audience_id = int(sys.argv[1])
    asyncio.run(refresh_audience_data(audience_id)) 