import asyncio

from app.core.database import get_session
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_posts():
    async for session in get_session():
        session: AsyncSession
        
        # Get subreddit names for audience 22
        result = await session.execute(
            text("SELECT subreddit_name FROM audience_subreddits WHERE audience_id = 22")
        )
        subreddits = result.scalars().all()
        
        # Check post counts for each subreddit
        print("\nPost counts by subreddit:")
        for subreddit in subreddits:
            result = await session.execute(
                text(f"""
                    SELECT COUNT(*) as post_count
                    FROM redditpost
                    WHERE subreddit_name = :subreddit
                """),
                {"subreddit": subreddit}
            )
            count = result.scalar()
            print(f"{subreddit}: {count} posts")
            
            # Show sample of recent posts
            result = await session.execute(
                text(f"""
                    SELECT id, title, score, num_comments, created_at
                    FROM redditpost
                    WHERE subreddit_name = :subreddit
                    ORDER BY created_at DESC
                    LIMIT 3
                """),
                {"subreddit": subreddit}
            )
            posts = result.all()
            if posts:
                print("Recent posts:")
                for post in posts:
                    print(f"  - {post[1]} (Score: {post[2]}, Comments: {post[3]})")
            print("---")
        
        break  # We only need one session

async def main():
    await check_posts()

if __name__ == "__main__":
    asyncio.run(main()) 