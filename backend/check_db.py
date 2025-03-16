import asyncio

from app.core.database import get_session
from sqlalchemy import text


async def check_db():
    async for session in get_session():
        # Check audience with explicit column names
        result = await session.execute(
            text("""
                SELECT id, name, description, timeframe, posts_per_subreddit,
                       is_collecting, collection_progress, created_at, updated_at
                FROM audiences WHERE id = 22
            """)
        )
        audience = result.first()
        if audience:
            print("\nAudience details:")
            print(f"ID: {audience[0]}")
            print(f"Name: {audience[1]}")
            print(f"Description: {audience[2]}")
            print(f"Timeframe: {audience[3]}")
            print(f"Posts per subreddit: {audience[4]}")
            print(f"Is collecting: {audience[5]}")
            print(f"Collection progress: {audience[6]}")
            print(f"Created at: {audience[7]}")
            print(f"Updated at: {audience[8]}")
        else:
            print("\nNo audience found with ID 22")
        
        # Check subreddits
        result = await session.execute(
            text("""
                SELECT s.name, s.subscribers, s.active_users, a.added_at
                FROM audience_subreddits a
                JOIN subreddits s ON s.name = a.subreddit_name
                WHERE a.audience_id = 22
            """)
        )
        subreddits = result.all()
        print("\nSubreddits:")
        for subreddit in subreddits:
            print(f"Name: {subreddit[0]}")
            print(f"Subscribers: {subreddit[1]}")
            print(f"Active users: {subreddit[2]}")
            print(f"Added at: {subreddit[3]}")
            print("---")
        
        # Check themes
        result = await session.execute(
            text("""
                SELECT id, category, summary, created_at, updated_at
                FROM theme WHERE audience_id = 22
                ORDER BY created_at DESC
            """)
        )
        themes = result.all()
        print("\nThemes:")
        if themes:
            for theme in themes:
                print(f"ID: {theme[0]}")
                print(f"Category: {theme[1]}")
                print(f"Summary: {theme[2]}")
                print(f"Created at: {theme[3]}")
                print(f"Updated at: {theme[4]}")
                print("---")
        else:
            print("No themes found")
        break

if __name__ == '__main__':
    asyncio.run(check_db())
