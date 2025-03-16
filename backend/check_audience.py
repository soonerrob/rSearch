import asyncio

from app.core.database import get_session
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_audience_and_themes():
    async for session in get_session():
        session: AsyncSession
        
        # Check audience
        result = await session.execute(
            text("SELECT * FROM audiences WHERE id = 22")
        )
        audience = result.first()
        print(f"\nAudience details:")
        print(f"ID: {audience.id if audience else None}")
        print(f"Name: {audience.name if audience else None}")
        print(f"Is collecting: {audience.is_collecting if audience else None}")
        
        # Check subreddits
        result = await session.execute(
            text("SELECT subreddit_name FROM audience_subreddits WHERE audience_id = 22")
        )
        subreddits = result.scalars().all()
        print(f"\nSubreddits: {subreddits}")
        
        # Check themes
        result = await session.execute(
            text("SELECT * FROM theme WHERE audience_id = 22")
        )
        themes = result.all()
        print(f"\nThemes count: {len(themes)}")
        for theme in themes:
            print(f"Theme ID: {theme.id}, Category: {theme.category}")
        
        break  # We only need one session

async def main():
    await check_audience_and_themes()

if __name__ == "__main__":
    asyncio.run(main())
