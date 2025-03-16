import asyncio

from app.core.database import AsyncSessionLocal
from app.models import Subreddit
from sqlalchemy import desc, select


async def verify_restore():
    async with AsyncSessionLocal() as session:
        # Get top 5 subreddits by subscribers
        query = select(Subreddit).order_by(desc(Subreddit.subscribers)).limit(5)
        result = await session.execute(query)
        subreddits = result.scalars().all()
        
        print("\nTop 5 subreddits by subscribers:")
        print("-" * 80)
        print(f"{'Name':<20} {'Display Name':<20} {'Subscribers':<12} {'Active Users':<12}")
        print("-" * 80)
        for sub in subreddits:
            print(f"{sub.name:<20} {sub.display_name:<20} {sub.subscribers:<12} {sub.active_users:<12}")
        
        # Get total count
        count_query = select(Subreddit)
        result = await session.execute(count_query)
        total = len(result.scalars().all())
        print(f"\nTotal subreddits restored: {total}")

if __name__ == "__main__":
    asyncio.run(verify_restore()) 