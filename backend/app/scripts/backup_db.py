import asyncio
import json
from datetime import datetime
from pathlib import Path

from app.core.database import AsyncSessionLocal
from app.models.subreddit import Subreddit
from sqlalchemy import select


async def backup_subreddits():
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Subreddit))
        subreddits = result.scalars().all()
        
        backup_data = [
            {
                "name": sub.name,
                "display_name": sub.display_name,
                "description": sub.description,
                "subscribers": sub.subscribers,
                "active_users": sub.active_users,
                "posts_per_day": sub.posts_per_day,
                "comments_per_day": sub.comments_per_day,
                "growth_rate": sub.growth_rate,
                "relevance_score": sub.relevance_score,
                "created_at": sub.created_at.isoformat(),
                "updated_at": sub.updated_at.isoformat(),
                "last_updated": sub.last_updated.isoformat()
            }
            for sub in subreddits
        ]
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"subreddits_backup_{timestamp}.json"
        
        with open(backup_file, "w") as f:
            json.dump(backup_data, f, indent=2)
        
        return str(backup_file)

if __name__ == "__main__":
    backup_file = asyncio.run(backup_subreddits())
    print(f"Backup created: {backup_file}") 