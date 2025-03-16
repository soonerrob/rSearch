import asyncio

from app.core.database import AsyncSessionLocal
from app.models import AudienceSubreddit
from sqlmodel import select


async def get_shared():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(AudienceSubreddit))
        subreddits = result.scalars().all()
        
        shared = {}
        for s in subreddits:
            if s.subreddit_name not in shared:
                shared[s.subreddit_name] = []
            shared[s.subreddit_name].append(s.audience_id)
        
        print('Shared subreddits:')
        print({k: v for k, v in shared.items() if len(v) > 1})

if __name__ == "__main__":
    asyncio.run(get_shared()) 