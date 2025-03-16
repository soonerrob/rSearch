import asyncio

from app.core.database import AsyncSessionLocal, get_session
from app.models import RedditPost
from sqlalchemy import text
from sqlmodel import select


async def count_posts(subreddit_name: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(RedditPost).where(RedditPost.subreddit_name == subreddit_name)
        )
        posts = result.scalars().all()
        print(f'Number of posts for {subreddit_name}: {len(posts)}')
        for post in posts[:5]:
            print(f'- {post.title[:100]} (Score: {post.score}, Comments: {post.num_comments})')

async def check_audience(audience_id: int):
    """Check details of a specific audience"""
    async with AsyncSessionLocal() as session:
        # Get audience details
        result = await session.execute(
            text("""
            SELECT a.*, array_agg(DISTINCT as2.subreddit_name) as subreddits
            FROM audiences a
            LEFT JOIN audience_subreddits as2 ON a.id = as2.audience_id
            WHERE a.id = :audience_id
            GROUP BY a.id
            """),
            {"audience_id": audience_id}
        )
        audience = result.first()
        
        if not audience:
            print(f"Audience {audience_id} not found!")
            return
            
        print(f"\nAudience {audience_id}:")
        print(f"Name: {audience.name}")
        print(f"Description: {audience.description}")
        print(f"Subreddits: {audience.subreddits}")
        
        # Check posts for each subreddit
        if audience.subreddits[0]:  # Check if there are any subreddits
            for subreddit in audience.subreddits:
                await count_posts(subreddit)

async def main():
    # Check all audiences
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT id FROM audiences ORDER BY id")
        )
        audience_ids = [row[0] for row in result.all()]
        
        if not audience_ids:
            print("No audiences found in the database!")
            return
            
        print(f"Found {len(audience_ids)} audiences")
        for audience_id in audience_ids:
            await check_audience(audience_id)

async def check_audience_state():
    async for session in get_session():
        # Check all audiences
        result = await session.execute(text("SELECT id, name, description FROM audiences ORDER BY id"))
        print("\nCurrent Audiences:")
        print("------------------")
        for row in result:
            print(f"ID: {row.id}, Name: {row.name}, Description: {row.description}")

        # Check audience_subreddits associations
        result = await session.execute(
            text("SELECT audience_id, subreddit_name FROM audience_subreddits ORDER BY audience_id")
        )
        print("\nAudience-Subreddit Associations:")
        print("--------------------------------")
        for row in result:
            print(f"Audience ID: {row.audience_id}, Subreddit: {row.subreddit_name}")

        # Check post counts per subreddit
        result = await session.execute(
            text("""
                SELECT subreddit_name, COUNT(*) as post_count 
                FROM redditpost 
                GROUP BY subreddit_name 
                ORDER BY post_count DESC
            """)
        )
        print("\nPost Counts per Subreddit:")
        print("-------------------------")
        for row in result:
            print(f"Subreddit: {row.subreddit_name}, Posts: {row.post_count}")
        
        break

if __name__ == "__main__":
    asyncio.run(check_audience_state()) 