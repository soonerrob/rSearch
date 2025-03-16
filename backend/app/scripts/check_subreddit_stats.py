import asyncio
from datetime import datetime

from app.core.config import get_settings
from app.services.reddit import RedditService
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


async def check_subreddit_stats():
    """Check statistics for specified subreddits."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with AsyncSession(engine) as session:
        reddit_service = RedditService(session)
        subreddits = ['dog_puppytraining', 'dog_training_grooming', 'dogtraining']
        
        for name in subreddits:
            sub = await reddit_service.reddit.subreddit(name)
            await sub.load()
            created_date = datetime.fromtimestamp(sub.created_utc).strftime('%Y-%m-%d')
            
            print(f'\nr/{name} stats:')
            print(f'- Subscribers: {sub.subscribers:,}')
            print(f'- Active users now: {sub.active_user_count:,}')
            print(f'- Created: {created_date}')
            print(f'- Description: {sub.public_description[:200] + "..." if len(sub.public_description) > 200 else sub.public_description}')
            
            # Get recent activity
            print('\nRecent activity:')
            new_posts = []
            async for post in sub.new(limit=100):
                new_posts.append(post)
            
            if new_posts:
                newest_post = new_posts[0]
                oldest_post = new_posts[-1]
                newest_date = datetime.fromtimestamp(newest_post.created_utc)
                oldest_date = datetime.fromtimestamp(oldest_post.created_utc)
                days_span = (newest_date - oldest_date).days
                posts_per_day = len(new_posts) / max(1, days_span) if days_span > 0 else len(new_posts)
                
                print(f'- Posts per day (based on last 100 posts): {posts_per_day:.1f}')
                print(f'- Most recent post: {newest_date.strftime("%Y-%m-%d %H:%M:%S")}')

if __name__ == "__main__":
    asyncio.run(check_subreddit_stats()) 